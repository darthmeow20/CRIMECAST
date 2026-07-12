# CRIMECAST - Level 1 DFD

```mermaid
flowchart LR
    %% External Entities
    E1[Crime Data Sources] -->|Raw CSVs| P1((1.0<br/>Ingest &amp; Clean<br/>Crime Data))
    E3[Text Data Sources] -->|Text / Narratives| P2((2.0<br/>Perform Sentiment<br/>Analysis))
    E2[User / Analyst] -->|Prediction Requests<br/>(area, target, year)| P5((5.0<br/>Generate Predictions<br/>&amp; Risk Index))
    E2 -->|View / Explore<br/>Requests| P6((6.0<br/>Serve Dashboard<br/>&amp; Outputs))

    %% Data Stores
    P1 -->|Cleaned Records| D2[(D2: ML-Ready Data<br/>crimecast_ml_ready.csv)]
    P2 -->|Polarity, Intensity,<br/>Labels| D3[(D3: Sentiment Scores<br/>sentiment_scores.csv)]

    %% Fuse step (feature eng + sentiment merge happens inside clean/enrich)
    D2 --> P3((3.0<br/>Fuse Sentiment +<br/>Build ML Dataset))
    D3 --> P3
    P3 -->|Enriched Features<br/>(+ year_centered, sentiment_*)| D2

    %% Training (offline, produces models)
    D2 --> P4((4.0<br/>Train ML Models<br/>(Temporal Validation)))
    P4 -->|Best Models +<br/>Metadata| D4[(D4: Trained Models<br/>.joblib + best_models.json)]

    %% Prediction uses data + models + sentiment
    D2 --> P5
    D3 --> P5
    D4 --> P5
    P5 -->|Predictions, Risk Index<br/>(volume + neg. sentiment)| D5[(D5: Prediction Results<br/>crime_predictions.csv + 2026)]

    %% Output layer (dashboard is interactive front-end)
    D5 --> P6
    D2 --> P6
    D4 --> P6
    P6 -->|Interactive Dashboard<br/>(live predict + sentiment)| E2
    P6 -->|Reports, CSVs,<br/>Visuals, 2026 Forecasts| E2

    style P1 fill:#e0f2fe
    style P2 fill:#e0f2fe
    style P3 fill:#e0f2fe
    style P4 fill:#e0f2fe
    style P5 fill:#e0f2fe
    style P6 fill:#e0f2fe
    style D2 fill:#fefce8
    style D3 fill:#fefce8
    style D4 fill:#fefce8
    style D5 fill:#fefce8
    style E1 fill:#fef3c7
    style E2 fill:#fef3c7
    style E3 fill:#fef3c7
```

## Level 1 Processes

| Process | Description |
|---------|-------------|
| **1.0 Ingest & Clean Crime Data** | Load raw TN crime CSVs (complaints, women crimes, murder), normalize columns, drop totals/aggregates, classify areas, output cleaned yearly files. |
| **2.0 Perform Sentiment Analysis** | Score unstructured text (template or live) with DistilBERT (primary) + crime lexicon. Compute polarity, confidence, sentiment_label, crime_intensity, keywords per record. |
| **3.0 Fuse Sentiment + Build ML Dataset** | Merge cleaned crime tables, add time features (year_centered, is_latest_year), population signals, ratios. Left-merge aggregated sentiment features (sentiment_*). Fillna(0) for missing signals. Produces `crimecast_ml_ready.csv`. |
| **4.0 Train ML Models (Temporal Validation)** | Load ML-ready data. Split temporally (older year train, latest test). Try RF/GB/Ridge (log target). Prune high-correlation features. Select best by temporal MAE. Persist .joblib pipelines + best_models.json. |
| **5.0 Generate Predictions & Risk Index** | For user-specified area/year (incl. 2026 future using latest row as template + year override): load model, predict, enrich with risk_index = f(volume, negative_sentiment). Supports all targets + rates. |
| **6.0 Serve Dashboard & Produce Outputs** | Streamlit dashboard (primary UI) for live predict, on-demand DistilBERT scoring, 2026 batch view, explorer, pre-generated charts. Also writes CSVs, figures, and reports. |

## Data Stores

- **D2**: Cleaned & Fused ML-Ready Data (`dataset/cleaned/crimecast_ml_ready.csv`)
- **D3**: Sentiment Scores (`model_outputs/sentiment_scores.csv`)
- **D4**: Trained Models (`models/*.joblib` + `model_outputs/best_models.json`)
- **D5**: Prediction Results (`model_outputs/crime_predictions.csv`, `rape_predictions_2026_*.csv`, risk scores)

## Balancing Note

External flows exactly match Level 0:
- In: Raw Crime CSVs (E1), Unstructured Text (E3)
- Out: Predictions + Risk, Sentiment Results, 2026 + Reports, Interactive Dashboard (all to E2 User)
All Level-1 stores and sub-flows are internal. P6 represents both the runtime dashboard interface and batch output generation. Full pipeline (app.py) orchestrates 1-4 offline. Dashboard can invoke 2 and 5 on-demand.
