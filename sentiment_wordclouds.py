# -*- coding: utf-8 -*-
"""
CRIMECAST — per-district sentiment word clouds from news headlines.

Tamil is drawn with Pillow + a verified font (Nirmala / full Noto Sans Tamil).
The `wordcloud` package is only used for English-only clouds — it often paints
□ boxes for Tamil even when font_path is set.

Frequency bars with Tamil labels are matplotlib PNGs (Plotly cannot load a local TTF).
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent
_FONTS_DIR = _ROOT / "assets" / "fonts"

# Full Noto Sans Tamil only (openmaptiles subset is ~38KB and misses many glyphs → □ boxes)
_NOTO_TAMIL_URLS = (
    "https://notofonts.github.io/tamil/fonts/NotoSansTamil/full/ttf/NotoSansTamil-Regular.ttf",
    "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTamil/NotoSansTamil-Regular.ttf",
)
_FONT_MAGIC = (b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf")
# Probe string must include a common consonant + vowel mark (complex cluster)
_TAMIL_PROBE = "கைது"
_MIN_FULL_FONT_BYTES = 40_000

# English + common crime tokens; Tamil stop words (minimal)
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
    # media names
    "dinamalar", "dinamani", "thanthi", "vikatan", "hindu", "times", "express",
    "etv", "bharat", "ndtv", "polimer",
    # Tamil function words (common)
    "ஒரு", "மற்றும்", "இந்த", "அந்த", "என்று", "உள்ள", "ஆனால்", "போன்ற",
    "இல்", "க்கு", "கள்", "ஆக", "என", "வேண்டும்",
}

# Latin words (3+) OR Tamil script runs (2+ code points, including combining marks)
_TOKEN_RE = re.compile(r"[A-Za-z]{3,}|[\u0B80-\u0BFF]{2,}")
_TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")


def has_tamil(text: str) -> bool:
    return bool(text and _TAMIL_RE.search(str(text)))


def is_english_token(word: str) -> bool:
    return bool(word and re.fullmatch(r"[A-Za-z][A-Za-z'-]*", str(word)))


def is_tamil_token(word: str) -> bool:
    """True if token is primarily Tamil script (not mixed Latin)."""
    s = str(word or "")
    if not s or not has_tamil(s):
        return False
    # Pure / mostly Tamil block
    ta = len(_TAMIL_RE.findall(s))
    return ta >= max(1, len(s) // 2)


def token_lang(word: str) -> str:
    """'ta' | 'en' | 'other' for coloring / balancing."""
    if is_tamil_token(word):
        return "ta"
    if is_english_token(word):
        return "en"
    return "other"


def _looks_like_font(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size < 8_000:
            return False
        head = path.read_bytes()[:4]
        return head in _FONT_MAGIC
    except OSError:
        return False


def _pil_font(path: str | Path, size: int = 28):
    """Load TTF/OTF/TTC for drawing (TTC needs index=0)."""
    from PIL import ImageFont

    p = str(path)
    try:
        return ImageFont.truetype(p, size=size)
    except OSError:
        return ImageFont.truetype(p, size=size, index=0)


def _font_renders_probe(path: str | Path | None, probe: str) -> bool:
    if not path:
        return False
    p = Path(path)
    if not _looks_like_font(p):
        return False
    try:
        from PIL import Image as PILImage
        from PIL import ImageDraw

        font = _pil_font(p, 40)
        img = PILImage.new("L", (320, 80), 0)
        draw = ImageDraw.Draw(img)
        draw.text((4, 4), probe, fill=255, font=font)
        return img.getbbox() is not None and max(img.getdata()) > 20
    except Exception:
        return False


def font_renders_tamil(path: str | Path | None) -> bool:
    """True if PIL can ink a real Tamil cluster (not □ boxes)."""
    return _font_renders_probe(path, _TAMIL_PROBE)


def font_renders_bilingual(path: str | Path | None) -> bool:
    """Font must draw English *and* Tamil (word clouds are mixed language)."""
    return _font_renders_probe(path, "Police") and _font_renders_probe(path, _TAMIL_PROBE)


def _candidate_font_paths() -> list[Path]:
    """Prefer system Nirmala/Latha (full coverage) before maybe-broken downloads."""
    out: list[Path] = []

    # Windows system first — Nirmala is reliable for Tamil + Latin
    if sys.platform == "win32":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        fonts = windir / "Fonts"
        for name in (
            "Nirmala.ttc",
            "Nirmala.ttf",
            "latha.ttf",
            "Latha.ttf",
            "vijaya.ttf",
            "Vijaya.ttf",
        ):
            out.append(fonts / name)

    # Bundled project fonts
    for name in (
        "Nirmala.ttc",
        "Nirmala.ttf",
        "Latha.ttf",
        "Lohit-Tamil.ttf",
        "NotoSansTamil-Regular.ttf",
        "NotoSansTamil.ttf",
        "NotoSansTamil-Medium.ttf",
    ):
        out.append(_FONTS_DIR / name)

    # Linux
    out.extend(
        [
            Path("/usr/share/fonts/truetype/lohit-tamil/Lohit-Tamil.ttf"),
            Path("/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf"),
            Path("/usr/share/fonts/truetype/noto/NotoSansTamilUI-Regular.ttf"),
            Path("/usr/share/fonts/opentype/noto/NotoSansTamil-Regular.ttf"),
        ]
    )

    # macOS
    out.extend(
        [
            Path("/System/Library/Fonts/Supplemental/Tamil MN.ttc"),
            Path("/Library/Fonts/NotoSansTamil-Regular.ttf"),
            Path("/System/Library/Fonts/Supplemental/NotoSansTamil-Regular.ttf"),
        ]
    )
    return out


def _first_bilingual_font(paths: list[Path]) -> Path | None:
    """Prefer faces that draw English + Tamil; fall back to Tamil-only."""
    tamil_only: Path | None = None
    for p in paths:
        if font_renders_bilingual(p):
            return p
        if tamil_only is None and font_renders_tamil(p):
            tamil_only = p
    return tamil_only


def ensure_tamil_font(force_download: bool = False) -> str | None:
    """
    Font path that paints Tamil (and ideally English too).

    Prefer Nirmala UI (full bilingual). Full Noto Sans Tamil also covers Latin.
    Rejects subset fonts that only produce □ boxes.
    """
    if not force_download:
        found = _first_bilingual_font(_candidate_font_paths())
        if found:
            return str(found.resolve())

    try:
        _FONTS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    # Copy Windows Nirmala into project (best EN+TA coverage offline)
    if sys.platform == "win32":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        for src_name, dst_name in (
            ("Nirmala.ttc", "Nirmala.ttc"),
            ("Nirmala.ttf", "Nirmala.ttf"),
            ("latha.ttf", "Latha.ttf"),
        ):
            src = windir / "Fonts" / src_name
            dst = _FONTS_DIR / dst_name
            if src.is_file():
                try:
                    import shutil

                    shutil.copy2(src, dst)
                    if font_renders_bilingual(dst) or font_renders_tamil(dst):
                        return str(dst.resolve())
                except OSError:
                    pass

    # Download full Noto Sans Tamil (includes basic Latin)
    target = _FONTS_DIR / "NotoSansTamil-Regular.ttf"
    if force_download or not font_renders_tamil(target):
        try:
            if target.is_file() and not font_renders_tamil(target):
                target.unlink(missing_ok=True)
        except OSError:
            pass
        try:
            import urllib.request

            for url in _NOTO_TAMIL_URLS:
                try:
                    req = urllib.request.Request(
                        url,
                        headers={"User-Agent": "CRIMECAST/1.0 (bilingual wordcloud font)"},
                    )
                    with urllib.request.urlopen(req, timeout=40) as resp:
                        data = resp.read()
                    if len(data) < _MIN_FULL_FONT_BYTES or data[:4] not in _FONT_MAGIC:
                        continue
                    target.write_bytes(data)
                    if font_renders_bilingual(target) or font_renders_tamil(target):
                        return str(target.resolve())
                    try:
                        target.unlink(missing_ok=True)
                    except OSError:
                        pass
                except Exception:
                    continue
        except Exception:
            pass

    found = _first_bilingual_font(_candidate_font_paths())
    if found:
        return str(found.resolve())

    try:
        from matplotlib import font_manager

        for fam in (
            "Nirmala UI",
            "Noto Sans Tamil",
            "Noto Sans Tamil UI",
            "Latha",
            "Vijaya",
            "Tamil MN",
            "Lohit Tamil",
        ):
            try:
                path = font_manager.findfont(
                    font_manager.FontProperties(family=fam),
                    fallback_to_default=False,
                )
                if path and (
                    font_renders_bilingual(path) or font_renders_tamil(path)
                ):
                    return str(Path(path).resolve())
            except Exception:
                continue
    except Exception:
        pass
    return None


@lru_cache(maxsize=1)
def resolve_wordcloud_font() -> str | None:
    """Path to a face that PIL can use to draw Tamil (not □ boxes)."""
    return ensure_tamil_font(force_download=False)


def font_for_plotly() -> str:
    """Browser font stack — only helps if the OS already installed a Tamil face."""
    return (
        "Nirmala UI, Noto Sans Tamil, Latha, Vijaya, Tamil MN, Lohit Tamil, "
        "Segoe UI, Arial Unicode MS, sans-serif"
    )


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
    """Stack headlines with district labels from available sources."""
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
    # Map to TN38 when possible
    try:
        from district_entities import to_tn38

        out["district"] = out["district"].map(lambda x: to_tn38(x, default=None) or x)
        # Drop junk that still looks non-district
        out = out[out["district"].astype(str).str.len() >= 3]
    except Exception:
        pass
    return out.dropna(subset=["district", "text"])


def tokenize(text: str) -> list[str]:
    """Keep Latin lowercased; leave Tamil script as-is (casefold breaks some tools)."""
    if not text:
        return []
    raw = str(text)
    toks: list[str] = []
    for m in _TOKEN_RE.finditer(raw):
        t = m.group(0)
        if re.fullmatch(r"[A-Za-z]+", t):
            t = t.lower()
        if t in _STOP or t.isdigit():
            continue
        toks.append(t)
    return toks


def word_freq_for_district(
    texts_df: pd.DataFrame,
    district: str,
    top_n: int = 60,
    lang_mode: str = "both",
) -> Counter:
    """
    Token frequencies for one district.

    lang_mode:
      - "both"    → balanced English + Tamil (neither starves the other)
      - "english" → Latin tokens only
      - "tamil"   → Tamil-script tokens only
    """
    dcf = str(district).strip().casefold()
    if texts_df.empty:
        return Counter()
    mask = texts_df["district"].astype(str).str.casefold() == dcf
    if not mask.any():
        mask = texts_df["district"].astype(str).str.casefold().str.contains(dcf[:6], na=False)
    sub = texts_df.loc[mask, "text"]
    raw: Counter = Counter()
    for t in sub:
        raw.update(tokenize(t))
    return balance_lang_frequencies(raw, top_n=top_n, lang_mode=lang_mode)


def balance_lang_frequencies(
    ctr: Counter,
    top_n: int = 40,
    lang_mode: str = "both",
) -> Counter:
    """
    Build a frequency counter that keeps English and Tamil visible together.

    Without balancing, most_common() can be 100% one language when that side
    has slightly higher counts — bilingual clouds then look “Tamil only” or
    “English only”.
    """
    if not ctr or top_n <= 0:
        return Counter()

    mode = (lang_mode or "both").strip().lower()
    en = Counter({w: c for w, c in ctr.items() if is_english_token(str(w))})
    ta = Counter({w: c for w, c in ctr.items() if is_tamil_token(str(w))})
    other = Counter(
        {
            w: c
            for w, c in ctr.items()
            if not is_english_token(str(w)) and not is_tamil_token(str(w))
        }
    )

    if mode in ("english", "en"):
        return Counter(dict(en.most_common(top_n)))
    if mode in ("tamil", "ta"):
        return Counter(dict(ta.most_common(top_n)))

    # both — reserve slots for each language when both exist
    has_en, has_ta = bool(en), bool(ta)
    if has_en and has_ta:
        # ~half each; give leftover to the larger side
        n_en = max(1, top_n // 2)
        n_ta = max(1, top_n - n_en)
        # If one side is thin, give unused slots to the other
        take_en = en.most_common(min(n_en, len(en)))
        take_ta = ta.most_common(min(n_ta, len(ta)))
        used = {w for w, _ in take_en} | {w for w, _ in take_ta}
        remaining = top_n - len(take_en) - len(take_ta)
        if remaining > 0:
            pool = Counter()
            pool.update({w: c for w, c in en.items() if w not in used})
            pool.update({w: c for w, c in ta.items() if w not in used})
            pool.update({w: c for w, c in other.items() if w not in used})
            take_en = list(take_en) + list(pool.most_common(remaining))
        merged = Counter(dict(take_en))
        merged.update(dict(take_ta))
        return Counter(dict(merged.most_common(top_n)))

    if has_en:
        out = Counter(dict(en.most_common(top_n)))
        rest = top_n - len(out)
        if rest > 0 and other:
            out.update(dict(other.most_common(rest)))
        return out
    if has_ta:
        out = Counter(dict(ta.most_common(top_n)))
        rest = top_n - len(out)
        if rest > 0 and other:
            out.update(dict(other.most_common(rest)))
        return out

    return Counter(dict(ctr.most_common(top_n)))


def lang_counts(ctr: Counter) -> dict[str, int]:
    """How many unique tokens per language in a counter."""
    n_en = sum(1 for w in ctr if is_english_token(str(w)))
    n_ta = sum(1 for w in ctr if is_tamil_token(str(w)))
    n_ot = len(ctr) - n_en - n_ta
    return {"english": n_en, "tamil": n_ta, "other": max(0, n_ot), "total": len(ctr)}


def freq_dataframe(ctr: Counter, top_n: int = 40) -> pd.DataFrame:
    items = ctr.most_common(top_n)
    if not items:
        return pd.DataFrame(columns=["word", "count", "lang"])
    rows = []
    for w, c in items:
        rows.append({"word": w, "count": c, "lang": token_lang(str(w))})
    return pd.DataFrame(rows)


def _resolve_font_for_cloud(freqs: dict[str, float]) -> str | None:
    sample = " ".join(str(k) for k in freqs.keys())
    resolve_wordcloud_font.cache_clear()
    if has_tamil(sample):
        # Prefer proven face; re-download if previous subset was bad
        path = ensure_tamil_font(force_download=False)
        if path and font_renders_tamil(path):
            return path
        return ensure_tamil_font(force_download=True)
    # English-only: any readable face (still prefer Tamil-capable for mixed later)
    return resolve_wordcloud_font() or ensure_tamil_font(force_download=False)


def _text_size(draw, text: str, font) -> tuple[int, int]:
    """Width/height of text for current Pillow API."""
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])
    except Exception:
        try:
            return font.getsize(text)
        except Exception:
            return (len(text) * 12, 20)


def _pil_word_image(
    freqs: dict[str, float],
    font_path: str | None,
    width: int = 900,
    height: int = 450,
):
    """
    Draw a word cloud with Pillow + the given TTF/TTC.

    Prefer this over the `wordcloud` package for Tamil: WordCloud often paints □
    even when font_path is set (complex-script / mask issues).
    """
    from PIL import Image as PILImage
    from PIL import ImageDraw

    if not freqs or not font_path:
        return None
    # Only block when Tamil words need glyphs the face cannot ink
    if any(has_tamil(w) for w in freqs) and not font_renders_tamil(font_path):
        return None

    items = sorted(freqs.items(), key=lambda x: -float(x[1]))[:55]
    max_c = max(float(c) for _, c in items) or 1.0
    min_c = min(float(c) for _, c in items) or 1.0

    bg = (14, 14, 18)
    img = PILImage.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)
    rng = np.random.default_rng(7)

    # English = blue family · Tamil = teal/amber so both languages are obvious
    en_colors = [
        (147, 197, 253),
        (96, 165, 250),
        (59, 130, 246),
        (37, 99, 235),
    ]
    ta_colors = [
        (253, 230, 138),
        (251, 191, 36),
        (45, 212, 191),
        (20, 184, 166),
    ]
    other_colors = [(209, 213, 219), (156, 163, 175)]

    occupied: list[tuple[int, int, int, int]] = []

    def overlaps(x0, y0, x1, y1, pad: int = 3) -> bool:
        for a, b, c, d in occupied:
            if not (x1 + pad < a or x0 - pad > c or y1 + pad < b or y0 - pad > d):
                return True
        return False

    def color_for(word: str, t: float) -> tuple[int, int, int]:
        lang = token_lang(word)
        if lang == "ta":
            palette = ta_colors
        elif lang == "en":
            palette = en_colors
        else:
            palette = other_colors
        return palette[int(t * (len(palette) - 1))]

    for i, (word, count) in enumerate(items):
        word = str(word)
        weight = float(count)
        t = (weight - min_c) / (max_c - min_c) if max_c > min_c else 1.0
        size = int(14 + t * 34)
        try:
            font = _pil_font(font_path, size)
        except Exception:
            continue
        tw, th = _text_size(draw, word, font)
        if tw <= 0 or th <= 0 or tw > width - 8:
            size = max(11, int(size * (width - 16) / max(tw, 1)))
            try:
                font = _pil_font(font_path, size)
            except Exception:
                continue
            tw, th = _text_size(draw, word, font)

        placed = False
        cx, cy = width // 2, height // 2
        for attempt in range(120):
            if attempt < 40 and i < 8:
                x = int(cx - tw / 2 + rng.integers(-40, 41))
                y = int(cy - th / 2 + rng.integers(-30, 31))
            else:
                x = int(rng.integers(4, max(5, width - tw - 4)))
                y = int(rng.integers(4, max(5, height - th - 4)))
            x = max(2, min(x, width - tw - 2))
            y = max(2, min(y, height - th - 2))
            if not overlaps(x, y, x + tw, y + th):
                draw.text((x, y), word, fill=color_for(word, t), font=font)
                occupied.append((x, y, x + tw, y + th))
                placed = True
                break
        if not placed:
            x = int(rng.integers(4, max(5, width - tw - 4)))
            y = int(rng.integers(4, max(5, height - th - 4)))
            draw.text((x, y), word, fill=color_for(word, t), font=font)

    # Legend strip so bilingual intent is clear
    try:
        legend_font = _pil_font(font_path, 14)
        draw.rectangle((0, height - 22), fill=(20, 20, 28))
        draw.text((8, height - 20), "EN (blue)", fill=en_colors[1], font=legend_font)
        draw.text((100, height - 20), "TA (teal/gold)", fill=ta_colors[2], font=legend_font)
    except Exception:
        pass

    return img


def make_freq_bar_image(
    ctr: Counter,
    top_n: int = 40,
    width: int = 900,
    height: int | None = None,
    title: str = "Top terms",
):
    """
    Horizontal bar chart as PNG using the Tamil font.

    Plotly/browser cannot load local TTF files → Tamil y-labels become □.
    This image embeds the font, so Tamil always shows correctly.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm

    fdf_items = Counter(ctr).most_common(top_n)
    if not fdf_items:
        return None

    words = [str(w) for w, _ in fdf_items][::-1]
    counts = [float(c) for _, c in fdf_items][::-1]
    langs = [token_lang(w) for w in words]
    font_path = ensure_tamil_font(force_download=False)

    bar_colors = []
    for lg in langs:
        if lg == "ta":
            bar_colors.append("#14b8a6")  # teal — Tamil
        elif lg == "en":
            bar_colors.append("#3b82f6")  # blue — English
        else:
            bar_colors.append("#6b7280")

    n = len(words)
    h = height or max(280, 18 * n + 80)
    fig_w = max(6.0, width / 100.0)
    fig_h = max(3.0, h / 100.0)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=110)
    fig.patch.set_facecolor("#0e0e12")
    ax.set_facecolor("#0e0e12")

    y_pos = np.arange(n)
    ax.barh(y_pos, counts, color=bar_colors, height=0.72)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(words)
    ax.set_xlabel("count", color="#9ca3af")
    ax.set_title(title + "  ·  blue=EN  teal=TA", color="#e5e7eb", fontsize=11, pad=8)
    ax.tick_params(colors="#d1d5db", labelsize=10)
    for spine in ax.spines.values():
        spine.set_color("#374151")
    ax.xaxis.label.set_color("#9ca3af")

    if font_path:
        try:
            fp = fm.FontProperties(fname=font_path)
            for lab in ax.get_yticklabels():
                lab.set_fontproperties(fp)
            ax.title.set_fontproperties(fp)
        except Exception:
            pass

    fig.tight_layout()
    try:
        from PIL import Image as PILImage
        import io

        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            facecolor=fig.get_facecolor(),
            edgecolor="none",
            bbox_inches="tight",
            pad_inches=0.12,
        )
        plt.close(fig)
        buf.seek(0)
        return PILImage.open(buf).convert("RGB")
    except Exception:
        plt.close(fig)
        return None


def make_wordcloud_image(
    ctr: Counter,
    width: int = 900,
    height: int = 450,
    *,
    return_error: bool = False,
):
    """
    Return PIL Image for the frequency cloud.

    For Tamil (or mixed) tokens we **always** draw with Pillow + a verified
    Tamil font. The `wordcloud` package is English-only-safe; it often emits □
    for Tamil even when font_path is set.

    If return_error=True, returns (image|None, err_msg|None).
    """
    if not ctr:
        return (None, "empty frequencies") if return_error else None

    freqs = {str(k): float(v) for k, v in ctr.items() if str(k).strip() and float(v) > 0}
    if not freqs:
        return (None, "no positive frequencies") if return_error else None

    has_ta = any(has_tamil(w) for w in freqs)
    font_path = _resolve_font_for_cloud(freqs)
    last_err: str | None = None

    if has_ta and not font_path:
        last_err = "no Tamil-capable font (Nirmala / Noto Sans Tamil)"
        return (None, last_err) if return_error else None

    # 1) Always prefer PIL for Tamil — reliable glyphs
    if has_ta or font_path:
        try:
            img = _pil_word_image(freqs, font_path, width=width, height=height)
            if img is not None:
                return (img, None) if return_error else img
            last_err = "PIL word layout failed"
        except Exception as e:
            last_err = f"PIL word layout: {type(e).__name__}: {e}"

    # 2) English-only path: optional wordcloud package
    if not has_ta:
        try:
            from wordcloud import WordCloud
            import matplotlib

            matplotlib.use("Agg")
            kwargs: dict[str, Any] = dict(
                width=width,
                height=height,
                background_color="#0e0e12",
                colormap="Blues",
                max_words=min(80, max(20, len(freqs))),
                prefer_horizontal=0.9,
                relative_scaling=0.45,
                min_font_size=12,
                margin=4,
                collocations=False,
            )
            if font_path:
                kwargs["font_path"] = font_path
            wc = WordCloud(**kwargs).generate_from_frequencies(freqs)
            img = wc.to_image()
            if img is not None:
                return (img, None) if return_error else img
        except ImportError as e:
            last_err = f"wordcloud not installed ({e})"
        except Exception as e:
            last_err = f"wordcloud failed: {type(e).__name__}: {e}"

        # English PIL fallback without Tamil check
        if font_path:
            try:
                from PIL import Image as PILImage
                from PIL import ImageDraw

                img = PILImage.new("RGB", (width, height), (14, 14, 18))
                draw = ImageDraw.Draw(img)
                # reuse pil layout but skip tamil check
                items = sorted(freqs.items(), key=lambda x: -float(x[1]))[:50]
                max_c = max(float(c) for _, c in items) or 1.0
                rng = np.random.default_rng(3)
                y = 12
                for word, count in items:
                    t = float(count) / max_c
                    size = int(12 + t * 28)
                    try:
                        font = _pil_font(font_path, size)
                    except Exception:
                        continue
                    tw, th = _text_size(draw, str(word), font)
                    x = int(rng.integers(8, max(9, width - tw - 8)))
                    draw.text((x, y % (height - th - 4)), str(word), fill=(96, 165, 250), font=font)
                    y += th + 6
                return (img, last_err) if return_error else img
            except Exception as e:
                last_err = f"{last_err}; english PIL: {e}"

    return (None, last_err) if return_error else None


def tamil_font_status() -> dict[str, Any]:
    """Diagnostics for UI captions / health."""
    path = resolve_wordcloud_font()
    return {
        "font_path": path,
        "ok": bool(path) and font_renders_tamil(path),
        "renders_tamil": font_renders_tamil(path) if path else False,
        "renders_bilingual": font_renders_bilingual(path) if path else False,
        "bundled_dir": str(_FONTS_DIR),
        "bundled_exists": _FONTS_DIR.is_dir(),
    }


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
