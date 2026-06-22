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

# Custom CSS for better colors and modern look
def apply_custom_theme():
    st.markdown("""
    <style>
    /* Main app background - clean white */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Sidebar - very light gray */
    [data-testid="stSidebar"] {
        background-color: #f1f5f9;
    }
    
    /* Sidebar text - dark */
    .stSidebar .stMarkdown, .stSidebar label, .stSidebar .stRadio label {
        color: #0f172a !important;
    }
    
    /* Primary buttons - red accent (crime/alert theme) */
    .stButton > button {
        background-color: #ef4444;
        color: white;
        border: none;
        font-weight: 600;
        border-radius: 6px;
    }
    .stButton > button:hover {
        background-color: #dc2626;
        color: white;
    }
    
    /* Metric cards - light with subtle border */
    [data-testid="stMetric"] {
        background-color: #f8fafc;
        padding: 12px 16px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    [data-testid="stMetric"] label {
        color: #64748b !important;
    }
    
    /* Headers - dark text */
    h1, h2, h3 {
        color: #0f172a !important;
    }
    
    /* Success / Error / Warning / Info boxes */
    .stAlert {
        border-radius: 8px;
        border-left: 5px solid #ef4444;
    }
    
    /* Dataframe */
    .stDataFrame {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }
    
    /* Radio / Select boxes */
    .stRadio > div, .stSelectbox > div {
        background-color: #f8fafc;
        padding: 6px;
        border-radius: 6px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #ef4444;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent
ML_READY_FILE = PROJECT_ROOT / "dataset" / "cleaned" / "crimecast_ml_ready.csv"
OUTPUT_DIR = PROJECT_ROOT / "model_outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
MODELS_DIR = PROJECT_ROOT / "models"
SENTIMENT_SCORES = OUTPUT_DIR / "sentiment_scores.csv"
CRIME_PREDICTIONS = OUTPUT_DIR / "crime_predictions.csv"
RAPE_2026 = OUTPUT_DIR / "rape_predictions_2026_all_districts.csv"

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
        from predict_2026_rape_all_districts import predict_2026_rape_all_districts, generate_rape_report
        return predict_2026_rape_all_districts, generate_rape_report
    except:
        return None, None

def main():
    st.set_page_config(
        page_title="CRIMECAST Dashboard",
        page_icon="🚨",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom dark + red theme
    apply_custom_theme()
    
    # Sidebar Navigation
    st.sidebar.title("🚨 CRIMECAST")
    st.sidebar.markdown("Crime Rate Prediction + Sentiment Dashboard")

    page = st.sidebar.radio(
        "Navigate",
        ["🏠 Overview", "🔮 Make Prediction", "💬 Sentiment Analysis", 
         "📅 2026 Forecasts", "📊 Visualizations", "📈 Data Explorer"]
    )

    # Load data
    ml_data = load_ml_data()
    sentiment_df = load_sentiment_scores()
    crime_preds = load_crime_predictions()
    rape_2026_df = load_rape_2026()

    # ============ OVERVIEW ============
    if page == "🏠 Overview":
        st.title("CRIMECAST Dashboard")
        st.markdown("""
        **Interactive web interface** for crime rate prediction and public sentiment analysis in Tamil Nadu.
        
        This dashboard brings together:
        - Machine learning models for crime counts and **rates**
        - DistilBERT-powered sentiment analysis
        - Blended **Risk Index** (crime volume + negative sentiment)
        - 2026 district-level forecasts
        """)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("ML Models Available", len([f for f in MODELS_DIR.glob("*.joblib") if "sentiment" not in f.name]))
        with col2:
            st.metric("Sentiment Records", len(sentiment_df) if not sentiment_df.empty else 0)
        with col3:
            st.metric("2026 Districts Forecasted", len(rape_2026_df) if not rape_2026_df.empty else 0)

        st.markdown("### Quick Start")
        st.info("Use the sidebar to navigate between sections. Start with **Make Prediction** or **Sentiment Analysis**.")

        st.markdown("### Project Highlights")
        st.markdown("""
        - **Temporal validation** for realistic forecasting
        - **Sentiment fusion** into ML features
        - Risk-aware predictions (HIGH / MEDIUM / LOW)
        - Full support for rate targets (not just raw counts)
        """)

    # ============ MAKE PREDICTION ============
    elif page == "🔮 Make Prediction":
        st.title("🔮 Crime Rate Prediction")
        st.markdown("Select parameters to get a prediction + Risk Index")

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
                        display_cols = [c for c in preds.columns if c in ["area", "year", "target_label", "prediction", "risk_index", "risk_label", "model_name"]]
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
                        
                    else:
                        st.error("No prediction returned. Check if the area exists in the data.")
                except Exception as e:
                    st.error(f"Prediction failed: {str(e)}")
                    st.info("Tip: Run the full pipeline first using the CLI (python app.py → option 1) if models are missing.")

    # ============ SENTIMENT ANALYSIS ============
    elif page == "💬 Sentiment Analysis":
        st.title("💬 Sentiment Analysis")
        st.markdown("Analyze public sentiment on crime-related text using DistilBERT")

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
        st.title("📅 2026 Rape Crime Forecasts")
        st.markdown("District-level predictions for 2026 (Section 376 IPC)")

        if st.button("Generate / Refresh 2026 Forecasts", type="primary"):
            with st.spinner("Running 2026 prediction..."):
                try:
                    predict_2026, generate_report = get_2026_functions()
                    if predict_2026:
                        preds = predict_2026()
                        st.success(f"Generated forecasts for {len(preds)} districts")
                        
                        # Show top risks
                        st.subheader("Top 10 High-Risk Districts")
                        if "rape_risk_index" in preds.columns:
                            st.dataframe(preds.sort_values("rape_risk_index", ascending=False).head(10)[
                                ["rank", "district", "predicted_2026_rape_incidents", "rape_risk_index", "risk_level"]
                            ], use_container_width=True)
                        else:
                            st.dataframe(preds.head(10), use_container_width=True)
                        
                        # Full table
                        st.subheader("All Districts")
                        st.dataframe(preds, use_container_width=True)
                        
                        # Download
                        csv = preds.to_csv(index=False)
                        st.download_button("Download CSV", csv, "rape_2026_predictions.csv")
                        
                    else:
                        st.error("2026 prediction modules not available")
                except Exception as e:
                    st.error(f"Failed: {e}")

        # Show existing if available
        if not rape_2026_df.empty:
            st.subheader("Latest Available 2026 Predictions")
            st.dataframe(rape_2026_df, use_container_width=True)

    # ============ VISUALIZATIONS ============
    elif page == "📊 Visualizations":
        st.title("📊 Key Visualizations")
        
        st.markdown("Select a chart to display (from existing generated figures)")

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
        st.title("📈 Data Explorer")
        
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
    st.sidebar.markdown("**CRIMECAST** | Run CLI version with `python app.py` for full pipeline control.")
    st.sidebar.markdown("Made with ❤️ for crime analytics research")


if __name__ == "__main__":
    main()