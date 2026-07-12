"""
CRIMECAST Interactive Dashboard
Run with: streamlit run dashboard.py
"""

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
    """Red (hot) → green (cool) like the reference DISTRICT HEAT panel."""
    if total <= 1:
        return "#dc2626"
    t = rank / max(total - 1, 1)
    # 0 = red, 1 = green
    r = int(220 - t * 160)
    g = int(38 + t * 140)
    b = int(38 + t * 20)
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
    if MEDIA_HARVEST.exists():
        return pd.read_csv(MEDIA_HARVEST)
    # fallback: news signals raw
    raw = OUTPUT_DIR / "news_signals_raw.csv"
    if raw.exists():
        return pd.read_csv(raw)
    return pd.DataFrame()


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
        import importlib
        import sys

        for mod_name in ("rape_2026_engine", "predict_2026_rape_all_districts"):
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

    # Load data
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

    # ============ LIVE FEED (Overview) ============
    if page == "🔴 Live Feed":
        ops_topbar("CRIMECAST — Tamil Nadu Live Intelligence")

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("EVENTS / MODELS", n_models, delta=None)
        with m2:
            st.metric("SENTIMENT ROWS", n_sent)
        with m3:
            st.metric("MEDIA SIGNALS", n_media or n_harvest)
        with m4:
            st.metric("2026 DISTRICTS", n_2026)
        with m5:
            open_alerts = 0
            if not rape_2026_df.empty and "risk_level" in rape_2026_df.columns:
                open_alerts = int((rape_2026_df["risk_level"].astype(str).str.upper() == "HIGH").sum())
            elif not rape_2026_df.empty and "rape_risk_index" in rape_2026_df.columns:
                open_alerts = int((rape_2026_df["rape_risk_index"] >= 0.65).sum())
            st.metric("OPEN ALERTS", open_alerts)

        from tn_map import plot_tn_choropleth

        # Prepare map data (prefer 2026 forecasts → news → ML rape/intensity)
        live_map_df = pd.DataFrame()
        live_vcol = ""
        live_ncol = "district"
        if not rape_2026_df.empty:
            live_map_df = rape_2026_df
            live_vcol = (
                "predicted_2026_rape_incidents"
                if "predicted_2026_rape_incidents" in rape_2026_df.columns
                else ("rape_risk_index" if "rape_risk_index" in rape_2026_df.columns else "")
            )
            if not live_vcol:
                nums = rape_2026_df.select_dtypes(include=[np.number]).columns.tolist()
                live_vcol = nums[0] if nums else ""
            live_ncol = "district" if "district" in rape_2026_df.columns else "district_city"
        elif not news_df.empty and "news_count" in news_df.columns:
            live_map_df = news_df.sort_values("year").groupby("district_city").tail(1) if "year" in news_df.columns else news_df
            live_vcol = "news_count"
            live_ncol = "district_city"
        elif not ml_data.empty:
            live_map_df = ml_data.sort_values("year").groupby("district_city").tail(1) if "year" in ml_data.columns else ml_data
            live_ncol = "district_city"
            ycols = [c for c in live_map_df.columns if "rape" in c.lower() and np.issubdtype(live_map_df[c].dtype, np.number)]
            if not ycols:
                ycols = [c for c in live_map_df.select_dtypes(include=[np.number]).columns if c != "year"]
            live_vcol = ycols[0] if ycols else ""

        left, right = st.columns([1.05, 1.15], gap="medium")

        with left:
            st.markdown(
                '<div class="panel"><div class="panel-title">● Live intelligence feed</div>',
                unsafe_allow_html=True,
            )
            feed = harvest_df if not harvest_df.empty else sentiment_df
            if not feed.empty:
                for _, r in feed.head(10).iterrows():
                    headline = str(r.get("headline") or r.get("text") or r.get("source_text") or "—")
                    source = str(r.get("source") or r.get("sentiment_method") or "News media")
                    label = str(r.get("sentiment_label") or r.get("label") or "Neutral").title()
                    district = str(r.get("district") or r.get("district_city") or "")
                    url = str(r.get("url") or "")
                    crime = str(r.get("crime_types") or r.get("crime_theme") or r.get("crime_type") or "Crime")
                    if isinstance(crime, str) and len(crime) > 24:
                        crime = crime[:24] + "…"
                    render_feed_card(source, headline[:220], label=label, crime=crime, district=district, url=url)
            else:
                st.info(
                    "No live media harvest yet. Run:\n\n"
                    "`python acquire_news_signals.py --populate-2024-2025`"
                )
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            # Tamil Nadu map (choropleth heat) — main live view like reference UI
            st.markdown(
                '<div class="panel"><div class="panel-title">Tamil Nadu — live hotspots map</div>',
                unsafe_allow_html=True,
            )
            if not live_map_df.empty and live_vcol:
                with st.spinner("Loading TN map..."):
                    fig_live = plot_tn_choropleth(
                        live_map_df,
                        value_col=live_vcol,
                        name_col=live_ncol,
                        title=f"District heat · {live_vcol}",
                    )
                if fig_live is not None:
                    fig_live.update_layout(height=420, margin=dict(l=0, r=0, t=48, b=0))
                    st.plotly_chart(fig_live, use_container_width=True, key="live_tn_map")
                    st.caption(
                        "All districts shown. Null/zero official values filled from news & media volume proxies."
                    )
                else:
                    st.caption("Map GeoJSON loading… showing ranking. Needs network once to cache assets/tamil_nadu_districts.geojson")
                    fig_fb = px.bar(
                        live_map_df.sort_values(live_vcol, ascending=True).tail(15),
                        x=live_vcol,
                        y=live_ncol,
                        orientation="h",
                        color=live_vcol,
                        color_continuous_scale=["#166534", "#eab308", "#dc2626"],
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
                st.info("No map data yet. Run pipeline (option 1) and option 7 for 2026 forecasts.")
            st.markdown("</div>", unsafe_allow_html=True)

            # District heat ranking under the map
            if not live_map_df.empty and live_vcol:
                lcol = "risk_level" if "risk_level" in live_map_df.columns else None
                render_district_heat(live_map_df, live_vcol, live_ncol, lcol, top_n=12)

        st.markdown(
            f"""
            <div class="ticker">
                <span class="live">● LIVE WIRE</span>
                &nbsp; Models {n_models} · Sentiment {n_sent} · Media {n_media or n_harvest}
                · 2026 districts {n_2026} · HIGH alerts {open_alerts}
                · Source: DistilBERT + news/X proxies + ML
            </div>
            """,
            unsafe_allow_html=True,
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
        - **Temporal validation** — train past years → test latest
        - **Sentiment + news fusion** into ML features
        - **Risk Index** = prediction volume + negative sentiment + media buzz
        - **2024–2025 gap-fill** via Google News RSS + X discussion volume
        - **2026 district forecasts** (rape / women crimes target)
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
                color_continuous_scale="Reds",
            )
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#121218", font_color="#d1d5db")
            st.plotly_chart(fig, use_container_width=True, key="analytics_news")

    # ============ GEOGRAPHIC — TN MAP ============
    elif page == "🗺️ Geographic":
        from tn_map import plot_tn_choropleth, plot_district_heatmap_matrix

        ops_topbar("Geographic Intelligence — Tamil Nadu Map")
        st.caption("District choropleth heat map (green = low → red = high). Data from 2026 forecasts or ML-ready crime features.")

        # Choose dataset + metric
        map_source = st.radio(
            "Data source",
            ["2026 rape forecasts", "ML-ready (latest year)", "Media news volume"],
            horizontal=True,
        )

        map_df = pd.DataFrame()
        value_col = ""
        name_col = "district"

        if map_source == "2026 rape forecasts" and not rape_2026_df.empty:
            map_df = rape_2026_df.copy()
            value_col = "predicted_2026_rape_incidents" if "predicted_2026_rape_incidents" in map_df.columns else (
                "rape_risk_index" if "rape_risk_index" in map_df.columns else map_df.select_dtypes(include=[np.number]).columns[-1]
            )
            name_col = "district" if "district" in map_df.columns else "district_city"
        elif map_source == "Media news volume" and not news_df.empty:
            map_df = news_df.sort_values("year").groupby("district_city").tail(1) if "year" in news_df.columns else news_df
            value_col = "news_count" if "news_count" in map_df.columns else "negative_news_share"
            name_col = "district_city"
        elif not ml_data.empty:
            map_df = ml_data.sort_values("year").groupby("district_city").tail(1) if "year" in ml_data.columns else ml_data
            name_col = "district_city"
            candidates = [c for c in map_df.columns if any(k in c.lower() for k in ("rape", "murder", "complaint", "risk")) and np.issubdtype(map_df[c].dtype, np.number)]
            value_col = st.selectbox(
                "Metric to colour the map",
                candidates or map_df.select_dtypes(include=[np.number]).columns.tolist()[:12],
            )
        else:
            st.warning("No data for map. Run full pipeline (option 1) and optionally option 7 for 2026 forecasts.")

        if not map_df.empty and value_col:
            if map_source != "ML-ready (latest year)":
                # only one metric — no selectbox above for 2026/media
                pass
            if map_source == "2026 rape forecasts" or map_source == "Media news volume":
                st.caption(f"Colour scale metric: **{value_col}**")

            left, right = st.columns([1.35, 1], gap="medium")
            with left:
                with st.spinner("Building Tamil Nadu district map..."):
                    fig_map = plot_tn_choropleth(
                        map_df,
                        value_col=value_col,
                        name_col=name_col,
                        title=f"Tamil Nadu district heat — {value_col}",
                    )
                if fig_map is not None:
                    st.plotly_chart(fig_map, use_container_width=True, key="tn_choropleth")
                else:
                    st.warning(
                        "Could not load TN district GeoJSON (network/cache). "
                        "Showing ranking bars instead. GeoJSON caches to `assets/tamil_nadu_districts.geojson` on first success."
                    )
                    fig = px.bar(
                        map_df.sort_values(value_col, ascending=True).tail(25),
                        x=value_col,
                        y=name_col,
                        orientation="h",
                        color=value_col,
                        color_continuous_scale=["#166534", "#eab308", "#dc2626"],
                        template="plotly_dark",
                        title="District ranking (map fallback)",
                    )
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0e0e12", height=520)
                    st.plotly_chart(fig, use_container_width=True, key="geo_fallback_bar")

            with right:
                lcol = "risk_level" if "risk_level" in map_df.columns else None
                render_district_heat(map_df, value_col, name_col, lcol, top_n=18)

    # ============ HEAT MAP (matrix) ============
    elif page == "🔥 Heat Map":
        from tn_map import plot_district_heatmap_matrix, plot_tn_choropleth

        ops_topbar("Heat Map — districts × metrics")
        st.caption("Matrix heatmap (z-scored) + optional Tamil Nadu map. Higher (red) = hotter relative intensity.")

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
                st.markdown("### Map view (first selected metric)")
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
                        
                        # Full results table
                        st.subheader("Detailed Result")
                        display_cols = [c for c in preds.columns if c in ["area", "year", "target_label", "prediction", "risk_index", "risk_label", "model_name", "news_negative_share_used", "news_count_used"]]
                        st.dataframe(preds[display_cols], use_container_width=True)
                        
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

    # ============ SENTIMENT ANALYSIS ============
    elif page == "💬 Sentiment":
        hero(
            "💬 Sentiment Analysis",
            "DistilBERT + crime lexicon — score free text or batch template data.",
            badges=[{"text": "DistilBERT", "cls": "dist"}, {"text": "Lexicon fallback", "cls": "pos"}],
        )

        _, score_text = get_sentiment_functions()

        text_input = st.text_area(
            "Enter crime-related text (complaint, news headline, social post...)", 
            height=150,
            placeholder="Example: Residents are terrified after the recent increase in robberies and assaults in the area."
        )

        if st.button("Analyze Sentiment", type="primary"):
            if text_input.strip():
                with st.spinner("Analyzing with DistilBERT..."):
                    try:
                        result = score_text(text_input)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            label = result.get("sentiment_label", "unknown").upper()
                            if label == "NEGATIVE":
                                st.error(f"**{label}**")
                            elif label == "POSITIVE":
                                st.success(f"**{label}**")
                            else:
                                st.info(f"**{label}**")
                        with col2:
                            st.metric("Polarity", f"{result.get('polarity', 0):.3f}")
                        with col3:
                            st.metric("Confidence", f"{result.get('confidence', 0):.3f}")
                        
                        st.subheader("Additional Insights")
                        st.write(f"**Crime Intensity**: {result.get('crime_intensity', 0)}")
                        st.write(f"**Crime Types Detected**: {result.get('crime_types', 'none')}")
                        
                        st.caption("Method: " + result.get("sentiment_method", "unknown"))
                        
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
            else:
                st.warning("Please enter some text.")

        st.divider()
        st.subheader("Batch: Analyze Template Data")
        if st.button("Run on sentiment_text_template.csv"):
            try:
                from sentiment_analysis import analyze_sentiment
                result = analyze_sentiment()
                st.success(f"Analyzed {result.get('rows', 0)} records")
                if SENTIMENT_SCORES.exists():
                    st.dataframe(pd.read_csv(SENTIMENT_SCORES).head(10), use_container_width=True)
            except Exception as e:
                st.error(str(e))

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
                        err_msg = "Could not import rape_2026_engine"
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
                            "Run: python rape_2026_engine.py  in the CRIMECAST folder."
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
            st.dataframe(rape_2026_df, use_container_width=True)
            st.caption(
                f"{len(rape_2026_df)} areas · file: model_outputs/rape_predictions_2026_all_districts.csv"
            )

            if not news_df.empty:
                st.caption("Note: 2026 risk scores in predictions now incorporate recent news/media buzz signals as a proxy.")

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
    st.sidebar.caption("CLI: `python app.py` · Dashboard: `streamlit run dashboard.py`")



if __name__ == "__main__":
    main()