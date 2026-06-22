# CRIMECAST Web Dashboard

A modern, interactive web interface built with Streamlit.

## How to Run

```bash
# 1. Install dependencies (includes streamlit)
pip install -r requirements.txt

# 2. Launch the dashboard
streamlit run dashboard.py
```

The dashboard will open in your browser (usually at http://localhost:8501).

## Features

- **Overview**: Project summary and quick metrics
- **Make Prediction**: Interactive crime rate + risk index predictions
  - Choose any district/city
  - Select target (including new rate targets)
  - Specify future year (e.g. 2026)
  - See Risk Index (HIGH/MEDIUM/LOW)
- **Sentiment Analysis**: Real-time text analysis with DistilBERT
  - Paste any crime-related text
  - Get polarity, confidence, crime intensity
- **2026 Forecasts**: Generate and explore district-level 2026 predictions
- **Visualizations**: View key charts from the project
- **Data Explorer**: Browse ML-ready data and sentiment scores with interactive plots

## Requirements

- All existing project dependencies + `streamlit` and `plotly`
- Pre-trained models and outputs in `model_outputs/` (run `python main.py` or `python app.py` option 1 first for best experience)

## Notes

- The dashboard reuses the same backend functions as the CLI (`predict.py`, `sentiment_analysis.py`, etc.).
- If models or data files are missing, it will guide you.
- Best experienced after running the full pipeline at least once.

This is the recommended way for end-users to interact with CRIMECAST.
