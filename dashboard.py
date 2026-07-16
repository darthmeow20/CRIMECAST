"""
CRIMECAST Interactive Dashboard
Run with: streamlit run dashboard.py
"""

from __future__ import annotations

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

    .ticker {
        background: #0c0c0f; border-top: 1px solid #1f1f28;
        padding: 8px 12px; border-radius: 0 0 12px 12px;
        font-size: 0.72rem; color: #9ca3af; margin-top: 8px;
    }
    .ticker .live { color: #f87171; font-weight: 700; }

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


# Cache heavy loads
@st.cache_data
def load_ml_data():
    if ML_READY_FILE.exists():
        return pd.read_csv(ML_READY_FILE)
    return pd.DataFrame()

@st.cache_data
def load_sentiment_scores():
    if SENTIMENT_SCORES.exists():
        return pd.read_csv(SENTIMENT_SCORES)
    return pd.DataFrame()

@st.cache_data
def load_crime_predictions():
    if CRIME_PREDICTIONS.exists():
        return pd.read_csv(CRIME_PREDICTIONS)
    return pd.DataFrame()

@st.cache_data
def load_rape_2026():
    if RAPE_2026.exists():
        return pd.read_csv(RAPE_2026)
    return pd.DataFrame()


@st.cache_data
def load_news_signals():
    news_path = OUTPUT_DIR / "news_signals.csv"
    if news_path.exists():
        return pd.read_csv(news_path)
    return pd.DataFrame()


@st.cache_data
def load_media_harvest():
    path = _latest_media_harvest_path()
    if path is not None and path.exists():
        return pd.read_csv(path)
    raw = OUTPUT_DIR / "news_signals_raw.csv"
    if raw.exists():
        return pd.read_csv(raw)
    return pd.DataFrame()


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
    Not official crime rates. Not 2026 model forecasts.
    """
    from datetime import datetime, timedelta

    try:
        from tn_map import TN_DISTRICT_CANONICAL, _normalize_name
    except Exception:
        TN_DISTRICT_CANONICAL = []
        def _normalize_name(x):  # type: ignore
            return str(x).strip().lower()

    junk = {
        "", "other / statewide", "unknown", "india", "tamil nadu", "tn",
        "quick", "killed", "teenage", "courier", "pushpa", "dinamani",
        "dmk’s", "dmk's", "telangana", "taramani", "poonamallee",
    }

    def _clean_dist_series(s: pd.Series) -> pd.Series:
        out = s.astype(str).str.strip()
        mask = ~out.str.lower().isin(junk) & (out.str.len() >= 3)
        return out.where(mask, other=pd.NA)

    def _counts_from_harvest(h: pd.DataFrame, mask: pd.Series | None = None) -> pd.Series:
        dcol = "district" if "district" in h.columns else (
            "district_city" if "district_city" in h.columns else None
        )
        if dcol is None or "headline" not in h.columns:
            return pd.Series(dtype=float)
        sub = h if mask is None else h.loc[mask]
        if sub.empty:
            return pd.Series(dtype=float)
        sub = sub.copy()
        sub["_d"] = _clean_dist_series(sub[dcol])
        sub = sub.dropna(subset=["_d"])
        if sub.empty:
            return pd.Series(dtype=float)
        return sub.groupby("_d")["headline"].count().astype(float)

    primary = pd.Series(dtype=float)
    all_time = pd.Series(dtype=float)
    window_label = f"{recent_days}d"

    if harvest_df is not None and not harvest_df.empty and "headline" in harvest_df.columns:
        h = harvest_df.copy()
        if "date" in h.columns:
            h["_dt"] = pd.to_datetime(h["date"], errors="coerce")
            cutoff = datetime.now() - timedelta(days=recent_days)
            recent_mask = h["_dt"].notna() & (h["_dt"] >= cutoff)
            primary = _counts_from_harvest(h, recent_mask)
            # If 90d is empty (stale harvest), use current calendar year as soft primary
            if primary.empty or primary.sum() == 0:
                y_now = datetime.now().year
                y_mask = h["_dt"].notna() & (h["_dt"].dt.year == y_now)
                primary = _counts_from_harvest(h, y_mask)
                window_label = f"YTD {y_now}"
            all_time = _counts_from_harvest(h, None)
        else:
            primary = _counts_from_harvest(h, None)
            all_time = primary.copy()
            window_label = "all"

    # news_signals fill for all-time / missing districts
    if news_df is not None and not news_df.empty and "district_city" in news_df.columns:
        n = news_df.copy()
        n["_d"] = _clean_dist_series(n["district_city"])
        n = n.dropna(subset=["_d"])
        if "news_count" in n.columns and not n.empty:
            # latest year for "current-ish" signal fill
            if "year" in n.columns:
                y = pd.to_numeric(n["year"], errors="coerce")
                latest = n[y == y.max()]
            else:
                latest = n
            sig = latest.groupby("_d")["news_count"].sum().astype(float)
            if primary.empty:
                primary = sig
                window_label = "signals"
            # all-time from signals
            sig_all = n.groupby("_d")["news_count"].sum().astype(float)
            for k, v in sig_all.items():
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

    g = primary.rename("news_90d").reset_index()
    g.columns = ["district", "news_90d"]
    g["news_90d"] = pd.to_numeric(g["news_90d"], errors="coerce").fillna(0.0)
    g["is_soft_fill"] = g["news_90d"] < 1.0
    g = g.sort_values("news_90d", ascending=False).reset_index(drop=True)
    # window label for UI caption
    g["heat_window"] = window_label
    return g, "news_90d", "district"


def _latest_ml_by_district(ml_data: pd.DataFrame) -> pd.DataFrame:
    if ml_data is None or ml_data.empty or "district_city" not in ml_data.columns:
        return pd.DataFrame()
    m = ml_data.copy()
    if "year" in m.columns:
        m = m.sort_values("year").groupby("district_city", as_index=False).tail(1)
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
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<title>CRIMECAST — {dist}</title>
<style>
 body {{ font-family: Segoe UI, Arial, sans-serif; margin: 32px; color: #111; }}
 h1 {{ color: #b91c1c; }}
 .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
 .box {{ border: 1px solid #ddd; border-radius: 8px; padding: 12px; }}
 .k {{ color: #666; font-size: 12px; text-transform: uppercase; }}
 .v {{ font-size: 22px; font-weight: 700; }}
</style></head><body>
<h1>CRIMECAST District Brief — {dist}</h1>
<p>Generated for Tamil Nadu crime intelligence (official rates + news + 2026 forecast).</p>
<div class="grid">
 <div class="box"><div class="k">Murder rate</div><div class="v">{card.get('murder_rate', '—')}</div></div>
 <div class="box"><div class="k">Rape rate</div><div class="v">{card.get('rape_rate', '—')}</div></div>
 <div class="box"><div class="k">News 90d</div><div class="v">{card.get('news_90d', '—')}</div></div>
 <div class="box"><div class="k">2026 rape forecast</div><div class="v">{card.get('forecast_2026_rape', '—')}</div></div>
</div>
<p><b>Risk:</b> {card.get('risk_level', '—')}
 &nbsp;·&nbsp; <b>Risk index:</b> {card.get('rape_risk_index', '—')}
 &nbsp;·&nbsp; <b>News rank:</b> #{card.get('news_rank', '—')}
 &nbsp;·&nbsp; <b>Year:</b> {card.get('year', '—')}</p>
<h2>Why this district stands out</h2>
<ul>{lines}</ul>
<h2>Recent headlines</h2>
<ul>{hls or '<li>No headlines on file. Use Refresh news.</li>'}</ul>
<p style="color:#888;font-size:12px;">CRIMECAST · Official training labels ≤2023 · Live heat from news · Print this page to PDF (Ctrl+P)</p>
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
        df, vcol, ncol = build_current_affairs_heat(harvest_df, news_df, recent_days=recent_days)
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
    heat, vcol, _ = build_current_affairs_heat(harvest_df, news_df, recent_days=90)
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
    heat, vcol, _ = build_current_affairs_heat(harvest_df, news_df, recent_days=90)
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
            ]:
                if col in r.index and pd.notna(r[col]):
                    try:
                        card[key] = float(r[col])
                    except Exception:
                        pass

    heat, vcol, _ = build_current_affairs_heat(harvest_df, news_df, recent_days=90)
    if not heat.empty and vcol in heat.columns:
        m = heat[heat["district"].astype(str).str.casefold() == area_cf]
        if m.empty:
            m = heat[heat["district"].astype(str).str.casefold().str.contains(area_cf[:5], na=False)]
        if not m.empty:
            card["news_90d"] = float(m.iloc[0][vcol])
            card["news_rank"] = int((heat[vcol] > m.iloc[0][vcol]).sum()) + 1

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
    Does NOT re-download already acquired news. Bulk one-time populate is CLI/app option n mode 1.
    """
    import subprocess
    import sys

    script = PROJECT_ROOT / "acquire_news_signals.py"
    if not script.exists():
        return False, f"Missing {script.name}"

    # Prefer incremental --refresh-new (new only)
    cmd = [sys.executable, "-B", str(script), "--refresh-new", "--max-items", "22"]
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
            _sync_db_after_news()
            return True, f"NEW news only (skipped already acquired).\n\n{tail}"
        # Fallback: in-process refresh_new_news
        try:
            from acquire_news_signals import refresh_new_news

            info = refresh_new_news()
            load_news_signals.clear()
            load_media_harvest.clear()
            _sync_db_after_news()
            return True, f"NEW news refresh (in-process): {info}\n\n{tail or result.stderr or ''}"
        except Exception as e2:
            err = (result.stderr or "")[-800:] or str(e2)
            return False, f"Refresh failed (exit {result.returncode}): {err}"
    except subprocess.TimeoutExpired:
        return False, "News refresh timed out. Try CLI: python acquire_news_signals.py --refresh-new"
    except Exception as e:
        try:
            from acquire_news_signals import refresh_new_news

            info = refresh_new_news()
            load_news_signals.clear()
            load_media_harvest.clear()
            _sync_db_after_news()
            return True, f"NEW news refresh (fallback): {info}"
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
    if need_score:
        try:
            from sentiment_analysis import score_text
            from district_entities import resolve_district
        except Exception:
            score_text = None
            resolve_district = None

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
                    dist = resolve_district(text, default="Other / Statewide")
                except Exception:
                    dist = "Other / Statewide"
            elif not dist:
                dist = "Other / Statewide"
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
            dist = str(r.get("district") or r.get("district_city") or "Other / Statewide")
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

    # Persist headlines
    try:
        from db import upsert_headlines, save_district_sentiment

        upsert_headlines(scored)
    except Exception:
        save_district_sentiment = None  # type: ignore

    # District aggregates
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
    st.set_page_config(
        page_title="CRIMECAST",
        page_icon="🔺",
        layout="wide",
        initial_sidebar_state="expanded",
    )

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

    page = st.sidebar.radio(
        "Command",
        [
            "🔴 Live Feed",
            "📡 Feed Controls",
            "🏛️ State Administration Comparison",
            "📋 District Scorecard",
            "✅ Accuracy Check",
            "📊 Analytics",
            "🗺️ Geographic",
            "🔥 Heat Map",
            "🔮 Predict",
            "💬 Sentiment",
            "📅 2026 Forecasts",
            "📈 Data Explorer",
        ],
        label_visibility="collapsed",
    )

    # Shared Live Feed controls (set on Feed Controls tab; used by Live Feed)
    if "live_map_metric" not in st.session_state:
        st.session_state["live_map_metric"] = "News (time window)"
    if "live_news_window" not in st.session_state:
        st.session_state["live_news_window"] = "90 days"

    st.sidebar.markdown(
        """
        <div class="ops-status">
            <span class="dot"></span><b style="color:#4ade80">ONLINE</b><br/>
            CRIMECAST · 3-LLM NLP · News + media fill<br/>
            Map: null/zero districts filled from news & media
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Sidebar: compact refresh icon ----
    st.sidebar.markdown("---")
    sc1, sc2 = st.sidebar.columns([1, 4])
    with sc1:
        st.markdown('<div class="refresh-icon-wrap">', unsafe_allow_html=True)
        if st.button("🔄", type="primary", key="sidebar_refresh_news", help="Refresh news"):
            with st.spinner("Fetching news…"):
                ok, msg = run_acquire_news_refresh()
            if ok:
                st.sidebar.success("Updated")
                st.rerun()
            else:
                st.sidebar.error("Failed")
        st.markdown("</div>", unsafe_allow_html=True)
    with sc2:
        st.caption("News")

    # Load data (after possible refresh + rerun)
    ml_data = load_ml_data()
    sentiment_df = load_sentiment_scores()
    crime_preds = load_crime_predictions()
    rape_2026_df = load_rape_2026()
    news_df = load_news_signals()
    harvest_df = load_media_harvest()

    n_models = len([f for f in MODELS_DIR.glob("*.joblib") if "sentiment" not in f.name])
    n_sent = len(sentiment_df) if not sentiment_df.empty else 0
    n_2026 = len(rape_2026_df) if not rape_2026_df.empty else 0
    n_media = len(news_df) if not news_df.empty else 0
    n_harvest = len(harvest_df) if not harvest_df.empty else 0

    # Ensure SQLite schema exists; soft-sync 2026 forecasts if present
    try:
        from db import init_db, save_rape_2026

        init_db()
        if not rape_2026_df.empty:
            save_rape_2026(rape_2026_df)
    except Exception:
        pass

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

    # ============ LIVE FEED — map + feed + HIGH alerts only ============
    if page == "🔴 Live Feed":
        tb1, tb2 = st.columns([20, 1])
        with tb1:
            ops_topbar("CRIMECAST — Tamil Nadu Live Intelligence")
        with tb2:
            st.markdown('<div class="refresh-icon-wrap" style="padding-top:6px;">', unsafe_allow_html=True)
            if st.button("🔄", type="secondary", key="live_refresh_news", help="Refresh news"):
                with st.spinner("Fetching news…"):
                    ok, msg = run_acquire_news_refresh()
                if ok:
                    st.toast("News updated", icon="✅")
                    st.rerun()
                else:
                    st.toast("Refresh failed", icon="⚠️")
            st.markdown("</div>", unsafe_allow_html=True)

        from tn_map import plot_tn_choropleth

        map_metric = st.session_state.get("live_map_metric", "News (time window)")
        time_window = st.session_state.get("live_news_window", "90 days")
        recent_days = _live_window_days(time_window)

        live_map_df, live_vcol, live_ncol, map_caption = build_map_metric_frame(
            map_metric, harvest_df, news_df, ml_data, rape_2026_df, recent_days=recent_days
        )

        # HIGH alerts only on Live Feed
        alerts = compute_alert_rules(ml_data, harvest_df, news_df, rape_2026_df)
        high_alerts = [a for a in alerts if a.get("level") == "HIGH"]
        if high_alerts:
            st.markdown("**HIGH alerts**")
            _render_alert_cards(high_alerts, levels={"HIGH"}, max_n=6)
        else:
            st.caption("No HIGH alerts · MED+HIGH and map settings → **Feed Controls**")

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("EVENTS / MODELS", n_models, delta=None)
        with m2:
            st.metric("SENTIMENT ROWS", n_sent)
        with m3:
            st.metric("MEDIA HEADLINES", n_harvest or n_media)
        with m4:
            active = 0
            if not live_map_df.empty and live_vcol in live_map_df.columns:
                active = int((live_map_df[live_vcol] >= 1).sum())
            st.metric("ACTIVE (window)", active)
        with m5:
            open_alerts = len(high_alerts)
            if not live_map_df.empty and live_vcol in live_map_df.columns:
                thr = live_map_df[live_vcol].quantile(0.75) if len(live_map_df) > 4 else live_map_df[live_vcol].median()
                hot = int((live_map_df[live_vcol] >= thr).sum())
            else:
                hot = 0
            st.metric("HOT DISTRICTS", hot)

        left, right = st.columns([1.05, 1.15], gap="medium")

        with left:
            st.markdown(
                '<div class="panel"><div class="panel-title">● Live intelligence feed · current affairs</div>',
                unsafe_allow_html=True,
            )
            feed = harvest_df if not harvest_df.empty else sentiment_df
            if not feed.empty:
                # First 3 = high negative; rest = other negative (no special labels)
                feed_show = build_negative_news_feed(feed, top_n=14, high_n=3)
                for _, r in feed_show.iterrows():
                    headline = str(r.get("headline") or r.get("text") or r.get("source_text") or "—")
                    source = str(r.get("source") or r.get("sentiment_method") or "News media")
                    label = str(r.get("sentiment_label") or r.get("label") or "News").title()
                    district = str(r.get("district") or r.get("district_city") or "")
                    url = str(r.get("url") or "")
                    crime = str(r.get("crime_types") or r.get("crime_theme") or r.get("crime_type") or "Current affairs")
                    if isinstance(crime, str) and len(crime) > 24:
                        crime = crime[:24] + "…"
                    date_s = str(r.get("date") or "")[:10]
                    if date_s and date_s != "nan":
                        source = f"{source} · {date_s}"
                    render_feed_card(
                        source, headline[:220], label=label, crime=crime, district=district, url=url
                    )
            else:
                st.info("No live media yet. Click **🔄** to refresh news.")
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown(
                f'<div class="panel"><div class="panel-title">Tamil Nadu district heat · {map_metric}</div>',
                unsafe_allow_html=True,
            )
            st.caption(f"Window: {time_window} · change on **📡 Feed Controls**")
            if not live_map_df.empty and live_vcol:
                with st.spinner("Loading map..."):
                    fig_live = plot_tn_choropleth(
                        live_map_df,
                        value_col=live_vcol,
                        name_col=live_ncol,
                        title=f"{map_metric}",
                    )
                if fig_live is not None:
                    fig_live.update_layout(height=420, margin=dict(l=0, r=0, t=48, b=0))
                    st.plotly_chart(fig_live, use_container_width=True, key="live_tn_map")
                    st.caption(map_caption)
                else:
                    st.caption("Map GeoJSON loading… ranking bars.")
                    fig_fb = px.bar(
                        live_map_df.sort_values(live_vcol, ascending=True).tail(15),
                        x=live_vcol,
                        y=live_ncol,
                        orientation="h",
                        color=live_vcol,
                        color_continuous_scale=["#ffffff", "#7dd3fc", "#0284c7", "#0c4a6e"],
                        template="plotly_dark",
                    )
                    fig_fb.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#0e0e12",
                        height=380,
                        margin=dict(l=8, r=8, t=8, b=8),
                    )
                    st.plotly_chart(fig_fb, use_container_width=True, key="live_map_fallback")
            else:
                st.info("No map data for this metric. Refresh news or run pipeline / option 7.")
            st.markdown("</div>", unsafe_allow_html=True)

            if not live_map_df.empty and live_vcol:
                st.caption(f"Top districts · {map_metric}")
                render_district_heat(live_map_df, live_vcol, live_ncol, None, top_n=12)

        st.markdown(
            f"""
            <div class="ticker">
                <span class="live">● LIVE WIRE</span>
                &nbsp; Models {n_models} · Sentiment {n_sent} · Media {n_media or n_harvest}
                · 2026 districts {n_2026} · HIGH alerts {open_alerts}
                · Map: {map_metric} · {time_window}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ============ FEED CONTROLS — MED+HIGH, map metric, window, language ============
    elif page == "📡 Feed Controls":
        ops_topbar("Feed Controls — alerts, map metric, news window, language")
        st.caption(
            "Settings here drive the **Live Feed** heat map. "
            "Live Feed shows district heat, headline feed, and HIGH alerts only."
        )

        st.markdown("### Map metric")
        st.radio(
            "Map metric",
            ["News (time window)", "Murder rate", "Rape rate", "2026 rape forecast"],
            horizontal=True,
            key="live_map_metric",
        )

        map_metric = st.session_state["live_map_metric"]
        if map_metric.startswith("News"):
            st.markdown("### News time window")
            st.radio(
                "News time window",
                ["30 days", "90 days", "YTD", "All time"],
                horizontal=True,
                key="live_news_window",
            )
        else:
            st.caption("Time window applies when Map metric is **News (time window)**.")

        time_window = st.session_state.get("live_news_window", "90 days")
        recent_days = _live_window_days(time_window)
        live_map_df, live_vcol, live_ncol, map_caption = build_map_metric_frame(
            map_metric, harvest_df, news_df, ml_data, rape_2026_df, recent_days=recent_days
        )
        st.info(f"**Live Feed map:** {map_metric} · window **{time_window}** ({recent_days}d) · {map_caption}")

        st.markdown("### Alerts (MEDIUM + HIGH)")
        alerts = compute_alert_rules(ml_data, harvest_df, news_df, rape_2026_df)
        if alerts:
            _render_alert_cards(alerts, levels={"HIGH", "MED"}, max_n=20)
        else:
            st.caption("No MED or HIGH alerts right now.")

        st.markdown("### News language split")
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
                    title="Tamil vs English headlines (harvest)",
                    template="plotly_dark",
                    color_discrete_sequence=["#ef4444", "#3b82f6", "#9ca3af"],
                )
                fig_lang.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=280,
                    margin=dict(l=10, r=10, t=40, b=10),
                    showlegend=True,
                )
                st.plotly_chart(fig_lang, use_container_width=True, key="controls_lang_pie")
        else:
            st.caption("No harvest language data. Click **🔄** in the sidebar to refresh news.")

        if not live_map_df.empty and live_vcol:
            st.markdown("### Preview · top districts (same metric as Live Feed)")
            render_district_heat(live_map_df, live_vcol, live_ncol, None, top_n=15)

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

        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg,#1a1a22,#14141a);border:1px solid #2a2a36;
            border-radius:14px;padding:16px 18px;margin-bottom:14px;">
              <div style="color:#9ca3af;font-size:0.72rem;font-weight:700;letter-spacing:0.08em;">
                DMK vs TVK · FROM OUR DATA (OFFICIAL + MEDIA SUPPORT)
              </div>
              <div style="color:#f3f4f6;font-size:1.35rem;font-weight:800;margin-top:6px;">
                {comb_winner}
              </div>
              <div style="color:#c8c8d0;font-size:0.92rem;margin-top:8px;line-height:1.45;">
                {comb_reason}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info(
            "**Data design:** Official/ML rates lag (best through ~2023). "
            "Media harvest bridges the gap and is the **only** statewide party signal for **TVK** "
            "(no CM term). Combined score weights official **65%** + media **35%** for DMK; "
            "TVK uses media only."
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
                    st.markdown(
                        f"""
                        <div style="background:#14141a;border:1px solid #2a2a36;border-radius:12px;
                        padding:14px;border-top:3px solid {PARTY_COLORS.get(p, '#666')};">
                          <div style="font-weight:800;color:#f3f4f6;font-size:1.1rem;">{p}</div>
                          <div style="color:#9ca3af;font-size:0.75rem;margin:4px 0 8px 0;">{r0.get('role','')}</div>
                          <div style="color:#e5e7eb;font-size:1.6rem;font-weight:800;">{comb_s}</div>
                          <div style="color:#6b7280;font-size:0.72rem;">combined / 100</div>
                          <div style="margin-top:10px;font-size:0.8rem;color:#c8c8d0;line-height:1.5;">
                            Official safety: {rs}<br/>
                            Media support: {ms}<br/>
                            Neg news: {int(r0.get('news_negative') or 0)} / {int(r0.get('news_mentions') or 0)}<br/>
                            <span style="color:#6b7280">{r0.get('data_basis','')}</span>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

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

    # ============ DISTRICT SCORECARD (Tier-1) ============
    elif page == "📋 District Scorecard":
        ops_topbar("District crime scorecard")
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

    # ============ ACCURACY CHECK (Tier-2) ============
    elif page == "✅ Accuracy Check":
        ops_topbar("Accuracy check — official vs model vs blend")
        st.caption(
            "Compares **official history mean** (≤2023), **model raw**, and **blended prediction**. "
            "Blend should usually be closer to official history for sticky rates (e.g. murder rate)."
        )

        tgt_opts = {
            "Murder rate": "murder_homicide_murder_rate",
            "Rape rate": "women_crimes_rape_r",
            "Murder incidence": "murder_homicide_murder_incidence",
            "Rape incidents": "women_crimes_rape_sec_376_i",
        }
        pick = st.multiselect(
            "Targets",
            list(tgt_opts.keys()),
            default=["Murder rate", "Rape rate"],
            key="acc_targets",
        )
        max_n = st.slider("Max districts", 10, 50, 25, key="acc_max")
        if st.button("Build accuracy table", type="primary", key="acc_build"):
            with st.spinner("Running predictions for sample districts…"):
                acc = build_accuracy_table(
                    ml_data,
                    targets=[tgt_opts[p] for p in pick if p in tgt_opts],
                    max_areas=max_n,
                )
            if acc.empty:
                st.warning("No accuracy rows. Train models first: `python train_model.py`")
            else:
                st.session_state["accuracy_table"] = acc

        acc = st.session_state.get("accuracy_table")
        if acc is not None and not acc.empty:
            st.dataframe(acc, use_container_width=True, hide_index=True)
            # Summary
            if "blend_better" in acc.columns and acc["blend_better"].notna().any():
                better = int(acc["blend_better"].fillna(False).sum())
                total = int(acc["blend_better"].notna().sum())
                st.success(
                    f"Blend closer to official history on **{better}/{total}** rows "
                    f"({100 * better / total:.0f}%)."
                )
            # Spotlight Thoothukudi vs Madurai
            spot = acc[acc["district"].isin(["Thoothukudi", "Madurai", "Madurai City"])]
            if not spot.empty:
                st.markdown("#### Spotlight: Thoothukudi vs Madurai")
                st.dataframe(spot, use_container_width=True, hide_index=True)
            csv_bytes = acc.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download accuracy CSV",
                data=csv_bytes,
                file_name="crimecast_accuracy_check.csv",
                mime="text/csv",
            )
        else:
            st.info("Click **Build accuracy table** to compare official vs model vs blend.")

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
        - Demo path: `docs/DEMO_SCRIPT.md`
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

    # ============ GEOGRAPHIC — TN MAP + DISTRICT COMPARE ============
    elif page == "🗺️ Geographic":
        from tn_map import plot_tn_choropleth, HEAT_WHITE_BLUE

        ops_topbar("Geographic Intelligence — TN map · district compare · 2026 detail")
        st.caption(
            "White → blue heat scale. Pick a **district** for full details + 2026 prediction. "
            "Compare two districts on the map metrics."
        )

        map_source = st.radio(
            "Map data source",
            ["2026 rape forecasts", "ML-ready (latest year)", "Media news volume"],
            horizontal=True,
            key="geo_map_source",
        )

        map_df = pd.DataFrame()
        value_col = ""
        name_col = "district"

        if map_source == "2026 rape forecasts" and not rape_2026_df.empty:
            map_df = rape_2026_df.copy()
            value_col = (
                "predicted_2026_rape_incidents"
                if "predicted_2026_rape_incidents" in map_df.columns
                else (
                    "rape_risk_index"
                    if "rape_risk_index" in map_df.columns
                    else map_df.select_dtypes(include=[np.number]).columns[-1]
                )
            )
            name_col = "district" if "district" in map_df.columns else "district_city"
        elif map_source == "Media news volume" and not news_df.empty:
            map_df = (
                news_df.sort_values("year").groupby("district_city").tail(1)
                if "year" in news_df.columns
                else news_df
            )
            value_col = "news_count" if "news_count" in map_df.columns else "negative_news_share"
            name_col = "district_city"
        elif not ml_data.empty:
            map_df = (
                ml_data.sort_values("year").groupby("district_city").tail(1)
                if "year" in ml_data.columns
                else ml_data
            )
            name_col = "district_city"
            candidates = [
                c
                for c in map_df.columns
                if any(k in c.lower() for k in ("rape", "murder", "complaint", "risk"))
                and np.issubdtype(map_df[c].dtype, np.number)
            ]
            value_col = st.selectbox(
                "Metric to colour the map",
                candidates or map_df.select_dtypes(include=[np.number]).columns.tolist()[:12],
                key="geo_metric_pick",
            )
        else:
            st.warning("No data for map. Run pipeline (option 1) and optionally option 7 for 2026.")

        # District list for individual selection
        district_opts: list[str] = []
        if not map_df.empty and name_col in map_df.columns:
            district_opts = sorted(map_df[name_col].dropna().astype(str).unique().tolist())
        elif not rape_2026_df.empty:
            nc = "district" if "district" in rape_2026_df.columns else "district_city"
            district_opts = sorted(rape_2026_df[nc].dropna().astype(str).unique().tolist())
        elif not ml_data.empty and "district_city" in ml_data.columns:
            district_opts = sorted(ml_data["district_city"].dropna().astype(str).unique().tolist())
        if not district_opts:
            district_opts = ["Chennai", "Madurai", "Thoothukudi", "Coimbatore"]

        st.markdown("### District-by-district")
        d1, d2, d3 = st.columns([2, 2, 1])
        with d1:
            default_ix = district_opts.index("Chennai") if "Chennai" in district_opts else 0
            pick_dist = st.selectbox(
                "Focus district",
                district_opts,
                index=default_ix,
                key="geo_focus_district",
            )
        with d2:
            compare_opts = [d for d in district_opts if d != pick_dist]
            pick_cmp = st.selectbox(
                "Compare with",
                compare_opts or district_opts,
                key="geo_compare_district",
            )
        with d3:
            st.write("")
            show_2026 = st.checkbox("2026 detail", value=True, key="geo_show_2026")

        if not map_df.empty and value_col:
            st.caption(f"Map metric: **{value_col}** · scale white (low) → blue (high)")
            left, right = st.columns([1.35, 1], gap="medium")
            with left:
                with st.spinner("Building Tamil Nadu district map..."):
                    fig_map = plot_tn_choropleth(
                        map_df,
                        value_col=value_col,
                        name_col=name_col,
                        title=f"TN districts · {value_col}",
                        color_scale=HEAT_WHITE_BLUE,
                        colorbar_title="Value",
                    )
                if fig_map is not None:
                    st.plotly_chart(fig_map, use_container_width=True, key="tn_choropleth")
                else:
                    st.warning("GeoJSON unavailable — ranking bars.")
                    fig = px.bar(
                        map_df.sort_values(value_col, ascending=True).tail(25),
                        x=value_col,
                        y=name_col,
                        orientation="h",
                        color=value_col,
                        color_continuous_scale=HEAT_WHITE_BLUE,
                        template="plotly_dark",
                        title="District ranking (map fallback)",
                    )
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#0e0e12",
                        height=520,
                    )
                    st.plotly_chart(fig, use_container_width=True, key="geo_fallback_bar")

            with right:
                lcol = "risk_level" if "risk_level" in map_df.columns else None
                render_district_heat(map_df, value_col, name_col, lcol, top_n=18)

            # --- Individual district detail ---
            st.markdown(f"### Focus · **{pick_dist}**")
            focus_row = map_df[map_df[name_col].astype(str) == pick_dist]
            cmp_row = map_df[map_df[name_col].astype(str) == pick_cmp]

            mcols = st.columns(4)
            if not focus_row.empty and value_col in focus_row.columns:
                try:
                    fv = float(pd.to_numeric(focus_row[value_col], errors="coerce").iloc[0])
                except Exception:
                    fv = None
                with mcols[0]:
                    st.metric(f"{pick_dist} · map metric", f"{fv:.2f}" if fv is not None else "—")
            if not cmp_row.empty and value_col in cmp_row.columns:
                try:
                    cv = float(pd.to_numeric(cmp_row[value_col], errors="coerce").iloc[0])
                except Exception:
                    cv = None
                with mcols[1]:
                    st.metric(f"{pick_cmp} · map metric", f"{cv:.2f}" if cv is not None else "—")

            # ML history for focus
            if not ml_data.empty and "district_city" in ml_data.columns:
                hist = ml_data[
                    ml_data["district_city"].astype(str).str.casefold()
                    == pick_dist.casefold()
                ].copy()
                if hist.empty:
                    hist = ml_data[
                        ml_data["district_city"].astype(str).str.contains(
                            pick_dist, case=False, na=False
                        )
                    ].copy()
                if not hist.empty and "year" in hist.columns:
                    rate_cols = [
                        c
                        for c in (
                            "murder_homicide_murder_rate",
                            "women_crimes_rape_r",
                            "complaints_total_complaints",
                        )
                        if c in hist.columns
                    ]
                    if rate_cols:
                        long = []
                        for _, r in hist.iterrows():
                            for c in rate_cols:
                                if pd.notna(r.get(c)):
                                    long.append({
                                        "year": int(r["year"]) if pd.notna(r["year"]) else None,
                                        "metric": c,
                                        "value": float(r[c]),
                                    })
                        if long:
                            fig_h = px.line(
                                pd.DataFrame(long),
                                x="year",
                                y="value",
                                color="metric",
                                markers=True,
                                title=f"{pick_dist} · official/ML trend",
                                template="plotly_dark",
                            )
                            fig_h.update_layout(
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="#0e0e12",
                                height=320,
                            )
                            st.plotly_chart(fig_h, use_container_width=True, key="geo_focus_hist")

            # 2026 prediction detail for selected district
            if show_2026 and not rape_2026_df.empty:
                st.markdown(f"#### 2026 prediction · **{pick_dist}**")
                rnc = "district" if "district" in rape_2026_df.columns else "district_city"
                r26 = rape_2026_df[
                    rape_2026_df[rnc].astype(str).str.casefold() == pick_dist.casefold()
                ]
                if r26.empty:
                    r26 = rape_2026_df[
                        rape_2026_df[rnc].astype(str).str.contains(
                            pick_dist, case=False, na=False
                        )
                    ]
                if not r26.empty:
                    row = r26.iloc[0]
                    c26 = st.columns(5)
                    pairs = [
                        ("Predicted 2026", "predicted_2026_rape_incidents"),
                        ("Low", "pred_low"),
                        ("High", "pred_high"),
                        ("Risk index", "rape_risk_index"),
                        ("Risk level", "risk_level"),
                    ]
                    for i, (lab, col) in enumerate(pairs):
                        with c26[i]:
                            v = row.get(col, "—")
                            if isinstance(v, (int, float, np.floating)) and pd.notna(v):
                                st.metric(lab, f"{float(v):.2f}" if abs(float(v)) < 1000 else f"{float(v):.0f}")
                            else:
                                st.metric(lab, str(v) if pd.notna(v) else "—")
                    st.dataframe(r26, use_container_width=True, hide_index=True)

                    # Side map: only 2026 values for context (full map already above)
                    r26_cmp = rape_2026_df[
                        rape_2026_df[rnc].astype(str).isin([pick_dist, pick_cmp])
                    ]
                    if not r26_cmp.empty and "predicted_2026_rape_incidents" in r26_cmp.columns:
                        fig_cmp = px.bar(
                            r26_cmp,
                            x=rnc,
                            y="predicted_2026_rape_incidents",
                            color=rnc,
                            title=f"2026 forecast · {pick_dist} vs {pick_cmp}",
                            template="plotly_dark",
                            color_discrete_sequence=["#0ea5e9", "#a855f7"],
                        )
                        fig_cmp.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="#0e0e12",
                            height=300,
                            showlegend=False,
                        )
                        st.plotly_chart(fig_cmp, use_container_width=True, key="geo_2026_cmp")
                else:
                    st.info(f"No 2026 forecast row for **{pick_dist}**. Run option 7 / Forecasts tab.")

            # Side-by-side table
            if not focus_row.empty or not cmp_row.empty:
                st.markdown("#### Side-by-side snapshot")
                snap_parts = []
                if not focus_row.empty:
                    t = focus_row.copy()
                    t.insert(0, "role", pick_dist)
                    snap_parts.append(t)
                if not cmp_row.empty:
                    t = cmp_row.copy()
                    t.insert(0, "role", pick_cmp)
                    snap_parts.append(t)
                if snap_parts:
                    st.dataframe(
                        pd.concat(snap_parts, ignore_index=True),
                        use_container_width=True,
                        hide_index=True,
                    )

    # ============ HEAT MAP (matrix) ============
    elif page == "🔥 Heat Map":
        from tn_map import plot_district_heatmap_matrix, plot_tn_choropleth

        ops_topbar("Heat Map — districts × metrics")
        st.caption(
            "Matrix heatmap (z-scored) + TN map. Colour scale **white (low) → blue (high)**."
        )

        source = st.radio("Source", ["ML-ready data", "2026 forecasts"], horizontal=True)
        if source == "2026 forecasts" and not rape_2026_df.empty:
            hm_df = rape_2026_df.copy()
            name_c = "district" if "district" in hm_df.columns else "district_city"
        elif not ml_data.empty:
            hm_df = ml_data.copy()
            name_c = "district_city"
        else:
            hm_df = pd.DataFrame()
            name_c = "district_city"

        if hm_df.empty:
            st.warning("No data. Run `python app.py` option 1 (and option 7 for 2026).")
        else:
            num_opts = [
                c for c in hm_df.select_dtypes(include=[np.number]).columns
                if c not in ("year", "year_centered", "is_latest_year", "rank", "Sl No", "sl_no")
            ]
            # Prefer crime-ish columns first
            preferred = [c for c in num_opts if any(k in c.lower() for k in ("rape", "murder", "complaint", "risk", "news", "sentiment"))]
            default_sel = preferred[:5] if preferred else num_opts[:5]
            selected_metrics = st.multiselect(
                "Metrics in heatmap",
                options=num_opts,
                default=default_sel,
            )
            if selected_metrics:
                fig_hm = plot_district_heatmap_matrix(
                    hm_df,
                    value_cols=selected_metrics,
                    name_col=name_c,
                    title="District × metric heat map (z-score)",
                    top_n=28,
                )
                if fig_hm:
                    st.plotly_chart(fig_hm, use_container_width=True, key="matrix_heatmap")

                # Also show map for first selected metric
                st.markdown("### Map view (first selected metric) · white → blue")
                fig_m = plot_tn_choropleth(
                    hm_df.sort_values("year").groupby(name_c).tail(1) if "year" in hm_df.columns else hm_df,
                    value_col=selected_metrics[0],
                    name_col=name_c,
                    title=f"TN map — {selected_metrics[0]}",
                )
                if fig_m:
                    st.plotly_chart(fig_m, use_container_width=True, key="heatmap_map")
                else:
                    st.info("TN map GeoJSON not available offline yet — matrix heatmap above still works.")
            else:
                st.info("Select at least one metric.")

    # ============ MAKE PREDICTION ============
    elif page == "🔮 Predict":
        hero(
            "🔮 Crime Rate Prediction",
            "Select district, target, and year. Risk blends volume + sentiment + media buzz.",
            badges=[{"text": "Live model", "cls": "dist"}, {"text": "Risk index", "cls": "neg"}],
        )

        predict_many, TARGET_ALIASES, TARGET_CONFIGS, resolve_target = get_predict_functions()

        # Inputs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            areas = sorted(ml_data["district_city"].unique().tolist()) if not ml_data.empty else ["Chennai"]
            area = st.selectbox("District / City", areas, index=areas.index("Chennai") if "Chennai" in areas else 0)
        
        with col2:
            target_options = list(TARGET_CONFIGS.keys())
            target_label_map = {k: v["label"] for k, v in TARGET_CONFIGS.items()}
            selected_target_label = st.selectbox(
                "Target (what to predict)", 
                list(target_label_map.values()),
                index=0
            )
            # Reverse map
            target = [k for k, v in target_label_map.items() if v == selected_target_label][0]
        
        with col3:
            year = st.number_input("Year (use 2026+ for forecasts)", min_value=2022, max_value=2030, value=2026, step=1)

        if st.button("🚀 Predict", type="primary"):
            with st.spinner("Running prediction..."):
                try:
                    preds = predict_many(
                        area=area,
                        targets=[target],
                        year=year
                    )
                    
                    if not preds.empty:
                        row = preds.iloc[0]
                        
                        st.success("Prediction Complete")
                        
                        # Main metrics
                        m1, m2, m3 = st.columns(3)
                        with m1:
                            st.metric("Predicted Value", f"{row['prediction']:.2f}")
                        with m2:
                            risk = row.get("risk_index", None)
                            risk_label = row.get("risk_label", "N/A")
                            if risk is not None:
                                st.metric("Risk Index", f"{risk:.3f}", delta=risk_label)
                            else:
                                st.metric("Risk Index", "N/A")
                        with m3:
                            st.metric("Model Used", row.get("model_name", "Unknown"))

                        if "model_raw" in row.index or "history_baseline" in row.index:
                            b1, b2 = st.columns(2)
                            with b1:
                                st.caption(f"Model raw: {row.get('model_raw', '—')}")
                            with b2:
                                st.caption(f"History blend: {row.get('history_baseline', '—')}")
                        
                        # Full results table
                        st.subheader("Detailed Result")
                        display_cols = [c for c in preds.columns if c in [
                            "area", "year", "target_label", "prediction", "model_raw",
                            "history_baseline", "risk_index", "risk_label", "model_name",
                            "news_negative_share_used", "news_count_used",
                        ]]
                        st.dataframe(preds[display_cols], use_container_width=True)

                        # Tier-1: explain drivers
                        st.markdown("### Why this prediction?")
                        pred_dict = row.to_dict()
                        for line in explain_prediction_drivers(
                            area, target, ml_data, news_df, harvest_df, pred_dict
                        ):
                            st.markdown(f"- {line}")
                        
                        # Explanation
                        st.markdown("### Interpretation")
                        st.write(f"**Area**: {area} | **Target**: {selected_target_label} | **Year**: {year}")
                        if risk is not None:
                            if risk > 0.7:
                                st.error("HIGH RISK - Consider enhanced prevention measures")
                            elif risk > 0.4:
                                st.warning("MEDIUM RISK - Standard protocols recommended")
                            else:
                                st.success("LOW RISK - Maintain existing systems")

                        # News / media signal contribution (hybrid data)
                        news_neg = row.get("news_negative_share_used") or row.get("negative_news_share")
                        news_cnt = row.get("news_count_used") or row.get("news_count")
                        if news_neg is not None or news_cnt is not None:
                            st.markdown("#### Media / News Signals Contribution")
                            cols = st.columns(3)
                            with cols[0]:
                                st.metric("News Neg. Share", f"{float(news_neg):.2f}" if news_neg is not None else "N/A")
                            with cols[1]:
                                st.metric("News Mentions (sample)", int(news_cnt) if news_cnt is not None else "N/A")
                            with cols[2]:
                                st.caption("News volume + negativity blended into Risk Index (proxy when official records are limited).")
                        
                    else:
                        st.error("No prediction returned. Check if the area exists in the data.")
                except Exception as e:
                    st.error(f"Prediction failed: {str(e)}")
                    st.info("Tip: Run the full pipeline first using the CLI (python app.py → option 1) if models are missing.")

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
            "on the TN map (white = lower concern → blue = higher). Scores cached in **SQLite**."
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

        # Metrics strip
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
                top = dist_sent.iloc[0]
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

            if not scored_hl.empty:
                st.markdown("### Scored headlines sample")
                show_hl = scored_hl.copy()
                if "polarity" in show_hl.columns:
                    show_hl = show_hl.sort_values("polarity", ascending=True)
                st.dataframe(show_hl.head(25), use_container_width=True, hide_index=True)
        else:
            st.warning(
                "No scored news yet. Click **🔄** to refresh media, then **Score news → map**."
            )

        st.divider()
        st.markdown("### Single-text analyser")
        _, score_text_fn = get_sentiment_functions()
        text_input = st.text_area(
            "Paste a headline or complaint",
            height=100,
            placeholder="Example: Residents are terrified after the recent increase in robberies…",
            key="sent_single_text",
        )
        if st.button("Analyze text", key="sent_analyze_one"):
            if text_input.strip():
                with st.spinner("Analyzing…"):
                    try:
                        result = score_text_fn(text_input)
                        c1, c2, c3 = st.columns(3)
                        lab = str(result.get("sentiment_label", "unknown")).upper()
                        with c1:
                            if lab == "NEGATIVE":
                                st.error(f"**{lab}**")
                            elif lab == "POSITIVE":
                                st.success(f"**{lab}**")
                            else:
                                st.info(f"**{lab}**")
                        with c2:
                            st.metric("Polarity", f"{result.get('polarity', 0):.3f}")
                        with c3:
                            st.metric("Confidence", f"{result.get('confidence', 0):.3f}")
                        st.caption(
                            f"Intensity {result.get('crime_intensity', 0)} · "
                            f"{result.get('crime_types', 'none')} · "
                            f"{result.get('sentiment_method', '')}"
                        )
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
            else:
                st.warning("Enter some text.")

        # DB status
        try:
            from db import db_status

            st.caption(f"Database: `{db_status()}`")
        except Exception:
            pass

    # ============ 2026 FORECASTS ============
    elif page == "📅 2026 Forecasts":
        hero(
            "📅 2026 Rape Crime Forecasts",
            "District-level Section 376 IPC forecasts with risk blending.",
            badges=[{"text": "All TN districts", "cls": ""}, {"text": "Media proxy", "cls": "green"}],
        )

        if st.button("Generate / Refresh 2026 Forecasts", type="primary"):
            with st.spinner("Running 2026 prediction (trend engine, no sklearn)..."):
                preds = None
                err_msg = None
                try:
                    predict_2026, generate_report = get_2026_functions()
                    if predict_2026:
                        preds = predict_2026()
                        if generate_report is not None:
                            try:
                                generate_report(preds)
                            except Exception:
                                pass
                    else:
                        err_msg = "Could not import predict_2026_rape_all_districts"
                except Exception as e:
                    err_msg = str(e)

                # Always coerce to DataFrame
                if preds is not None and not isinstance(preds, pd.DataFrame):
                    try:
                        preds = pd.DataFrame(preds)
                    except Exception:
                        preds = None

                # Fallback: existing CSV (already generated successfully)
                if preds is None or getattr(preds, "empty", True):
                    csv_path = Path("model_outputs") / "rape_predictions_2026_all_districts.csv"
                    if csv_path.exists():
                        preds = pd.read_csv(csv_path)
                        st.warning(
                            "Live recompute had an issue; showing saved forecasts. "
                            f"({err_msg})" if err_msg else "Showing saved forecasts."
                        )
                    else:
                        st.error(
                            f"Could not generate forecasts. {err_msg or ''}\n"
                            "Run: python predict_2026_rape_all_districts.py  in the CRIMECAST folder."
                        )
                        preds = None

                if preds is not None and not preds.empty:
                    st.success(f"Forecasts ready for {len(preds)} districts/areas")
                    st.subheader("Top 10 High-Risk Districts")
                    show = preds.copy()
                    if "rape_risk_index" in show.columns:
                        show = show.sort_values("rape_risk_index", ascending=False)
                    elif "predicted_2026_rape_incidents" in show.columns:
                        show = show.sort_values("predicted_2026_rape_incidents", ascending=False)
                    cols = [c for c in [
                        "rank", "district", "predicted_2026_rape_incidents",
                        "rape_risk_index", "risk_level", "method",
                    ] if c in show.columns]
                    st.dataframe(show[cols].head(10) if cols else show.head(10), use_container_width=True)
                    st.subheader("All Districts")
                    st.dataframe(preds, use_container_width=True)
                    st.download_button(
                        "Download CSV",
                        preds.to_csv(index=False),
                        "rape_2026_predictions.csv",
                        "text/csv",
                    )
                    # refresh in-memory cache for rest of page
                    rape_2026_df = preds

        # Show existing if available
        if not rape_2026_df.empty:
            st.subheader("Latest Available 2026 Predictions")
            show_cols = [c for c in [
                "rank", "district", "pred_low", "predicted_2026_rape_incidents", "pred_high",
                "uncertainty_width", "rape_risk_index", "risk_level", "confidence", "method",
            ] if c in rape_2026_df.columns]
            st.dataframe(
                rape_2026_df[show_cols] if show_cols else rape_2026_df,
                use_container_width=True,
                hide_index=True,
            )
            st.caption(
                f"{len(rape_2026_df)} areas · model_outputs/rape_predictions_2026_all_districts.csv"
            )

            # Tier-3 uncertainty bands chart
            if {"pred_low", "predicted_2026_rape_incidents", "pred_high", "district"}.issubset(
                set(rape_2026_df.columns)
            ):
                st.markdown("#### Uncertainty bands (low · mid · high)")
                top = rape_2026_df.sort_values(
                    "predicted_2026_rape_incidents", ascending=False
                ).head(15).copy()
                # error bars relative to mid
                top["err_minus"] = top["predicted_2026_rape_incidents"] - top["pred_low"]
                top["err_plus"] = top["pred_high"] - top["predicted_2026_rape_incidents"]
                fig_u = go.Figure()
                fig_u.add_trace(
                    go.Bar(
                        name="2026 mid",
                        x=top["district"],
                        y=top["predicted_2026_rape_incidents"],
                        error_y=dict(
                            type="data",
                            symmetric=False,
                            array=top["err_plus"],
                            arrayminus=top["err_minus"],
                            color="#fbbf24",
                        ),
                        marker_color="#ef4444",
                    )
                )
                fig_u.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#0e0e12",
                    height=400,
                    title="Top 15 districts · forecast with uncertainty",
                    xaxis_tickangle=-35,
                    yaxis_title="Incidents",
                    showlegend=False,
                )
                st.plotly_chart(fig_u, use_container_width=True, key="rape2026_uncertainty")
                st.caption(
                    "Band from trend residual RMSE × horizon (and ≥15% of mid). "
                    "Wider band = less stable history."
                )
            else:
                st.info(
                    "Re-run **Generate / Refresh 2026 Forecasts** to compute pred_low / pred_high uncertainty columns."
                )

            if not news_df.empty:
                st.caption("Note: Live news heat is separate (Live Feed). This page is the 2026 rape trend model.")

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

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"Media rows: {n_media} signals · {n_harvest} harvest headlines"
    )
    st.sidebar.caption("CLI: `python app.py --news` · `streamlit run dashboard.py`")



if __name__ == "__main__":
    main()