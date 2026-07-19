# -*- coding: utf-8 -*-
"""
CRIMECAST — per-district sentiment word clouds from news headlines.
Uses `wordcloud` if installed; otherwise frequency bars (always works).
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

import numpy as np
import pandas as pd

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

_TOKEN_RE = re.compile(r"[A-Za-z]{3,}|[\u0B80-\u0BFF]{2,}")


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
    if not text:
        return []
    toks = _TOKEN_RE.findall(str(text).lower())
    return [t for t in toks if t not in _STOP and not t.isdigit()]


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
    """
    if not ctr:
        return None
    try:
        from wordcloud import WordCloud
        from PIL import Image as PILImage
        import matplotlib

        matplotlib.use("Agg")
        wc = WordCloud(
            width=width,
            height=height,
            background_color="#0e0e12",
            colormap="Blues",
            max_words=80,
            prefer_horizontal=0.85,
            relative_scaling=0.45,
            min_font_size=10,
        ).generate_from_frequencies(dict(ctr))
        return wc.to_image()
    except Exception:
        return None


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
