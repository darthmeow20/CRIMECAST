"""
CRIMECAST Interactive Dashboard
Run with: streamlit run dashboard.py

BUILD_ID must match the Live Feed status line (proves Streamlit loaded this file).
"""

from __future__ import annotations

BUILD_ID = "classic-dashboard"

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
import warnings
import logging


def _safe_live_status(n_models, n_media, n_harvest, high_count, metric, window) -> None:
    """Bottom Live Feed status — no HTML ticker, no fragile open_alerts f-string."""
    try:
        med = int(n_media or 0) or int(n_harvest or 0)
    except Exception:
        med = 0
    try:
        hi = int(high_count or 0)
    except Exception:
        hi = 0
    st.caption(
        f"Status {BUILD_ID} · models {n_models} · media {med} · HIGH {hi} · "
        f"{metric} · {window}"
    )

# Suppress the common "missing ScriptRunContext" warning when running in bare mode
# or during certain import/caching phases. This is harmless.
warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")
logging.getLogger("streamlit").setLevel(logging.ERROR)

# Custom CSS — CRIMECAST dark ops UI
def apply_custom_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Pure black ops background like reference */
    .stApp {
        background-color: #0a0a0c !important;
        color: #e8e8ed;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Sidebar — pure black with red accent active items */
    [data-testid="stSidebar"] {
        background-color: #0c0c0f !important;
        border-right: 1px solid #1f1f28 !important;
    }
    [data-testid="stSidebar"] * { color: #c8c8d0 !important; }
    [data-testid="stSidebar"] .stRadio > div { gap: 2px; }
    [data-testid="stSidebar"] .stRadio label {
        padding: 10px 14px !important;
        border-radius: 10px;
        margin: 2px 0;
        border: 1px solid transparent;
        transition: all 0.15s ease;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(220, 38, 38, 0.08) !important;
        border-color: rgba(220, 38, 38, 0.25) !important;
    }
    /* Selected radio look */
    [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {
        background: transparent !important;
    }

    /* Brand block */
    .ops-brand {
        display: flex; align-items: center; gap: 10px;
        padding: 6px 4px 14px 4px;
        border-bottom: 1px solid #1f1f28;
        margin-bottom: 12px;
    }
    .ops-logo {
        width: 36px; height: 36px; border-radius: 10px;
        background: linear-gradient(135deg, #ef4444, #f97316);
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; color: white; font-size: 14px;
        box-shadow: 0 0 18px rgba(239,68,68,0.45);
    }
    .ops-brand-text { line-height: 1.15; }
    .ops-brand-text .t1 { font-size: 0.68rem; color: #9ca3af; letter-spacing: 0.06em; font-weight: 600; }
    .ops-brand-text .t2 { font-size: 0.95rem; color: #f3f4f6; font-weight: 800; letter-spacing: 0.02em; }

    .ops-status {
        margin-top: 18px; padding: 10px 12px; border-radius: 10px;
        background: #121218; border: 1px solid #1f1f28;
        font-size: 0.72rem; color: #9ca3af;
    }
    .ops-status .dot {
        display: inline-block; width: 7px; height: 7px; border-radius: 50%;
        background: #22c55e; box-shadow: 0 0 8px #22c55e; margin-right: 6px;
    }

    /* Top ops bar */
    .ops-topbar {
        display: flex; flex-wrap: wrap; align-items: center; gap: 12px;
        background: #0e0e12; border: 1px solid #1f1f28; border-radius: 12px;
        padding: 10px 14px; margin-bottom: 1rem;
    }
    .ops-topbar .crumb { color: #6b7280; font-size: 0.78rem; font-weight: 600; }
    .ops-topbar .title { color: #f3f4f6; font-weight: 700; font-size: 0.95rem; }
    .stream-pill {
        background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.45);
        color: #4ade80; font-size: 0.68rem; font-weight: 700;
        padding: 3px 10px; border-radius: 999px; letter-spacing: 0.04em;
    }
    .stream-pill::before {
        content: ''; display: inline-block; width: 6px; height: 6px;
        background: #22c55e; border-radius: 50%; margin-right: 6px;
        box-shadow: 0 0 6px #22c55e;
    }

    /* Metric glass cards with glow */
    [data-testid="stMetric"] {
        background: linear-gradient(160deg, #14141a 0%, #0f0f14 100%);
        border: 1px solid #24242e;
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 8px 28px rgba(0,0,0,0.45);
    }
    [data-testid="stMetric"] label {
        color: #9ca3af !important;
        font-size: 0.7rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #f9fafb !important;
        font-weight: 800 !important;
        font-size: 1.65rem !important;
    }

    h1, h2, h3 { color: #f3f4f6 !important; font-weight: 700 !important; }
    p, label, .stMarkdown, span { color: #d1d5db; }

    /* Compact icon-only refresh control */
    .refresh-icon-wrap div[data-testid="stButton"] > button {
        min-width: 2.25rem !important;
        width: 2.25rem !important;
        height: 2.25rem !important;
        padding: 0 !important;
        border-radius: 8px !important;
        font-size: 0.95rem !important;
        line-height: 1 !important;
    }
    div[data-testid="stSidebar"] .refresh-icon-wrap div[data-testid="stButton"] > button {
        min-width: 2.1rem !important;
        width: 2.1rem !important;
        height: 2.1rem !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%) !important;
        color: #fff !important; border: none !important;
        font-weight: 700 !important; border-radius: 10px !important;
        box-shadow: 0 4px 18px rgba(220, 38, 38, 0.35);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
        color: #fff !important;
    }

    .stAlert {
        background: #14141a !important;
        border: 1px solid #2a2a35 !important;
        border-left: 4px solid #dc2626 !important;
        border-radius: 12px !important;
        color: #e5e7eb !important;
    }

    .stDataFrame, [data-testid="stDataFrame"] {
        border-radius: 12px; border: 1px solid #24242e;
    }
    .stSelectbox > div > div, .stNumberInput input, .stTextInput input, .stTextArea textarea {
        background-color: #14141a !important;
        border: 1px solid #2a2a35 !important;
        border-radius: 10px !important;
        color: #e5e7eb !important;
    }

    /* Live feed news cards */
    .feed-card {
        background: #121218;
        border: 1px solid #24242e;
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    .feed-card .src {
        font-size: 0.72rem; color: #9ca3af; margin-bottom: 4px;
    }
    .feed-card .src .news-tag {
        background: rgba(59,130,246,0.15); color: #60a5fa;
        padding: 1px 6px; border-radius: 4px; font-weight: 700; margin-right: 6px;
    }
    .feed-card .headline {
        color: #f3f4f6; font-weight: 600; font-size: 0.92rem; line-height: 1.35;
        margin-bottom: 8px;
    }
    .chip {
        display: inline-block; font-size: 0.68rem; font-weight: 600;
        padding: 2px 8px; border-radius: 999px; margin-right: 4px; margin-bottom: 2px;
    }
    .chip.pos { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
    .chip.neg { background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
    .chip.neu { background: rgba(156,163,175,0.12); color: #d1d5db; border: 1px solid rgba(156,163,175,0.25); }
    .chip.dist { background: rgba(99,102,241,0.12); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3); }
    .chip.crime { background: rgba(249,115,22,0.12); color: #fb923c; border: 1px solid rgba(249,115,22,0.3); }

    /* District heat bars */
    .heat-row {
        display: flex; align-items: center; gap: 10px;
        padding: 8px 12px; margin-bottom: 6px;
        border-radius: 8px; background: #14141a; border: 1px solid #24242e;
    }
    .heat-rank { width: 22px; color: #6b7280; font-size: 0.75rem; font-weight: 700; }
    .heat-name { flex: 1; color: #f3f4f6; font-weight: 600; font-size: 0.88rem; }
    .heat-meta { color: #9ca3af; font-size: 0.72rem; text-align: right; min-width: 90px; }
    .heat-val { color: #f9fafb; font-weight: 700; font-size: 0.9rem; min-width: 42px; text-align: right; }

    .panel {
        background: #0e0e12; border: 1px solid #24242e; border-radius: 14px;
        padding: 14px 16px; margin-bottom: 12px;
    }
    .panel-title {
        color: #9ca3af; font-size: 0.72rem; font-weight: 700;
        letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 10px;
    }

    div[data-testid="stSidebarNav"] { display: none; }
    </style>
    """, unsafe_allow_html=True)


def ops_topbar(title: str = "CRIMECAST — Tamil Nadu"):
    st.markdown(
        f"""
        <div class="ops-topbar">
            <span class="crumb">CRIMECAST /</span>
            <span class="title">{title}</span>
            <span class="stream-pill">STREAMING</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str, badges: list | None = None):
    """Compat wrapper — ops style section header."""
    ops_topbar(title)
    st.caption(subtitle)
    if badges:
        chips = " ".join(
            f'<span class="chip {b.get("cls","neu")}">{b["text"]}</span>' for b in badges
        )
        st.markdown(chips, unsafe_allow_html=True)


# Severe crime / harm language → high negative score
_HIGH_NEG_KW = (
    "murder", "killed", "homicide", "rape", "sexual assault", "pocso",
    "massacre", "lynch", "beheaded", "shot dead", "stabbed to death",
    "acid attack", "gang rape", "molest", "kidnap", "abduct",
    "dead body", "body found", "suicide", "blast", "bomb",
    "கொலை", "பாலியல்", "கற்பழிப்பு", "கொலைமுயற்சி", "பிணம்",
    "கடத்தல்", "தாக்குதலில் பலி", "சுட்டுக் கொலை",
)
_NEG_KW = (
    "attack", "assault", "violence", "clash", "fir", "arrest", "accused",
    "charge", "complaint", "vandal", "threat", "riot", "beaten", "crime",
    "police", "booked", "custody", "theft", "robbery", "bribery", "corruption",
    "narcotics", "drug", "scandal", "controversy", "injury", "injured",
    "தாக்குதல்", "கைது", "வன்முறை", "புகார்", "வழக்கு", "திருட்டு",
    "லஞ்சம்", "போதைப்பொருள்", "சர்ச்சை", "குற்றம்", "காயம்",
)
_TVK_MARKERS = (
    "tvk", "tamilaga", "vettri kazhagam", "vetti kazhagam",
    "தமிழக வெற்றி", "தமிழகவெற்றி", "வெற்றி கழகம்",
)


def _headline_text(row, hcol: str | None) -> str:
    if hcol:
        return str(row.get(hcol) or "")
    return str(row.get("headline") or row.get("text") or row.get("source_text") or "")


def is_tvk_related(text: str) -> bool:
    t = (text or "").casefold()
    if not t:
        return False
    if any(m in t for m in _TVK_MARKERS) or "tvk" in t:
        return True
    if ("vijay" in t or "விஜய்" in t) and any(
        k in t for k in ("party", "tvk", "kazhagam", "கட்சி", "rally", "cadre")
    ):
        return True
    return False


def negativity_score(
    text: str,
    *,
    sentiment_label: str = "",
    polarity: float | None = None,
    crime_intensity: float | None = None,
    priority: str = "",
) -> float:
    """Higher = more negative. 0 = not treated as negative news."""
    t = (text or "").casefold()
    lab = (sentiment_label or "").strip().lower()
    score = 0.0

    if lab in ("negative", "neg", "high"):
        score += 2.5
    elif lab in ("positive", "pos", "low"):
        score -= 2.0

    if polarity is not None:
        try:
            p = float(polarity)
            if p < 0:
                score += min(4.0, abs(p) * 5.0)
            elif p > 0.15:
                score -= 1.5
        except (TypeError, ValueError):
            pass

    if crime_intensity is not None:
        try:
            ci = float(crime_intensity)
            if ci >= 6:
                score += 3.0
            elif ci >= 3:
                score += 1.5
            elif ci > 0:
                score += 0.5
        except (TypeError, ValueError):
            pass

    high_hits = sum(1 for k in _HIGH_NEG_KW if k in t)
    neg_hits = sum(1 for k in _NEG_KW if k in t)
    score += high_hits * 2.5 + min(3.0, neg_hits * 0.6)

    # Soft boost: negative TVK / tagged priority (still no UI label)
    if is_tvk_related(t) and (high_hits or neg_hits or lab in ("negative", "neg") or (polarity is not None and float(polarity or 0) < 0)):
        score += 1.2
    if str(priority or "").lower() in ("tvk_negative", "tvk_crime"):
        score += 1.0

    return score


def is_high_negative(score: float, text: str = "") -> bool:
    """Top-tier severity for the first 3 feed slots."""
    t = (text or "").casefold()
    if any(k in t for k in _HIGH_NEG_KW):
        return True
    return score >= 4.0


def build_negative_news_feed(
    feed: pd.DataFrame,
    *,
    top_n: int = 14,
    high_n: int = 3,
) -> pd.DataFrame:
    """
    Live Feed order:
      1–3  → high negative news (worst first)
      4+   → other negative news (newest first)
    Positive/neutral items are excluded when enough negative rows exist.
    """
    if feed is None or feed.empty:
        return feed if feed is not None else pd.DataFrame()

    show = feed.copy()
    hcol = next((c for c in ("headline", "text", "source_text") if c in show.columns), None)
    if "date" in show.columns:
        show["_dt"] = pd.to_datetime(show["date"], errors="coerce")
    else:
        show["_dt"] = pd.NaT

    def _row_score(row) -> float:
        text = _headline_text(row, hcol)
        sent = str(row.get("sentiment_label") or row.get("label") or "")
        pol = row.get("polarity")
        try:
            pol_f = float(pol) if pol is not None and str(pol) not in ("", "nan") else None
        except (TypeError, ValueError):
            pol_f = None
        ci = row.get("crime_intensity")
        try:
            ci_f = float(ci) if ci is not None and str(ci) not in ("", "nan") else None
        except (TypeError, ValueError):
            ci_f = None
        return negativity_score(
            text,
            sentiment_label=sent,
            polarity=pol_f,
            crime_intensity=ci_f,
            priority=str(row.get("priority") or ""),
        )

    show["_neg_score"] = show.apply(_row_score, axis=1)
    show["_text"] = show.apply(lambda r: _headline_text(r, hcol), axis=1)

    # Negative = score above floor (keyword/sentiment hit)
    neg = show[show["_neg_score"] > 0.4].copy()
    if neg.empty:
        # fallback: newest items if nothing scores negative
        return show.sort_values("_dt", ascending=False, na_position="last").head(top_n)

    neg["_high"] = neg.apply(
        lambda r: is_high_negative(float(r["_neg_score"]), str(r.get("_text") or "")),
        axis=1,
    )

    high = neg[neg["_high"]].sort_values(
        by=["_neg_score", "_dt"], ascending=[False, False], na_position="last"
    )
    other = neg[~neg["_high"]].sort_values(
        by=["_dt", "_neg_score"], ascending=[False, False], na_position="last"
    )

    # If fewer than high_n "high" rows, pull next-worst negatives into the top block
    high_pick = high.head(high_n)
    if len(high_pick) < high_n:
        need = high_n - len(high_pick)
        filler = other.head(need)
        other = other.iloc[need:]
        high_pick = pd.concat([high_pick, filler], ignore_index=True)

    # Remaining high (beyond top 3) join the "other negative" section by date
    high_rest = high.iloc[high_n:] if len(high) > high_n else high.iloc[0:0]
    other_block = pd.concat([high_rest, other], ignore_index=True)
    other_block = other_block.sort_values(
        by=["_dt", "_neg_score"], ascending=[False, False], na_position="last"
    )

    out = pd.concat([high_pick, other_block], ignore_index=True)
    # Dedupe by headline if present
    if hcol and hcol in out.columns:
        out = out.drop_duplicates(subset=[hcol], keep="first")
    elif "headline" in out.columns:
        out = out.drop_duplicates(subset=["headline"], keep="first")

    return out.head(top_n)


def render_feed_card(source: str, headline: str, label: str = "Neutral",
                     crime: str = "Crime", district: str = "", url: str = ""):
    lab = (label or "Neutral").strip().lower()
    chip_cls = "neg" if lab in ("negative", "high") else ("pos" if lab in ("positive", "low") else "neu")
    dist_html = f'<span class="chip dist">@ {district}</span>' if district else ""
    url_html = f' · <a href="{url}" style="color:#60a5fa;text-decoration:none;" target="_blank">link</a>' if url else ""
    st.markdown(
        f"""
        <div class="feed-card">
            <div class="src"><span class="news-tag">NEWS</span> {source}{url_html}</div>
            <div class="headline">{headline}</div>
            <div>
                <span class="chip {chip_cls}">{label}</span>
                <span class="chip crime">{crime}</span>
                {dist_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def heat_color(rank: int, total: int) -> str:
    """White/light (cool) → deep blue (hot) for district heat bars."""
    if total <= 1:
        return "#0c4a6e"
    t = rank / max(total - 1, 1)  # 0 = hottest, 1 = coolest
    # hottest deep blue → coolest near white
    r = int(12 + t * (255 - 12))
    g = int(74 + t * (255 - 74))
    b = int(110 + t * (255 - 110))
    return f"rgb({r},{g},{b})"


def render_district_heat(df: pd.DataFrame, value_col: str, name_col: str = "district",
                         label_col: str | None = None, top_n: int = 15):
    if df.empty or value_col not in df.columns:
        st.info("No district ranking data yet. Run option 7 or populate media data.")
        return
    work = df.copy()
    if name_col not in work.columns and "district_city" in work.columns:
        name_col = "district_city"
    work = work.sort_values(value_col, ascending=False).head(top_n).reset_index(drop=True)
    st.markdown('<div class="panel"><div class="panel-title">District heat · ranking</div>', unsafe_allow_html=True)
    for i, r in work.iterrows():
        name = str(r.get(name_col, "?"))
        val = r.get(value_col, 0)
        try:
            val_f = float(val)
            val_s = f"{val_f:.0f}" if val_f >= 10 else f"{val_f:.2f}"
        except Exception:
            val_s = str(val)
        meta = str(r.get(label_col, "")) if label_col and label_col in work.columns else ""
        bg = heat_color(int(i), len(work))
        st.markdown(
            f"""
            <div class="heat-row" style="border-left: 3px solid {bg};">
                <span class="heat-rank">{int(i)+1}</span>
                <span class="heat-name">{name}</span>
                <span class="heat-meta">{meta}</span>
                <span class="heat-val">{val_s}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
ML_READY_FILE = PROJECT_ROOT / "dataset" / "cleaned" / "crimecast_ml_ready.csv"
OUTPUT_DIR = PROJECT_ROOT / "model_outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
MODELS_DIR = PROJECT_ROOT / "models"
SENTIMENT_SCORES = OUTPUT_DIR / "sentiment_scores.csv"
CRIME_PREDICTIONS = OUTPUT_DIR / "crime_predictions.csv"
RAPE_2026 = OUTPUT_DIR / "rape_predictions_2026_all_districts.csv"
MEDIA_HARVEST = OUTPUT_DIR / "media_harvest_tn_crime_2024_2025.csv"


def _latest_media_harvest_path() -> Path | None:
    """Prefer rolling combined harvest, else newest media_harvest_*.csv, then legacy."""
    combined = OUTPUT_DIR / "media_harvest_tn_crime_latest.csv"
    if combined.exists():
        return combined
    candidates = sorted(
        OUTPUT_DIR.glob("media_harvest_tn_crime_*.csv"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    if MEDIA_HARVEST.exists():
        return MEDIA_HARVEST
    return None


# Cache heavy loads — prefer SQLite (data/crimecast.db), fall back to CSV
@st.cache_data
def load_ml_data():
    try:
        from db import load_dataset_or_csv

        df = load_dataset_or_csv("ml_ready", ML_READY_FILE)
        if not df.empty:
            return df
    except Exception:
        pass
    if ML_READY_FILE.exists():
        return pd.read_csv(ML_READY_FILE)
    return pd.DataFrame()

@st.cache_data
def load_sentiment_scores():
    try:
        from db import load_dataset_or_csv

        df = load_dataset_or_csv("sentiment_scores", SENTIMENT_SCORES)
        if not df.empty:
            return df
    except Exception:
        pass
    if SENTIMENT_SCORES.exists():
        return pd.read_csv(SENTIMENT_SCORES)
    return pd.DataFrame()

@st.cache_data
def load_crime_predictions():
    try:
        from db import load_dataset_or_csv

        df = load_dataset_or_csv("crime_predictions", CRIME_PREDICTIONS)
        if not df.empty:
            return df
    except Exception:
        pass
    if CRIME_PREDICTIONS.exists():
        return pd.read_csv(CRIME_PREDICTIONS)
    return pd.DataFrame()

def normalize_2026_forecast_df(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Roll city units into TN38 parents, drop junk, re-rank.
    Madurai City→Madurai, Avadi/Tambaram→Chennai. Never fills from news.
    """
    if raw is None or not isinstance(raw, pd.DataFrame) or raw.empty:
        return pd.DataFrame()
    df = raw.copy()
    rnc = "district" if "district" in df.columns else (
        "district_city" if "district_city" in df.columns else None
    )
    if not rnc:
        return df
    try:
        from district_entities import to_tn38, TN38
    except Exception:
        to_tn38 = None  # type: ignore
        TN38 = []  # type: ignore

    if to_tn38 is not None:
        df["_d38"] = df[rnc].astype(str).map(lambda x: to_tn38(x, default=None))
    else:
        df["_d38"] = df[rnc].astype(str)
    # Drop junk / unmapped (Railway, Cyber Cell, Other Units, …)
    df = df[df["_d38"].notna() & (df["_d38"].astype(str).str.strip() != "")].copy()
    if df.empty:
        return pd.DataFrame()

    skip = {
        "district", "district_city", "_d38", "risk_level", "method", "model",
        "confidence", "rank", "is_fallback",
    }
    num_cols = [
        c for c in df.columns
        if c not in skip and pd.api.types.is_numeric_dtype(df[c])
    ]
    sum_keys = ("incident", "pred_low", "pred_high", "width", "data_point")
    agg: dict[str, str] = {}
    for c in num_cols:
        cl = c.lower()
        agg[c] = "sum" if any(k in cl for k in sum_keys) else "mean"
    keep_first = [c for c in ("method", "model", "confidence") if c in df.columns]
    g = df.groupby("_d38", as_index=False)
    if agg:
        out = g.agg({**agg, **{c: "first" for c in keep_first}}) if keep_first else g.agg(agg)
    else:
        cols = ["_d38"] + keep_first
        out = df.drop_duplicates(subset=["_d38"], keep="first")[cols]
    out = out.rename(columns={"_d38": "district"})

    # Ensure full TN38 (missing → NaN forecast — map must not paint news)
    if TN38:
        base = pd.DataFrame({"district": list(TN38)})
        out = base.merge(out, on="district", how="left")

    metric = None
    for cand in ("predicted_2026_rape_incidents", "predicted_value"):
        if cand in out.columns:
            metric = cand
            break
    if metric:
        out[metric] = pd.to_numeric(out[metric], errors="coerce")
        # Keep both column names for map/radio compatibility
        if metric == "predicted_value" and "predicted_2026_rape_incidents" not in out.columns:
            out["predicted_2026_rape_incidents"] = out[metric]
        if metric == "predicted_2026_rape_incidents" and "predicted_value" not in out.columns:
            out["predicted_value"] = out[metric]

        def _risk(v):
            try:
                p = float(v) if pd.notna(v) else 0.0
            except Exception:
                p = 0.0
            r = round(min(1.0, 0.7 * min(max(p, 0.0) / 25.0, 1.0)), 3)
            lv = "HIGH" if r > 0.65 else ("MEDIUM" if r > 0.35 else "LOW")
            return r, lv

        risks, levels = zip(*(_risk(v) for v in out[metric])) if len(out) else ([], [])
        if len(out):
            out["rape_risk_index"] = list(risks)
            out["risk_level"] = list(levels)
        out = out.sort_values(metric, ascending=False, na_position="last").reset_index(drop=True)
        out["rank"] = range(1, len(out) + 1)
    return out


@st.cache_data
def load_rape_2026():
    raw = None
    try:
        from db import load_dataset_or_csv, load_rape_2026 as _db_rape

        raw = load_dataset_or_csv("rape_2026", RAPE_2026)
        if raw is None or raw.empty:
            raw = _db_rape()
            # structured table may use payload_json only — keep full CSV prefer
            if raw is not None and not raw.empty and "predicted_2026_rape_incidents" not in raw.columns:
                if RAPE_2026.exists():
                    raw = pd.read_csv(RAPE_2026)
    except Exception:
        raw = None
    if raw is None or (isinstance(raw, pd.DataFrame) and raw.empty):
        if RAPE_2026.exists():
            try:
                raw = pd.read_csv(RAPE_2026)
            except Exception:
                return pd.DataFrame()
        else:
            return pd.DataFrame()
    try:
        return normalize_2026_forecast_df(raw)
    except Exception:
        return raw if isinstance(raw, pd.DataFrame) else pd.DataFrame()


@st.cache_data
def load_news_signals():
    news_path = OUTPUT_DIR / "news_signals.csv"
    try:
        from db import load_dataset_or_csv

        df = load_dataset_or_csv("news_signals", news_path)
        if not df.empty:
            return df
    except Exception:
        pass
    if news_path.exists():
        return pd.read_csv(news_path)
    return pd.DataFrame()


@st.cache_data
def load_media_harvest():
    path = _latest_media_harvest_path()
    try:
        from db import load_dataset_or_csv

        df = load_dataset_or_csv("media_harvest", path)
        if not df.empty:
            return df
    except Exception:
        pass
    if path is not None and path.exists():
        return pd.read_csv(path)
    raw = OUTPUT_DIR / "news_signals_raw.csv"
    if raw.exists():
        return pd.read_csv(raw)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def cached_current_affairs_heat(
    harvest_sig: str,
    news_sig: str,
    recent_days: int,
) -> tuple[pd.DataFrame, str, str]:
    """Cache heat by file signature so Live Feed / scoreboard don't recompute every click."""
    harvest_df = load_media_harvest()
    news_df = load_news_signals()
    return build_current_affairs_heat(harvest_df, news_df, recent_days=recent_days)


def _data_sig(*paths: Path) -> str:
    parts = []
    for p in paths:
        if p is None:
            continue
        try:
            if p.exists():
                st_ = p.stat()
                parts.append(f"{p.name}:{st_.st_mtime_ns}:{st_.st_size}")
        except Exception:
            parts.append(str(p))
    return "|".join(parts) if parts else "none"


def get_current_affairs_heat(recent_days: int = 90) -> tuple[pd.DataFrame, str, str]:
    """Public helper: cached news heat for a time window."""
    hpath = _latest_media_harvest_path()
    npath = OUTPUT_DIR / "news_signals.csv"
    return cached_current_affairs_heat(
        _data_sig(hpath) if hpath else "no-harvest",
        _data_sig(npath),
        int(recent_days),
    )


def data_freshness_caption() -> str:
    """Short 'as of' line for demos / viva (college-usable transparency)."""
    from datetime import datetime

    bits = []
    for label, path in (
        ("ML data", ML_READY_FILE),
        ("News", _latest_media_harvest_path() or (OUTPUT_DIR / "news_signals.csv")),
        ("2026 forecast", RAPE_2026),
    ):
        try:
            if path is not None and Path(path).exists():
                ts = datetime.fromtimestamp(Path(path).stat().st_mtime)
                bits.append(f"{label} {ts.strftime('%Y-%m-%d %H:%M')}")
        except Exception:
            pass
    if not bits:
        return "Data: load pipeline outputs under model_outputs/ and dataset/cleaned/"
    return "As of · " + " · ".join(bits)


# Language packs — switch via sidebar (English ↔ Tamil)
UI_EN: dict[str, str] = {
    "Live Feed": "Live Feed",
    "District Map & Scoreboard": "District Map & Scoreboard",
    "Accuracy Check": "Accuracy Check",
    "Predict": "Predict",
    "Sentiment": "Sentiment",
    "2026 Forecasts": "2026 Forecasts",
    "Word Clouds": "Word Clouds",
    "District Compare": "District Compare",
    "Risk Explain": "Risk Explain",
    "Health": "Health",
    "How it works": "How it works",
    "Refresh news": "Refresh news",
    "News time window": "News time window",
    "Live view": "Live view",
    "Feed controls": "Feed controls",
    "Export brief": "Export brief",
    "Alert log": "Alert log",
    "Official vs media": "Official vs media",
    "Scenario only": "Scenario only (not fact)",
    "Language": "Language",
    "Murder rate": "Murder rate",
    "Rape rate": "Rape rate",
    "News 90d": "News 90d",
    "Focus district": "Focus district",
    "Compare with": "Compare with",
    "Map data source": "Map data source",
    "Show map": "Show TN map (slower)",
    "District detail": "District detail",
    "HIGH alerts": "HIGH alerts",
    "Build accuracy": "Build accuracy table",
    "Targets": "Targets",
    "Max districts": "Max districts",
    "Media news volume": "Media news volume",
    "ML-ready": "ML-ready (latest year)",
    "Scoreboard rank by": "Scoreboard rank by (high → low)",
    "none": "— none —",
    "Recent headlines": "Recent headlines",
    "Preview top districts": "Preview · top districts",
    "News language split": "News language split",
}

UI_TA: dict[str, str] = {
    "Live Feed": "நேரடி ஊட்டம்",
    "District Map & Scoreboard": "மாவட்ட வரைபடம்",
    "Accuracy Check": "துல்லியப் பரிசோதனை",
    "Predict": "கணிப்பு",
    "Sentiment": "உணர்வுப் பகுப்பாய்வு",
    "2026 Forecasts": "2026 கணிப்புகள்",
    "Word Clouds": "சொல் மேகங்கள்",
    "District Compare": "மாவட்ட ஒப்பீடு",
    "Risk Explain": "இடர் விளக்கம்",
    "Health": "ஆரோக்கியம்",
    "How it works": "எப்படி வேலை செய்கிறது",
    "Refresh news": "செய்தி புதுப்பி",
    "News time window": "செய்தி கால அளவு",
    "Live view": "நேரடி பார்வை",
    "Feed controls": "ஊட்டக் கட்டுப்பாடு",
    "Export brief": "அறிக்கை பதிவிறக்கு",
    "Alert log": "எச்சரிக்கை பதிவு",
    "Official vs media": "அதிகாரப்பூர்வ vs ஊடகம்",
    "Scenario only": "காட்சி மட்டும் (உண்மை அல்ல)",
    "Language": "மொழி",
    "Murder rate": "கொலை விகிதம்",
    "Rape rate": "பாலியல் குற்ற விகிதம்",
    "News 90d": "செய்தி 90 நாள்",
    "Focus district": "மாவட்டம்",
    "Compare with": "ஒப்பிடு",
    "Map data source": "வரைபடத் தரவு",
    "Show map": "தமிழ்நாடு வரைபடம் (மெதுவு)",
    "District detail": "மாவட்ட விவரம்",
    "HIGH alerts": "உயர் எச்சரிக்கை",
    "Build accuracy": "துல்லிய அட்டவணை",
    "Targets": "இலக்குகள்",
    "Max districts": "மாவட்ட எண்ணிக்கை",
    "Media news volume": "ஊடக செய்தி அளவு",
    "ML-ready": "ML தரவு (சமீப ஆண்டு)",
    "Scoreboard rank by": "தரவரிசை (உயர் → தாழ்)",
    "none": "— இல்லை —",
    "Recent headlines": "சமீபத்திய தலைப்புகள்",
    "Preview top districts": "முன்னணி மாவட்டங்கள்",
    "News language split": "செய்தி மொழிப் பிரிவு",
}


def t(key: str) -> str:
    """UI string for current language (session: ui_lang = EN | TA)."""
    try:
        lang = st.session_state.get("ui_lang", "EN")
    except Exception:
        lang = "EN"
    if lang == "TA":
        return UI_TA.get(key, UI_EN.get(key, key))
    return UI_EN.get(key, key)


def plot_official_vs_news_chart(
    area: str,
    ml_data: pd.DataFrame,
    harvest_df: pd.DataFrame,
    news_df: pd.DataFrame,
) -> go.Figure | None:
    """Priority 5: before/after style — official rates vs current news heat for one district."""
    card = build_district_scorecard(
        area, ml_data, news_df, harvest_df, pd.DataFrame(), pd.DataFrame()
    )
    rows = []
    for lab, key in (
        ("Murder rate (official)", "murder_rate"),
        ("Rape rate (official)", "rape_rate"),
        ("News 90d (media)", "news_90d"),
    ):
        v = card.get(key)
        if v is not None and pd.notna(v):
            try:
                rows.append({
                    "metric": lab,
                    "value": float(v),
                    "layer": "Official" if "official" in lab.lower() else "Media",
                })
            except (TypeError, ValueError):
                pass
    if len(rows) < 1:
        return None
    df = pd.DataFrame(rows)
    fig = px.bar(
        df,
        x="metric",
        y="value",
        color="layer",
        title=f"{area} · official rates vs media news heat",
        template="plotly_dark",
        color_discrete_map={"Official": "#0ea5e9", "Media": "#a855f7"},
        barmode="group",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0e0e12",
        height=320,
        xaxis_title="",
        yaxis_title="Value (different units — compare pattern, not absolute)",
        legend_title_text="",
    )
    return fig


def persist_and_load_alerts(
    ml_data: pd.DataFrame,
    harvest_df: pd.DataFrame,
    news_df: pd.DataFrame,
    rape_2026_df: pd.DataFrame,
) -> tuple[list, pd.DataFrame]:
    """Compute alerts, log new ones, return (alerts, log_df)."""
    alerts = compute_alert_rules(ml_data, harvest_df, news_df, rape_2026_df)
    try:
        from db import log_alerts, load_alert_log, init_db

        init_db()
        log_alerts(alerts)
        log_df = load_alert_log(limit=40)
    except Exception:
        log_df = pd.DataFrame()
    return alerts, log_df


def build_current_affairs_heat(
    harvest_df: pd.DataFrame,
    news_df: pd.DataFrame,
    *,
    recent_days: int = 90,
) -> tuple[pd.DataFrame, str, str]:
    """
    Best Live Feed heat map strategy:

      Primary  → last `recent_days` (default 90) headline **count** per district
      Soft fill → districts with no recent news get a mild score from **all-time**
                 harvest totals (scaled down so they don't dominate the map)
      Fallback → latest-year news_signals counts

    Metric name: `news_90d` (headline count in window; + soft_fill flag).
    Districts only — never newspaper/source names.
    """
    from datetime import datetime, timedelta

    try:
        from tn_map import TN_DISTRICT_CANONICAL, _normalize_name
    except Exception:
        TN_DISTRICT_CANONICAL = []
        def _normalize_name(x):  # type: ignore
            return str(x).strip().lower()

    try:
        from district_entities import resolve_district, TN_DISTRICTS
    except Exception:
        TN_DISTRICTS = TN_DISTRICT_CANONICAL

        def resolve_district(text: str, default: str = "Other / Statewide") -> str:
            return default

    # Newspaper / outlet / junk tokens that must never appear as district ranks
    junk = {
        "", "other / statewide", "unknown", "india", "tamil nadu", "tn", "nan", "none",
        "quick", "killed", "teenage", "courier", "pushpa", "dinamani", "dinamalar",
        "dmk’s", "dmk's", "telangana", "taramani", "poonamallee",
        "the hindu", "hindu", "times of india", "toi", "indian express", "new indian express",
        "dt next", "deccan chronicle", "hindustan times", "news18", "india today",
        "the quint", "bbc", "bbc tamil", "ananda vikatan", "vikatan", "puthiya thalaimurai",
        "daily thanthi", "dina thanthi", "thanthi", "maalai malar", "dinakaran",
        "google news", "google news tamil", "news media", "social media reports",
        "local news", "local reports", "reuters", "ani", "ptI", "pti",
        "sun news", "zee news", "ndtv", "republic", "polimer", "jaya tv",
        "latest", "source", "headline", "other units", "cyber cell",
    }
    # Canonical set for validation (casefold)
    canon_cf = {_normalize_name(d) for d in list(TN_DISTRICT_CANONICAL) + list(TN_DISTRICTS)}
    # Also accept common city suffixes mapped via resolve
    outlet_tokens = (
        "hindu", "thanthi", "dinamalar", "dinamani", "times", "express", "vikatan",
        "news18", "ndtv", "bbc", "google", "thanthi", "maalai", "dt next", "chronicle",
    )

    def _is_valid_district_name(name: str) -> bool:
        n = str(name or "").strip()
        if len(n) < 3:
            return False
        nl = n.casefold()
        if nl in junk or any(t in nl for t in outlet_tokens if len(t) > 3):
            # allow real districts that contain substring? e.g. none
            if _normalize_name(n) not in canon_cf:
                return False
        if _normalize_name(n) in canon_cf:
            return True
        # resolve may return canonical
        try:
            r = resolve_district(n, default="")
            return bool(r) and _normalize_name(r) in canon_cf
        except Exception:
            return False

    def _resolve_row_district(district_val: object, headline: object) -> str | None:
        """Map row → canonical TN district; never return newspaper names."""
        d = str(district_val or "").strip()
        h = str(headline or "")
        # Prefer entity resolve on combined text
        try:
            from_h = resolve_district(f"{d} {h}", default="")
            if from_h and _is_valid_district_name(from_h) and from_h.casefold() not in (
                "other / statewide", "other",
            ):
                return from_h
        except Exception:
            pass
        if d and _is_valid_district_name(d):
            try:
                r = resolve_district(d, default=d)
                if r and _is_valid_district_name(r):
                    return r
            except Exception:
                if _normalize_name(d) in canon_cf:
                    return d
        if h:
            try:
                r = resolve_district(h, default="")
                if r and _is_valid_district_name(r) and r.casefold() not in (
                    "other / statewide", "other",
                ):
                    return r
            except Exception:
                pass
        return None

    def _assign_districts_fast(h: pd.DataFrame) -> pd.Series:
        """Map rows → district using unique district strings only (fast)."""
        dcol = "district" if "district" in h.columns else (
            "district_city" if "district_city" in h.columns else None
        )
        hcol = "headline" if "headline" in h.columns else None
        n = len(h)
        if n == 0:
            return pd.Series(dtype=object)

        raw_d = (
            h[dcol].astype(str).str.strip()
            if dcol
            else pd.Series([""] * n, index=h.index)
        )
        # Build map unique district_raw → canonical (once each)
        uniq_vals = raw_d.unique().tolist()
        val_map: dict[str, str | None] = {}
        for val in uniq_vals:
            if not val or str(val).lower() in ("nan", "none", ""):
                val_map[val] = None
                continue
            if _is_valid_district_name(str(val)):
                try:
                    canon = resolve_district(str(val), default=str(val))
                except Exception:
                    canon = str(val)
                val_map[val] = canon if _is_valid_district_name(canon) else None
            else:
                val_map[val] = _resolve_row_district(val, "")

        out = raw_d.map(val_map)
        # Fill missing from unique headlines (capped) — only if many still missing
        need = out.isna()
        if need.any() and hcol is not None and int(need.sum()) <= 400:
            headlines = h.loc[need, hcol].astype(str)
            uniq_hl = headlines.unique().tolist()[:300]
            hl_map: dict[str, str | None] = {
                hl: _resolve_row_district("", hl[:120]) for hl in uniq_hl
            }
            out.loc[need] = headlines.map(hl_map)
        return out

    primary = pd.Series(dtype=float)
    all_time = pd.Series(dtype=float)
    window_label = f"{recent_days}d"

    if harvest_df is not None and not harvest_df.empty and (
        "headline" in harvest_df.columns
        or "district" in harvest_df.columns
        or "district_city" in harvest_df.columns
    ):
        h = harvest_df.copy()
        # Resolve districts once for whole harvest (was 2–3× full iterrows — very slow)
        h["_dist"] = _assign_districts_fast(h)
        h = h.dropna(subset=["_dist"])
        if not h.empty:
            all_time = h.groupby("_dist").size().astype(float)
            if "date" in h.columns:
                h["_dt"] = pd.to_datetime(h["date"], errors="coerce")
                cutoff = datetime.now() - timedelta(days=recent_days)
                recent = h[h["_dt"].notna() & (h["_dt"] >= cutoff)]
                primary = recent.groupby("_dist").size().astype(float)
                if primary.empty or primary.sum() == 0:
                    y_now = datetime.now().year
                    ymask = h["_dt"].notna() & (h["_dt"].dt.year == y_now)
                    primary = h.loc[ymask].groupby("_dist").size().astype(float)
                    window_label = f"YTD {y_now}"
            else:
                primary = all_time.copy()
                window_label = "all"

    # news_signals fill — only valid districts
    if news_df is not None and not news_df.empty and "district_city" in news_df.columns:
        n = news_df.copy()
        n["_d"] = n["district_city"].map(
            lambda x: _resolve_row_district(x, "") or (x if _is_valid_district_name(str(x)) else None)
        )
        n = n.dropna(subset=["_d"])
        if "news_count" in n.columns and not n.empty:
            if "year" in n.columns:
                y = pd.to_numeric(n["year"], errors="coerce")
                latest = n[y == y.max()]
            else:
                latest = n
            sig = latest.groupby("_d")["news_count"].sum().astype(float)
            # Drop invalid keys
            sig = sig[[k for k in sig.index if _is_valid_district_name(str(k))]]
            if primary.empty and not sig.empty:
                primary = sig
                window_label = "signals"
            sig_all = n.groupby("_d")["news_count"].sum().astype(float)
            for k, v in sig_all.items():
                if _is_valid_district_name(str(k)):
                    all_time[k] = all_time.get(k, 0) + float(v)

    if primary.empty and all_time.empty:
        return pd.DataFrame(), "", "district"

    # Soft fill: districts with no recent news get up to 25% of all-time max scale
    # so map isn't blank, but hotspots stay driven by recent volume
    if not all_time.empty:
        at_max = float(all_time.max()) if all_time.max() > 0 else 1.0
        fill_cap = 0.25 * (float(primary.max()) if not primary.empty and primary.max() > 0 else at_max)
        for dist, vol in all_time.items():
            if dist not in primary.index or primary.get(dist, 0) <= 0:
                soft = fill_cap * (float(vol) / at_max)
                primary[dist] = max(float(primary.get(dist, 0) or 0), soft)

    # Ensure known TN districts appear (0 if truly no data after fill)
    for d in TN_DISTRICT_CANONICAL:
        if d not in primary.index:
            # try normalized match
            key = d
            primary[key] = float(primary.get(key, 0) or 0)

    # Final filter: districts only
    primary = primary[[k for k in primary.index if _is_valid_district_name(str(k))]]
    if primary.empty:
        return pd.DataFrame(), "", "district"

    g = primary.rename("news_90d").reset_index()
    g.columns = ["district", "news_90d"]
    g["news_90d"] = pd.to_numeric(g["news_90d"], errors="coerce").fillna(0.0)
    g = g[g["district"].map(lambda x: _is_valid_district_name(str(x)))]
    g["is_soft_fill"] = g["news_90d"] < 1.0
    g = g.sort_values("news_90d", ascending=False).reset_index(drop=True)
    g["heat_window"] = window_label
    return g, "news_90d", "district"


def _latest_ml_by_district(ml_data: pd.DataFrame) -> pd.DataFrame:
    """
    Latest year per district, constrained to **38 TN districts**.
    Merges city units (Madurai City → Madurai, Avadi → Chennai, …).
    Always fills population_lakhs (estimate if missing/zero).
    """
    if ml_data is None or ml_data.empty or "district_city" not in ml_data.columns:
        return pd.DataFrame()
    m = ml_data.copy()
    if "year" in m.columns:
        m = m.sort_values("year").groupby("district_city", as_index=False).tail(1)

    try:
        from district_entities import to_tn38, TN38, fill_population_lakhs_series
    except Exception:
        TN38 = []

        def to_tn38(x: str, default=None):  # type: ignore
            return str(x)

        def fill_population_lakhs_series(names, existing=None):  # type: ignore
            return [15.0] * len(list(names))

    m["_d38"] = m["district_city"].astype(str).map(lambda x: to_tn38(x, default=None))
    m = m[m["_d38"].notna()].copy()
    if m.empty:
        return pd.DataFrame()
    m["district_city"] = m["_d38"]
    m = m.drop(columns=["_d38"], errors="ignore")

    # Collapse duplicates after merge (Madurai + Madurai City → one row)
    num_cols = m.select_dtypes(include=[np.number]).columns.tolist()
    year_col = "year" if "year" in m.columns else None
    pop_col = None
    for c in ("population_lakhs", "complaints_projected_population_lakhs"):
        if c in m.columns:
            pop_col = c
            break

    out_rows = []
    for dist, g in m.groupby("district_city"):
        row: dict[str, Any] = {"district_city": dist}
        if year_col:
            row[year_col] = pd.to_numeric(g[year_col], errors="coerce").max()
        if "area_type" in g.columns:
            row["area_type"] = g["area_type"].iloc[0]

        pop_vals = None
        if pop_col:
            pop_vals = pd.to_numeric(g[pop_col], errors="coerce")
        elif "population_lakhs" in g.columns:
            pop_vals = pd.to_numeric(g["population_lakhs"], errors="coerce")
        if pop_vals is not None:
            # sum positive pops only (city+district); zeros ignored for estimate later
            pos = pop_vals[pop_vals > 0.05]
            row["population_lakhs"] = float(pos.sum()) if len(pos) else np.nan
        else:
            row["population_lakhs"] = np.nan

        for c in num_cols:
            if c in (year_col, pop_col, "population_lakhs", "log_population"):
                continue
            s = pd.to_numeric(g[c], errors="coerce")
            cl = c.lower()
            if any(
                k in cl
                for k in ("incidence", "incidents", "complaints", "victims", "news_count", "count")
            ) and "rate" not in cl and "share" not in cl and "ratio" not in cl:
                row[c] = float(s.sum(skipna=True)) if s.notna().any() else np.nan
            elif "rate" in cl or cl.endswith("_r") or "polarity" in cl or "intensity" in cl:
                w = pop_vals if pop_vals is not None else None
                if w is not None and w.fillna(0).sum() > 0 and s.notna().any():
                    ww = w.reindex(s.index).fillna(0).clip(lower=0)
                    if ww.sum() > 0:
                        row[c] = float((s.fillna(0) * ww).sum() / ww.sum())
                    else:
                        row[c] = float(s.mean(skipna=True))
                else:
                    row[c] = float(s.mean(skipna=True)) if s.notna().any() else np.nan
            else:
                row[c] = float(s.mean(skipna=True)) if s.notna().any() else np.nan
        out_rows.append(row)

    m = pd.DataFrame(out_rows)
    # Force population estimates for zeros / missing
    m["population_lakhs"] = fill_population_lakhs_series(
        m["district_city"].astype(str).tolist(),
        pd.to_numeric(m["population_lakhs"], errors="coerce"),
    )
    m["population_lakhs"] = pd.to_numeric(m["population_lakhs"], errors="coerce")
    m["log_population"] = np.log1p(m["population_lakhs"].clip(lower=0))
    # Ensure only TN38 (max 38 rows)
    if TN38:
        m = m[m["district_city"].isin(TN38)]
    return m.reset_index(drop=True)


def news_lang_split(harvest_df: pd.DataFrame) -> pd.DataFrame:
    """Counts of Tamil vs English headlines in harvest (Tier-2)."""
    if harvest_df is None or harvest_df.empty:
        return pd.DataFrame(columns=["language", "headlines", "share_pct"])
    h = harvest_df.copy()
    if "lang" in h.columns:
        lang = h["lang"].astype(str).str.lower().map(
            lambda x: "Tamil" if x.startswith("ta") else ("English" if x.startswith("en") else x)
        )
    else:
        # Heuristic: Tamil script in headline
        def _guess(s: str) -> str:
            s = str(s)
            return "Tamil" if any("\u0b80" <= c <= "\u0bff" for c in s) else "English"
        lang = h["headline"].map(_guess) if "headline" in h.columns else pd.Series(["Unknown"] * len(h))
    counts = lang.value_counts().reset_index()
    counts.columns = ["language", "headlines"]
    total = counts["headlines"].sum()
    counts["share_pct"] = (counts["headlines"] / total * 100).round(1) if total else 0
    return counts


# Head-to-head: DMK vs TVK (official data lags → media is support signal)
TN_COMPARE_PARTIES: list[str] = ["DMK", "TVK"]
PARTY_COLORS = {"DMK": "#ef4444", "TVK": "#a855f7"}

# Ruling context (only DMK has CM-term data in CRIMECAST years)
TN_REGIME_PERIODS: list[dict[str, Any]] = [
    {
        "regime_id": "dmk_stalin",
        "regime": "DMK (Stalin)",
        "party": "DMK",
        "cm": "M.K. Stalin",
        "start_year": 2021,
        "end_year": 2030,
        "color": "#ef4444",
        "note": "In office from May 2021 · official crime rates available (lagging)",
    },
    {
        "regime_id": "tvk_none",
        "regime": "TVK (not ruled)",
        "party": "TVK",
        "cm": "—",
        "start_year": None,
        "end_year": None,
        "color": "#a855f7",
        "note": "No CM term yet · media / news is the support data source",
    },
]

# Headline markers for party-linked news (EN + TA) — DMK vs TVK
PARTY_NEWS_MARKERS: dict[str, tuple[str, ...]] = {
    "DMK": (
        "dmk", "dravida munnetra", "mk stalin", "m.k. stalin", "stalin govt",
        "stalin government", "திமுக", "ஸ்டாலின்", "தி.மு.க",
    ),
    "TVK": (
        "tvk", "tamilaga vettri", "tamilaga vetti", "vettri kazhagam",
        "தமிழக வெற்றி", "தமிழகவெற்றி", "வெற்றி கழகம்",
    ),
}

# Preferred crime metrics for regime scoring (lower = better public safety)
REGIME_METRIC_COLS: list[tuple[str, str, str]] = [
    # (column, short label, type: rate|count)
    ("murder_homicide_murder_rate", "Murder rate", "rate"),
    ("women_crimes_rape_r", "Rape rate", "rate"),
    ("women_crimes_assault_on_women_with_intent_to_outrage_her_modesty_r_crime_rate", "Assault on women rate", "rate"),
    ("complaints_rate_of_cognizable_crime_ipc_sll", "Cognizable crime rate", "rate"),
    ("complaints_total_complaints", "Total complaints", "count"),
    ("murder_homicide_murder_incidence", "Murder incidents", "count"),
    ("women_crimes_rape_sec_376_i", "Rape incidents", "count"),
]


def regime_for_year(year: int) -> dict[str, Any]:
    """Map calendar year → ruling party. CRIMECAST years are DMK-led; TVK never ruler."""
    dmk = next(r for r in TN_REGIME_PERIODS if r["party"] == "DMK")
    y = int(year)
    if y == 2021:
        return {**dmk, "note": "Transition year (DMK from May 2021)"}
    # 2022+ (and any earlier years still in file) → DMK for this product frame
    return dmk


def detect_parties_in_text(text: str) -> list[str]:
    """Return which of DMK / TVK are mentioned in a headline."""
    t = (text or "").casefold()
    if not t:
        return []
    hits = []
    for party, markers in PARTY_NEWS_MARKERS.items():
        if any(m in t for m in markers):
            hits.append(party)
    return hits


def build_party_news_comparison(
    harvest_df: pd.DataFrame,
    news_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    DMK vs TVK media support data (party-linked crime/negative coverage).
    Used because official stats lag. Lower negative load → higher clean_score.
    """
    frames = []
    for df in (harvest_df, news_df):
        if df is not None and not df.empty:
            frames.append(df)
    if not frames:
        return pd.DataFrame(), {
            "winner": "—",
            "reason": "No news harvest yet. Refresh news for DMK vs TVK media support.",
        }

    h = pd.concat(frames, ignore_index=True, sort=False)
    hcol = next((c for c in ("headline", "text", "source_text") if c in h.columns), None)
    if hcol is None:
        return pd.DataFrame(), {"winner": "—", "reason": "No headline column in news data."}

    if "date" in h.columns:
        h = h.drop_duplicates(subset=[hcol, "date"], keep="last")
    else:
        h = h.drop_duplicates(subset=[hcol], keep="last")

    tallies: dict[str, dict[str, float]] = {
        p: {
            "party": p,
            "mentions": 0,
            "negative_mentions": 0,
            "high_neg_mentions": 0,
            "neg_score_sum": 0.0,
        }
        for p in TN_COMPARE_PARTIES
    }

    for _, row in h.iterrows():
        text = str(row.get(hcol) or "")
        parties = detect_parties_in_text(text)
        if not parties:
            continue
        sent = str(row.get("sentiment_label") or row.get("label") or "")
        try:
            pol = float(row["polarity"]) if "polarity" in row.index and pd.notna(row.get("polarity")) else None
        except (TypeError, ValueError):
            pol = None
        try:
            ci = (
                float(row["crime_intensity"])
                if "crime_intensity" in row.index and pd.notna(row.get("crime_intensity"))
                else None
            )
        except (TypeError, ValueError):
            ci = None
        nscore = negativity_score(text, sentiment_label=sent, polarity=pol, crime_intensity=ci)
        is_neg = nscore > 0.4 or (sent or "").lower() in ("negative", "neg", "high")
        is_high = is_high_negative(nscore, text)
        for p in parties:
            if p not in tallies:
                continue
            tallies[p]["mentions"] += 1
            if is_neg:
                tallies[p]["negative_mentions"] += 1
                tallies[p]["neg_score_sum"] += float(nscore)
            if is_high:
                tallies[p]["high_neg_mentions"] += 1

    rows = []
    for p in TN_COMPARE_PARTIES:
        t = tallies[p]
        m = int(t["mentions"])
        neg = int(t["negative_mentions"])
        high = int(t["high_neg_mentions"])
        avg_neg = (t["neg_score_sum"] / neg) if neg else 0.0
        neg_share = (neg / m * 100.0) if m else 0.0
        load = neg * 1.0 + high * 1.5 + avg_neg * 0.5
        rows.append({
            "party": p,
            "mentions": m,
            "negative_mentions": neg,
            "high_neg_mentions": high,
            "neg_share_pct": round(neg_share, 1),
            "avg_neg_score": round(avg_neg, 2),
            "negative_load": round(load, 2),
        })

    party_df = pd.DataFrame(rows)
    if len(party_df) and party_df["negative_load"].max() > 0:
        lo = float(party_df["negative_load"].min())
        hi = float(party_df["negative_load"].max())
        if hi > lo:
            party_df["clean_score"] = (
                (1.0 - (party_df["negative_load"] - lo) / (hi - lo)) * 100.0
            ).round(1)
        else:
            party_df["clean_score"] = party_df.apply(
                lambda r: 100.0 if r["mentions"] == 0 else 50.0, axis=1
            )
    else:
        party_df["clean_score"] = 50.0

    party_df.loc[party_df["mentions"] == 0, "clean_score"] = np.nan
    ranked = party_df.dropna(subset=["clean_score"]).sort_values(
        "clean_score", ascending=False
    ).reset_index(drop=True)
    party_df = party_df.sort_values("negative_load", ascending=True).reset_index(drop=True)
    party_df["rank_clean"] = party_df["clean_score"].rank(ascending=False, method="min")

    if not ranked.empty:
        winner = str(ranked.iloc[0]["party"])
        reason = (
            f"**{winner}** cleaner on party-linked negative/crime news "
            f"({float(ranked.iloc[0]['clean_score']):.1f}/100) · DMK vs TVK media support. "
            f"Official stats lag — media is a bridge signal, not a verdict alone."
        )
    else:
        winner = "—"
        reason = "No DMK / TVK party mentions in current news harvest. Refresh news."

    return party_df, {"winner": winner, "reason": reason}


def build_dmk_tvk_scoreboard(
    regime_df: pd.DataFrame,
    party_news_df: pd.DataFrame,
    year_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    DMK vs TVK board.
    - DMK: official/ML statewide safety (primary) + media clean (support)
    - TVK: media clean only (no CM-term official rates)
    Combined weights media less when official exists (official lags but still primary).
    """
    rows = []
    reg_map = {}
    if regime_df is not None and not regime_df.empty and "party" in regime_df.columns:
        for _, r in regime_df.iterrows():
            reg_map[str(r["party"]).upper()] = r

    news_map = {}
    if party_news_df is not None and not party_news_df.empty and "party" in party_news_df.columns:
        for _, r in party_news_df.iterrows():
            news_map[str(r["party"]).upper()] = r

    # Latest official-era year safety for DMK context
    dmk_latest_official = np.nan
    if year_df is not None and not year_df.empty and "year_safety_score" in year_df.columns:
        y = year_df.copy()
        y["year"] = pd.to_numeric(y["year"], errors="coerce")
        # Prefer ≤2023 official-era when present
        off = y[y["year"] <= 2023] if y["year"].notna().any() else y
        use = off if not off.empty else y
        if not use.empty and use["year_safety_score"].notna().any():
            dmk_latest_official = float(
                use.sort_values("year").iloc[-1]["year_safety_score"]
            )

    for p in TN_COMPARE_PARTIES:
        reg = reg_map.get(p)
        news = news_map.get(p)
        if p == "DMK":
            role = "Ruling · official crime data (lagging) + media support"
            official = (
                float(reg["safety_score"])
                if reg is not None
                else dmk_latest_official
            )
        else:
            role = "Not ruled · media support only (no official CM-term rates)"
            official = np.nan

        media = (
            float(news["clean_score"])
            if news is not None and pd.notna(news.get("clean_score"))
            else np.nan
        )
        row: dict[str, Any] = {
            "party": p,
            "role": role,
            "years_in_crime_data": str(reg["years_in_data"]) if reg is not None else "—",
            "official_safety_score": official,
            "ruling_trend": str(reg["trend"]) if reg is not None else "n/a",
            "news_mentions": int(news["mentions"]) if news is not None else 0,
            "news_negative": int(news["negative_mentions"]) if news is not None else 0,
            "news_high_neg": int(news["high_neg_mentions"]) if news is not None else 0,
            "media_clean_score": media,
            "data_basis": (
                "Official + media support" if p == "DMK" else "Media support only"
            ),
        }
        # Weighted combined: official primary when present, media always support
        if pd.notna(row["official_safety_score"]) and pd.notna(media):
            row["combined_score"] = round(
                0.65 * float(row["official_safety_score"]) + 0.35 * float(media), 1
            )
        elif pd.notna(row["official_safety_score"]):
            row["combined_score"] = round(float(row["official_safety_score"]), 1)
        elif pd.notna(media):
            row["combined_score"] = round(float(media), 1)
        else:
            row["combined_score"] = np.nan
        rows.append(row)

    out = pd.DataFrame(rows)
    if not out.empty and out["combined_score"].notna().any():
        out = out.sort_values(
            "combined_score", ascending=False, na_position="last"
        ).reset_index(drop=True)
        out["rank"] = range(1, len(out) + 1)
    return out


def _pick_regime_metrics(ml_data: pd.DataFrame) -> list[tuple[str, str, str]]:
    available = []
    for col, label, kind in REGIME_METRIC_COLS:
        if col in ml_data.columns and pd.to_numeric(ml_data[col], errors="coerce").notna().any():
            available.append((col, label, kind))
    return available


def build_year_crime_summary(ml_data: pd.DataFrame) -> pd.DataFrame:
    """Statewide mean of key crime metrics per year + regime label."""
    if ml_data is None or ml_data.empty or "year" not in ml_data.columns:
        return pd.DataFrame()
    m = ml_data.copy()
    m["year"] = pd.to_numeric(m["year"], errors="coerce")
    m = m.dropna(subset=["year"])
    m["year"] = m["year"].astype(int)
    metrics = _pick_regime_metrics(m)
    if not metrics:
        return pd.DataFrame()

    rows = []
    for y, g in m.groupby("year"):
        reg = regime_for_year(int(y))
        row: dict[str, Any] = {
            "year": int(y),
            "regime": reg["regime"],
            "party": reg["party"],
            "cm": reg["cm"],
            "n_districts": int(g["district_city"].nunique()) if "district_city" in g.columns else len(g),
            "data_tier": "official-era" if int(y) <= 2023 else "media/proxy-era",
        }
        for col, label, _kind in metrics:
            vals = pd.to_numeric(g[col], errors="coerce").dropna()
            row[label] = float(vals.mean()) if len(vals) else np.nan
            row[f"{label}__col"] = col
        rows.append(row)
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def build_regime_comparison(ml_data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """
    Aggregate crime metrics by TN regime from ML-ready data.
    Higher safety_score = better (lower crime rates relative to peers in dataset).

    Returns (regime_table, year_table, verdict_dict).
    """
    year_df = build_year_crime_summary(ml_data)
    empty_verdict = {
        "winner": "—",
        "reason": "Not enough multi-regime data in CRIMECAST ML-ready file.",
        "caveat": "",
    }
    if year_df.empty:
        return pd.DataFrame(), year_df, empty_verdict

    metric_labels = [
        lab for _c, lab, _k in REGIME_METRIC_COLS
        if lab in year_df.columns
    ]
    if not metric_labels:
        return pd.DataFrame(), year_df, empty_verdict

    # Min-max invert each metric across years → 0–100 component (higher = safer)
    scored = year_df.copy()
    component_cols = []
    for lab in metric_labels:
        s = pd.to_numeric(scored[lab], errors="coerce")
        lo, hi = s.min(skipna=True), s.max(skipna=True)
        if pd.isna(lo) or pd.isna(hi) or hi <= lo:
            comp = pd.Series(50.0, index=scored.index)
        else:
            # lower crime → higher score
            comp = (1.0 - (s - lo) / (hi - lo)) * 100.0
        cname = f"score_{lab}"
        scored[cname] = comp
        component_cols.append(cname)

    scored["year_safety_score"] = scored[component_cols].mean(axis=1, skipna=True)

    # Regime aggregates (mean of year means)
    reg_rows = []
    for regime_name, g in scored.groupby("regime"):
        party = str(g["party"].iloc[0]) if "party" in g.columns else ""
        cm = str(g["cm"].iloc[0]) if "cm" in g.columns else ""
        r: dict[str, Any] = {
            "regime": regime_name,
            "party": party,
            "cm": cm,
            "years_in_data": ", ".join(str(int(y)) for y in sorted(g["year"].unique())),
            "n_years": int(g["year"].nunique()),
            "safety_score": float(g["year_safety_score"].mean()),
        }
        for lab in metric_labels:
            r[lab] = float(pd.to_numeric(g[lab], errors="coerce").mean())
        # YoY direction within regime
        g2 = g.sort_values("year")
        if len(g2) >= 2 and g2["year_safety_score"].notna().sum() >= 2:
            first = float(g2["year_safety_score"].iloc[0])
            last = float(g2["year_safety_score"].iloc[-1])
            r["trend"] = "improving" if last > first + 2 else ("worsening" if last < first - 2 else "stable")
            r["trend_delta"] = round(last - first, 1)
        else:
            r["trend"] = "n/a"
            r["trend_delta"] = 0.0
        reg_rows.append(r)

    regime_df = pd.DataFrame(reg_rows)
    if not regime_df.empty:
        regime_df = regime_df.sort_values("safety_score", ascending=False).reset_index(drop=True)
        regime_df["rank"] = regime_df.index + 1

    # Verdict
    years_covered = sorted(scored["year"].unique().tolist())
    regimes_with_data = regime_df["regime"].tolist() if not regime_df.empty else []
    caveat = (
        "Official crime stats lag. Years ≤2023 ≈ official-era labels; 2024–2026 may be thinner/proxy. "
        "Safety score = lower statewide crime rates (relative in our file only). "
        "Media headlines are support data for DMK vs TVK — not a substitute for official rates."
    )

    if len(regimes_with_data) >= 2:
        winner = str(regime_df.iloc[0]["regime"])
        wscore = float(regime_df.iloc[0]["safety_score"])
        reason = (
            f"**{winner}** ranks higher on composite crime-safety score "
            f"({wscore:.1f}/100) vs other regime(s) present in the dataset "
            f"({', '.join(regimes_with_data)}). Years covered: {years_covered}."
        )
    elif len(regimes_with_data) == 1:
        only = regimes_with_data[0]
        best_year_row = scored.loc[scored["year_safety_score"].idxmax()]
        worst_year_row = scored.loc[scored["year_safety_score"].idxmin()]
        trend = regime_df.iloc[0].get("trend", "n/a")
        winner = only
        reason = (
            f"**{only}** is the ruling party in ML-ready years {years_covered}. "
            f"TVK has no official CM-term rates — use **media support** for DMK vs TVK. "
            f"Best official year: **{int(best_year_row['year'])}** "
            f"({float(best_year_row['year_safety_score']):.1f}); "
            f"weakest: **{int(worst_year_row['year'])}** "
            f"({float(worst_year_row['year_safety_score']):.1f}). Trend: **{trend}**."
        )
    else:
        winner = "—"
        reason = empty_verdict["reason"]

    year_out = scored[
        ["year", "regime", "party", "cm", "n_districts", "data_tier", "year_safety_score"]
        + metric_labels
    ].copy()
    year_out = year_out.sort_values("year").reset_index(drop=True)

    verdict = {"winner": winner, "reason": reason, "caveat": caveat, "metric_labels": metric_labels}
    return regime_df, year_out, verdict


def build_regime_subperiod_compare(year_df: pd.DataFrame) -> pd.DataFrame:
    """Compare sub-periods when only one party is in the dataset (e.g. early vs later DMK term)."""
    if year_df is None or year_df.empty or "year" not in year_df.columns:
        return pd.DataFrame()
    y = year_df.copy()
    y["year"] = pd.to_numeric(y["year"], errors="coerce").astype("Int64")

    def _bucket(yr) -> str:
        if pd.isna(yr):
            return "unknown"
        yr = int(yr)
        if yr <= 2023:
            return "2022–2023 (early term / official-era)"
        if yr <= 2025:
            return "2024–2025 (mid term / mixed data)"
        return "2026 (latest / forecast-era)"

    y["subperiod"] = y["year"].map(_bucket)
    metric_cols = [
        c for c in y.columns
        if c not in ("year", "regime", "party", "cm", "n_districts", "data_tier",
                     "year_safety_score", "subperiod") and not str(c).endswith("__col")
    ]
    rows = []
    for sp, g in y.groupby("subperiod"):
        r: dict[str, Any] = {
            "subperiod": sp,
            "years": ", ".join(str(int(x)) for x in sorted(g["year"].dropna().unique())),
            "n_years": int(g["year"].nunique()),
        }
        if "year_safety_score" in g.columns:
            r["safety_score"] = float(pd.to_numeric(g["year_safety_score"], errors="coerce").mean())
        for c in metric_cols:
            r[c] = float(pd.to_numeric(g[c], errors="coerce").mean())
        rows.append(r)
    out = pd.DataFrame(rows)
    if not out.empty and "safety_score" in out.columns:
        out = out.sort_values("safety_score", ascending=False).reset_index(drop=True)
    return out


def build_accuracy_table(
    ml_data: pd.DataFrame,
    targets: list[str] | None = None,
    max_areas: int = 40,
) -> pd.DataFrame:
    """
    Before/after style table: official history vs model_raw vs blended prediction.
    Uses predict_for_area for a sample of districts (Tier-2 evaluation).
    """
    if ml_data is None or ml_data.empty:
        return pd.DataFrame()
    try:
        from predict import predict_for_area, resolve_target
    except Exception:
        return pd.DataFrame()

    targets = targets or [
        "murder_homicide_murder_rate",
        "women_crimes_rape_r",
    ]
    areas = sorted(ml_data["district_city"].dropna().astype(str).unique().tolist())
    # Prefer interesting districts first
    prefer = ["Thoothukudi", "Madurai", "Chennai", "Coimbatore", "Salem", "Tirunelveli", "Villupuram"]
    ordered = [a for a in prefer if a in areas] + [a for a in areas if a not in prefer]
    ordered = ordered[:max_areas]

    rows = []
    for area in ordered:
        for t in targets:
            if t not in ml_data.columns:
                continue
            try:
                r = predict_for_area(t, area, year=2026)
                official = r.get("history_baseline")
                raw = r.get("model_raw")
                final = r.get("prediction")
                actual = r.get("actual")
                # ranking helper for murder rate
                err_raw = abs(float(raw) - float(official)) if raw is not None and official is not None else None
                err_blend = abs(float(final) - float(official)) if final is not None and official is not None else None
                rows.append({
                    "district": area,
                    "target": r.get("target_label", t),
                    "official_hist_mean": official,
                    "model_raw": raw,
                    "blended_pred": round(float(final), 3) if final is not None else None,
                    "template_actual": actual,
                    "abs_err_raw": round(err_raw, 3) if err_raw is not None else None,
                    "abs_err_blend": round(err_blend, 3) if err_blend is not None else None,
                    "blend_better": (
                        err_blend < err_raw if err_raw is not None and err_blend is not None else None
                    ),
                })
            except Exception:
                continue
    return pd.DataFrame(rows)


def district_brief_html(card: dict[str, Any], drivers: list[str]) -> str:
    """HTML brief printable to PDF from browser (no extra deps)."""
    dist = card.get("district", "District")
    lines = "\n".join(f"<li>{d}</li>" for d in drivers)
    hls = "\n".join(f"<li>{h}</li>" for h in card.get("headlines", [])[:8])

    def _fmt(v, nd=2):
        if v is None or (isinstance(v, float) and (v != v)):
            return "—"
        try:
            return f"{float(v):.{nd}f}"
        except Exception:
            return str(v)

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<title>CRIMECAST — {dist}</title>
<style>
 body {{ font-family: Segoe UI, Arial, sans-serif; margin: 32px; color: #111; max-width: 900px; }}
 h1 {{ color: #b91c1c; margin-bottom: 4px; }}
 .sub {{ color: #555; margin-top: 0; }}
 .grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }}
 .box {{ border: 1px solid #ddd; border-radius: 8px; padding: 12px; background: #fafafa; }}
 .k {{ color: #666; font-size: 11px; text-transform: uppercase; letter-spacing: .04em; }}
 .v {{ font-size: 20px; font-weight: 700; margin-top: 4px; }}
 .risk {{ display: inline-block; padding: 4px 10px; border-radius: 6px; background: #fee2e2; color: #991b1b; font-weight: 700; }}
 .pipe {{ font-size: 13px; color: #444; border-left: 3px solid #b91c1c; padding-left: 12px; margin: 16px 0; }}
</style></head><body>
<h1>CRIMECAST District Brief — {dist}</h1>
<p class="sub"><b>College prototype</b> · Tamil Nadu · official rates + news media.
 Not a live police / SCRB system.</p>
<p>Risk level: <span class="risk">{card.get('risk_level', '—')}</span>
 &nbsp;·&nbsp; Data year: <b>{card.get('year', '—')}</b>
 &nbsp;·&nbsp; News rank 90d: <b>#{card.get('news_rank', '—')}</b></p>
<div class="grid">
 <div class="box"><div class="k">Population (lakh) · மக்கள் தொகை</div><div class="v">{_fmt(card.get('population_lakhs'), 1)}</div></div>
 <div class="box"><div class="k">Murder rate · கொலை</div><div class="v">{_fmt(card.get('murder_rate'))}</div></div>
 <div class="box"><div class="k">Rape rate · பாலியல்</div><div class="v">{_fmt(card.get('rape_rate'))}</div></div>
 <div class="box"><div class="k">Murder / lakh</div><div class="v">{_fmt(card.get('murder_per_lakh'))}</div></div>
 <div class="box"><div class="k">Rape / lakh</div><div class="v">{_fmt(card.get('rape_per_lakh'))}</div></div>
 <div class="box"><div class="k">Complaints / lakh</div><div class="v">{_fmt(card.get('complaints_per_lakh'))}</div></div>
 <div class="box"><div class="k">News 90d · செய்தி</div><div class="v">{_fmt(card.get('news_90d'), 0)}</div></div>
 <div class="box"><div class="k">News / lakh</div><div class="v">{_fmt(card.get('news_per_lakh'))}</div></div>
 <div class="box"><div class="k">Complaints (raw)</div><div class="v">{_fmt(card.get('complaints'), 0)}</div></div>
 <div class="box"><div class="k">2026 rape forecast</div><div class="v">{_fmt(card.get('forecast_2026_rape'), 1)}</div></div>
 <div class="box"><div class="k">2026 risk index</div><div class="v">{_fmt(card.get('rape_risk_index'), 3)}</div></div>
 <div class="box"><div class="k">Sentiment polarity</div><div class="v">{_fmt(card.get('sentiment_polarity'), 3)}</div></div>
</div>
<div class="pipe">
 <b>How to read:</b> Rates / per-lakh are fairer across big vs small districts.
 News is media volume, not FIRs. 2026 numbers are <i>scenario trends</i>, not facts.
</div>
<h2>Why this district stands out · முக்கியம்</h2>
<ul>{lines}</ul>
<h2>Recent headlines · தலைப்புகள்</h2>
<ul>{hls or '<li>No headlines on file. Use Refresh news.</li>'}</ul>
<p style="color:#888;font-size:12px;">CRIMECAST · Media ≠ FIR · Print PDF (Ctrl+P) · Scenario models are not facts</p>
</body></html>"""


def build_map_metric_frame(
    metric: str,
    harvest_df: pd.DataFrame,
    news_df: pd.DataFrame,
    ml_data: pd.DataFrame,
    rape_2026_df: pd.DataFrame,
    *,
    recent_days: int = 90,
) -> tuple[pd.DataFrame, str, str, str]:
    """
    Live map metric toggle.
    Returns (df, value_col, name_col, caption).
    """
    if metric.startswith("News"):
        df, vcol, ncol = get_current_affairs_heat(recent_days=recent_days)
        cap = f"Crime news headline count · last {recent_days} days (+ soft fill). Not official rates."
        return df, vcol, ncol, cap

    latest = _latest_ml_by_district(ml_data)
    if metric == "Murder rate" and not latest.empty:
        col = "murder_homicide_murder_rate"
        if col in latest.columns:
            out = latest[["district_city", col]].copy()
            out = out.rename(columns={"district_city": "district", col: "murder_rate"})
            out["murder_rate"] = pd.to_numeric(out["murder_rate"], errors="coerce")
            return out.dropna(subset=["murder_rate"]), "murder_rate", "district", (
                "Official/latest ML-ready murder rate (per unit population). Prefer year ≤2023 for training truth."
            )

    if metric == "Rape rate" and not latest.empty:
        col = "women_crimes_rape_r"
        if col in latest.columns:
            out = latest[["district_city", col]].copy()
            out = out.rename(columns={"district_city": "district", col: "rape_rate"})
            out["rape_rate"] = pd.to_numeric(out["rape_rate"], errors="coerce")
            return out.dropna(subset=["rape_rate"]), "rape_rate", "district", (
                "Official/latest ML-ready rape rate."
            )

    if metric == "2026 rape forecast" and rape_2026_df is not None and not rape_2026_df.empty:
        df = rape_2026_df.copy()
        vcol = (
            "predicted_2026_rape_incidents"
            if "predicted_2026_rape_incidents" in df.columns
            else ("rape_risk_index" if "rape_risk_index" in df.columns else "")
        )
        ncol = "district" if "district" in df.columns else "district_city"
        return df, vcol, ncol, "Model / trend 2026 rape forecast (not live news)."

    return pd.DataFrame(), "", "district", "No data for this metric."


def compute_alert_rules(
    ml_data: pd.DataFrame,
    harvest_df: pd.DataFrame,
    news_df: pd.DataFrame,
    rape_2026_df: pd.DataFrame,
) -> list[dict[str, str]]:
    """Tier-1 alert rules → list of {level, title, detail}."""
    alerts: list[dict[str, str]] = []
    latest = _latest_ml_by_district(ml_data)

    # Rule 1: Thoothukudi murder rate > Madurai
    if not latest.empty and "murder_homicide_murder_rate" in latest.columns:
        def _rate(name: str) -> float | None:
            m = latest["district_city"].astype(str).str.casefold() == name.casefold()
            if not m.any():
                # partial match
                m = latest["district_city"].astype(str).str.casefold().str.contains(name.casefold(), na=False)
            if not m.any():
                return None
            v = pd.to_numeric(latest.loc[m, "murder_homicide_murder_rate"], errors="coerce").dropna()
            return float(v.iloc[0]) if len(v) else None

        t_rate = _rate("Thoothukudi") or _rate("Tuticorin")
        m_rate = _rate("Madurai")
        # Prefer district Madurai over Madurai City if both exist
        m_dist = latest[
            latest["district_city"].astype(str).str.casefold().eq("madurai")
        ]
        if not m_dist.empty:
            v = pd.to_numeric(m_dist["murder_homicide_murder_rate"], errors="coerce").dropna()
            if len(v):
                m_rate = float(v.iloc[0])
        if t_rate is not None and m_rate is not None and t_rate > m_rate:
            alerts.append({
                "level": "HIGH",
                "title": "Murder rate: Thoothukudi > Madurai",
                "detail": f"Thoothukudi {t_rate:.2f} vs Madurai {m_rate:.2f} (latest ML-ready / official-era data).",
            })

    # Rule 2: news_90d spike — district ≥ 2× median of active districts
    heat, vcol, _ = get_current_affairs_heat(recent_days=90)
    if not heat.empty and vcol in heat.columns:
        active = heat[heat[vcol] >= 1.0]
        if len(active) >= 3:
            med = float(active[vcol].median())
            if med > 0:
                spikes = active[active[vcol] >= 2.0 * med].sort_values(vcol, ascending=False)
                for _, row in spikes.head(5).iterrows():
                    alerts.append({
                        "level": "MED",
                        "title": f"News spike: {row['district']}",
                        "detail": f"90d news score {row[vcol]:.1f} (≥ 2× median {med:.1f}).",
                    })

    # Rule 3: 2026 HIGH rape risk districts
    if rape_2026_df is not None and not rape_2026_df.empty:
        r = rape_2026_df
        high = pd.DataFrame()
        if "risk_level" in r.columns:
            high = r[r["risk_level"].astype(str).str.upper() == "HIGH"]
        elif "rape_risk_index" in r.columns:
            high = r[r["rape_risk_index"] >= 0.65]
        if not high.empty:
            ncol = "district" if "district" in high.columns else "district_city"
            names = ", ".join(high[ncol].astype(str).head(6).tolist())
            alerts.append({
                "level": "HIGH",
                "title": f"2026 HIGH rape-risk districts ({len(high)})",
                "detail": names + ("…" if len(high) > 6 else ""),
            })

    return alerts


def explain_prediction_drivers(
    area: str,
    target: str,
    ml_data: pd.DataFrame,
    news_df: pd.DataFrame,
    harvest_df: pd.DataFrame,
    pred_row: dict | None = None,
) -> list[str]:
    """Top human-readable drivers for a district prediction (Tier-1 explainability)."""
    drivers: list[str] = []
    area_cf = str(area).strip().casefold()
    latest = _latest_ml_by_district(ml_data)

    # 1) Official / history baseline for this target
    tcol = target
    if pred_row and pred_row.get("target"):
        tcol = str(pred_row["target"])
    if not latest.empty and tcol in latest.columns:
        row = latest[latest["district_city"].astype(str).str.casefold() == area_cf]
        if not row.empty:
            hist = pd.to_numeric(row.iloc[0][tcol], errors="coerce")
            if pd.notna(hist):
                drivers.append(f"Latest table value for this target: **{float(hist):.2f}** (strong anchor for rates).")

    if pred_row:
        if pred_row.get("history_baseline") is not None:
            drivers.append(
                f"Official-history blend baseline: **{pred_row['history_baseline']}** "
                f"(model raw {pred_row.get('model_raw', '—')})."
            )
        if pred_row.get("prediction") is not None:
            drivers.append(f"Final prediction: **{float(pred_row['prediction']):.2f}**.")

    # 2) News volume rank
    heat, vcol, _ = get_current_affairs_heat(recent_days=90)
    if not heat.empty and vcol in heat.columns:
        h = heat.copy()
        h["_cf"] = h["district"].astype(str).str.casefold()
        match = h[h["_cf"] == area_cf]
        if match.empty:
            match = h[h["_cf"].str.contains(area_cf[:6], na=False)]
        if not match.empty:
            score = float(match.iloc[0][vcol])
            rank = int((h[vcol] > score).sum()) + 1
            drivers.append(f"Recent news heat (90d): **{score:.1f}** (rank #{rank} of {len(h)}).")

    # 3) Peer comparison (same target statewide median)
    if not latest.empty and tcol in latest.columns:
        series = pd.to_numeric(latest[tcol], errors="coerce").dropna()
        if len(series) > 3:
            med = float(series.median())
            row = latest[latest["district_city"].astype(str).str.casefold() == area_cf]
            if not row.empty:
                val = pd.to_numeric(row.iloc[0][tcol], errors="coerce")
                if pd.notna(val):
                    if float(val) > med * 1.15:
                        drivers.append(f"Above state median ({med:.2f}) for this metric — elevated relative risk.")
                    elif float(val) < med * 0.85:
                        drivers.append(f"Below state median ({med:.2f}) for this metric — lower relative level.")
                    else:
                        drivers.append(f"Near state median ({med:.2f}) for this metric.")

    # 4) Top local headlines
    if harvest_df is not None and not harvest_df.empty:
        h = harvest_df.copy()
        dcol = "district" if "district" in h.columns else "district_city"
        if dcol in h.columns and "headline" in h.columns:
            local = h[h[dcol].astype(str).str.casefold().str.contains(area_cf[:5], na=False)]
            if "date" in local.columns:
                local = local.copy()
                local["_dt"] = pd.to_datetime(local["date"], errors="coerce")
                local = local.sort_values("_dt", ascending=False)
            for _, r in local.head(2).iterrows():
                drivers.append(f"Recent headline: _{str(r.get('headline', ''))[:120]}_")

    if not drivers:
        drivers.append("Limited local features — prediction leans on statewide patterns and model prior.")
    return drivers[:6]


def build_media_news_volume_by_district(
    harvest_df: pd.DataFrame,
    news_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Aggregate **news headlines** into district-level volume (not raw signal rows).
    Uses cached heat (all-time window) — districts only.
    """
    g, vcol, ncol = get_current_affairs_heat(recent_days=365 * 5)
    if not g.empty and vcol in g.columns:
        out = g[[ncol, vcol]].copy()
        out = out.rename(columns={ncol: "district", vcol: "news_volume"})
        return out.sort_values("news_volume", ascending=False).reset_index(drop=True)
    return pd.DataFrame(columns=["district", "news_volume"])


def build_crime_density_frame(
    ml_data: pd.DataFrame,
    harvest_df: pd.DataFrame | None = None,
    news_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    District-level crime density for choropleth (population-aware).

    Columns:
      district, population_lakhs,
      murder_rate, rape_rate, cognizable_rate (official rates — already density-like),
      murder_per_lakh, rape_per_lakh, complaints_per_lakh, news_per_lakh,
      density_index (0–100 composite of available rates / per-lakh metrics)
    """
    latest = _latest_ml_by_district(ml_data)
    if latest.empty and (harvest_df is None or harvest_df.empty):
        return pd.DataFrame()

    if not latest.empty and "district_city" in latest.columns:
        d = latest.copy()
        d["district"] = d["district_city"].astype(str)
    else:
        d = pd.DataFrame({"district": []})

    # Population — always re-estimate zeros (latest may still carry 0 after merge)
    if not d.empty:
        if "population_lakhs" not in d.columns:
            d["population_lakhs"] = np.nan
        try:
            from district_entities import fill_population_lakhs_series, to_tn38, TN38

            d["district"] = d["district"].map(lambda x: to_tn38(str(x), default=None))
            d = d[d["district"].notna()].copy()
            d["population_lakhs"] = fill_population_lakhs_series(
                d["district"].astype(str).tolist(),
                pd.to_numeric(d["population_lakhs"], errors="coerce"),
            )
            d["population_lakhs"] = pd.to_numeric(d["population_lakhs"], errors="coerce")
            if TN38:
                # ensure one row per TN38 present
                d = d.drop_duplicates(subset=["district"], keep="first")
        except Exception:
            pass

    # Official rates (SCRB-style — already population-normalised)
    rate_map = {
        "murder_rate": "murder_homicide_murder_rate",
        "rape_rate": "women_crimes_rape_r",
        "cognizable_rate": "complaints_rate_of_cognizable_crime_ipc_sll",
    }
    if not latest.empty:
        for out_k, col in rate_map.items():
            if col in latest.columns:
                d[out_k] = pd.to_numeric(latest[col], errors="coerce").values

    # Counts → per lakh
    count_map = {
        "murder_incidence": "murder_homicide_murder_incidence",
        "rape_incidents": "women_crimes_rape_sec_376_i",
        "complaints": "complaints_total_complaints",
    }
    if not latest.empty:
        for out_k, col in count_map.items():
            if col in latest.columns:
                d[out_k] = pd.to_numeric(latest[col], errors="coerce").values

    pop_s = pd.to_numeric(d.get("population_lakhs"), errors="coerce").replace(0, np.nan)
    if "murder_incidence" in d.columns:
        d["murder_per_lakh"] = d["murder_incidence"] / pop_s
    if "rape_incidents" in d.columns:
        d["rape_per_lakh"] = d["rape_incidents"] / pop_s
    if "complaints" in d.columns:
        d["complaints_per_lakh"] = d["complaints"] / pop_s

    # News density (headlines / population)
    heat, vcol, _ = get_current_affairs_heat(recent_days=90)
    if not heat.empty and vcol in heat.columns:
        h = heat[["district", vcol]].copy()
        h = h.rename(columns={vcol: "news_90d"})
        h["district"] = h["district"].astype(str)
        d["district"] = d["district"].astype(str)
        d = d.merge(h, on="district", how="outer")
        # Re-fill population for any districts only present in news
        try:
            from district_entities import fill_population_lakhs_series

            d["population_lakhs"] = fill_population_lakhs_series(
                d["district"].astype(str).tolist(),
                pd.to_numeric(d.get("population_lakhs"), errors="coerce"),
            )
        except Exception:
            pass
        pop2 = pd.to_numeric(d.get("population_lakhs"), errors="coerce").replace(0, np.nan)
        d["news_per_lakh"] = pd.to_numeric(d["news_90d"], errors="coerce") / pop2

    # Prefer official rate when present; else per-lakh count
    if "murder_rate" not in d.columns and "murder_per_lakh" in d.columns:
        d["murder_rate"] = d["murder_per_lakh"]
    if "rape_rate" not in d.columns and "rape_per_lakh" in d.columns:
        d["rape_rate"] = d["rape_per_lakh"]

    # Composite density index 0–100 (mean of available z-scored metrics)
    dens_cols = [
        c
        for c in (
            "murder_rate",
            "rape_rate",
            "news_90d",
        )
        if c in d.columns and pd.to_numeric(d[c], errors="coerce").notna().any()
    ]
    if dens_cols:
        z_parts = []
        for c in dens_cols:
            s = pd.to_numeric(d[c], errors="coerce")
            mu, sd = s.mean(), s.std(ddof=0)
            if sd and sd > 0:
                z_parts.append((s - mu) / sd)
            else:
                z_parts.append(s * 0.0)
        zmean = sum(z_parts) / len(z_parts)
        # Map roughly to 0–100 via percentile rank
        d["density_index"] = zmean.rank(pct=True, method="average") * 100.0
    else:
        d["density_index"] = np.nan

    d = d[d["district"].notna() & (d["district"].astype(str).str.len() > 1)]
    d = d[~d["district"].astype(str).str.casefold().isin({"nan", "none", ""})]

    # Keep a lean frame only (latest.copy() is huge and can confuse select_dtypes)
    keep = [
        "district",
        "population_lakhs",
        "murder_rate",
        "rape_rate",
        "cognizable_rate",
        "murder_incidence",
        "rape_incidents",
        "complaints",
        "murder_per_lakh",
        "rape_per_lakh",
        "complaints_per_lakh",
        "news_90d",
        "news_per_lakh",
        "density_index",
    ]
    keep = [c for c in keep if c in d.columns]
    # Drop duplicate column names if any (merge / rename edge cases)
    out = d.loc[:, keep].copy()
    out = out.loc[:, ~out.columns.duplicated()].copy()
    return out.reset_index(drop=True)


def build_district_scoreboard_table(
    ml_data: pd.DataFrame,
    harvest_df: pd.DataFrame,
    news_df: pd.DataFrame,
    rape_2026_df: pd.DataFrame,
    *,
    rank_by: str = "news_90d",
) -> pd.DataFrame:
    """
    All-district scoreboard sorted high → low.
    Fast path: vectorized merges + cached news heat.
    """
    heat, vcol, _ = get_current_affairs_heat(recent_days=90)
    latest = _latest_ml_by_district(ml_data)

    board = pd.DataFrame()
    if not latest.empty and "district_city" in latest.columns:
        board = latest[["district_city"]].copy()
        board = board.rename(columns={"district_city": "district"})
        board["district"] = board["district"].astype(str)
        for key, col in [
            ("murder_rate", "murder_homicide_murder_rate"),
            ("rape_rate", "women_crimes_rape_r"),
            ("complaints", "complaints_total_complaints"),
            ("population_lakhs", "population_lakhs"),
        ]:
            if col in latest.columns:
                board[key] = pd.to_numeric(latest[col], errors="coerce").values
        # Fallback population column name from complaints
        if "population_lakhs" not in board.columns or board["population_lakhs"].isna().all():
            if "complaints_projected_population_lakhs" in latest.columns:
                board["population_lakhs"] = pd.to_numeric(
                    latest["complaints_projected_population_lakhs"], errors="coerce"
                ).values
    elif not heat.empty:
        board = heat[["district"]].copy()
        board["district"] = board["district"].astype(str)

    if board.empty:
        return pd.DataFrame()

    board = board.drop_duplicates(subset=["district"], keep="first")

    # Fill zero/missing population with TN district estimates
    try:
        from district_entities import fill_population_lakhs_series

        board["population_lakhs"] = fill_population_lakhs_series(
            board["district"].astype(str).tolist(),
            pd.to_numeric(board["population_lakhs"], errors="coerce")
            if "population_lakhs" in board.columns
            else None,
        )
    except Exception:
        board["population_lakhs"] = 15.0  # mid-TN fallback if estimate helper fails

    # News 90d (one heat build, left-join)
    if not heat.empty and vcol in heat.columns:
        h = heat[["district", vcol]].copy()
        h = h.rename(columns={vcol: "news_90d"})
        h["district"] = h["district"].astype(str)
        board = board.merge(h, on="district", how="outer")
        try:
            from district_entities import fill_population_lakhs_series

            board["population_lakhs"] = fill_population_lakhs_series(
                board["district"].astype(str).tolist(),
                pd.to_numeric(board["population_lakhs"], errors="coerce"),
            )
        except Exception:
            pass
    else:
        board["news_90d"] = np.nan

    # Per-lakh helpers (fairer compare across big vs small districts)
    if "population_lakhs" in board.columns:
        pop = pd.to_numeric(board["population_lakhs"], errors="coerce")
        if "complaints" in board.columns:
            board["complaints_per_lakh"] = pd.to_numeric(board["complaints"], errors="coerce") / pop.replace(0, np.nan)
        if "news_90d" in board.columns:
            board["news_per_lakh"] = pd.to_numeric(board["news_90d"], errors="coerce") / pop.replace(0, np.nan)

    # 2026 forecast join
    if rape_2026_df is not None and not rape_2026_df.empty:
        r26 = rape_2026_df.copy()
        ncol = "district" if "district" in r26.columns else "district_city"
        keep = [ncol]
        ren = {ncol: "district"}
        if "predicted_2026_rape_incidents" in r26.columns:
            keep.append("predicted_2026_rape_incidents")
            ren["predicted_2026_rape_incidents"] = "forecast_2026_rape"
        if "rape_risk_index" in r26.columns:
            keep.append("rape_risk_index")
        if "risk_level" in r26.columns:
            keep.append("risk_level")
        r26 = r26[keep].rename(columns=ren)
        r26["district"] = r26["district"].astype(str)
        board = board.merge(r26, on="district", how="outer")

    board = board[board["district"].notna() & (board["district"].astype(str).str.len() > 1)]
    board = board[~board["district"].astype(str).str.casefold().isin({"nan", "none", ""})]

    # Constrain to 38 TN districts; merge city duplicates
    try:
        from district_entities import to_tn38, TN38, fill_population_lakhs_series

        board["district"] = board["district"].map(lambda x: to_tn38(str(x), default=None))
        board = board[board["district"].notna()]
        # re-aggregate numeric cols if city+district both existed
        if not board.empty and board["district"].duplicated().any():
            num_b = [
                c
                for c in board.select_dtypes(include=[np.number]).columns.tolist()
                if c != "rank"
            ]
            if num_b:
                agg = {c: "mean" for c in num_b}
                for c in num_b:
                    cl = c.lower()
                    if any(
                        k in cl
                        for k in ("count", "news_90d", "complaints", "incidence", "forecast")
                    ):
                        agg[c] = "sum"
                board = board.groupby("district", as_index=False).agg(agg)
            else:
                board = board.drop_duplicates(subset=["district"], keep="first")
        if TN38 and not board.empty:
            board = board[board["district"].isin(TN38)]
        if not board.empty:
            board["population_lakhs"] = fill_population_lakhs_series(
                board["district"].astype(str).tolist(),
                pd.to_numeric(board["population_lakhs"], errors="coerce")
                if "population_lakhs" in board.columns
                else None,
            )
            board["population_lakhs"] = pd.to_numeric(
                board["population_lakhs"], errors="coerce"
            )
    except Exception:
        pass

    if board.empty:
        return pd.DataFrame()

    sort_col = rank_by if rank_by in board.columns else "news_90d"
    if sort_col not in board.columns:
        nums = board.select_dtypes(include=[np.number]).columns.tolist()
        sort_col = nums[0] if nums else "district"
    board = board.sort_values(sort_col, ascending=False, na_position="last").reset_index(drop=True)
    if "rank" in board.columns:
        board = board.drop(columns=["rank"])
    board.insert(0, "rank", range(1, len(board) + 1))
    return board


def build_district_scorecard(
    area: str,
    ml_data: pd.DataFrame,
    news_df: pd.DataFrame,
    harvest_df: pd.DataFrame,
    rape_2026_df: pd.DataFrame,
    sentiment_df: pd.DataFrame,
) -> dict[str, Any]:
    """Aggregate scorecard fields for one district."""
    area_cf = str(area).strip().casefold()
    card: dict[str, Any] = {"district": area}

    latest = _latest_ml_by_district(ml_data)
    if not latest.empty:
        row = latest[latest["district_city"].astype(str).str.casefold() == area_cf]
        if row.empty:
            row = latest[latest["district_city"].astype(str).str.casefold().str.contains(area_cf[:5], na=False)]
        if not row.empty:
            r = row.iloc[0]
            card["year"] = r.get("year")
            card["area_type"] = r.get("area_type")
            for key, col in [
                ("murder_rate", "murder_homicide_murder_rate"),
                ("murder_incidence", "murder_homicide_murder_incidence"),
                ("rape_rate", "women_crimes_rape_r"),
                ("rape_incidents", "women_crimes_rape_sec_376_i"),
                ("complaints", "complaints_total_complaints"),
                ("cognizable_rate", "complaints_rate_of_cognizable_crime_ipc_sll"),
            ]:
                if col in r.index and pd.notna(r[col]):
                    try:
                        card[key] = float(r[col])
                    except Exception:
                        pass

            # Population (lakhs) — SCRB if present, else district estimate
            for pop_col in (
                "population_lakhs",
                "complaints_projected_population_lakhs",
            ):
                if pop_col in r.index and pd.notna(r[pop_col]):
                    try:
                        v = float(r[pop_col])
                        if v > 0:
                            card["population_lakhs"] = v
                            break
                    except Exception:
                        pass
            if "population_lakhs" not in card or not card.get("population_lakhs"):
                try:
                    from district_entities import estimate_population_lakhs

                    est = estimate_population_lakhs(area)
                    if est:
                        card["population_lakhs"] = float(est)
                        card["population_source"] = "estimate"
                except Exception:
                    pass

            # Derived per-lakh (kept for optional expanders; not shown on heat map)
            pop = card.get("population_lakhs")
            if pop and pop > 0:
                if "murder_incidence" in card and "murder_per_lakh" not in card:
                    card["murder_per_lakh"] = round(float(card["murder_incidence"]) / pop, 3)
                if "rape_incidents" in card and "rape_per_lakh" not in card:
                    card["rape_per_lakh"] = round(float(card["rape_incidents"]) / pop, 3)
                if "complaints" in card and "complaints_per_lakh" not in card:
                    card["complaints_per_lakh"] = round(float(card["complaints"]) / pop, 2)

    heat, vcol, _ = get_current_affairs_heat(recent_days=90)
    if not heat.empty and vcol in heat.columns:
        m = heat[heat["district"].astype(str).str.casefold() == area_cf]
        if m.empty:
            m = heat[heat["district"].astype(str).str.casefold().str.contains(area_cf[:5], na=False)]
        if not m.empty:
            card["news_90d"] = float(m.iloc[0][vcol])
            card["news_rank"] = int((heat[vcol] > m.iloc[0][vcol]).sum()) + 1
            # News volume per lakh people (fairer Chennai vs small district)
            pop = card.get("population_lakhs")
            if pop and pop > 0:
                card["news_per_lakh"] = round(float(card["news_90d"]) / pop, 3)

    if rape_2026_df is not None and not rape_2026_df.empty:
        r26 = rape_2026_df
        ncol = "district" if "district" in r26.columns else "district_city"
        m = r26[r26[ncol].astype(str).str.casefold() == area_cf]
        if not m.empty:
            rr = m.iloc[0]
            if "predicted_2026_rape_incidents" in rr.index:
                card["forecast_2026_rape"] = float(rr["predicted_2026_rape_incidents"])
            if "rape_risk_index" in rr.index and pd.notna(rr["rape_risk_index"]):
                card["rape_risk_index"] = float(rr["rape_risk_index"])
            if "risk_level" in rr.index:
                card["risk_level"] = str(rr["risk_level"])

    if sentiment_df is not None and not sentiment_df.empty and "district_city" in sentiment_df.columns:
        s = sentiment_df
        if "year" in s.columns:
            s = s.sort_values("year")
        m = s[s["district_city"].astype(str).str.casefold() == area_cf]
        if not m.empty:
            last = m.iloc[-1]
            if "polarity" in last.index and pd.notna(last["polarity"]):
                card["sentiment_polarity"] = float(last["polarity"])
            if "crime_intensity" in last.index and pd.notna(last["crime_intensity"]):
                card["crime_intensity"] = float(last["crime_intensity"])

    # Headlines
    headlines: list[str] = []
    if harvest_df is not None and not harvest_df.empty:
        h = harvest_df
        dcol = "district" if "district" in h.columns else "district_city"
        if dcol in h.columns:
            local = h[h[dcol].astype(str).str.casefold().str.contains(area_cf[:5], na=False)]
            if "date" in local.columns:
                local = local.copy()
                local["_dt"] = pd.to_datetime(local["date"], errors="coerce")
                local = local.sort_values("_dt", ascending=False)
            for _, r in local.head(5).iterrows():
                headlines.append(str(r.get("headline", ""))[:200])
    card["headlines"] = headlines
    return card


def run_acquire_news_refresh(years: list[int] | None = None) -> tuple[bool, str]:
    """
    Dashboard refresh: fetch only NEW headlines (incremental).
    Uses lexicon-only scoring (no DistilBERT/transformers) so Streamlit does not
    hit torchvision/SAM ModuleNotFoundError while refreshing.
    Bulk one-time populate is CLI/app option n mode 1.
    """
    import subprocess
    import sys

    script = PROJECT_ROOT / "acquire_news_signals.py"
    if not script.exists():
        return False, f"Missing {script.name}"

    # Incremental + light score (default path — never loads transformers)
    cmd = [
        sys.executable,
        "-B",
        str(script),
        "--refresh-new",
        "--light-score",
        "--max-items",
        "22",
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        tail = (result.stdout or "")[-1800:]
        if result.returncode == 0:
            load_news_signals.clear()
            load_media_harvest.clear()
            try:
                cached_current_affairs_heat.clear()
            except Exception:
                pass
            _sync_db_after_news()
            return True, f"NEW news (lexicon score, no transformers).\n\n{tail}"
        # Fallback: in-process refresh with light_score (still no DistilBERT)
        try:
            from acquire_news_signals import refresh_new_news

            info = refresh_new_news(light_score=True)
            load_news_signals.clear()
            load_media_harvest.clear()
            try:
                cached_current_affairs_heat.clear()
            except Exception:
                pass
            _sync_db_after_news()
            return True, f"NEW news refresh (in-process light): {info}\n\n{tail or result.stderr or ''}"
        except Exception as e2:
            err = (result.stderr or "")[-800:] or str(e2)
            return False, f"Refresh failed (exit {result.returncode}): {err}"
    except subprocess.TimeoutExpired:
        return False, "News refresh timed out. Try CLI: python acquire_news_signals.py --refresh-new"
    except Exception as e:
        try:
            from acquire_news_signals import refresh_new_news

            info = refresh_new_news(light_score=True)
            load_news_signals.clear()
            load_media_harvest.clear()
            try:
                cached_current_affairs_heat.clear()
            except Exception:
                pass
            _sync_db_after_news()
            return True, f"NEW news refresh (fallback light): {info}"
        except Exception as e2:
            return False, f"Could not refresh news: {e2}"


def _sync_db_after_news() -> None:
    """Push latest CSVs into SQLite after a news refresh."""
    try:
        from db import sync_from_csv_outputs

        sync_from_csv_outputs()
    except Exception:
        pass


def build_news_sentiment_by_district(
    harvest_df: pd.DataFrame,
    news_df: pd.DataFrame | None = None,
    *,
    max_score: int = 120,
    rescore: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Score news headlines → district-level sentiment aggregates for TN map.
    Returns (district_agg, scored_headlines).
    Uses SQLite cache when available; rescore=True forces re-run score_text.
    """
    frames = []
    for df in (harvest_df, news_df):
        if df is not None and not df.empty:
            frames.append(df)
    if not frames:
        try:
            from db import load_district_sentiment, load_scored_headlines

            return load_district_sentiment(), load_scored_headlines(limit=max_score)
        except Exception:
            return pd.DataFrame(), pd.DataFrame()

    raw = pd.concat(frames, ignore_index=True, sort=False)
    hcol = next((c for c in ("headline", "text", "source_text") if c in raw.columns), None)
    if hcol is None:
        return pd.DataFrame(), pd.DataFrame()

    if "date" in raw.columns:
        raw = raw.drop_duplicates(subset=[hcol, "date"], keep="last")
    else:
        raw = raw.drop_duplicates(subset=[hcol], keep="last")

    # Prefer rows that already have polarity
    has_pol = "polarity" in raw.columns and pd.to_numeric(raw["polarity"], errors="coerce").notna().any()
    need_score = rescore or not has_pol

    scored_rows = []
    try:
        from district_entities import resolve_district, to_tn38
    except Exception:
        resolve_district = None
        def to_tn38(x, default=None):  # type: ignore
            return x if x and str(x) not in ("Other / Statewide", "nan") else default

    if need_score:
        try:
            from sentiment_analysis import score_text
        except Exception:
            score_text = None

        sample = raw.head(max_score)
        for _, r in sample.iterrows():
            text = str(r.get(hcol) or "")
            if not text.strip():
                continue
            if score_text is not None and (
                rescore
                or r.get("polarity") is None
                or str(r.get("polarity")) in ("", "nan")
            ):
                try:
                    res = score_text(text)
                except Exception:
                    res = {
                        "polarity": 0.0,
                        "sentiment_label": "neutral",
                        "confidence": 0.0,
                        "crime_intensity": 0,
                        "crime_types": "",
                    }
            else:
                res = {
                    "polarity": r.get("polarity", 0.0),
                    "sentiment_label": r.get("sentiment_label") or r.get("label") or "neutral",
                    "confidence": r.get("confidence", 0.0),
                    "crime_intensity": r.get("crime_intensity", 0),
                    "crime_types": r.get("crime_types") or r.get("crime_type") or "",
                }
            dist = str(r.get("district") or r.get("district_city") or "")
            if (not dist or dist.lower() in ("nan", "none", "")) and resolve_district:
                try:
                    dist = resolve_district(text, default="")
                except Exception:
                    dist = ""
            dist = to_tn38(dist, default=None) if dist else None
            if not dist:
                continue  # drop non-TN38 / junk
            try:
                pol = float(res.get("polarity", 0) or 0)
            except (TypeError, ValueError):
                pol = 0.0
            lab = str(res.get("sentiment_label") or "neutral").lower()
            scored_rows.append({
                "headline": text[:300],
                "date": str(r.get("date") or "")[:12],
                "district": dist,
                "source": str(r.get("source") or ""),
                "url": str(r.get("url") or ""),
                "polarity": pol,
                "sentiment_label": lab,
                "confidence": float(res.get("confidence") or 0),
                "crime_intensity": float(res.get("crime_intensity") or 0),
                "crime_types": str(res.get("crime_types") or ""),
            })
    else:
        for _, r in raw.head(max_score * 2).iterrows():
            text = str(r.get(hcol) or "")
            if not text.strip():
                continue
            try:
                pol = float(r.get("polarity"))
            except (TypeError, ValueError):
                continue
            dist = str(r.get("district") or r.get("district_city") or "")
            if resolve_district and (not dist or dist.lower() in ("nan", "none", "other / statewide")):
                try:
                    dist = resolve_district(text, default="")
                except Exception:
                    dist = ""
            dist = to_tn38(dist, default=None) if dist else None
            if not dist:
                continue
            scored_rows.append({
                "headline": text[:300],
                "date": str(r.get("date") or "")[:12],
                "district": dist,
                "source": str(r.get("source") or ""),
                "url": str(r.get("url") or ""),
                "polarity": pol,
                "sentiment_label": str(r.get("sentiment_label") or r.get("label") or "neutral").lower(),
                "confidence": float(r.get("confidence") or 0) if pd.notna(r.get("confidence")) else 0.0,
                "crime_intensity": float(r.get("crime_intensity") or 0) if pd.notna(r.get("crime_intensity")) else 0.0,
                "crime_types": str(r.get("crime_types") or r.get("crime_type") or ""),
            })

    scored = pd.DataFrame(scored_rows)
    if scored.empty:
        return pd.DataFrame(), scored

    # Only TN38 districts in headlines
    scored["district"] = scored["district"].map(lambda x: to_tn38(str(x), default=None))
    scored = scored[scored["district"].notna()].copy()
    if scored.empty:
        return pd.DataFrame(), scored

    # Persist headlines
    try:
        from db import upsert_headlines, save_district_sentiment

        upsert_headlines(scored)
    except Exception:
        save_district_sentiment = None  # type: ignore

    # District aggregates (TN38 only)
    agg_rows = []
    for dist, g in scored.groupby("district"):
        n = len(g)
        if n == 0:
            continue
        labs = g["sentiment_label"].astype(str).str.lower()
        neg = int((labs == "negative").sum())
        pos = int((labs == "positive").sum())
        pol_mean = float(pd.to_numeric(g["polarity"], errors="coerce").mean())
        intensity_mean = float(pd.to_numeric(g["crime_intensity"], errors="coerce").fillna(0).mean())
        concern = max(0.0, -pol_mean) * 50.0 + (neg / n) * 40.0 + intensity_mean * 1.0
        agg_rows.append({
            "district": str(dist),
            "n_headlines": n,
            "polarity_mean": round(pol_mean, 4),
            "negative_share": round(neg / n, 4),
            "positive_share": round(pos / n, 4),
            "intensity_mean": round(intensity_mean, 3),
            "concern_score": round(concern, 2),
        })
    district_agg = pd.DataFrame(agg_rows)
    if not district_agg.empty:
        district_agg = district_agg.sort_values("concern_score", ascending=False).reset_index(drop=True)

    try:
        from db import save_district_sentiment

        save_district_sentiment(district_agg)
    except Exception:
        pass

    return district_agg, scored


# Import core functions (lazy to avoid heavy imports on start)
def get_predict_functions():
    from predict import predict_many, TARGET_ALIASES, resolve_target
    from train_model import TARGET_CONFIGS
    return predict_many, TARGET_ALIASES, TARGET_CONFIGS, resolve_target

def get_sentiment_functions():
    from sentiment_analysis import analyze_sentiment, score_text
    return analyze_sentiment, score_text

def get_2026_functions():
    try:
        import sys

        mod_name = "predict_2026_rape_all_districts"
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        import predict_2026_rape_all_districts as eng

        return eng.predict_2026_rape_all_districts, eng.generate_rape_report
    except Exception:
        return None, None

def main():
    """Full classic CRIMECAST dashboard UI."""
    st.set_page_config(
        page_title="CRIMECAST",
        page_icon="🔺",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    try:
        _main_impl()
    except Exception as e:
        import traceback

        st.error(f"**{type(e).__name__}**: {e}")
        st.code(traceback.format_exc())


def _main_impl():
    apply_custom_theme()

    # ---- Sidebar brand: CRIMECAST ----
    st.sidebar.markdown(
        """
        <div class="ops-brand">
            <div class="ops-logo">CC</div>
            <div class="ops-brand-text">
                <div class="t1">TAMIL NADU</div>
                <div class="t2">CRIMECAST</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Language default (widget is at bottom of sidebar)
    if "ui_lang" not in st.session_state:
        st.session_state["ui_lang"] = "EN"

    # Stable page keys (language-independent)
    _NAV = [
        ("live", "🔴", "Live Feed"),
        ("map", "🗺️", "District Map & Scoreboard"),
        ("acc", "✅", "Accuracy Check"),
        ("pred", "🔮", "Predict"),
        ("sent", "💬", "Sentiment"),
        ("f2026", "📅", "2026 Forecasts"),
        ("compare", "⚖️", "District Compare"),
        ("explain", "🔍", "Risk Explain"),
        ("health", "🩺", "Health"),
    ]
    _nav_labels = [f"{emoji} {t(key)}" for _, emoji, key in _NAV]
    _nav_ix = st.sidebar.radio(
        "Command",
        list(range(len(_NAV))),
        format_func=lambda i: _nav_labels[i],
        label_visibility="collapsed",
        key="main_nav_ix",
    )
    page = {
        "live": "🔴 Live Feed",
        "map": "🗺️ District Map & Scoreboard",
        "acc": "✅ Accuracy Check",
        "pred": "🔮 Predict",
        "sent": "💬 Sentiment",
        "f2026": "📅 2026 Forecasts",
        "compare": "⚖️ District Compare",
        "explain": "🔍 Risk Explain",
        "health": "🩺 Health",
    }[_NAV[_nav_ix][0]]

    # Shared Live Feed controls (news heat only) — set defaults once
    if "live_map_metric" not in st.session_state:
        st.session_state["live_map_metric"] = "News (time window)"
    else:
        st.session_state["live_map_metric"] = "News (time window)"
    if "live_news_window" not in st.session_state:
        st.session_state["live_news_window"] = "90 days"

    # ---- Sidebar: news refresh ----
    st.sidebar.markdown("---")
    if st.sidebar.button(
        f"🔄 {t('Refresh news')}",
        type="primary",
        key="sidebar_refresh_news",
        help=t("Refresh news"),
    ):
        with st.spinner("Fetching news…"):
            ok, msg = run_acquire_news_refresh()
        if ok:
            st.sidebar.success("Updated" if st.session_state["ui_lang"] == "EN" else "புதுப்பிக்கப்பட்டது")
            st.rerun()
        else:
            st.sidebar.error("Failed" if st.session_state["ui_lang"] == "EN" else "தோல்வி")

    # ---- Language at bottom of sidebar ----
    st.sidebar.markdown("---")
    st.sidebar.caption("Lang")
    _lang_choice = st.sidebar.radio(
        "Lang",
        ["EN", "TA"],
        index=0 if st.session_state["ui_lang"] == "EN" else 1,
        horizontal=True,
        key="ui_lang_radio",
        label_visibility="collapsed",
    )
    if _lang_choice != st.session_state["ui_lang"]:
        st.session_state["ui_lang"] = _lang_choice
        st.rerun()

    # Lazy / cached loads — only what this page needs (faster page switches)
    def _empty() -> pd.DataFrame:
        return pd.DataFrame()

    # Lightweight globals used by several pages
    ml_data = load_ml_data()
    rape_2026_df = load_rape_2026()
    # Heavy news tables: load only for pages that use them
    _need_news = page in (
        "🔴 Live Feed",
        "🗺️ District Map & Scoreboard",
        "💬 Sentiment",
        "✅ Accuracy Check",
        "🔮 Predict",
        "⚖️ District Compare",
        "🔍 Risk Explain",
        "🩺 Health",
    )
    if _need_news:
        news_df = load_news_signals()
        harvest_df = load_media_harvest()
        sentiment_df = load_sentiment_scores()
    else:
        news_df = _empty()
        harvest_df = _empty()
        sentiment_df = _empty()
    crime_preds = _empty()  # rarely needed; avoid extra CSV on every click

    n_models = len([f for f in MODELS_DIR.glob("*.joblib") if "sentiment" not in f.name])
    n_sent = len(sentiment_df) if not sentiment_df.empty else 0
    n_2026 = len(rape_2026_df) if not rape_2026_df.empty else 0
    n_media = len(news_df) if not news_df.empty else 0
    n_harvest = len(harvest_df) if not harvest_df.empty else 0

    def _live_window_days(time_window: str) -> int:
        if time_window == "30 days":
            return 30
        if time_window == "90 days":
            return 90
        if time_window == "YTD":
            from datetime import datetime as _dt
            return max(1, (_dt.now() - _dt(_dt.now().year, 1, 1)).days)
        return 365 * 10  # All time

    def _render_alert_cards(alerts: list, *, levels: set[str] | None = None, max_n: int = 12) -> None:
        shown = 0
        for a in alerts:
            level = a.get("level", "MED")
            if levels is not None and level not in levels:
                continue
            color = "#ef4444" if level == "HIGH" else "#f59e0b"
            st.markdown(
                f"""
                <div style="border-left:4px solid {color};background:#14141a;border:1px solid #24242e;
                border-radius:10px;padding:10px 14px;margin-bottom:8px;">
                <span style="color:{color};font-weight:800;font-size:0.72rem;letter-spacing:0.06em;">{level}</span>
                <div style="color:#f3f4f6;font-weight:700;margin-top:2px;">{a.get("title","")}</div>
                <div style="color:#9ca3af;font-size:0.85rem;">{a.get("detail","")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            shown += 1
            if shown >= max_n:
                break
        if shown == 0:
            st.caption("No alerts at this level.")

    # ============ LIVE FEED (classic ops UI) ============
    if page == "🔴 Live Feed":
        tb1, tb2 = st.columns([20, 1])
        with tb1:
            ops_topbar("CRIMECAST — Tamil Nadu Live Intelligence")
        with tb2:
            if st.button("🔄", type="secondary", key="live_refresh_news", help="Refresh news"):
                with st.spinner("Fetching news…"):
                    ok, msg = run_acquire_news_refresh()
                if ok:
                    st.toast("News updated", icon="✅")
                    st.rerun()
                else:
                    st.toast("Refresh failed", icon="⚠️")

        st.caption(data_freshness_caption())

        # Always define before any UI uses them (prevents open_alerts NameError)
        map_metric = "News (time window)"
        time_window = st.session_state.get("live_news_window", "90 days")
        open_alerts = 0
        high_alerts: list = []

        # ---- How it works + health strip (demo / viva) ----
        with st.expander(f"📘 {t('How it works')} · pipeline", expanded=False):
            st.markdown(
                """
**CRIMECAST data → model → map**

1. **Official tables** (SCRB-style complaints / murder / women crimes) → `clean_data` → ML-ready CSV  
2. **Train** only on **official-era years (≤2023)** — media years are not training labels  
3. **News harvest** (Tamil + English) → Live heat, sentiment, word clouds (support layer)  
4. **Predict** district rates/counts · **blend** with history for sticky rates  
5. **2026 scenarios** — linear / last-year / blend trends (not SCRB forecasts)  
6. **Explain** — composite risk + LIME-style / SHAP-proxy  

| Layer | Is it “fact”? |
|-------|----------------|
| Official rates (≤2023) | Best available stats in this prototype |
| News heat / sentiment | Media volume & tone — **not FIRs** |
| 2026 forecast | **Scenario only** for discussion |

Demo path: Live → Map → Accuracy → Predict → 2026 → Sentiment → Explain · see `docs/DEMO_SCRIPT.md`
"""
            )
        try:
            from health_check import run_health_check

            _hc = run_health_check()
            _bits = []
            for c in _hc.get("checks", [])[:6]:
                mark = {"ok": "🟢", "warn": "🟡", "fail": "🔴"}.get(c["status"], "⚪")
                _bits.append(f"{mark} **{c['name']}**")
            st.caption(
                " · ".join(_bits)
                + f"  · overall **{_hc.get('overall', '?')}** · full page: **🩺 Health**"
            )
        except Exception:
            st.caption("Health strip unavailable — open **🩺 Health** or run `python health_check.py`")

        _live_subs = [t("Live view"), t("Feed controls")]
        live_sub_ix = st.radio(
            "Live Feed section",
            [0, 1],
            format_func=lambda i: f"{'▶' if i == 0 else '⚙'} {_live_subs[i]}",
            horizontal=True,
            key="live_sub_nav_ix",
            label_visibility="collapsed",
        )

        from tn_map import plot_tn_choropleth, HEAT_WHITE_BLUE

        st.radio(
            t("News time window"),
            ["30 days", "90 days", "YTD", "All time"],
            horizontal=True,
            key="live_news_window",
        )
        time_window = st.session_state.get("live_news_window", "90 days")
        recent_days = _live_window_days(time_window)
        live_map_df, live_vcol, live_ncol, map_caption = build_map_metric_frame(
            map_metric, harvest_df, news_df, ml_data, rape_2026_df, recent_days=recent_days
        )

        try:
            alerts, alert_log = persist_and_load_alerts(
                ml_data, harvest_df, news_df, rape_2026_df
            )
        except Exception:
            alerts, alert_log = [], pd.DataFrame()
        high_alerts = [a for a in (alerts or []) if a.get("level") == "HIGH"]
        open_alerts = len(high_alerts)

        if live_sub_ix == 1:
            st.markdown(f"### {t('Feed controls')}")
            st.caption("Time window, MED+HIGH alerts, language split, alert log.")
            st.markdown("### Alerts (MEDIUM + HIGH)")
            if alerts:
                _render_alert_cards(alerts, levels={"HIGH", "MED"}, max_n=20)
            else:
                st.caption("No MED or HIGH alerts right now.")
            st.markdown(f"### {t('Alert log')}")
            st.caption("Persisted in SQLite (`alert_log`) — unique HIGH/MED rules with timestamps.")
            if alert_log is not None and not alert_log.empty:
                st.dataframe(alert_log, use_container_width=True, hide_index=True)
                st.download_button(
                    "Download alert log CSV",
                    alert_log.to_csv(index=False).encode("utf-8"),
                    "crimecast_alert_log.csv",
                    "text/csv",
                    key="live_alert_log_dl",
                )
            else:
                st.caption("No saved alerts yet — open Live view once to log them.")
            st.markdown(f"### {t('News language split')}")
            lang_df = news_lang_split(harvest_df)
            if not lang_df.empty:
                lc1, lc2 = st.columns([1.2, 1.8])
                with lc1:
                    st.dataframe(lang_df, use_container_width=True, hide_index=True)
                with lc2:
                    fig_lang = px.pie(
                        lang_df,
                        names="language",
                        values="headlines",
                        title="Tamil vs English",
                        template="plotly_dark",
                        color_discrete_sequence=["#ef4444", "#3b82f6", "#9ca3af"],
                    )
                    fig_lang.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        height=280,
                        margin=dict(l=10, r=10, t=40, b=10),
                    )
                    st.plotly_chart(fig_lang, use_container_width=True, key="controls_lang_pie")
            if not live_map_df.empty and live_vcol:
                st.markdown(f"### {t('Preview top districts')}")
                render_district_heat(live_map_df, live_vcol, live_ncol, None, top_n=15)
        else:
            if high_alerts:
                st.markdown(f"**{t('HIGH alerts')}**")
                _render_alert_cards(high_alerts, levels={"HIGH"}, max_n=6)
            else:
                st.caption(f"No HIGH · MED+HIGH → **⚙ {t('Feed controls')}**")

            with st.expander(f"📜 {t('Alert log')}", expanded=False):
                if alert_log is not None and not alert_log.empty:
                    st.dataframe(alert_log.head(15), use_container_width=True, hide_index=True)
                else:
                    st.caption("Empty — alerts are saved when Live Feed runs.")

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("EVENTS / MODELS", n_models)
            with m2:
                st.metric("MEDIA HEADLINES", n_harvest or n_media)
            with m3:
                active = 0
                if not live_map_df.empty and live_vcol in live_map_df.columns:
                    active = int((live_map_df[live_vcol] >= 1).sum())
                st.metric("ACTIVE (window)", active)
            with m4:
                hot = 0
                if not live_map_df.empty and live_vcol in live_map_df.columns:
                    thr = (
                        live_map_df[live_vcol].quantile(0.75)
                        if len(live_map_df) > 4
                        else live_map_df[live_vcol].median()
                    )
                    hot = int((live_map_df[live_vcol] >= thr).sum())
                st.metric("HOT DISTRICTS", hot)

            left, right = st.columns([1.05, 1.15], gap="medium")
            with left:
                st.markdown(
                    '<div class="panel"><div class="panel-title">● Live intelligence feed</div>',
                    unsafe_allow_html=True,
                )
                feed = harvest_df if not harvest_df.empty else sentiment_df
                if not feed.empty:
                    feed_show = build_negative_news_feed(feed, top_n=14, high_n=3)
                    for _, r in feed_show.iterrows():
                        headline = str(
                            r.get("headline") or r.get("text") or r.get("source_text") or "—"
                        )
                        source = str(r.get("source") or r.get("sentiment_method") or "News media")
                        label = str(r.get("sentiment_label") or r.get("label") or "News").title()
                        district = str(r.get("district") or r.get("district_city") or "")
                        url = str(r.get("url") or "")
                        crime = str(
                            r.get("crime_types")
                            or r.get("crime_theme")
                            or r.get("crime_type")
                            or "Current affairs"
                        )
                        if isinstance(crime, str) and len(crime) > 24:
                            crime = crime[:24] + "…"
                        date_s = str(r.get("date") or "")[:10]
                        if date_s and date_s != "nan":
                            source = f"{source} · {date_s}"
                        render_feed_card(
                            source,
                            headline[:220],
                            label=label,
                            crime=crime,
                            district=district,
                            url=url,
                        )
                else:
                    st.info("No live media yet. Click **🔄** to refresh news.")
                st.markdown("</div>", unsafe_allow_html=True)

            with right:
                st.markdown(
                    f'<div class="panel"><div class="panel-title">'
                    f"District heat · {map_metric} · {time_window}</div>",
                    unsafe_allow_html=True,
                )
                if not live_map_df.empty and live_vcol:
                    show_map = st.checkbox(
                        "Show TN map (slower)",
                        value=False,
                        key="live_show_choropleth",
                    )
                    if show_map:
                        with st.spinner("Loading map…"):
                            fig_live = plot_tn_choropleth(
                                live_map_df,
                                value_col=live_vcol,
                                name_col=live_ncol,
                                title=f"{map_metric}",
                                fill_nulls_from_media=False,
                                color_scale=HEAT_WHITE_BLUE,
                            )
                        if fig_live is not None:
                            fig_live.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
                            st.plotly_chart(fig_live, use_container_width=True, key="live_tn_map")
                    fig_fb = px.bar(
                        live_map_df.sort_values(live_vcol, ascending=True).tail(15),
                        x=live_vcol,
                        y=live_ncol,
                        orientation="h",
                        color=live_vcol,
                        color_continuous_scale=HEAT_WHITE_BLUE,
                        template="plotly_dark",
                        title="Top districts (news volume)",
                    )
                    fig_fb.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#0e0e12",
                        height=380,
                        margin=dict(l=8, r=8, t=40, b=8),
                    )
                    st.plotly_chart(fig_fb, use_container_width=True, key="live_map_bars")
                    st.caption(map_caption)
                    render_district_heat(live_map_df, live_vcol, live_ncol, None, top_n=12)
                else:
                    st.info("No map data. Refresh news.")
                st.markdown("</div>", unsafe_allow_html=True)

        # Status footer — open_alerts always defined above (no NameError)
        _safe_live_status(
            n_models,
            n_media,
            n_harvest,
            open_alerts,
            map_metric,
            time_window,
        )

    # ============ STATE ADMINISTRATION COMPARISON — DMK vs TVK ============
    elif page == "🏛️ State Administration Comparison":
        tb1, tb2 = st.columns([20, 1])
        with tb1:
            ops_topbar("State Administration Comparison — DMK vs TVK")
        with tb2:
            st.markdown('<div class="refresh-icon-wrap" style="padding-top:6px;">', unsafe_allow_html=True)
            if st.button("🔄", type="secondary", key="admin_refresh_news", help="Refresh media news (support data)"):
                with st.spinner("Fetching news…"):
                    ok, msg = run_acquire_news_refresh()
                if ok:
                    st.toast("Media support updated", icon="✅")
                    st.rerun()
                else:
                    st.toast("Refresh failed", icon="⚠️")
            st.markdown("</div>", unsafe_allow_html=True)

        cap_l, cap_r = st.columns([4, 1])
        with cap_l:
            st.caption(
                "**DMK vs TVK.** Official crime data lags → used as primary for the ruling party (DMK). "
                "**Media** is support data for both (and the only fair signal for TVK until they have a CM term)."
            )
        with cap_r:
            if st.button("🔄 Refresh media", type="primary", key="admin_refresh_media_btn", use_container_width=True):
                with st.spinner("Fetching news for DMK vs TVK media support…"):
                    ok, msg = run_acquire_news_refresh()
                if ok:
                    st.success("Media support refreshed")
                    st.rerun()
                else:
                    st.error(msg or "Refresh failed")

        if not ml_data.empty and "year" in ml_data.columns:
            regime_df, year_df, verdict = build_regime_comparison(ml_data)
        else:
            regime_df, year_df = pd.DataFrame(), pd.DataFrame()
            verdict = {
                "winner": "—",
                "reason": "No ML-ready year data.",
                "caveat": "",
                "metric_labels": [],
            }
        metric_labels: list[str] = list(verdict.get("metric_labels") or [])
        party_news_df, news_verdict = build_party_news_comparison(harvest_df, news_df)
        board = build_dmk_tvk_scoreboard(regime_df, party_news_df, year_df)

        if not board.empty and board["combined_score"].notna().any():
            top = board.dropna(subset=["combined_score"]).iloc[0]
            comb_winner = str(top["party"])
            comb_reason = (
                f"**{comb_winner}** leads on combined score "
                f"({float(top['combined_score']):.1f}/100) · DMK vs TVK "
                f"(official primary when available · media as support)."
            )
        else:
            comb_winner = news_verdict.get("winner") or verdict.get("winner") or "—"
            comb_reason = news_verdict.get("reason") or verdict.get("reason") or ""

        # Plain Streamlit (no f-string HTML — braces in reason text used to crash)
        st.subheader("DMK vs TVK · from our data")
        st.markdown(f"### {comb_winner}")
        if comb_reason:
            st.write(comb_reason)
        st.info(
            "Official/ML rates lag (best through ~2023). "
            "Media is support data; TVK has media-only signal until a CM term exists."
        )

        st.markdown("### Scoreboard · DMK vs TVK")
        if not board.empty:
            cols = st.columns(2)
            for i, p in enumerate(TN_COMPARE_PARTIES):
                row = board[board["party"] == p]
                with cols[i]:
                    if row.empty:
                        st.metric(p, "—")
                        continue
                    r0 = row.iloc[0]
                    comb = r0.get("combined_score")
                    comb_s = f"{float(comb):.1f}" if pd.notna(comb) else "—"
                    rs = (
                        f"{float(r0['official_safety_score']):.1f}"
                        if pd.notna(r0.get("official_safety_score"))
                        else "—"
                    )
                    ms = (
                        f"{float(r0['media_clean_score']):.1f}"
                        if pd.notna(r0.get("media_clean_score"))
                        else "—"
                    )
                    st.markdown(f"**{p}** · {r0.get('role', '')}")
                    st.metric("Combined / 100", comb_s)
                    st.caption(
                        f"Official safety: {rs} · Media: {ms} · "
                        f"Neg news: {int(r0.get('news_negative') or 0)} / {int(r0.get('news_mentions') or 0)}"
                    )
                    if r0.get("data_basis"):
                        st.caption(str(r0.get("data_basis")))

            show_b = board.copy()
            for c in ("official_safety_score", "media_clean_score", "combined_score"):
                if c in show_b.columns:
                    show_b[c] = pd.to_numeric(show_b[c], errors="coerce").round(1)
            st.dataframe(show_b, use_container_width=True, hide_index=True)

            bplot = board.dropna(subset=["combined_score"])
            if not bplot.empty:
                fig_board = px.bar(
                    bplot,
                    x="party",
                    y="combined_score",
                    color="party",
                    text=bplot["combined_score"].map(lambda x: f"{float(x):.1f}"),
                    title="DMK vs TVK · combined (official primary + media support)",
                    template="plotly_dark",
                    color_discrete_map=PARTY_COLORS,
                )
                fig_board.update_traces(textposition="outside")
                fig_board.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#0e0e12",
                    height=360,
                    showlegend=False,
                    yaxis_title="Combined score",
                    xaxis_title="",
                )
                st.plotly_chart(fig_board, use_container_width=True, key="dmk_tvk_combined_bar")

        med_h, med_btn = st.columns([5, 1])
        with med_h:
            st.markdown("### Media support · party-linked negative / crime news")
            st.caption(
                "Because official data lags, media is the live bridge for **DMK vs TVK**. "
                + str(news_verdict.get("reason", ""))
            )
        with med_btn:
            st.write("")  # align with heading
            if st.button("🔄 Refresh", key="admin_media_section_refresh", help="Refresh news harvest"):
                with st.spinner("Fetching news…"):
                    ok, msg = run_acquire_news_refresh()
                if ok:
                    st.toast("Media updated", icon="✅")
                    st.rerun()
                else:
                    st.toast("Refresh failed", icon="⚠️")
        if not party_news_df.empty:
            st.dataframe(party_news_df, use_container_width=True, hide_index=True)
            c1, c2 = st.columns(2)
            with c1:
                fig_neg = px.bar(
                    party_news_df,
                    x="party",
                    y="negative_mentions",
                    color="party",
                    title="Negative mentions · DMK vs TVK",
                    template="plotly_dark",
                    color_discrete_map=PARTY_COLORS,
                )
                fig_neg.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#0e0e12",
                    height=320,
                    showlegend=False,
                )
                st.plotly_chart(fig_neg, use_container_width=True, key="dmk_tvk_neg_bar")
            with c2:
                fig_cl = px.bar(
                    party_news_df.dropna(subset=["clean_score"]),
                    x="party",
                    y="clean_score",
                    color="party",
                    title="Media clean score (higher = less negative load)",
                    template="plotly_dark",
                    color_discrete_map=PARTY_COLORS,
                )
                fig_cl.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#0e0e12",
                    height=320,
                    showlegend=False,
                )
                st.plotly_chart(fig_cl, use_container_width=True, key="dmk_tvk_clean_bar")
        else:
            st.warning("No party-tagged news yet. Click **🔄** to refresh harvest (media support).")

        st.markdown("### Official / ML crime under ruling DMK (lagging)")
        st.caption(
            "Statewide rates while **DMK** is CM. TVK has no official CM-term rows. "
            "Prefer years ≤2023 as closer to official labels."
        )
        if verdict.get("caveat"):
            st.info(verdict["caveat"])

        with st.expander("Party / regime timeline", expanded=False):
            tl_rows = []
            for r in TN_REGIME_PERIODS:
                ys = (
                    f"{r['start_year']}–{r['end_year']}"
                    if r.get("start_year") is not None
                    else "—"
                )
                tl_rows.append({
                    "Party": r["party"],
                    "Regime": r["regime"],
                    "CM": r["cm"],
                    "Years": ys,
                    "Note": r["note"],
                })
            st.dataframe(pd.DataFrame(tl_rows), use_container_width=True, hide_index=True)

        if not regime_df.empty:
            show_reg = regime_df.copy()
            prefer_cols = [
                c for c in (
                    "rank", "party", "regime", "cm", "years_in_data", "n_years",
                    "safety_score", "trend", "trend_delta",
                ) + tuple(metric_labels)
                if c in show_reg.columns
            ]
            show_reg = show_reg[prefer_cols]
            if "safety_score" in show_reg.columns:
                show_reg["safety_score"] = show_reg["safety_score"].map(
                    lambda x: round(float(x), 1)
                )
            for lab in metric_labels:
                if lab in show_reg.columns:
                    show_reg[lab] = pd.to_numeric(show_reg[lab], errors="coerce").round(2)
            st.dataframe(show_reg, use_container_width=True, hide_index=True)

            fig_reg = px.bar(
                regime_df,
                x="party",
                y="safety_score",
                color="party",
                text=regime_df["safety_score"].map(lambda x: f"{float(x):.1f}"),
                title="Official/ML safety under DMK rule (higher = lower crime)",
                template="plotly_dark",
                color_discrete_map=PARTY_COLORS,
            )
            fig_reg.update_traces(textposition="outside")
            fig_reg.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#0e0e12",
                height=340,
                showlegend=False,
                yaxis_title="Safety score",
                xaxis_title="",
            )
            st.plotly_chart(fig_reg, use_container_width=True, key="regime_safety_bar")
            st.caption(verdict.get("reason", ""))
        else:
            st.caption("No official/ML year aggregates yet — media support still works after news refresh.")

        st.markdown("### Year-by-year statewide crime (DMK term · official/ML)")
        if not year_df.empty:
            yshow = year_df.copy()
            if "year_safety_score" in yshow.columns:
                yshow["year_safety_score"] = pd.to_numeric(
                    yshow["year_safety_score"], errors="coerce"
                ).round(1)
            for lab in metric_labels:
                if lab in yshow.columns:
                    yshow[lab] = pd.to_numeric(yshow[lab], errors="coerce").round(2)
            st.dataframe(yshow, use_container_width=True, hide_index=True)

            c1, c2 = st.columns(2)
            with c1:
                fig_ys = px.line(
                    year_df.sort_values("year"),
                    x="year",
                    y="year_safety_score",
                    color="party",
                    markers=True,
                    title="Safety score by year · DMK term (official/ML, lagging)",
                    template="plotly_dark",
                    color_discrete_map=PARTY_COLORS,
                )
                fig_ys.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#0e0e12",
                    height=340,
                    yaxis_title="Safety score",
                )
                st.plotly_chart(fig_ys, use_container_width=True, key="regime_year_score")
            with c2:
                if metric_labels:
                    long_rows = []
                    for _, r in year_df.iterrows():
                        for lab in metric_labels[:4]:
                            if lab in r.index and pd.notna(r[lab]):
                                long_rows.append({
                                    "year": int(r["year"]),
                                    "metric": lab,
                                    "value": float(r[lab]),
                                    "party": r.get("party", ""),
                                })
                    if long_rows:
                        fig_m = px.line(
                            pd.DataFrame(long_rows),
                            x="year",
                            y="value",
                            color="metric",
                            markers=True,
                            title="Key crime metrics (statewide mean)",
                            template="plotly_dark",
                        )
                        fig_m.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="#0e0e12",
                            height=340,
                            legend_title_text="",
                        )
                        st.plotly_chart(fig_m, use_container_width=True, key="regime_metric_lines")

            y_scored = year_df.dropna(subset=["year_safety_score"])
            if not y_scored.empty:
                best = y_scored.loc[y_scored["year_safety_score"].idxmax()]
                worst = y_scored.loc[y_scored["year_safety_score"].idxmin()]
                b1, b2, b3 = st.columns(3)
                with b1:
                    st.metric(
                        "Best year (safety)",
                        f"{int(best['year'])}",
                        delta=f"{float(best['year_safety_score']):.1f} · {best.get('party','')}",
                    )
                with b2:
                    st.metric(
                        "Weakest year (safety)",
                        f"{int(worst['year'])}",
                        delta=f"{float(worst['year_safety_score']):.1f} · {worst.get('party','')}",
                        delta_color="inverse",
                    )
                with b3:
                    st.metric("Years in ML file", str(year_df["year"].nunique()))
        else:
            st.warning("No ML-ready year series. Media support still available after **🔄**.")

        sub = build_regime_subperiod_compare(year_df)
        if not sub.empty and len(sub) >= 2:
            st.markdown("### DMK term windows (official lag · early vs later)")
            sub_show = sub.copy()
            if "safety_score" in sub_show.columns:
                sub_show["safety_score"] = pd.to_numeric(
                    sub_show["safety_score"], errors="coerce"
                ).round(1)
            st.dataframe(sub_show, use_container_width=True, hide_index=True)
            if "safety_score" in sub.columns:
                fig_sp = px.bar(
                    sub,
                    x="subperiod",
                    y="safety_score",
                    title="Sub-period safety (higher = better)",
                    template="plotly_dark",
                    color="safety_score",
                    color_continuous_scale=["#dc2626", "#eab308", "#22c55e"],
                )
                fig_sp.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#0e0e12",
                    height=320,
                    xaxis_title="",
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_sp, use_container_width=True, key="regime_subperiod_bar")

        st.markdown("### Metric deep-dive by year")
        if metric_labels and not year_df.empty:
            pick = st.selectbox("Metric", metric_labels, key="regime_metric_pick")
            if pick in year_df.columns:
                fig_d = px.bar(
                    year_df.sort_values("year"),
                    x="year",
                    y=pick,
                    color="party",
                    title=f"{pick} — statewide mean under DMK term",
                    template="plotly_dark",
                    color_discrete_map=PARTY_COLORS,
                )
                fig_d.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#0e0e12",
                    height=360,
                    yaxis_title=pick,
                )
                st.plotly_chart(fig_d, use_container_width=True, key="regime_metric_deep")
                st.caption(
                    "Lower usually = better crime outcome. "
                    "Pair with **media support** above for current DMK vs TVK signal."
                )

    # ============ DISTRICT SCORECARD (merged into Geographic — hidden from nav) ============
    elif page == "📋 District Scorecard":
        st.info("District Scorecard is now inside **🗺️ District Map & Scoreboard**.")
        ops_topbar("District crime scorecard (legacy)")
        st.caption(
            "One district view: official rates · news heat · 2026 forecast · risk · headlines."
        )

        area_opts: list[str] = []
        if not ml_data.empty and "district_city" in ml_data.columns:
            area_opts = sorted(ml_data["district_city"].dropna().astype(str).unique().tolist())
        elif not rape_2026_df.empty:
            ncol = "district" if "district" in rape_2026_df.columns else "district_city"
            area_opts = sorted(rape_2026_df[ncol].dropna().astype(str).unique().tolist())
        if not area_opts:
            area_opts = ["Chennai", "Madurai", "Thoothukudi", "Coimbatore"]

        default_ix = 0
        for prefer in ("Thoothukudi", "Madurai", "Chennai"):
            if prefer in area_opts:
                default_ix = area_opts.index(prefer)
                break

        csel, ccmp = st.columns([2, 2])
        with csel:
            area = st.selectbox("District", area_opts, index=default_ix, key="scorecard_area")
        with ccmp:
            compare = st.selectbox(
                "Compare with (optional)",
                ["— none —"] + [a for a in area_opts if a != area],
                key="scorecard_compare",
            )

        def _render_card(dist: str) -> None:
            card = build_district_scorecard(
                dist, ml_data, news_df, harvest_df, rape_2026_df, sentiment_df
            )
            st.markdown(f"### {dist}")
            mcols = st.columns(4)
            with mcols[0]:
                st.metric("Murder rate", f"{card['murder_rate']:.2f}" if "murder_rate" in card else "—")
            with mcols[1]:
                st.metric("Rape rate", f"{card['rape_rate']:.2f}" if "rape_rate" in card else "—")
            with mcols[2]:
                st.metric("News 90d", f"{card['news_90d']:.1f}" if "news_90d" in card else "—")
            with mcols[3]:
                st.metric(
                    "2026 rape forecast",
                    f"{card['forecast_2026_rape']:.1f}" if "forecast_2026_rape" in card else "—",
                )
            r1, r2, r3 = st.columns(3)
            with r1:
                st.write(
                    f"**Murder incidence:** {card.get('murder_incidence', '—')}  \n"
                    f"**Rape incidents:** {card.get('rape_incidents', '—')}  \n"
                    f"**Complaints:** {card.get('complaints', '—')}"
                )
            with r2:
                st.write(
                    f"**News rank (90d):** #{card.get('news_rank', '—')}  \n"
                    f"**Risk level:** {card.get('risk_level', '—')}  \n"
                    f"**Risk index:** {card.get('rape_risk_index', '—')}"
                )
            with r3:
                st.write(
                    f"**Sentiment polarity:** {card.get('sentiment_polarity', '—')}  \n"
                    f"**Crime intensity:** {card.get('crime_intensity', '—')}  \n"
                    f"**Data year:** {card.get('year', '—')}"
                )
            # Explain drivers
            st.markdown("#### Why this district stands out")
            for line in explain_prediction_drivers(
                dist, "murder_homicide_murder_rate", ml_data, news_df, harvest_df, None
            ):
                st.markdown(f"- {line}")
            if card.get("headlines"):
                st.markdown("#### Recent headlines")
                for hl in card["headlines"]:
                    st.markdown(f"- {hl}")
            # Tier-2: export HTML brief (print to PDF)
            drivers = explain_prediction_drivers(
                dist, "murder_homicide_murder_rate", ml_data, news_df, harvest_df, None
            )
            html = district_brief_html(card, drivers)
            st.download_button(
                "⬇️ Download district brief (HTML → print PDF)",
                data=html.encode("utf-8"),
                file_name=f"CRIMECAST_{dist.replace(' ', '_')}_brief.html",
                mime="text/html",
                key=f"dl_brief_{dist}",
            )

        if compare and compare != "— none —":
            left_c, right_c = st.columns(2)
            with left_c:
                _render_card(area)
            with right_c:
                _render_card(compare)
            # Quick delta table + chart (Tier-3 richer compare)
            c1 = build_district_scorecard(area, ml_data, news_df, harvest_df, rape_2026_df, sentiment_df)
            c2 = build_district_scorecard(compare, ml_data, news_df, harvest_df, rape_2026_df, sentiment_df)
            rows = []
            chart_rows = []
            for k, label in [
                ("murder_rate", "Murder rate"),
                ("rape_rate", "Rape rate"),
                ("news_90d", "News 90d"),
                ("forecast_2026_rape", "2026 rape forecast"),
                ("murder_incidence", "Murder incidence"),
                ("rape_incidents", "Rape incidents"),
            ]:
                if k in c1 or k in c2:
                    rows.append({
                        "Metric": label,
                        area: c1.get(k, "—"),
                        compare: c2.get(k, "—"),
                    })
                    try:
                        v1 = float(c1.get(k)) if c1.get(k) is not None else None
                        v2 = float(c2.get(k)) if c2.get(k) is not None else None
                    except Exception:
                        v1 = v2 = None
                    if v1 is not None:
                        chart_rows.append({"Metric": label, "District": area, "Value": v1})
                    if v2 is not None:
                        chart_rows.append({"Metric": label, "District": compare, "Value": v2})
            if rows:
                st.markdown("#### Side-by-side")
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            if chart_rows:
                fig_cmp = px.bar(
                    pd.DataFrame(chart_rows),
                    x="Metric",
                    y="Value",
                    color="District",
                    barmode="group",
                    title=f"{area} vs {compare}",
                    template="plotly_dark",
                    color_discrete_sequence=["#ef4444", "#3b82f6"],
                )
                fig_cmp.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#0e0e12",
                    height=360,
                    legend_title_text="",
                )
                st.plotly_chart(fig_cmp, use_container_width=True, key="scorecard_compare_chart")
            # Multi-year murder rate history if available
            if not ml_data.empty and "murder_homicide_murder_rate" in ml_data.columns:
                hist = ml_data[
                    ml_data["district_city"].astype(str).isin([area, compare])
                    & ml_data["year"].notna()
                ].copy()
                if not hist.empty:
                    hist["murder_homicide_murder_rate"] = pd.to_numeric(
                        hist["murder_homicide_murder_rate"], errors="coerce"
                    )
                    fig_h = px.line(
                        hist.sort_values("year"),
                        x="year",
                        y="murder_homicide_murder_rate",
                        color="district_city",
                        markers=True,
                        title="Murder rate over years",
                        template="plotly_dark",
                        color_discrete_sequence=["#ef4444", "#3b82f6"],
                    )
                    fig_h.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#0e0e12",
                        height=320,
                    )
                    st.plotly_chart(fig_h, use_container_width=True, key="scorecard_murder_hist")
        else:
            _render_card(area)

    # ============ ACCURACY CHECK (Tier-2 · polished + story + backtest) ============
    elif page == "✅ Accuracy Check":
        ops_topbar(f"{t('Accuracy Check')} — metrics · claims · blend · backtest")
        st.caption(
            f"{t('Official vs media')} honesty check: **training metrics**, **official vs model vs blend**, "
            "optional **holdout backtest**. Temporal R² can be weak — we show it."
        )
        st.caption(data_freshness_caption())

        # ---- Training metrics (best models) ----
        st.markdown("### Training metrics (best models)")
        try:
            from forecast_engine import load_training_metrics_best

            tm = load_training_metrics_best()
        except Exception:
            tm = pd.DataFrame()
            p = OUTPUT_DIR / "training_metrics.csv"
            if p.exists():
                tm = pd.read_csv(p)
                if "is_best" in tm.columns:
                    tm = tm[tm["is_best"].astype(str).str.lower().isin(("true", "1"))]
        if not tm.empty:
            show_tm = tm.copy()
            prefer = [
                c
                for c in (
                    "target_label", "model_name", "test_mae", "test_r2",
                    "cv_r2", "temporal_mae", "temporal_r2", "official_label_max_year",
                )
                if c in show_tm.columns
            ]
            st.dataframe(
                show_tm[prefer] if prefer else show_tm,
                use_container_width=True,
                hide_index=True,
            )
            if "test_r2" in show_tm.columns:
                try:
                    st.caption(
                        f"Median test R² (best models): "
                        f"**{float(pd.to_numeric(show_tm['test_r2'], errors='coerce').median()):.3f}**"
                    )
                except Exception:
                    pass
        else:
            st.info("No `training_metrics.csv` — run `python train_model.py`.")

        with st.expander("What we claim / don’t claim", expanded=True):
            c_a, c_b = st.columns(2)
            with c_a:
                st.markdown(
                    """
**We claim**
- Models trained mainly on **official-era labels (≤2023)**
- Holdout / CV metrics from `training_metrics.csv`
- **Blend** often closer to multi-year district history for sticky *rates*
- Live map = **news volume**, labelled as such
- 2026 = **scenario trend**, with uncertainty bands
"""
                )
            with c_b:
                st.markdown(
                    """
**We do not claim**
- Official SCRB forecast authority
- Media headlines = FIRs / court facts
- Perfect temporal generalization (see temporal R²)
- Real-time police dispatch accuracy
- Causality (“X causes crime”)
"""
                )

        # ---- Official vs model vs blend ----
        st.markdown("### Official history vs model raw vs blend")
        tgt_opts = {
            "Murder rate · கொலை விகிதம்": "murder_homicide_murder_rate",
            "Rape rate · பாலியல் குற்ற விகிதம்": "women_crimes_rape_r",
            "Murder incidence": "murder_homicide_murder_incidence",
            "Rape incidents": "women_crimes_rape_sec_376_i",
            "Cognizable crime rate": "complaints_rate_of_cognizable_crime_ipc_sll",
        }
        tgt_opts = {k: v for k, v in tgt_opts.items() if ml_data.empty or v in ml_data.columns}
        pick = st.multiselect(
            t("Targets"),
            list(tgt_opts.keys()),
            default=list(tgt_opts.keys())[:2],
            key="acc_targets",
        )
        max_n = st.slider(t("Max districts"), 8, 40, 20, key="acc_max")
        if st.button(t("Build accuracy"), type="primary", key="acc_build"):
            with st.spinner("Running predictions for sample districts…"):
                acc = build_accuracy_table(
                    ml_data,
                    targets=[tgt_opts[p] for p in pick if p in tgt_opts],
                    max_areas=max_n,
                )
            if acc.empty:
                st.warning("No accuracy rows. Train models: `python train_model.py`")
            else:
                st.session_state["accuracy_table"] = acc

        acc = st.session_state.get("accuracy_table")
        if acc is not None and isinstance(acc, pd.DataFrame) and not acc.empty:
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.metric("Rows", len(acc))
            with s2:
                if "abs_err_blend" in acc.columns and acc["abs_err_blend"].notna().any():
                    st.metric("Mean |err| blend", f"{float(acc['abs_err_blend'].mean()):.3f}")
                else:
                    st.metric("Mean |err| blend", "—")
            with s3:
                if "abs_err_raw" in acc.columns and acc["abs_err_raw"].notna().any():
                    st.metric("Mean |err| raw", f"{float(acc['abs_err_raw'].mean()):.3f}")
                else:
                    st.metric("Mean |err| raw", "—")
            with s4:
                if "blend_better" in acc.columns and acc["blend_better"].notna().any():
                    better = int(acc["blend_better"].fillna(False).sum())
                    total = int(acc["blend_better"].notna().sum())
                    pct = 100 * better / total if total else 0
                    st.metric("Blend better %", f"{pct:.0f}%")
                else:
                    st.metric("Blend better %", "—")

            if "blend_better" in acc.columns and acc["blend_better"].notna().any():
                better = int(acc["blend_better"].fillna(False).sum())
                total = int(acc["blend_better"].notna().sum())
                st.success(
                    f"Blend closer to official history on **{better}/{total}** rows "
                    f"({100 * better / total:.0f}%)."
                )

            if {"abs_err_raw", "abs_err_blend", "district"}.issubset(acc.columns):
                chart_acc = acc.dropna(subset=["abs_err_raw", "abs_err_blend"]).copy()
                if not chart_acc.empty:
                    long = []
                    for _, r in chart_acc.head(15).iterrows():
                        long.append({
                            "district": r["district"],
                            "error": float(r["abs_err_raw"]),
                            "kind": "Model raw",
                        })
                        long.append({
                            "district": r["district"],
                            "error": float(r["abs_err_blend"]),
                            "kind": "Blended",
                        })
                    fig_e = px.bar(
                        pd.DataFrame(long),
                        x="district",
                        y="error",
                        color="kind",
                        barmode="group",
                        title="Absolute error vs official history (lower is better)",
                        template="plotly_dark",
                        color_discrete_map={"Model raw": "#f59e0b", "Blended": "#0ea5e9"},
                    )
                    fig_e.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#0e0e12",
                        height=360,
                        xaxis_tickangle=-35,
                        legend_title_text="",
                    )
                    st.plotly_chart(fig_e, use_container_width=True, key="acc_err_chart")

            st.dataframe(acc, use_container_width=True, hide_index=True)
            spot = acc[acc["district"].astype(str).isin(
                ["Thoothukudi", "Madurai", "Madurai City", "Chennai"]
            )]
            if not spot.empty:
                st.markdown("#### Spotlight · Thoothukudi / Madurai / Chennai")
                st.dataframe(spot, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Download accuracy CSV",
                data=acc.to_csv(index=False).encode("utf-8"),
                file_name="crimecast_accuracy_check.csv",
                mime="text/csv",
                key="acc_dl_csv",
            )
        else:
            st.info("Click **Build accuracy table** to compare official vs model vs blend.")

        # ---- Holdout backtest (linear trend) ----
        st.markdown("### Holdout backtest (linear trend)")
        st.caption(
            "Fit linear trend on years **before** holdout year from `fitted_predictions.csv`, "
            "compare to actual when present. Honest check when multi-year labels exist."
        )
        bt1, bt2, bt3 = st.columns([1.2, 1, 1])
        with bt1:
            bt_tgt = st.selectbox(
                "Backtest target",
                [
                    ("Rape incidents", "women_crimes_rape_sec_376_i"),
                    ("Murder incidence", "murder_homicide_murder_incidence"),
                    ("Total complaints", "complaints_total_complaints"),
                ],
                format_func=lambda x: x[0],
                key="acc_bt_tgt",
            )
        with bt2:
            bt_year = st.number_input(
                "Holdout year", min_value=2022, max_value=2026, value=2024, key="acc_bt_year"
            )
        with bt3:
            bt_n = st.slider("Max districts", 8, 38, 20, key="acc_bt_n")
        if st.button("Run holdout backtest", type="secondary", key="acc_bt_run"):
            with st.spinner("Backtesting…"):
                try:
                    from forecast_engine import backtest_year

                    bdf = backtest_year(bt_tgt[1], int(bt_year), max_districts=int(bt_n))
                    st.session_state["acc_backtest"] = bdf
                except Exception as e:
                    st.error(str(e))
                    st.session_state["acc_backtest"] = pd.DataFrame()
        bdf = st.session_state.get("acc_backtest")
        if isinstance(bdf, pd.DataFrame) and not bdf.empty:
            if "abs_error" in bdf.columns and bdf["abs_error"].notna().any():
                st.metric("Mean |error| (rows with actual)", f"{float(bdf['abs_error'].mean()):.3f}")
            st.dataframe(bdf, use_container_width=True, hide_index=True)
            if {"district", "predicted", "actual"}.issubset(bdf.columns):
                plot_b = bdf.dropna(subset=["actual"]).head(15)
                if not plot_b.empty:
                    long_b = []
                    for _, r in plot_b.iterrows():
                        long_b.append({"district": r["district"], "value": r["predicted"], "kind": "Predicted"})
                        long_b.append({"district": r["district"], "value": r["actual"], "kind": "Actual"})
                    fig_bt = px.bar(
                        pd.DataFrame(long_b),
                        x="district",
                        y="value",
                        color="kind",
                        barmode="group",
                        template="plotly_dark",
                        title=f"Holdout {int(bt_year)} · predicted vs actual",
                    )
                    fig_bt.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#0e0e12",
                        height=360,
                        xaxis_tickangle=-35,
                    )
                    st.plotly_chart(fig_bt, use_container_width=True, key="acc_bt_chart")
            st.download_button(
                "Download backtest CSV",
                bdf.to_csv(index=False).encode("utf-8"),
                f"backtest_{int(bt_year)}.csv",
                "text/csv",
                key="acc_bt_dl",
            )
        elif bdf is not None and isinstance(bdf, pd.DataFrame):
            st.warning(
                "No backtest rows with actuals — fitted history may lack that holdout year. "
                "Training metrics temporal columns are still informative."
            )

    # ============ ANALYTICS ============
    elif page == "📊 Analytics":
        ops_topbar("Analytics — models & media")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("ML Models", n_models)
        with c2:
            st.metric("Sentiment rows", n_sent)
        with c3:
            st.metric("2026 forecasts", n_2026)
        with c4:
            st.metric("Media signals", n_media or n_harvest)

        st.markdown("### System capabilities")
        st.markdown("""
        - **Official-year training** (≤2023 labels) — media-proxy years not used as y
        - **Temporal validation** — train past years → test latest official year
        - **Sentiment + news fusion** into ML features
        - **Risk Index** = prediction volume + negative sentiment + media buzz
        - **Live map toggle** — news window / murder rate / rape rate / 2026 forecast
        - **Time window** — 30d / 90d / YTD / all time for news heat
        - **Tamil vs English** news split on **Feed Controls** tab
        - **District scorecard** + HTML brief export + **Accuracy Check** table
        """)

        if not news_df.empty and "negative_news_share" in news_df.columns:
            latest_news = news_df.sort_values("year").groupby("district_city").tail(1)
            fig = px.bar(
                latest_news,
                x="district_city",
                y="negative_news_share",
                color="news_count" if "news_count" in latest_news.columns else None,
                title="Negative news share by district",
                template="plotly_dark",
                color_continuous_scale=["#ffffff", "#7dd3fc", "#0284c7", "#0c4a6e"],
            )
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#121218", font_color="#d1d5db")
            st.plotly_chart(fig, use_container_width=True, key="analytics_news")

    # ============ DISTRICT MAP & SCOREBOARD (simplified · 3 tabs) ============
    elif page == "🗺️ District Map & Scoreboard":
        import importlib
        import sys

        if "tn_map" in sys.modules:
            importlib.reload(sys.modules["tn_map"])
        import tn_map as _tn_map
        from tn_map import TN_DISTRICT_CANONICAL

        plot_tn_choropleth = _tn_map.plot_tn_choropleth
        plot_district_heatmap_matrix = getattr(_tn_map, "plot_district_heatmap_matrix", None)
        HEAT_DENSITY = getattr(_tn_map, "HEAT_DENSITY", ["#fff7ed", "#fb923c", "#c2410c"])
        HEAT_WHITE_BLUE = getattr(
            _tn_map,
            "HEAT_WHITE_BLUE",
            ["#ffffff", "#7dd3fc", "#0284c7", "#0c4a6e"],
        )
        HEAT_DENSITY_PLOTLY = getattr(
            _tn_map,
            "HEAT_DENSITY_PLOTLY",
            [[0, "#fff7ed"], [0.5, "#fb923c"], [1, "#7c2d12"]],
        )
        COMPARE_PALETTE = getattr(
            _tn_map, "COMPARE_PALETTE", ["#ef4444", "#3b82f6", "#22c55e"]
        )
        plot_district_carved_out = getattr(_tn_map, "plot_district_carved_out", None)

        ops_topbar("District Map — choropleth · heat · scoreboard")

        density_df = build_crime_density_frame(ml_data, harvest_df, news_df)
        # Default rank: population-normalised murder rate when available
        board = build_district_scoreboard_table(
            ml_data, harvest_df, news_df, rape_2026_df, rank_by="murder_per_lakh"
        )
        if board.empty or "murder_per_lakh" not in board.columns:
            board = build_district_scoreboard_table(
                ml_data, harvest_df, news_df, rape_2026_df, rank_by="murder_rate"
            )

        # Strict 38 TN districts only
        try:
            from district_entities import TN38, to_tn38
        except Exception:
            TN38 = list(TN_DISTRICT_CANONICAL)
            def to_tn38(x, default=None):  # type: ignore
                return x

        district_opts = list(TN38) if TN38 else list(TN_DISTRICT_CANONICAL)
        if not board.empty and "district" in board.columns:
            board = board.copy()
            board["district"] = board["district"].map(lambda x: to_tn38(str(x), default=None))
            board = board[board["district"].notna()]
            board = board.drop_duplicates(subset=["district"], keep="first")

        # Compare lives on sidebar ⚖️ District Compare (merged map carve + full metrics)
        tab_choro, tab_heat, tab_board = st.tabs(
            ["🗺️ Choropleth", "▦ Heat map", "📋 Scoreboard"]
        )
        st.caption(
            "Side-by-side district comparison (carve maps, rates, 2026, ML) → "
            "**⚖️ District Compare** in the sidebar."
        )

        # ---- TAB 1: DISTRICT CHOROPLETH (full TN · every district polygon) ----
        with tab_choro:
            st.markdown("#### Tamil Nadu district choropleth")
            choro_metric_labels = {
                "density_index": "Composite density (0–100)",
                "murder_rate": "Murder rate",
                "rape_rate": "Rape rate",
                "news_90d": "News headlines (90d)",
            }
            choro_available = [
                k
                for k in choro_metric_labels
                if not density_df.empty
                and k in density_df.columns
                and pd.to_numeric(density_df[k], errors="coerce").notna().any()
            ]
            if not choro_available:
                choro_available = ["density_index"]

            c_left, c_right = st.columns([2, 1])
            with c_left:
                choro_pick = st.selectbox(
                    "Colour districts by",
                    choro_available,
                    format_func=lambda k: choro_metric_labels.get(k, k),
                    key="geo_choropleth_metric",
                )
            with c_right:
                choro_scale_name = st.selectbox(
                    "Colour scale",
                    ["Orange–red (density)", "White–blue"],
                    key="geo_choropleth_scale",
                )
            color_scale = (
                HEAT_WHITE_BLUE
                if choro_scale_name.startswith("White")
                else HEAT_DENSITY
            )

            if density_df.empty or choro_pick not in density_df.columns:
                st.warning(
                    "No district metrics yet — run clean pipeline for rates + population. "
                    "GeoJSON still needs data to colour polygons."
                )
            else:
                ranked = density_df.copy()
                ranked[choro_pick] = pd.to_numeric(ranked[choro_pick], errors="coerce")
                ranked = ranked.dropna(subset=[choro_pick]).sort_values(
                    choro_pick, ascending=False
                )
                n_dist = int(ranked["district"].nunique()) if "district" in ranked.columns else len(ranked)
                top3 = ranked.head(3)
                mcols = st.columns(4)
                with mcols[0]:
                    st.metric("Districts on map", n_dist)
                for i, (_, row) in enumerate(top3.iterrows()):
                    with mcols[min(i + 1, 3)]:
                        st.metric(
                            f"#{i + 1} {row['district']}",
                            f"{float(row[choro_pick]):.2f}",
                        )

                with st.spinner("Building district choropleth…"):
                    fig_choro = plot_tn_choropleth(
                        density_df,
                        value_col=choro_pick,
                        name_col="district",
                        title=(
                            f"TN district choropleth · "
                            f"{choro_metric_labels.get(choro_pick, choro_pick)}"
                        ),
                        color_scale=color_scale,
                        colorbar_title=choro_metric_labels.get(choro_pick, "Value"),
                        fill_nulls_from_media=False,
                    )
                if fig_choro is not None:
                    st.plotly_chart(
                        fig_choro, use_container_width=True, key="tn_district_choropleth"
                    )
                    st.caption(
                        "Hover a district for value. Missing metrics stay low/unfilled — "
                        "not the same as zero crime."
                    )
                else:
                    st.warning(
                        "Choropleth unavailable (missing `assets/tamil_nadu_districts.geojson`). "
                        "Re-open the page once online so GeoJSON can cache."
                    )

                with st.expander("Top districts + table", expanded=False):
                    bar_df = ranked.head(15).sort_values(choro_pick, ascending=True)
                    if not bar_df.empty:
                        fig_db = px.bar(
                            bar_df,
                            x=choro_pick,
                            y="district",
                            orientation="h",
                            color=choro_pick,
                            color_continuous_scale=color_scale,
                            template="plotly_dark",
                            title="Top districts (same metric)",
                        )
                        fig_db.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="#0e0e12",
                            height=360,
                            showlegend=False,
                        )
                        st.plotly_chart(fig_db, use_container_width=True, key="tn_choro_bars")
                    show_cols = []
                    for c in (
                        "district",
                        "population_lakhs",
                        choro_pick,
                        "murder_rate",
                        "rape_rate",
                    ):
                        if c in density_df.columns and c not in show_cols:
                            show_cols.append(c)
                    tbl = density_df.loc[:, show_cols].copy()
                    tbl = tbl.loc[:, ~tbl.columns.duplicated()]
                    for c in list(tbl.columns):
                        if c == "district":
                            continue
                        ser = tbl[c]
                        if isinstance(ser, pd.DataFrame):
                            ser = ser.iloc[:, 0]
                        tbl[c] = pd.to_numeric(ser, errors="coerce").round(2)
                    if choro_pick in tbl.columns:
                        tbl = tbl.sort_values(choro_pick, ascending=False, na_position="last")
                    st.dataframe(tbl, use_container_width=True, hide_index=True)

        # ---- TAB 2: HEAT MAP (district × metric grid) ----
        with tab_heat:
            st.caption("Rows = districts · columns = rates / news only (z-score colours).")
            heat_top_n = st.slider("Districts shown", 10, 38, 20, key="geo_heat_top_n")

            # Prefer lean density frame; else latest ML
            heat_src = density_df.copy() if not density_df.empty else pd.DataFrame()
            if heat_src.empty and not ml_data.empty:
                heat_src = _latest_ml_by_district(ml_data)
                if "district_city" in heat_src.columns and "district" not in heat_src.columns:
                    heat_src = heat_src.rename(columns={"district_city": "district"})

            # Allowed heat metrics only (no per-lakh, no population, no complaints, no cognizable)
            _HEAT_ALLOWED = (
                "murder_rate",
                "rape_rate",
                "density_index",
                "news_90d",
            )
            heat_metric_opts = [
                c
                for c in _HEAT_ALLOWED
                if not heat_src.empty and c in heat_src.columns
            ]
            # Fallback from raw ML column names
            if len(heat_metric_opts) < 2 and not ml_data.empty:
                latest = _latest_ml_by_district(ml_data)
                heat_src = latest.copy()
                if "district_city" in heat_src.columns:
                    heat_src["district"] = heat_src["district_city"].astype(str)
                for src, dst in [
                    ("murder_homicide_murder_rate", "murder_rate"),
                    ("women_crimes_rape_r", "rape_rate"),
                ]:
                    if src in heat_src.columns and dst not in heat_src.columns:
                        heat_src[dst] = pd.to_numeric(heat_src[src], errors="coerce")
                heat_metric_opts = [c for c in _HEAT_ALLOWED if c in heat_src.columns]

            if heat_src.empty or len(heat_metric_opts) < 1:
                st.warning("No numeric metrics for heat map yet.")
            else:
                default_heat = [c for c in ("murder_rate", "rape_rate", "news_90d", "density_index") if c in heat_metric_opts]
                heat_cols = st.multiselect(
                    "Metrics (columns)",
                    heat_metric_opts,
                    default=default_heat or heat_metric_opts[:3],
                    key="geo_heat_metrics",
                )
                # Hard filter in case session state still has old metrics
                heat_cols = [
                    c
                    for c in heat_cols
                    if c in _HEAT_ALLOWED and "per_lakh" not in c and c not in (
                        "population_lakhs",
                        "complaints",
                        "cognizable_rate",
                        "complaints_per_lakh",
                        "news_per_lakh",
                        "murder_per_lakh",
                        "rape_per_lakh",
                    )
                ]
                if not heat_cols:
                    st.info("Pick at least one metric.")
                else:
                    # Sort districts by first selected metric
                    work = heat_src.copy()
                    if "district" not in work.columns and "district_city" in work.columns:
                        work["district"] = work["district_city"].astype(str)
                    for c in heat_cols:
                        work[c] = pd.to_numeric(work[c], errors="coerce")
                    sort_c = heat_cols[0]
                    work = work.dropna(subset=[sort_c], how="all")
                    work = work.sort_values(sort_c, ascending=False).head(heat_top_n)

                    fig_hm = None
                    if plot_district_heatmap_matrix is not None:
                        fig_hm = plot_district_heatmap_matrix(
                            work,
                            value_cols=heat_cols,
                            name_col="district",
                            title="District × metric heat map (z-score)",
                            top_n=heat_top_n,
                        )
                    # Fallback inline heatmap if helper fails
                    if fig_hm is None and not work.empty:
                        mat = work.set_index("district")[heat_cols]
                        z = (mat - mat.mean()) / mat.std(ddof=0).replace(0, 1)
                        z = z.fillna(0)
                        fig_hm = go.Figure(
                            data=go.Heatmap(
                                z=z.values,
                                x=[c.replace("_", " ") for c in z.columns],
                                y=list(z.index),
                                colorscale=HEAT_DENSITY_PLOTLY,
                                colorbar=dict(title="z-score"),
                                hovertemplate="%{y}<br>%{x}: %{z:.2f}<extra></extra>",
                            )
                        )
                        fig_hm.update_layout(
                            title="District × metric heat map (z-score)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="#0e0e12",
                            font_color="#d1d5db",
                            height=max(380, 22 * len(z)),
                            margin=dict(l=10, r=10, t=48, b=10),
                            yaxis=dict(autorange="reversed"),
                        )
                    if fig_hm is not None:
                        # Prefer density colour scale for heat tab look
                        try:
                            fig_hm.update_traces(colorscale=HEAT_DENSITY_PLOTLY)
                        except Exception:
                            pass
                        st.plotly_chart(fig_hm, use_container_width=True, key="tn_heatmap_matrix")
                    else:
                        st.warning("Could not build heat map.")

                    with st.expander("Raw values (not z-score)", expanded=False):
                        raw = work[["district"] + heat_cols].copy()
                        for c in heat_cols:
                            raw[c] = pd.to_numeric(raw[c], errors="coerce").round(2)
                        st.dataframe(raw, use_container_width=True, hide_index=True)

        # ---- TAB: SCOREBOARD ----
        with tab_board:
            st.caption(
                "Default sort prefers **per-lakh** metrics so large districts are not "
                "always top just by size. Switch to raw counts if needed."
            )
            _rank_opts = [
                "murder_per_lakh",
                "rape_per_lakh",
                "news_per_lakh",
                "complaints_per_lakh",
                "murder_rate",
                "rape_rate",
                "news_90d",
                "complaints",
                "population_lakhs",
            ]
            # Keep only columns that will exist after build (allow all; empty cols sort gracefully)
            rank_metric = st.selectbox(
                t("Scoreboard rank by"),
                _rank_opts,
                index=0,
                key="geo_rank_by",
            )
            board2 = build_district_scoreboard_table(
                ml_data, harvest_df, news_df, rape_2026_df, rank_by=rank_metric
            )
            if board2.empty:
                st.info("No scoreboard rows yet.")
            else:
                show_b = board2.copy()
                for c in show_b.select_dtypes(include=[np.number]).columns:
                    if c != "rank":
                        show_b[c] = pd.to_numeric(show_b[c], errors="coerce").round(2)
                # Compact columns
                prefer_cols = [
                    c
                    for c in (
                        "rank",
                        "district",
                        "population_lakhs",
                        rank_metric,
                        "murder_rate",
                        "rape_rate",
                        "news_90d",
                    )
                    if c in show_b.columns
                ]
                # unique preserve order
                seen = set()
                cols = []
                for c in prefer_cols:
                    if c not in seen:
                        cols.append(c)
                        seen.add(c)
                st.dataframe(
                    show_b[cols].head(30),
                    use_container_width=True,
                    hide_index=True,
                )
                if rank_metric in board2.columns:
                    top = board2.dropna(subset=[rank_metric]).head(12)
                    if not top.empty:
                        fig_b = px.bar(
                            top.sort_values(rank_metric, ascending=True),
                            x=rank_metric,
                            y="district",
                            orientation="h",
                            template="plotly_dark",
                            color=rank_metric,
                            color_continuous_scale=HEAT_DENSITY,
                        )
                        fig_b.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="#0e0e12",
                            height=380,
                            showlegend=False,
                        )
                        st.plotly_chart(fig_b, use_container_width=True, key="geo_board_bars")

    # ============ MAKE PREDICTION ============
    elif page == "🔮 Predict":
        from tn_map import plot_tn_choropleth, HEAT_WHITE_BLUE
        from predict import predict_for_area

        ops_topbar(f"{t('Predict')} — murder · rape · cognizable · TN map")
        st.caption(
            f"{t('Targets')}: **{t('Murder rate')}**, **{t('Rape rate')}**, Cognizable. "
            "Model estimate + history blend — not FIR truth. "
            f"{data_freshness_caption()}"
        )

        predict_many, TARGET_ALIASES, TARGET_CONFIGS, resolve_target = get_predict_functions()

        PREDICT_TARGETS = [
            ("murder_homicide_murder_rate", "Murder rate"),
            ("women_crimes_rape_r", "Rape rate"),
            ("complaints_rate_of_cognizable_crime_ipc_sll", "Cognizable crime rate"),
        ]
        # Only keep targets that exist in configs
        available = [(k, lab) for k, lab in PREDICT_TARGETS if k in TARGET_CONFIGS]
        if not available:
            available = PREDICT_TARGETS

        col1, col2, col3 = st.columns(3)
        with col1:
            areas = (
                sorted(ml_data["district_city"].unique().tolist())
                if not ml_data.empty
                else ["Chennai"]
            )
            area = st.selectbox(
                "Focus district",
                areas,
                index=areas.index("Chennai") if "Chennai" in areas else 0,
                key="pred_area",
            )
        with col2:
            labels = [lab for _, lab in available]
            selected_target_label = st.selectbox("Target", labels, key="pred_target_lab")
            target = [k for k, lab in available if lab == selected_target_label][0]
        with col3:
            year = st.number_input(
                "Year", min_value=2022, max_value=2030, value=2026, step=1, key="pred_year"
            )

        run_map = st.checkbox(
            "Populate all-district prediction map (TN38)",
            value=True,
            key="pred_map_all",
            help="Runs model for every district and colours the map (no news fill).",
        )
        max_map_n = st.slider("Max districts on map", 10, 40, 38, 1, key="pred_map_n") if run_map else 38

        if st.button("🚀 Predict & populate map", type="primary", key="pred_run"):
            with st.spinner("Running prediction for focus district…"):
                try:
                    preds = predict_many(area=area, targets=[target], year=int(year))
                    if not preds.empty:
                        row = preds.iloc[0]
                        st.success("Focus district prediction complete")
                        m1, m2, m3 = st.columns(3)
                        with m1:
                            st.metric("Predicted value", f"{float(row['prediction']):.2f}")
                        with m2:
                            risk = row.get("risk_index", None)
                            risk_label = row.get("risk_label", "N/A")
                            if risk is not None and pd.notna(risk):
                                st.metric("Risk index", f"{float(risk):.3f}", delta=str(risk_label))
                            else:
                                st.metric("Risk index", "N/A")
                        with m3:
                            st.metric("Model", str(row.get("model_name", "Unknown")))

                        st.markdown("### Why this prediction?")
                        for line in explain_prediction_drivers(
                            area, target, ml_data, news_df, harvest_df, row.to_dict()
                        ):
                            st.markdown(f"- {line}")

                        display_cols = [
                            c
                            for c in preds.columns
                            if c in (
                                "area", "year", "target_label", "prediction", "model_raw",
                                "history_baseline", "risk_index", "risk_label", "model_name",
                            )
                        ]
                        st.dataframe(
                            preds[display_cols] if display_cols else preds,
                            use_container_width=True,
                            hide_index=True,
                        )
                        st.session_state["last_pred"] = {
                            "area": area,
                            "target": target,
                            "label": selected_target_label,
                            "year": int(year),
                            "value": float(row["prediction"]),
                        }
                    else:
                        st.error("No prediction returned for focus district.")
                except Exception as e:
                    st.error(f"Prediction failed: {e}")
                    st.info("Run full pipeline (python app.py option 1) if models are missing.")

            if run_map:
                with st.spinner("Populating predictions for all TN districts…"):
                    try:
                        from predict import populate_all_district_predictions

                        map_pred = populate_all_district_predictions(
                            target, int(year), max_districts=int(max_map_n)
                        )
                    except Exception as e:
                        st.warning(f"Bulk populate helper failed ({e}); using per-district loop.")
                        map_pred = pd.DataFrame()
                        try:
                            from district_entities import TN38
                            areas_all = list(TN38)[:max_map_n]
                        except Exception:
                            areas_all = sorted(
                                ml_data["district_city"].dropna().astype(str).unique().tolist()
                            )[:max_map_n]
                        rows = []
                        for dist in areas_all:
                            try:
                                r = predict_for_area(target, dist, year=int(year))
                                rows.append({
                                    "district": r.get("area", dist),
                                    "prediction": float(r["prediction"]),
                                    "source": "model",
                                })
                            except Exception:
                                latest = _latest_ml_by_district(ml_data)
                                if not latest.empty and target in latest.columns:
                                    m = latest[
                                        latest["district_city"].astype(str).str.casefold()
                                        == str(dist).casefold()
                                    ]
                                    if not m.empty and pd.notna(m.iloc[0][target]):
                                        rows.append({
                                            "district": dist,
                                            "prediction": float(m.iloc[0][target]),
                                            "source": "official_history",
                                        })
                        map_pred = pd.DataFrame(rows)

                if not map_pred.empty:
                    st.session_state["pred_map_df"] = map_pred
                    st.session_state["pred_map_meta"] = {
                        "label": selected_target_label,
                        "year": int(year),
                        "target": target,
                    }
                    n_model = int((map_pred.get("source") == "model").sum()) if "source" in map_pred.columns else len(map_pred)
                    st.success(
                        f"Populated **{len(map_pred)}** districts "
                        f"({n_model} from model; rest official/median fallback)."
                    )
                else:
                    st.warning("Could not populate any district predictions.")

        # Always show last populated map if present
        map_pred = st.session_state.get("pred_map_df")
        meta = st.session_state.get("pred_map_meta") or {}
        if map_pred is not None and isinstance(map_pred, pd.DataFrame) and not map_pred.empty:
            lab = meta.get("label", selected_target_label)
            yr = meta.get("year", year)
            st.markdown(f"### TN prediction map · {lab} · {yr}")
            st.caption(
                "Colours = **prediction values only** (model, or official history / median if model fails). "
                "**No news fill.**"
            )
            fig_pm = plot_tn_choropleth(
                map_pred,
                value_col="prediction",
                name_col="district",
                title=f"Predicted {lab} · {yr}",
                fill_nulls_from_media=False,
                color_scale=HEAT_WHITE_BLUE,
                colorbar_title="Predicted",
            )
            if fig_pm is not None:
                st.plotly_chart(fig_pm, use_container_width=True, key="pred_tn_map")
            show = map_pred.copy()
            if "prediction" in show.columns:
                show = show.sort_values("prediction", ascending=False)
            st.dataframe(show, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Download populated predictions CSV",
                data=show.to_csv(index=False).encode("utf-8"),
                file_name=f"predictions_{meta.get('target', target)}_{yr}.csv",
                mime="text/csv",
                key="pred_dl_csv",
            )

    # ============ SENTIMENT ANALYSIS (news → score → TN map) ============
    elif page == "💬 Sentiment":
        from tn_map import plot_tn_choropleth, HEAT_WHITE_BLUE

        tb1, tb2 = st.columns([20, 1])
        with tb1:
            ops_topbar("Sentiment — news headlines scored · TN district map")
        with tb2:
            st.markdown('<div class="refresh-icon-wrap" style="padding-top:6px;">', unsafe_allow_html=True)
            if st.button("🔄", type="secondary", key="sent_refresh_news", help="Refresh news then re-score"):
                with st.spinner("Fetching news…"):
                    ok, msg = run_acquire_news_refresh()
                if ok:
                    st.toast("News updated", icon="✅")
                    st.rerun()
                else:
                    st.toast("Refresh failed", icon="⚠️")
            st.markdown("</div>", unsafe_allow_html=True)

        st.caption(
            "Uses **media harvest / news** → DistilBERT/lexicon sentiment → district **concern score** "
            "on the TN map (white = lower concern → blue = higher). "
            "**Word clouds** per district below. Scores cached in **SQLite**."
        )

        sc1, sc2, sc3 = st.columns([1, 1, 2])
        with sc1:
            do_score = st.button("Score news → map", type="primary", key="sent_run_score")
        with sc2:
            rescore = st.checkbox("Force re-score", value=False, key="sent_rescore")
        with sc3:
            max_n = st.slider("Max headlines to score", 40, 300, 120, 20, key="sent_max_n")

        if do_score or st.session_state.get("sent_map_ready"):
            with st.spinner("Scoring headlines and building district sentiment…"):
                dist_sent, scored_hl = build_news_sentiment_by_district(
                    harvest_df,
                    news_df,
                    max_score=max_n,
                    rescore=bool(rescore and do_score),
                )
            st.session_state["sent_map_ready"] = True
            st.session_state["sent_dist"] = dist_sent
            st.session_state["sent_hl"] = scored_hl
        else:
            # Try load from SQLite cache
            try:
                from db import load_district_sentiment, load_scored_headlines, db_status

                dist_sent = load_district_sentiment()
                scored_hl = load_scored_headlines(limit=max_n)
                if dist_sent.empty:
                    dist_sent, scored_hl = build_news_sentiment_by_district(
                        harvest_df, news_df, max_score=max_n, rescore=False
                    )
            except Exception:
                dist_sent, scored_hl = build_news_sentiment_by_district(
                    harvest_df, news_df, max_score=max_n, rescore=False
                )

        if "sent_dist" in st.session_state and st.session_state.get("sent_dist") is not None:
            if do_score:
                pass  # already set
            elif not dist_sent.empty:
                pass
            else:
                dist_sent = st.session_state.get("sent_dist", dist_sent)
                scored_hl = st.session_state.get("sent_hl", scored_hl)

        # Metrics strip — TN38 districts only (drop junk / Other / City duplicates)
        if not dist_sent.empty and "district" in dist_sent.columns:
            try:
                from district_entities import to_tn38, TN38

                dist_sent = dist_sent.copy()
                dist_sent["district"] = dist_sent["district"].map(
                    lambda x: to_tn38(str(x), default=None)
                )
                dist_sent = dist_sent[dist_sent["district"].notna()]
                if not dist_sent.empty and dist_sent["district"].duplicated().any():
                    num_cols = [
                        c
                        for c in dist_sent.columns
                        if c != "district" and pd.api.types.is_numeric_dtype(dist_sent[c])
                    ]
                    agg = {c: ("sum" if c == "n_headlines" else "mean") for c in num_cols}
                    dist_sent = dist_sent.groupby("district", as_index=False).agg(agg)
                if TN38:
                    dist_sent = dist_sent[dist_sent["district"].isin(TN38)]
            except Exception:
                pass

        if not dist_sent.empty:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Districts scored", len(dist_sent))
            with m2:
                st.metric("Headlines used", int(dist_sent["n_headlines"].sum()) if "n_headlines" in dist_sent.columns else 0)
            with m3:
                avg_pol = float(dist_sent["polarity_mean"].mean()) if "polarity_mean" in dist_sent.columns else 0
                st.metric("Avg polarity", f"{avg_pol:.3f}")
            with m4:
                top = dist_sent.sort_values(
                    "concern_score" if "concern_score" in dist_sent.columns else dist_sent.columns[0],
                    ascending=False,
                ).iloc[0]
                st.metric("Highest concern", str(top.get("district", "—")))

            map_metric = st.radio(
                "Map metric",
                ["concern_score", "negative_share", "polarity_mean (inverted)"],
                horizontal=True,
                key="sent_map_metric",
            )
            plot_df = dist_sent.copy()
            if map_metric.startswith("polarity"):
                plot_df["map_value"] = -pd.to_numeric(plot_df["polarity_mean"], errors="coerce")
                vcol = "map_value"
                cbar = "−polarity"
            elif map_metric == "negative_share":
                vcol = "negative_share"
                cbar = "Neg share"
            else:
                vcol = "concern_score"
                cbar = "Concern"

            left, right = st.columns([1.3, 1], gap="medium")
            with left:
                with st.spinner("TN sentiment map…"):
                    fig_s = plot_tn_choropleth(
                        plot_df,
                        value_col=vcol,
                        name_col="district",
                        title=f"TN news sentiment · {map_metric}",
                        fill_nulls_from_media=False,
                        color_scale=HEAT_WHITE_BLUE,
                        colorbar_title=cbar,
                    )
                if fig_s is not None:
                    st.plotly_chart(fig_s, use_container_width=True, key="sent_tn_map")
                else:
                    fig_fb = px.bar(
                        plot_df.sort_values(vcol, ascending=True).tail(20),
                        x=vcol,
                        y="district",
                        orientation="h",
                        color=vcol,
                        color_continuous_scale=HEAT_WHITE_BLUE,
                        template="plotly_dark",
                        title="District sentiment ranking",
                    )
                    fig_fb.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#0e0e12",
                        height=480,
                    )
                    st.plotly_chart(fig_fb, use_container_width=True, key="sent_map_fallback")
            with right:
                st.markdown("**District concern ranking**")
                render_district_heat(plot_df, vcol, "district", None, top_n=15)
                st.dataframe(
                    dist_sent.head(20),
                    use_container_width=True,
                    hide_index=True,
                )

            # District selector → filter data for that district
            dist_opts = ["All districts"] + sorted(
                dist_sent["district"].dropna().astype(str).unique().tolist()
            )
            pick_sent = st.selectbox(
                "Select district (shows related scores & headlines)",
                dist_opts,
                key="sent_pick_district",
            )

            if pick_sent != "All districts":
                st.markdown(f"### District · **{pick_sent}**")
                row_d = dist_sent[
                    dist_sent["district"].astype(str).str.casefold() == pick_sent.casefold()
                ]
                if row_d.empty:
                    row_d = dist_sent[
                        dist_sent["district"].astype(str).str.contains(
                            pick_sent, case=False, na=False
                        )
                    ]
                if not row_d.empty:
                    r0 = row_d.iloc[0]
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.metric("Concern score", f"{float(r0.get('concern_score', 0)):.2f}")
                    with c2:
                        st.metric("Polarity", f"{float(r0.get('polarity_mean', 0)):.3f}")
                    with c3:
                        st.metric("Neg share", f"{float(r0.get('negative_share', 0))*100:.1f}%")
                    with c4:
                        st.metric("Headlines", int(r0.get("n_headlines") or 0))
                    st.dataframe(row_d, use_container_width=True, hide_index=True)
                if not scored_hl.empty and "district" in scored_hl.columns:
                    local_hl = scored_hl[
                        scored_hl["district"].astype(str).str.casefold().str.contains(
                            pick_sent.casefold()[:6], na=False
                        )
                    ]
                    if "polarity" in local_hl.columns:
                        local_hl = local_hl.sort_values("polarity", ascending=True)
                    st.markdown("#### Headlines for this district")
                    st.dataframe(
                        local_hl.head(30) if not local_hl.empty else scored_hl.head(5),
                        use_container_width=True,
                        hide_index=True,
                    )
                    if local_hl.empty:
                        st.caption("No headlines matched this district name — showing sample of all.")
            else:
                if not scored_hl.empty:
                    st.markdown("### All scored headlines (sample)")
                    show_hl = scored_hl.copy()
                    if "polarity" in show_hl.columns:
                        show_hl = show_hl.sort_values("polarity", ascending=True)
                    st.dataframe(show_hl.head(25), use_container_width=True, hide_index=True)
        else:
            st.warning(
                "No scored news yet. Click **🔄** to refresh media, then **Score news → map**."
            )

        # ---- Word clouds (per district) inside Sentiment ----
        st.markdown("---")
        st.markdown("### ☁️ Word clouds by district")
        st.caption(
            "Terms from media harvest / scored headlines. "
            "Image cloud needs `pip install wordcloud`; frequency bars always work."
        )
        try:
            from sentiment_wordclouds import (
                collect_district_texts,
                district_list,
                word_freq_for_district,
                freq_dataframe,
                make_wordcloud_image,
            )

            _hl_for_wc = locals().get("scored_hl")
            if not isinstance(_hl_for_wc, pd.DataFrame) or _hl_for_wc.empty:
                _hl_for_wc = st.session_state.get("sent_hl")
            if not isinstance(_hl_for_wc, pd.DataFrame):
                _hl_for_wc = pd.DataFrame()

            texts_df = collect_district_texts(harvest_df, news_df, _hl_for_wc)
            wc_dists = district_list(texts_df)
            if not texts_df.empty and wc_dists:
                # Default to district selected above (if any)
                focus = st.session_state.get("sent_pick_district") or "All districts"
                default_wc = 0
                if focus and str(focus) != "All districts":
                    for i, d in enumerate(wc_dists):
                        if str(d).casefold() == str(focus).casefold():
                            default_wc = i
                            break
                wc1, wc2 = st.columns([2, 1])
                with wc1:
                    wc_dist = st.selectbox(
                        "Word cloud district",
                        wc_dists,
                        index=min(default_wc, max(0, len(wc_dists) - 1)),
                        key="sent_wc_district",
                    )
                with wc2:
                    wc_topn = st.slider("Top words", 15, 80, 40, key="sent_wc_topn")

                ctr = word_freq_for_district(texts_df, wc_dist, top_n=wc_topn + 20)
                n_rows = int(
                    (texts_df["district"].astype(str).str.casefold() == str(wc_dist).casefold()).sum()
                )
                st.caption(
                    f"**{wc_dist}** · {n_rows} text rows · "
                    f"{sum(ctr.values()) if ctr else 0} tokens"
                )
                if not ctr:
                    st.info(
                        f"No tokens for **{wc_dist}**. Refresh news or pick a district with headlines."
                    )
                else:
                    img = make_wordcloud_image(ctr)
                    wca, wcb = st.columns([1.25, 1])
                    with wca:
                        if img is not None:
                            st.image(
                                img,
                                use_container_width=True,
                                caption=f"Word cloud · {wc_dist}",
                            )
                        else:
                            st.caption("Install `wordcloud` for image cloud · showing bars.")
                        fdf = freq_dataframe(ctr, top_n=wc_topn)
                        if not fdf.empty:
                            fig_wc = px.bar(
                                fdf.sort_values("count", ascending=True),
                                x="count",
                                y="word",
                                orientation="h",
                                template="plotly_dark",
                                color="count",
                                color_continuous_scale="Blues",
                                title=f"Top terms · {wc_dist}",
                            )
                            fig_wc.update_layout(
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="#0e0e12",
                                height=min(520, 22 * len(fdf) + 90),
                                showlegend=False,
                                margin=dict(l=8, r=8, t=40, b=8),
                            )
                            st.plotly_chart(
                                fig_wc, use_container_width=True, key="sent_wc_bar"
                            )
                    with wcb:
                        fdf = freq_dataframe(ctr, top_n=min(30, wc_topn))
                        st.dataframe(fdf, use_container_width=True, hide_index=True)
                        st.download_button(
                            "Download word freqs CSV",
                            fdf.to_csv(index=False).encode("utf-8"),
                            f"sentiment_words_{str(wc_dist).replace(' ', '_')}.csv",
                            "text/csv",
                            key="sent_wc_dl",
                        )
            else:
                st.info(
                    "No district-linked headlines for word clouds yet. "
                    "Click **🔄** to refresh news, then re-open Sentiment."
                )
        except Exception as e:
            st.warning(f"Word cloud section unavailable: {e}")

        try:
            from db import db_status

            st.caption(f"Database: `{db_status()}`")
        except Exception:
            pass

    # ============ 2026 FORECASTS (multi-target · method toggle) ============
    elif page == "📅 2026 Forecasts":
        from tn_map import plot_tn_choropleth, HEAT_WHITE_BLUE

        ops_topbar(f"{t('2026 Forecasts')} — multi-target · method toggle · TN map")
        st.warning(
            f"**{t('Scenario only')}** — model/trend estimate for discussion. "
            "Not an official SCRB forecast and not a fact about future crime."
        )
        st.caption(
            "TN **38 districts** · **rape / murder / complaints** · methods: "
            "**linear · last year · blend** · map = forecast only (no news fill). "
            f"{data_freshness_caption()}"
        )

        try:
            from forecast_engine import FORECAST_TARGETS, METHODS, forecast_districts
        except Exception:
            FORECAST_TARGETS = {
                "rape_incidents": {"label": "Rape incidents (Sec 376)"},
            }
            METHODS = ("linear", "last_year", "blend")
            forecast_districts = None  # type: ignore

        tgt_keys = list(FORECAST_TARGETS.keys())
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            f_tgt = st.selectbox(
                "Forecast target",
                tgt_keys,
                format_func=lambda k: FORECAST_TARGETS[k].get("label", k),
                key="f2026_target",
            )
        with fc2:
            f_method = st.selectbox(
                "Method",
                list(METHODS),
                format_func=lambda m: {
                    "linear": "Linear trend",
                    "last_year": "Last year carry",
                    "blend": "Blend 50/50",
                }.get(m, m),
                key="f2026_method",
            )
        with fc3:
            f_year = st.number_input(
                "Horizon year", min_value=2024, max_value=2030, value=2026, key="f2026_year"
            )

        if st.button("Generate / Refresh Forecasts ", type="primary", key="f2026_gen"):
            with st.spinner(f"Running {f_method} forecast · {f_tgt} · TN38…"):
                preds = None
                err_msg = None
                try:
                    if forecast_districts is not None:
                        preds = forecast_districts(
                            f_tgt, method=f_method, target_year=int(f_year), save=True
                        )
                    else:
                        # Fallback rape-only engine
                        predict_2026, generate_report = get_2026_functions()
                        if predict_2026 and f_tgt == "rape_incidents":
                            preds = predict_2026()
                            if generate_report:
                                try:
                                    generate_report(preds)
                                except Exception:
                                    pass
                        else:
                            err_msg = "forecast_engine unavailable"
                except Exception as e:
                    err_msg = str(e)

                if preds is not None and not isinstance(preds, pd.DataFrame):
                    try:
                        preds = pd.DataFrame(preds)
                    except Exception:
                        preds = None

                if preds is None or getattr(preds, "empty", True):
                    # Fallback CSV by target
                    candidates = [
                        OUTPUT_DIR / "rape_predictions_2026_all_districts.csv",
                        OUTPUT_DIR / f"forecast_{int(f_year)}_{f_tgt}.csv",
                    ]
                    try:
                        from forecast_engine import FORECAST_TARGETS as _FT

                        candidates.insert(0, OUTPUT_DIR / _FT[f_tgt]["out_csv"])
                    except Exception:
                        pass
                    for csv_path in candidates:
                        if csv_path.exists():
                            preds = pd.read_csv(csv_path)
                            st.warning(
                                f"Using saved `{csv_path.name}`. "
                                f"({err_msg})" if err_msg else ""
                            )
                            break
                    if preds is None or getattr(preds, "empty", True):
                        st.error(
                            f"Could not generate. {err_msg or ''}\n"
                            "Check fitted_predictions.csv / run train pipeline."
                        )
                        preds = None

                if preds is not None and not preds.empty:
                    # Ensure map column
                    if (
                        "predicted_2026_rape_incidents" not in preds.columns
                        and "predicted_value" in preds.columns
                    ):
                        preds = preds.copy()
                        preds["predicted_2026_rape_incidents"] = preds["predicted_value"]
                    preds = normalize_2026_forecast_df(preds)
                    # After normalize, re-attach predicted_value if only rape col remains
                    if "predicted_value" not in preds.columns and "predicted_2026_rape_incidents" in preds.columns:
                        preds["predicted_value"] = preds["predicted_2026_rape_incidents"]
                    n_hi = int(
                        (preds.get("risk_level", pd.Series(dtype=str)).astype(str) == "HIGH").sum()
                    ) if "risk_level" in preds.columns else 0
                    st.success(
                        f"**{FORECAST_TARGETS.get(f_tgt, {}).get('label', f_tgt)}** · "
                        f"**{f_method}** · **{len(preds)}** districts · {n_hi} HIGH"
                    )
                    rape_2026_df = preds
                    st.session_state["f2026_df"] = preds
                    st.session_state["f2026_meta"] = {
                        "target": f_tgt,
                        "method": f_method,
                        "year": int(f_year),
                    }
                    try:
                        load_rape_2026.clear()
                    except Exception:
                        pass
                    try:
                        from db import save_rape_2026

                        if f_tgt == "rape_incidents":
                            save_rape_2026(preds)
                    except Exception:
                        pass

        # Prefer session data; always normalize for map (TN38, no cities/junk)
        if "f2026_df" in st.session_state and isinstance(st.session_state["f2026_df"], pd.DataFrame):
            if not st.session_state["f2026_df"].empty:
                rape_2026_df = st.session_state["f2026_df"]
        if not rape_2026_df.empty:
            rape_2026_df = normalize_2026_forecast_df(rape_2026_df)
            if "predicted_value" not in rape_2026_df.columns and "predicted_2026_rape_incidents" in rape_2026_df.columns:
                rape_2026_df = rape_2026_df.copy()
                rape_2026_df["predicted_value"] = rape_2026_df["predicted_2026_rape_incidents"]
            st.session_state["f2026_df"] = rape_2026_df

        meta_f = st.session_state.get("f2026_meta") or {}
        if meta_f:
            st.caption(
                f"Showing: **{meta_f.get('target', '—')}** · method **{meta_f.get('method', '—')}** · "
                f"year **{meta_f.get('year', 2026)}**"
            )

        if not rape_2026_df.empty:
            rnc = "district"
            if rnc not in rape_2026_df.columns:
                rnc = "district_city" if "district_city" in rape_2026_df.columns else rape_2026_df.columns[0]

            metric_opts = [
                c
                for c in (
                    "predicted_value",
                    "predicted_2026_rape_incidents",
                    "rape_risk_index",
                    "pred_high",
                    "pred_low",
                )
                if c in rape_2026_df.columns
            ] or [
                c for c in rape_2026_df.select_dtypes(include=[np.number]).columns
                if c != "rank"
            ][:3]

            if not metric_opts:
                st.warning("Forecast table has no numeric columns to map.")
            else:
                map_metric_2026 = st.radio(
                    "Map metric",
                    metric_opts,
                    horizontal=True,
                    key="f2026_map_metric",
                )

                n_filled = int(
                    pd.to_numeric(rape_2026_df[map_metric_2026], errors="coerce").notna().sum()
                )

                with left:
                    with st.spinner("Building 2026 TN map…"):
                        fig_26 = plot_tn_choropleth(
                            rape_2026_df,
                            value_col=map_metric_2026,
                            name_col=rnc,
                            title=f"2026 forecast · {map_metric_2026}",
                            fill_nulls_from_media=False,  # never paint news on forecast map
                            color_scale=HEAT_WHITE_BLUE,
                            colorbar_title="Forecast",
                        )
                    if fig_26 is not None:
                        st.plotly_chart(fig_26, use_container_width=True, key="f2026_tn_map")
                    else:
                        st.warning("Map GeoJSON unavailable — ranking bars.")
                        fig_b = px.bar(
                            rape_2026_df.dropna(subset=[map_metric_2026])
                            .sort_values(map_metric_2026, ascending=True)
                            .tail(20),
                            x=map_metric_2026,
                            y=rnc,
                            orientation="h",
                            color=map_metric_2026,
                            color_continuous_scale=HEAT_WHITE_BLUE,
                            template="plotly_dark",
                        )
                        fig_b.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="#0e0e12",
                            height=480,
                        )
                        st.plotly_chart(fig_b, use_container_width=True, key="f2026_bar_fallback")
                with right:
                    st.markdown("**High → low ranking**")
                    ranked = rape_2026_df.sort_values(
                        map_metric_2026, ascending=False, na_position="last"
                    )
                    render_district_heat(
                        ranked.dropna(subset=[map_metric_2026]),
                        map_metric_2026,
                        rnc,
                        "risk_level" if "risk_level" in ranked.columns else None,
                        top_n=18,
                    )

                # District picker for detail
                dopts = ranked[rnc].dropna().astype(str).tolist()
                pick_f = st.selectbox("District detail", dopts, key="f2026_pick_dist")
                detail = ranked[ranked[rnc].astype(str) == pick_f]
                if not detail.empty:
                    st.dataframe(detail, use_container_width=True, hide_index=True)

                show_cols = [
                    c
                    for c in (
                        "rank", "district", "pred_low", "predicted_2026_rape_incidents", "pred_high",
                        "uncertainty_width", "rape_risk_index", "risk_level", "confidence", "method",
                    )
                    if c in rape_2026_df.columns
                ]
                st.markdown("### Full table (high → low · TN38)")
                st.dataframe(
                    ranked[show_cols] if show_cols else ranked,
                    use_container_width=True,
                    hide_index=True,
                )
                st.download_button(
                    "Download CSV",
                    rape_2026_df.to_csv(index=False).encode("utf-8"),
                    "rape_2026_predictions.csv",
                    "text/csv",
                    key="f2026_dl",
                )

                mid_col = (
                    "predicted_value"
                    if "predicted_value" in rape_2026_df.columns
                    else (
                        "predicted_2026_rape_incidents"
                        if "predicted_2026_rape_incidents" in rape_2026_df.columns
                        else None
                    )
                )
                if mid_col and {"pred_low", "pred_high", rnc}.issubset(set(rape_2026_df.columns)):
                    st.markdown("#### Uncertainty bands (top 15)")
                    top = ranked.dropna(subset=[mid_col]).head(15).copy()
                    if not top.empty:
                        top["err_minus"] = (top[mid_col] - top["pred_low"]).clip(lower=0)
                        top["err_plus"] = (top["pred_high"] - top[mid_col]).clip(lower=0)
                        fig_u = go.Figure()
                        fig_u.add_trace(
                            go.Bar(
                                name="forecast mid",
                                x=top[rnc],
                                y=top[mid_col],
                                error_y=dict(
                                    type="data",
                                    symmetric=False,
                                    array=top["err_plus"],
                                    arrayminus=top["err_minus"],
                                    color="#38bdf8",
                                ),
                                marker_color="#0284c7",
                            )
                        )
                        fig_u.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="#0e0e12",
                            height=400,
                            title="Top 15 · forecast with uncertainty",
                            xaxis_tickangle=-35,
                            yaxis_title="Value",
                            showlegend=False,
                        )
                        st.plotly_chart(fig_u, use_container_width=True, key="rape2026_uncertainty")
        else:
            st.info(
                "No forecasts loaded yet. Click **Generate / Refresh Forecasts** "
                "or run: `python predict_2026_rape_all_districts.py` / forecast_engine."
            )

    # ============ DISTRICT COMPARE (merged map carve + full metrics) ============
    elif page == "⚖️ District Compare":
        # Palette + carve maps (from former Map → Compare tab)
        try:
            import tn_map as _tn_cmp

            COMPARE_PALETTE = getattr(
                _tn_cmp, "COMPARE_PALETTE", ["#ef4444", "#3b82f6", "#22c55e", "#a855f7"]
            )
            plot_district_carved_out = getattr(_tn_cmp, "plot_district_carved_out", None)
        except Exception:
            COMPARE_PALETTE = ["#ef4444", "#3b82f6", "#22c55e", "#a855f7"]
            plot_district_carved_out = None

        ops_topbar(
            f"{t('District Compare')} — carve maps · rates · per-lakh · 2026 · ML"
        )
        st.caption(
            "Merged from **Map → Compare** + full scorecard. Pick **2–4** districts: "
            "outline maps, official rates, per-lakh, news, sentiment, 2026, optional ML."
        )
        try:
            from district_entities import TN38

            area_opts = list(TN38)
        except Exception:
            area_opts = []
            if not ml_data.empty and "district_city" in ml_data.columns:
                area_opts = sorted(
                    ml_data["district_city"].dropna().astype(str).unique().tolist()
                )
            if not area_opts and not rape_2026_df.empty:
                ncol = "district" if "district" in rape_2026_df.columns else "district_city"
                area_opts = sorted(rape_2026_df[ncol].dropna().astype(str).unique().tolist())

        default_pick = [
            d for d in ("Thoothukudi", "Madurai", "Chennai", "Salem") if d in area_opts
        ][:2]
        if len(default_pick) < 2:
            default_pick = [d for d in ("Chennai", "Madurai", "Coimbatore") if d in area_opts][:2]
        if not default_pick and area_opts:
            default_pick = area_opts[:2]

        picks = st.multiselect(
            "Districts to compare (2–4)",
            area_opts,
            default=default_pick,
            max_selections=4,
            key="cmp_districts",
        )
        if len(picks) < 2:
            st.info("Select at least **two** districts.")
        else:
            cards = [
                build_district_scorecard(
                    d, ml_data, news_df, harvest_df, rape_2026_df, sentiment_df
                )
                for d in picks
            ]

            # ---- Carved map shapes (from Map Compare) ----
            st.markdown("### District outlines")
            if plot_district_carved_out is not None:
                n_map = len(picks)
                map_cols = st.columns(n_map)
                for i, (col, d) in enumerate(zip(map_cols, picks)):
                    with col:
                        color = COMPARE_PALETTE[i % len(COMPARE_PALETTE)]
                        fig_c = plot_district_carved_out(
                            d, color=color, title=d, height=300
                        )
                        if fig_c is not None:
                            st.plotly_chart(
                                fig_c,
                                use_container_width=True,
                                key=f"cmp_carve_{i}_{d}",
                            )
                        else:
                            st.caption(f"Map outline unavailable for {d}")
            else:
                st.caption("Carved outlines unavailable (GeoJSON / tn_map helper).")

            # Optional live ML predictions
            pc1, pc2, pc3 = st.columns([1.4, 1, 1])
            with pc1:
                pred_target_label = st.selectbox(
                    "ML prediction target",
                    [
                        "Murder rate",
                        "Rape rate",
                        "Rape incidents",
                        "Murder incidence",
                        "Total complaints",
                        "Cognizable crime rate",
                    ],
                    key="cmp_pred_target",
                )
            with pc2:
                pred_year = st.number_input(
                    "Prediction year",
                    min_value=2022,
                    max_value=2030,
                    value=2026,
                    key="cmp_pred_year",
                )
            with pc3:
                st.write("")
                st.write("")
                run_ml = st.button("Run ML for selected", type="primary", key="cmp_run_pred")

            _label_to_target = {
                "Murder rate": "murder_homicide_murder_rate",
                "Rape rate": "women_crimes_rape_r",
                "Rape incidents": "women_crimes_rape_sec_376_i",
                "Murder incidence": "murder_homicide_murder_incidence",
                "Total complaints": "complaints_total_complaints",
                "Cognizable crime rate": "complaints_rate_of_cognizable_crime_ipc_sll",
            }
            tgt = _label_to_target[pred_target_label]
            if run_ml:
                with st.spinner("Predicting…"):
                    try:
                        from predict import predict_for_area

                        for i, d in enumerate(picks):
                            try:
                                r = predict_for_area(tgt, d, year=int(pred_year))
                                cards[i]["ml_prediction"] = float(r["prediction"])
                                cards[i]["ml_model_raw"] = r.get("model_raw")
                                cards[i]["ml_history"] = r.get("history_baseline")
                            except Exception as ex:
                                cards[i]["ml_prediction"] = None
                                cards[i]["ml_error"] = str(ex)
                        st.session_state["cmp_cards"] = cards
                        st.session_state["cmp_picks"] = picks
                        st.session_state["cmp_target_label"] = pred_target_label
                    except Exception as e:
                        st.error(f"Predict failed: {e}")

            if st.session_state.get("cmp_picks") == picks and st.session_state.get("cmp_cards"):
                # Keep ML fields from session if same picks
                saved = st.session_state["cmp_cards"]
                if len(saved) == len(cards):
                    for i in range(len(cards)):
                        for k in ("ml_prediction", "ml_model_raw", "ml_history", "ml_error"):
                            if k in saved[i]:
                                cards[i][k] = saved[i][k]

            metric_keys = [
                ("population_lakhs", "Pop. (lakhs)"),
                ("murder_rate", "Murder rate"),
                ("rape_rate", "Rape rate"),
                ("murder_per_lakh", "Murder / lakh"),
                ("rape_per_lakh", "Rape / lakh"),
                ("news_90d", "News 90d"),
                ("news_per_lakh", "News / lakh"),
                ("complaints", "Complaints"),
                ("complaints_per_lakh", "Complaints / lakh"),
                ("sentiment_polarity", "Sentiment polarity"),
                ("forecast_2026_rape", "2026 rape forecast"),
                ("rape_risk_index", "2026 risk index"),
                ("ml_prediction", f"ML · {pred_target_label}"),
            ]

            # Side-by-side metric cards + brief download
            st.markdown("### Side-by-side metrics")
            cols = st.columns(len(picks))
            for i, (col, d, card) in enumerate(zip(cols, picks, cards)):
                with col:
                    accent = COMPARE_PALETTE[i % len(COMPARE_PALETTE)]
                    st.markdown(
                        f"<div style='height:3px;width:48px;background:{accent};"
                        f"border-radius:2px;margin:0 0 8px 0;'></div>",
                        unsafe_allow_html=True,
                    )
                    risk = str(card.get("risk_level") or "—")
                    st.markdown(f"### {d}")
                    st.caption(f"Risk: **{risk}**")
                    for k, lab in metric_keys:
                        v = card.get(k)
                        if v is None:
                            st.metric(lab, "—")
                        else:
                            try:
                                st.metric(lab, f"{float(v):.2f}")
                            except Exception:
                                st.metric(lab, str(v))
                    drivers = explain_prediction_drivers(
                        d, "murder_homicide_murder_rate", ml_data, news_df, harvest_df, None
                    )
                    html = district_brief_html(card, drivers)
                    st.download_button(
                        f"⬇️ Brief HTML · {d}",
                        data=html.encode("utf-8"),
                        file_name=f"CRIMECAST_{str(d).replace(' ', '_')}_brief.html",
                        mime="text/html",
                        key=f"cmp_dl_brief_{i}_{d}",
                    )

            # Comparison table
            rows = []
            for k, lab in metric_keys:
                row = {"Metric": lab}
                for d, card in zip(picks, cards):
                    v = card.get(k)
                    try:
                        row[d] = None if v is None else float(v)
                    except Exception:
                        row[d] = v
                rows.append(row)
            cmp_df = pd.DataFrame(rows)
            st.markdown("### Comparison table")
            st.dataframe(cmp_df, use_container_width=True, hide_index=True)

            # Grouped bars
            chart_rows = []
            for k, lab in metric_keys:
                if k in ("population_lakhs",):
                    continue
                for d, card in zip(picks, cards):
                    v = card.get(k)
                    try:
                        if v is not None and pd.notna(v):
                            chart_rows.append(
                                {"Metric": lab, "District": d, "Value": float(v)}
                            )
                    except Exception:
                        pass
            if chart_rows:
                cdf = pd.DataFrame(chart_rows)
                rate_labs = {
                    "Murder rate",
                    "Rape rate",
                    "Murder / lakh",
                    "Rape / lakh",
                    "News / lakh",
                    "Complaints / lakh",
                    "Sentiment polarity",
                    "2026 risk index",
                }
                fig1 = px.bar(
                    cdf[cdf["Metric"].isin(rate_labs)],
                    x="Metric",
                    y="Value",
                    color="District",
                    barmode="group",
                    template="plotly_dark",
                    color_discrete_sequence=COMPARE_PALETTE,
                    title="Rates & per-lakh (side-by-side)",
                )
                fig1.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#0e0e12",
                    height=380,
                )
                st.plotly_chart(fig1, use_container_width=True, key="cmp_rates")
                fig2 = px.bar(
                    cdf[~cdf["Metric"].isin(rate_labs)],
                    x="Metric",
                    y="Value",
                    color="District",
                    barmode="group",
                    template="plotly_dark",
                    color_discrete_sequence=COMPARE_PALETTE,
                    title="Counts & volumes (side-by-side)",
                )
                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#0e0e12",
                    height=380,
                )
                st.plotly_chart(fig2, use_container_width=True, key="cmp_counts")

            # Murder rate history (from Map Compare)
            if not ml_data.empty and "murder_homicide_murder_rate" in ml_data.columns:
                st.markdown("### Murder rate over years")
                pair_cf = {str(d).casefold() for d in picks}
                hist = ml_data[
                    ml_data["district_city"].astype(str).str.casefold().isin(pair_cf)
                    & ml_data["year"].notna()
                ].copy()
                if not hist.empty:
                    hist["murder_homicide_murder_rate"] = pd.to_numeric(
                        hist["murder_homicide_murder_rate"], errors="coerce"
                    )
                    fig_h = px.line(
                        hist.sort_values("year"),
                        x="year",
                        y="murder_homicide_murder_rate",
                        color="district_city",
                        markers=True,
                        template="plotly_dark",
                        color_discrete_sequence=COMPARE_PALETTE,
                        title="Murder rate history (official / ML-ready rows)",
                    )
                    fig_h.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#0e0e12",
                        height=320,
                    )
                    st.plotly_chart(fig_h, use_container_width=True, key="cmp_murder_hist")
                else:
                    st.caption("No multi-year murder-rate rows for these districts.")

            # Radar
            st.markdown("### Normalized profile (0–1 within selection)")
            radar_keys = [
                k
                for k, _ in metric_keys
                if k not in ("population_lakhs", "sentiment_polarity")
            ]
            vals_by_key = {k: [] for k in radar_keys}
            for card in cards:
                for k in radar_keys:
                    try:
                        vals_by_key[k].append(
                            float(card[k]) if card.get(k) is not None else np.nan
                        )
                    except Exception:
                        vals_by_key[k].append(np.nan)
            fig_r = go.Figure()
            for d, card in zip(picks, cards):
                rvals = []
                labs = []
                for k, lab in metric_keys:
                    if k not in radar_keys:
                        continue
                    series = np.array(vals_by_key[k], dtype=float)
                    lo, hi = np.nanmin(series), np.nanmax(series)
                    try:
                        v = float(card.get(k)) if card.get(k) is not None else np.nan
                    except Exception:
                        v = np.nan
                    if np.isnan(v) or not np.isfinite(hi - lo) or hi <= lo:
                        norm = 0.0
                    else:
                        norm = (v - lo) / (hi - lo)
                    rvals.append(norm)
                    labs.append(lab)
                if rvals:
                    fig_r.add_trace(
                        go.Scatterpolar(
                            r=rvals + [rvals[0]],
                            theta=labs + [labs[0]],
                            fill="toself",
                            name=d,
                        )
                    )
            fig_r.update_layout(
                polar=dict(bgcolor="#0e0e12", radialaxis=dict(visible=True, range=[0, 1])),
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                height=480,
                title="Relative profile within selection (1 = highest among picks)",
            )
            st.plotly_chart(fig_r, use_container_width=True, key="cmp_radar")

            st.download_button(
                "Download comparison CSV",
                cmp_df.to_csv(index=False).encode("utf-8"),
                "district_compare.csv",
                "text/csv",
                key="cmp_dl",
            )

            with st.expander("Recent headlines by district"):
                for d, card in zip(picks, cards):
                    st.markdown(f"**{d}**")
                    hls = card.get("headlines") or []
                    if hls:
                        for h in hls[:5]:
                            st.markdown(f"- {h}")
                    else:
                        st.caption("No headlines cached for this district.")

    # ============ RISK EXPLAIN (SHAP / LIME) ============
    elif page == "🔍 Risk Explain":
        ops_topbar(
            f"{t('Risk Explain')} — why a district has high risk (SHAP / LIME-style)"
        )
        st.warning(
            "Explanations are **model-based / analytical**, not legal determinations. "
            "SHAP uses the `shap` package when installed; otherwise a transparent proxy "
            "and LIME-style local linear model are used."
        )
        try:
            from district_entities import TN38

            dist_opts = list(TN38)
        except Exception:
            dist_opts = sorted(
                ml_data["district_city"].dropna().astype(str).unique().tolist()
            ) if not ml_data.empty else ["Chennai", "Madurai", "Salem"]

        # Suggest high-risk from 2026 if available
        default_ix = 0
        if not rape_2026_df.empty:
            rnc = "district" if "district" in rape_2026_df.columns else "district_city"
            mcol = (
                "predicted_2026_rape_incidents"
                if "predicted_2026_rape_incidents" in rape_2026_df.columns
                else None
            )
            if mcol and rnc in rape_2026_df.columns:
                top = (
                    rape_2026_df.dropna(subset=[mcol])
                    .sort_values(mcol, ascending=False)
                )
                if not top.empty:
                    top_d = str(top.iloc[0][rnc])
                    if top_d in dist_opts:
                        default_ix = dist_opts.index(top_d)

        c1, c2, c3 = st.columns([1.4, 1.2, 1])
        with c1:
            area = st.selectbox(
                "District",
                dist_opts,
                index=default_ix,
                key="explain_district",
            )
        with c2:
            exp_label = st.selectbox(
                "Model target",
                [
                    "Rape incidents",
                    "Rape rate",
                    "Murder rate",
                    "Murder incidence",
                    "Total complaints",
                    "Cognizable crime rate",
                ],
                key="explain_target",
            )
        with c3:
            exp_year = st.number_input(
                "Year", min_value=2022, max_value=2030, value=2026, key="explain_year"
            )

        _lt = {
            "Rape incidents": "women_crimes_rape_sec_376_i",
            "Rape rate": "women_crimes_rape_r",
            "Murder rate": "murder_homicide_murder_rate",
            "Murder incidence": "murder_homicide_murder_incidence",
            "Total complaints": "complaints_total_complaints",
            "Cognizable crime rate": "complaints_rate_of_cognizable_crime_ipc_sll",
        }
        exp_target = _lt[exp_label]

        run_exp = st.button("Explain risk drivers", type="primary", key="explain_run")

        card = build_district_scorecard(
            area, ml_data, news_df, harvest_df, rape_2026_df, sentiment_df
        )
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("District", area)
        with m2:
            st.metric("Risk level", str(card.get("risk_level") or "—"))
        with m3:
            st.metric(
                "2026 rape forecast",
                f"{card['forecast_2026_rape']:.1f}" if card.get("forecast_2026_rape") is not None else "—",
            )
        with m4:
            st.metric(
                "Murder rate",
                f"{card['murder_rate']:.2f}" if card.get("murder_rate") is not None else "—",
            )

        # Narrative drivers (existing)
        drivers = explain_prediction_drivers(
            area, exp_target, ml_data, news_df, harvest_df, pred_row=None
        )
        st.markdown("#### Quick narrative drivers")
        for line in drivers:
            st.markdown(f"- {line}")

        if run_exp or st.session_state.get("explain_done"):
            st.session_state["explain_done"] = True
            try:
                from risk_explain import (
                    composite_risk_factors,
                    global_feature_importances,
                    lime_local_explain,
                    shap_or_proxy_explain,
                )
            except Exception as e:
                st.error(f"Could not import risk_explain: {e}")
                composite_risk_factors = None  # type: ignore

            if composite_risk_factors is not None:
                # State medians for composite
                latest = _latest_ml_by_district(ml_data)
                meds: dict[str, float] = {}
                if not latest.empty:
                    for key, col in [
                        ("murder_rate", "murder_homicide_murder_rate"),
                        ("rape_rate", "women_crimes_rape_r"),
                        ("rape_incidents", "women_crimes_rape_sec_376_i"),
                        ("complaints", "complaints_total_complaints"),
                    ]:
                        if col in latest.columns:
                            s = pd.to_numeric(latest[col], errors="coerce").dropna()
                            if len(s):
                                meds[key] = float(s.median())
                if not rape_2026_df.empty and "predicted_2026_rape_incidents" in rape_2026_df.columns:
                    s = pd.to_numeric(
                        rape_2026_df["predicted_2026_rape_incidents"], errors="coerce"
                    ).dropna()
                    if len(s):
                        meds["forecast_2026_rape"] = float(s.median())

                st.markdown("### Multi-source risk push (why this district looks high-risk)")
                comp = composite_risk_factors(area, card, state_medians=meds)
                if not comp.empty:
                    fig_c = px.bar(
                        comp,
                        x="risk_push",
                        y="factor",
                        orientation="h",
                        color="risk_push",
                        color_continuous_scale="Reds",
                        template="plotly_dark",
                        title="Composite risk factors (vs state medians)",
                        hover_data=["value", "state_median", "vs_median"],
                    )
                    fig_c.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#0e0e12",
                        height=360,
                        yaxis=dict(autorange="reversed"),
                    )
                    st.plotly_chart(fig_c, use_container_width=True, key="explain_composite")
                    st.dataframe(comp, use_container_width=True, hide_index=True)
                else:
                    st.info("Not enough scorecard fields for composite factors.")

                tab_shap, tab_lime, tab_glob = st.tabs(
                    ["SHAP / proxy", "LIME-style local", "Global model importance"]
                )

                with tab_shap:
                    with st.spinner("Computing SHAP or importance×z proxy…"):
                        try:
                            res = shap_or_proxy_explain(
                                exp_target, area, year=int(exp_year), top_n=12
                            )
                        except Exception as e:
                            res = {
                                "method": "error",
                                "base_prediction": None,
                                "contributions": pd.DataFrame(),
                                "note": str(e),
                            }
                    st.caption(res.get("note") or "")
                    if res.get("base_prediction") is not None:
                        st.metric(
                            f"Model prediction · {exp_label}",
                            f"{float(res['base_prediction']):.3f}",
                        )
                    contr = res.get("contributions")
                    if isinstance(contr, pd.DataFrame) and not contr.empty:
                        ycol = "feature"
                        vcol = "contribution" if "contribution" in contr.columns else contr.columns[-1]
                        fig_s = px.bar(
                            contr.sort_values(
                                "abs_contribution" if "abs_contribution" in contr.columns else vcol,
                                ascending=True,
                            ),
                            x=vcol,
                            y=ycol,
                            orientation="h",
                            color=vcol,
                            color_continuous_scale="RdBu_r",
                            template="plotly_dark",
                            title=f"{res.get('method', 'explain')} · top drivers for {area}",
                        )
                        fig_s.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="#0e0e12",
                            height=420,
                        )
                        st.plotly_chart(fig_s, use_container_width=True, key="explain_shap")
                        st.dataframe(contr, use_container_width=True, hide_index=True)
                    else:
                        st.warning("No SHAP/proxy contributions returned.")

                with tab_lime:
                    with st.spinner("LIME-style local linear model (perturbations)…"):
                        try:
                            lime = lime_local_explain(
                                exp_target, area, year=int(exp_year), top_n=12
                            )
                        except Exception as e:
                            lime = {
                                "contributions": pd.DataFrame(),
                                "note": str(e),
                                "base_prediction": None,
                            }
                    st.caption(lime.get("note") or "")
                    if lime.get("base_prediction") is not None:
                        st.metric("Base model prediction", f"{float(lime['base_prediction']):.3f}")
                    lcontr = lime.get("contributions")
                    if isinstance(lcontr, pd.DataFrame) and not lcontr.empty:
                        fig_l = px.bar(
                            lcontr.sort_values("abs_contribution", ascending=True),
                            x="contribution",
                            y="feature",
                            orientation="h",
                            color="contribution",
                            color_continuous_scale="RdBu_r",
                            template="plotly_dark",
                            title=f"LIME-style local contributions · {area}",
                        )
                        fig_l.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="#0e0e12",
                            height=420,
                        )
                        st.plotly_chart(fig_l, use_container_width=True, key="explain_lime")
                        st.dataframe(lcontr, use_container_width=True, hide_index=True)
                    else:
                        st.warning("LIME-style explanation unavailable for this target/area.")

                with tab_glob:
                    with st.spinner("Global feature importances…"):
                        try:
                            gimp = global_feature_importances(exp_target, top_n=15)
                        except Exception as e:
                            gimp = pd.DataFrame()
                            st.warning(str(e))
                    if not gimp.empty:
                        fig_g = px.bar(
                            gimp.sort_values("importance", ascending=True),
                            x="importance",
                            y="feature",
                            orientation="h",
                            template="plotly_dark",
                            color="importance",
                            color_continuous_scale="Blues",
                            title=f"Global model importance · {exp_label}",
                        )
                        fig_g.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="#0e0e12",
                            height=420,
                        )
                        st.plotly_chart(fig_g, use_container_width=True, key="explain_global")
                        st.dataframe(gimp, use_container_width=True, hide_index=True)
                        st.caption(f"Method: `{gimp['method'].iloc[0]}`")
                    else:
                        st.info("No global importances extracted.")

                if card.get("headlines"):
                    st.markdown("#### Supporting headlines")
                    for h in card["headlines"][:6]:
                        st.markdown(f"- {h}")
        else:
            st.info("Click **Explain risk drivers** to run SHAP/proxy + LIME-style analysis.")

    # ============ HEALTH CHECK ============
    elif page == "🩺 Health":
        ops_topbar(f"{t('Health')} — demo readiness · files · models · news · DB")
        st.caption(
            "Green = OK · Yellow = usable with gaps · Red = fix before demo. "
            "CLI: `python health_check.py`"
        )
        hc1, hc2 = st.columns(2)
        with hc1:
            if st.button("Re-run health check", type="primary", key="health_rerun"):
                try:
                    st.cache_data.clear()
                except Exception:
                    pass
                st.rerun()
        with hc2:
            if st.button("Migrate CSVs → SQLite DB", type="secondary", key="health_migrate_csv"):
                with st.spinner("Loading CSVs into data/crimecast.db…"):
                    try:
                        from db import migrate_csvs_to_db

                        stats = migrate_csvs_to_db(also_structured=True)
                        ok_n = sum(
                            1
                            for v in stats.get("datasets", {}).values()
                            if v.get("status") == "ok"
                        )
                        st.success(
                            f"Migrated **{ok_n}** datasets into `{stats.get('db_path')}`"
                        )
                        try:
                            st.cache_data.clear()
                        except Exception:
                            pass
                        st.session_state["last_migrate_stats"] = stats
                    except Exception as e:
                        st.error(f"Migrate failed: {e}")

        if st.session_state.get("last_migrate_stats"):
            with st.expander("Last migrate report", expanded=False):
                st.json(st.session_state["last_migrate_stats"])

        try:
            from health_check import run_health_check

            report = run_health_check()
        except Exception as e:
            report = {
                "overall": "blocked",
                "blocking": 1,
                "warnings": 0,
                "checks": [{"name": "health_check", "status": "fail", "detail": str(e), "blocking": True}],
                "generated_at": "",
            }

        overall = report.get("overall", "?")
        ocolor = {
            "ready": "🟢",
            "ready_with_warnings": "🟡",
            "blocked": "🔴",
        }.get(overall, "⚪")
        h1, h2, h3, h4 = st.columns(4)
        with h1:
            st.metric("Overall", f"{ocolor} {overall}")
        with h2:
            st.metric("Blocking", int(report.get("blocking") or 0))
        with h3:
            st.metric("Warnings", int(report.get("warnings") or 0))
        with h4:
            st.metric("Checks", len(report.get("checks") or []))

        rows = []
        for c in report.get("checks") or []:
            rows.append(
                {
                    "status": c.get("status"),
                    "name": c.get("name"),
                    "detail": c.get("detail"),
                    "blocking": c.get("blocking"),
                }
            )
        hdf = pd.DataFrame(rows)
        if not hdf.empty:
            # Colour-ish display via emoji column
            def _em(s):
                return {"ok": "🟢 OK", "warn": "🟡 WARN", "fail": "🔴 FAIL"}.get(str(s), s)

            show_h = hdf.copy()
            show_h["status"] = show_h["status"].map(_em)
            st.dataframe(show_h, use_container_width=True, hide_index=True)

        # Alert log + DB status + dataset registry
        st.markdown("### SQLite / datasets / alert log")
        try:
            from db import db_status, load_alert_log, list_datasets

            st.json(db_status())
            reg = list_datasets()
            if not reg.empty:
                st.markdown("#### CSV datasets in DB")
                st.dataframe(reg, use_container_width=True, hide_index=True)
            else:
                st.caption(
                    "No dataset tables yet — click **Migrate CSVs → SQLite DB** "
                    "or run `python migrate_csv_to_db.py`"
                )
            alog = load_alert_log(limit=25)
            if not alog.empty:
                st.markdown("#### Recent alert log")
                st.dataframe(alog, use_container_width=True, hide_index=True)
            else:
                st.caption("Alert log empty — open Live Feed once to persist alerts.")
        except Exception as e:
            st.caption(f"DB status unavailable: {e}")

        st.markdown("### How it works (short)")
        st.markdown(
            """
1. Official tables → clean → **ML-ready**  
2. Train on official years ≤2023 → **models/**  
3. News harvest → Live heat / sentiment  
4. Predict + 2026 scenario (linear / last-year / blend)  
5. Explain + compare for viva  

Full path: `docs/DEMO_SCRIPT.md` · screenshots: `docs/REPORTS_SCREENSHOTS_README.md`
"""
        )
        if report.get("generated_at"):
            st.caption(f"Generated at {report['generated_at']}")

    # ============ VISUALIZATIONS ============
    elif page == "📊 Visualizations":
        hero(
            "📊 Visualizations",
            "Charts from the pipeline (`model_outputs/figures`) plus any report screenshots.",
            badges=[{"text": "PNG gallery", "cls": "blue"}],
        )

        fig_files = list(FIGURES_DIR.glob("*.png")) if FIGURES_DIR.exists() else []
        if fig_files:
            selected = st.selectbox("Choose visualization", [f.name for f in fig_files])
            img_path = FIGURES_DIR / selected
            if img_path.exists():
                st.image(str(img_path), use_container_width=True, caption=selected)
        else:
            st.warning("No figures found. Run the full pipeline or visualizations first.")

        st.caption("Tip: Run `python visualize.py` or option 3 in the CLI app to generate more charts.")

    # ============ DATA EXPLORER ============
    elif page == "📈 Data Explorer":
        hero(
            "📈 Data Explorer",
            "Browse ML-ready rows and sentiment scores with quick scatter plots.",
            badges=[{"text": "Interactive", "cls": "blue"}],
        )
        
        st.subheader("ML-Ready Data Sample")
        if not ml_data.empty:
            st.dataframe(ml_data.head(20), use_container_width=True)
            
            # Simple interactive plot
            numeric_cols = ml_data.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                x_col = st.selectbox("X axis", numeric_cols, index=0)
                y_col = st.selectbox("Y axis", numeric_cols, index=1 if len(numeric_cols)>1 else 0)
                
                fig = px.scatter(ml_data, x=x_col, y=y_col, color="area_type", 
                                hover_data=["district_city", "year"])
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ML data not loaded. Check dataset/cleaned/")

        if not sentiment_df.empty:
            st.subheader("Sentiment Scores")
            st.dataframe(sentiment_df.head(15), use_container_width=True)

if __name__ == "__main__":
    main()