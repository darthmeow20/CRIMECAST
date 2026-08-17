# -*- coding: utf-8 -*-
"""
CRIMECAST — per-district word clouds from news headlines (English + Tamil).

Simple design (on purpose):
  • Tokenize Latin + Tamil script from headlines
  • Balance EN/TA so both show up
  • Draw with Pillow + Nirmala / Noto (local TTF — not browser fonts)
  • Image is two columns: English | Tamil  (no □ boxes, no random overlap mess)
"""
from __future__ import annotations

import io
import os
import re
import shutil
import sys
import urllib.request
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent
_FONTS_DIR = _ROOT / "assets" / "fonts"

_NOTO_URLS = (
    "https://notofonts.github.io/tamil/fonts/NotoSansTamil/full/ttf/NotoSansTamil-Regular.ttf",
)
_FONT_MAGIC = (b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf")
_PROBE_TA = "கைது"
_PROBE_EN = "Police"

_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are", "was",
    "were", "be", "been", "with", "by", "at", "from", "as", "that", "this", "it",
    "its", "their", "his", "her", "they", "he", "she", "we", "you", "i", "not",
    "has", "have", "had", "will", "would", "can", "could", "should", "may", "also",
    "after", "before", "over", "under", "into", "about", "than", "then", "when",
    "who", "what", "which", "while", "where", "how", "all", "any", "more", "most",
    "some", "such", "no", "nor", "only", "own", "same", "so", "too", "very",
    "just", "but", "if", "out", "up", "down", "new", "said", "says", "report",
    "news", "today", "tamil", "nadu", "india", "indian", "district", "city",
    "https", "http", "www", "com", "html", "amp",
    "dinamalar", "dinamani", "thanthi", "vikatan", "hindu", "times", "express",
    "etv", "bharat", "ndtv", "polimer",
    "ஒரு", "மற்றும்", "இந்த", "அந்த", "என்று", "உள்ள", "ஆனால்", "போன்ற",
    "இல்", "க்கு", "கள்", "ஆக", "என", "வேண்டும்",
}

# English words (3+) OR Tamil runs (2+)
_TOKEN_RE = re.compile(r"[A-Za-z]{3,}|[\u0B80-\u0BFF]{2,}")
_TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")


# ---------------------------------------------------------------------------
# Language helpers
# ---------------------------------------------------------------------------

def has_tamil(text: str) -> bool:
    return bool(text and _TAMIL_RE.search(str(text)))


def is_english_token(word: str) -> bool:
    return bool(word and re.fullmatch(r"[A-Za-z][A-Za-z'-]*", str(word)))


def is_tamil_token(word: str) -> bool:
    s = str(word or "")
    return bool(s) and bool(_TAMIL_RE.search(s)) and not re.search(r"[A-Za-z]", s)


def token_lang(word: str) -> str:
    if is_tamil_token(word):
        return "ta"
    if is_english_token(word):
        return "en"
    return "other"


# ---------------------------------------------------------------------------
# Font (Nirmala preferred — full English + Tamil)
# ---------------------------------------------------------------------------

def _is_font_file(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size < 10_000:
            return False
        return path.read_bytes()[:4] in _FONT_MAGIC
    except OSError:
        return False


def _pil_font(path: str | Path, size: int = 24):
    from PIL import ImageFont

    p = str(path)
    try:
        return ImageFont.truetype(p, size=size)
    except OSError:
        return ImageFont.truetype(p, size=size, index=0)


def _renders(path: str | Path, probe: str) -> bool:
    try:
        from PIL import Image, ImageDraw

        if not _is_font_file(Path(path)):
            return False
        font = _pil_font(path, 36)
        img = Image.new("L", (280, 70), 0)
        ImageDraw.Draw(img).text((4, 4), probe, fill=255, font=font)
        return img.getbbox() is not None and max(img.getdata()) > 20
    except Exception:
        return False


def font_renders_tamil(path: str | Path | None) -> bool:
    return bool(path) and _renders(path, _PROBE_TA)


def font_renders_bilingual(path: str | Path | None) -> bool:
    return bool(path) and _renders(path, _PROBE_EN) and _renders(path, _PROBE_TA)


def _font_candidates() -> list[Path]:
    paths: list[Path] = []
    if sys.platform == "win32":
        fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        for name in ("Nirmala.ttc", "Nirmala.ttf", "latha.ttf", "Latha.ttf", "vijaya.ttf"):
            paths.append(fonts / name)
    for name in (
        "Nirmala.ttc", "Nirmala.ttf", "Latha.ttf", "Lohit-Tamil.ttf",
        "NotoSansTamil-Regular.ttf", "NotoSansTamil.ttf",
    ):
        paths.append(_FONTS_DIR / name)
    paths.extend(
        [
            Path("/usr/share/fonts/truetype/lohit-tamil/Lohit-Tamil.ttf"),
            Path("/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf"),
            Path("/System/Library/Fonts/Supplemental/Tamil MN.ttc"),
        ]
    )
    return paths


def ensure_tamil_font(force_download: bool = False) -> str | None:
    """Return path to a font that draws English + Tamil (prefer Nirmala)."""
    if not force_download:
        for p in _font_candidates():
            if font_renders_bilingual(p):
                return str(p.resolve())
        for p in _font_candidates():
            if font_renders_tamil(p):
                return str(p.resolve())

    try:
        _FONTS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    # Windows: copy Nirmala into project
    if sys.platform == "win32":
        src = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "Nirmala.ttc"
        dst = _FONTS_DIR / "Nirmala.ttc"
        if src.is_file():
            try:
                shutil.copy2(src, dst)
                if font_renders_bilingual(dst) or font_renders_tamil(dst):
                    return str(dst.resolve())
            except OSError:
                pass

    # Download full Noto Sans Tamil
    target = _FONTS_DIR / "NotoSansTamil-Regular.ttf"
    if force_download or not font_renders_tamil(target):
        for url in _NOTO_URLS:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "CRIMECAST/1.0"})
                with urllib.request.urlopen(req, timeout=40) as resp:
                    data = resp.read()
                if len(data) < 40_000 or data[:4] not in _FONT_MAGIC:
                    continue
                target.write_bytes(data)
                if font_renders_tamil(target):
                    return str(target.resolve())
            except Exception:
                continue

    for p in _font_candidates():
        if font_renders_bilingual(p) or font_renders_tamil(p):
            return str(p.resolve())
    return None


@lru_cache(maxsize=1)
def resolve_wordcloud_font() -> str | None:
    return ensure_tamil_font(force_download=False)


def ensure_latin_font() -> str | None:
    """Latin-only face for English word clouds (never Lohit Tamil)."""
    paths: list[Path] = []
    if sys.platform == "win32":
        fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        for name in (
            "arial.ttf", "calibri.ttf", "tahoma.ttf", "segoeui.ttf",
            "Nirmala.ttc", "Nirmala.ttf",
        ):
            paths.append(fonts / name)
    paths.extend(
        [
            _FONTS_DIR / "DejaVuSans.ttf",
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
            Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
        ]
    )
    for p in paths:
        if "lohit" in str(p).lower():
            continue
        if _renders(p, _PROBE_EN):
            return str(p.resolve())
    try:
        from matplotlib import font_manager as fm

        path = fm.findfont(fm.FontProperties(family="DejaVu Sans"))
        if path and _renders(path, _PROBE_EN):
            return str(Path(path).resolve())
    except Exception:
        pass
    return None


def font_for_plotly() -> str:
    return "DejaVu Sans, Arial, Segoe UI, sans-serif"


def tamil_font_status() -> dict[str, Any]:
    path = resolve_wordcloud_font()
    return {
        "font_path": path,
        "ok": bool(path) and font_renders_tamil(path),
        "renders_tamil": font_renders_tamil(path) if path else False,
        "renders_bilingual": font_renders_bilingual(path) if path else False,
        "bundled_dir": str(_FONTS_DIR),
        "bundled_exists": _FONTS_DIR.is_dir(),
    }


# ---------------------------------------------------------------------------
# Data → tokens
# ---------------------------------------------------------------------------

def _resolve_district_col(df: pd.DataFrame) -> str | None:
    for c in ("district", "district_city", "area"):
        if c in df.columns:
            return c
    return None


def _headline_col(df: pd.DataFrame) -> str | None:
    for c in ("headline", "title", "text", "summary"):
        if c in df.columns:
            return c
    return None


def collect_district_texts(
    harvest_df: pd.DataFrame | None,
    news_df: pd.DataFrame | None = None,
    sentiment_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    frames = []
    for src in (harvest_df, news_df, sentiment_df):
        if src is None or not isinstance(src, pd.DataFrame) or src.empty:
            continue
        dcol = _resolve_district_col(src)
        hcol = _headline_col(src)
        if not dcol or not hcol:
            continue
        part = src[[dcol, hcol]].copy()
        part.columns = ["district", "text"]
        frames.append(part)
    if not frames:
        return pd.DataFrame(columns=["district", "text"])
    out = pd.concat(frames, ignore_index=True)
    out["district"] = out["district"].astype(str).str.strip()
    out["text"] = out["text"].astype(str)
    out = out[out["text"].str.len() > 3]
    try:
        from district_entities import to_tn38

        out["district"] = out["district"].map(lambda x: to_tn38(x, default=None) or x)
        out = out[out["district"].astype(str).str.len() >= 3]
    except Exception:
        pass
    return out.dropna(subset=["district", "text"])


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    out: list[str] = []
    for m in _TOKEN_RE.finditer(str(text)):
        t = m.group(0)
        if re.fullmatch(r"[A-Za-z]+", t):
            t = t.lower()
        if t in _STOP or t.isdigit():
            continue
        out.append(t)
    return out


def balance_lang_frequencies(
    ctr: Counter,
    top_n: int = 40,
    lang_mode: str = "both",
) -> Counter:
    """Keep English and Tamil both visible (≈ half each when both exist)."""
    if not ctr or top_n <= 0:
        return Counter()

    mode = (lang_mode or "both").strip().lower()
    en = Counter({w: c for w, c in ctr.items() if is_english_token(str(w))})
    ta = Counter({w: c for w, c in ctr.items() if is_tamil_token(str(w))})

    if mode in ("english", "en"):
        return Counter(dict(en.most_common(top_n)))
    if mode in ("tamil", "ta"):
        return Counter(dict(ta.most_common(top_n)))

    # both
    if en and ta:
        n_en = max(1, top_n // 2)
        n_ta = max(1, top_n - n_en)
        take = list(en.most_common(n_en)) + list(ta.most_common(n_ta))
        # fill leftover if one side was short
        used = {w for w, _ in take}
        rest_n = top_n - len(take)
        if rest_n > 0:
            pool = Counter({w: c for w, c in ctr.items() if w not in used})
            take.extend(pool.most_common(rest_n))
        return Counter(dict(take[:top_n]))
    if en:
        return Counter(dict(en.most_common(top_n)))
    if ta:
        return Counter(dict(ta.most_common(top_n)))
    return Counter(dict(ctr.most_common(top_n)))


def lang_counts(ctr: Counter) -> dict[str, int]:
    n_en = sum(1 for w in ctr if is_english_token(str(w)))
    n_ta = sum(1 for w in ctr if is_tamil_token(str(w)))
    return {
        "english": n_en,
        "tamil": n_ta,
        "other": max(0, len(ctr) - n_en - n_ta),
        "total": len(ctr),
    }


def word_freq_for_district(
    texts_df: pd.DataFrame,
    district: str,
    top_n: int = 60,
    lang_mode: str = "both",
) -> Counter:
    dcf = str(district).strip().casefold()
    if texts_df.empty:
        return Counter()
    mask = texts_df["district"].astype(str).str.casefold() == dcf
    if not mask.any():
        mask = texts_df["district"].astype(str).str.casefold().str.contains(
            dcf[:6], na=False
        )
    raw: Counter = Counter()
    for t in texts_df.loc[mask, "text"]:
        raw.update(tokenize(t))
    return balance_lang_frequencies(raw, top_n=top_n, lang_mode=lang_mode)


def freq_dataframe(ctr: Counter, top_n: int = 40) -> pd.DataFrame:
    items = ctr.most_common(top_n)
    if not items:
        return pd.DataFrame(columns=["word", "count", "lang"])
    return pd.DataFrame(
        [{"word": w, "count": c, "lang": token_lang(str(w))} for w, c in items]
    )


def district_list(texts_df: pd.DataFrame) -> list[str]:
    if texts_df.empty:
        return []
    try:
        from district_entities import TN38, to_tn38

        counts = texts_df["district"].astype(str).map(
            lambda x: to_tn38(x, default=None) or x
        ).value_counts()
        ordered = [d for d in TN38 if d in counts.index]
        rest = [d for d in counts.index if d not in ordered]
        return ordered + rest
    except Exception:
        return sorted(texts_df["district"].astype(str).unique().tolist())


# ---------------------------------------------------------------------------
# Drawing — two-column EN | TA (clear, bilingual, no boxes)
# ---------------------------------------------------------------------------

def _text_size(draw, text: str, font) -> tuple[int, int]:
    try:
        b = draw.textbbox((0, 0), text, font=font)
        return int(b[2] - b[0]), int(b[3] - b[1])
    except Exception:
        try:
            return font.getsize(text)
        except Exception:
            return (max(8, len(text) * 10), 18)


def _draw_column(
    draw,
    items: list[tuple[str, float]],
    font_path: str,
    x0: int,
    y0: int,
    col_w: int,
    max_h: int,
    color: tuple[int, int, int],
    title: str,
    title_color: tuple[int, int, int],
) -> None:
    """Draw a vertical list of words sized by frequency."""
    if not items:
        try:
            f = _pil_font(font_path, 16)
            draw.text((x0 + 8, y0 + 8), "(none)", fill=(100, 100, 110), font=f)
        except Exception:
            pass
        return

    max_c = max(c for _, c in items) or 1.0
    # Title
    try:
        tf = _pil_font(font_path, 18)
        draw.text((x0 + 8, y0), title, fill=title_color, font=tf)
    except Exception:
        pass

    y = y0 + 28
    for word, count in items:
        t = float(count) / max_c
        size = int(13 + t * 20)
        try:
            font = _pil_font(font_path, size)
        except Exception:
            continue
        tw, th = _text_size(draw, word, font)
        # wrap long words by shrinking
        if tw > col_w - 16:
            size = max(11, int(size * (col_w - 16) / max(tw, 1)))
            try:
                font = _pil_font(font_path, size)
            except Exception:
                continue
            tw, th = _text_size(draw, word, font)
        if y + th > y0 + max_h:
            break
        draw.text((x0 + 10, y), word, fill=color, font=font)
        # small count
        try:
            cf = _pil_font(font_path, 11)
            draw.text((x0 + 12 + tw, y + 4), f" {int(count)}", fill=(120, 120, 130), font=cf)
        except Exception:
            pass
        y += th + 6


def make_english_wordcloud_image(
    ctr: Counter,
    width: int = 900,
    height: int = 420,
    *,
    return_error: bool = False,
):
    """
    English-only word cloud (safe on Streamlit Cloud — no Tamil fonts).

    Uses `wordcloud` + DejaVu/Arial when available; otherwise a simple PIL layout.
    """
    if not ctr:
        return (None, "empty") if return_error else None

    # Force English tokens only
    freqs = {
        str(k).lower(): float(v)
        for k, v in ctr.items()
        if is_english_token(str(k)) and float(v) > 0
    }
    if not freqs:
        return (None, "no English tokens in headlines") if return_error else None

    font_path = ensure_latin_font()
    last_err: str | None = None

    # 1) Classic wordcloud library (English + Latin font)
    try:
        from wordcloud import WordCloud
        import matplotlib

        matplotlib.use("Agg")
        kwargs: dict[str, Any] = dict(
            width=width,
            height=height,
            background_color="#0e0e12",
            colormap="Blues",
            max_words=min(80, max(15, len(freqs))),
            prefer_horizontal=0.9,
            relative_scaling=0.45,
            min_font_size=11,
            collocations=False,
            regexp=r"[A-Za-z']+",
        )
        if font_path:
            kwargs["font_path"] = font_path
        img = WordCloud(**kwargs).generate_from_frequencies(freqs).to_image()
        if img is not None:
            return (img, None) if return_error else img
    except ImportError as e:
        last_err = f"wordcloud not installed ({e})"
    except Exception as e:
        last_err = f"wordcloud failed: {type(e).__name__}: {e}"

    # 2) PIL fallback — frequency-sized list (always works with Arial/DejaVu)
    try:
        from PIL import Image, ImageDraw

        if not font_path:
            last_err = (last_err or "") + "; no Latin font"
            return (None, last_err.strip("; ")) if return_error else None

        items = sorted(freqs.items(), key=lambda x: -x[1])[:40]
        max_c = max(c for _, c in items) or 1.0
        img = Image.new("RGB", (width, height), (14, 14, 18))
        draw = ImageDraw.Draw(img)
        try:
            draw.text(
                (12, 8),
                "English terms only",
                fill=(160, 160, 170),
                font=_pil_font(font_path, 14),
            )
        except Exception:
            pass

        y = 36
        for word, count in items:
            t = float(count) / max_c
            size = int(12 + t * 22)
            try:
                font = _pil_font(font_path, size)
            except Exception:
                continue
            tw, th = _text_size(draw, word, font)
            if y + th > height - 8:
                break
            draw.text((16, y), word, fill=(96, 165, 250), font=font)
            try:
                cf = _pil_font(font_path, 11)
                draw.text((20 + tw, y + 3), f" {int(count)}", fill=(120, 120, 130), font=cf)
            except Exception:
                pass
            y += th + 5

        return (img, last_err) if return_error else img
    except Exception as e:
        msg = f"{last_err}; PIL: {e}" if last_err else str(e)
        return (None, msg) if return_error else None


def make_wordcloud_image(
    ctr: Counter,
    width: int = 900,
    height: int = 420,
    *,
    return_error: bool = False,
):
    """Alias → English-only cloud (Tamil disabled in UI to avoid font boxes)."""
    return make_english_wordcloud_image(
        ctr, width=width, height=height, return_error=return_error
    )


def make_freq_bar_image(
    ctr: Counter,
    top_n: int = 40,
    width: int = 900,
    height: int | None = None,
    title: str = "Top terms",
):
    """Horizontal bars as PNG (embeds font so Tamil is not □)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm

    items = Counter(ctr).most_common(top_n)
    if not items:
        return None

    words = [str(w) for w, _ in items][::-1]
    counts = [float(c) for _, c in items][::-1]
    colors = []
    for w in words:
        lg = token_lang(w)
        if lg == "ta":
            colors.append("#14b8a6")
        elif lg == "en":
            colors.append("#3b82f6")
        else:
            colors.append("#6b7280")

    font_path = ensure_tamil_font(force_download=False)
    n = len(words)
    h = height or max(260, 16 * n + 70)
    fig, ax = plt.subplots(figsize=(max(6.0, width / 100.0), max(2.8, h / 100.0)), dpi=110)
    fig.patch.set_facecolor("#0e0e12")
    ax.set_facecolor("#0e0e12")
    y = np.arange(n)
    ax.barh(y, counts, color=colors, height=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels(words)
    ax.set_xlabel("count", color="#9ca3af")
    ax.set_title(f"{title}  (blue=EN  teal=TA)", color="#e5e7eb", fontsize=11)
    ax.tick_params(colors="#d1d5db", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#374151")

    if font_path:
        try:
            fp = fm.FontProperties(fname=font_path)
            for lab in ax.get_yticklabels():
                lab.set_fontproperties(fp)
        except Exception:
            pass

    fig.tight_layout()
    try:
        from PIL import Image

        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor=fig.get_facecolor(),
                    edgecolor="none", bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf).convert("RGB")
    except Exception:
        plt.close(fig)
        return None
