# -*- coding: utf-8 -*-
"""
CRIMECAST — per-district sentiment word clouds from news headlines.
Uses `wordcloud` if installed; otherwise frequency bars (always works).

Tamil headlines need a Tamil-capable TTF (default WordCloud fonts show □ boxes).
We prefer a bundled font under assets/fonts/, then system fonts (Nirmala UI, etc.).
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

# Download mirrors for Noto Sans Tamil (used when OS has no Tamil face — e.g. Streamlit Cloud)
_NOTO_TAMIL_URLS = (
    "https://notofonts.github.io/tamil/fonts/NotoSansTamil/full/ttf/NotoSansTamil-Regular.ttf",
    "https://cdn.jsdelivr.net/gh/openmaptiles/fonts@master/noto-sans/NotoSansTamil-Regular.ttf",
    "https://raw.githubusercontent.com/openmaptiles/fonts/master/noto-sans/NotoSansTamil-Regular.ttf",
)
_FONT_MAGIC = (b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf")

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


def _looks_like_font(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size < 8_000:
            return False
        head = path.read_bytes()[:4]
        return head in _FONT_MAGIC
    except OSError:
        return False


def _candidate_font_paths() -> list[Path]:
    """All known locations that may contain a Tamil-capable face."""
    out: list[Path] = []

    # Bundled with the repo (best for cloud after first download / git add)
    for name in (
        "NotoSansTamil-Regular.ttf",
        "NotoSansTamil.ttf",
        "NotoSansTamil-Medium.ttf",
        "Nirmala.ttf",
        "Nirmala.ttc",
        "Latha.ttf",
        "Lohit-Tamil.ttf",
    ):
        out.append(_FONTS_DIR / name)

    # Windows — Nirmala is usually .ttc (collection), not .ttf
    if sys.platform == "win32":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        fonts = windir / "Fonts"
        for name in (
            "Nirmala.ttc",
            "Nirmala.ttf",
            "NirmalaS.ttf",
            "latha.ttf",
            "Latha.ttf",
            "vijaya.ttf",
            "Vijaya.ttf",
        ):
            out.append(fonts / name)

    # Linux (Streamlit Cloud / Render after packages.txt fonts-lohit-taml)
    out.extend(
        [
            Path("/usr/share/fonts/truetype/lohit-tamil/Lohit-Tamil.ttf"),
            Path("/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf"),
            Path("/usr/share/fonts/truetype/noto/NotoSansTamilUI-Regular.ttf"),
            Path("/usr/share/fonts/opentype/noto/NotoSansTamil-Regular.ttf"),
            # Do NOT use NotoSans-Regular / DejaVu — no Tamil glyphs → □ boxes
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


def _first_valid_font(paths: list[Path]) -> Path | None:
    for p in paths:
        if _looks_like_font(p):
            return p
    return None


def ensure_tamil_font(force_download: bool = False) -> str | None:
    """
    Make sure a Tamil-capable font exists on disk.

    Order:
      1. Existing bundled / system font
      2. Copy Windows Nirmala.ttc into assets/fonts/
      3. Download Noto Sans Tamil into assets/fonts/ (cloud-friendly)
    """
    found = _first_valid_font(_candidate_font_paths())
    if found and not force_download:
        return str(found.resolve())

    try:
        _FONTS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    # Copy Windows system Tamil font into project (works offline locally)
    if sys.platform == "win32":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        for src_name, dst_name in (
            ("Nirmala.ttc", "Nirmala.ttc"),
            ("Nirmala.ttf", "Nirmala.ttf"),
            ("latha.ttf", "Latha.ttf"),
        ):
            src = windir / "Fonts" / src_name
            dst = _FONTS_DIR / dst_name
            if src.is_file() and (force_download or not _looks_like_font(dst)):
                try:
                    import shutil

                    shutil.copy2(src, dst)
                    if _looks_like_font(dst):
                        return str(dst.resolve())
                except OSError:
                    pass

    # Download free Noto Sans Tamil (needed on Linux cloud without apt fonts)
    target = _FONTS_DIR / "NotoSansTamil-Regular.ttf"
    if force_download or not _looks_like_font(target):
        try:
            import urllib.request

            for url in _NOTO_TAMIL_URLS:
                try:
                    req = urllib.request.Request(
                        url,
                        headers={"User-Agent": "CRIMECAST/1.0 (wordcloud Tamil font)"},
                    )
                    with urllib.request.urlopen(req, timeout=25) as resp:
                        data = resp.read()
                    if len(data) < 8_000 or data[:4] not in _FONT_MAGIC:
                        continue
                    target.write_bytes(data)
                    if _looks_like_font(target):
                        return str(target.resolve())
                except Exception:
                    continue
        except Exception:
            pass

    found = _first_valid_font(_candidate_font_paths())
    if found:
        return str(found.resolve())

    # matplotlib family probe last
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
                if path and _looks_like_font(Path(path)):
                    return str(Path(path).resolve())
            except Exception:
                continue
    except Exception:
        pass
    return None


@lru_cache(maxsize=1)
def resolve_wordcloud_font() -> str | None:
    """
    Path to a TTF/OTF/TTC that can draw Tamil + basic Latin.
    Without this, WordCloud's default font renders Tamil as empty boxes (□).
    """
    path = ensure_tamil_font(force_download=False)
    return path


def font_for_plotly() -> str:
    """CSS-style font stack so Plotly bar labels show Tamil when the OS has a face."""
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
) -> Counter:
    dcf = str(district).strip().casefold()
    if texts_df.empty:
        return Counter()
    mask = texts_df["district"].astype(str).str.casefold() == dcf
    if not mask.any():
        mask = texts_df["district"].astype(str).str.casefold().str.contains(dcf[:6], na=False)
    sub = texts_df.loc[mask, "text"]
    ctr: Counter = Counter()
    for t in sub:
        ctr.update(tokenize(t))
    return Counter(dict(ctr.most_common(top_n)))


def freq_dataframe(ctr: Counter, top_n: int = 40) -> pd.DataFrame:
    items = ctr.most_common(top_n)
    if not items:
        return pd.DataFrame(columns=["word", "count"])
    return pd.DataFrame(items, columns=["word", "count"])


def make_wordcloud_image(ctr: Counter, width: int = 900, height: int = 450):
    """
    Return PIL Image if wordcloud+matplotlib available, else None.

    Uses a Tamil-capable font when any token contains Tamil script so glyphs
    render instead of □ boxes (common on cloud with default DejaVu fonts).
    """
    if not ctr:
        return None
    try:
        from wordcloud import WordCloud
        import matplotlib

        matplotlib.use("Agg")
        freqs = dict(ctr)
        sample = " ".join(freqs.keys())
        # Force ensure when Tamil present (copy/download if first run)
        if has_tamil(sample):
            resolve_wordcloud_font.cache_clear()
            font_path = ensure_tamil_font(force_download=False)
        else:
            font_path = resolve_wordcloud_font()

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
            # Latin + full Tamil Unicode block (prevents drop of TA tokens)
            regexp=r"[A-Za-z']+|[\u0B80-\u0BFF]+",
        )
        if font_path:
            kwargs["font_path"] = font_path

        wc = WordCloud(**kwargs).generate_from_frequencies(freqs)
        return wc.to_image()
    except Exception:
        return None


def tamil_font_status() -> dict[str, Any]:
    """Diagnostics for UI captions / health."""
    path = resolve_wordcloud_font()
    return {
        "font_path": path,
        "ok": bool(path),
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
