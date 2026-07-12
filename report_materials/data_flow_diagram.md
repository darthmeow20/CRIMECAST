# CRIMECAST - Data Flow Diagram

```mermaid
flowchart LR
    subgraph Inputs
        R1[Raw TN Crime CSVs<br/>2022/2023<br/>complaints, women_crimes, murder]
        R2[Sentiment Text Template<br/>or Auto-Generated Text]
    end

    subgraph Processing
        C1[Ingest + Clean<br/>clean_data.py]
        S1[DistilBERT Sentiment Scoring<br/>+ Crime Lexicon Intensity<br/>sentiment_analysis.py]
        S2[Aggregate per District-Year<br/>polarity, negative_share, intensity]
    end

    subgraph ML_Prep_Train
        F1[Add Time/Pop Features +<br/>Enrich with Sentiment<br/>(fillna 0)]
        DB1[(crimecast_ml_ready.csv)]
        T1[Train Models<br/>Temporal Validation<br/>train_model.py]
        DB3[(best_models.json<br/>.joblib Models)]
    end

    subgraph User_Interface
        D1[Web Dashboard<br/>streamlit run dashboard.py<br/>(primary)]
        D2[CLI / Full Pipeline]
    end

    subgraph Prediction_Risk
        P1[Predictions + Risk Index<br/>predict.py<br/>(volume + neg. sentiment)]
        P2[2026 All-Districts Forecasts]
    end

    subgraph Outputs
        V1[Interactive Charts + Tables<br/>Plotly + Matplotlib]
        R1[CSVs + Reports<br/>predictions, 2026, sentiment, training]
    end

    R1 --> C1
    R2 --> S1
    S1 --> S2
    C1 --> F1
    S2 --> F1
    F1 --> DB1

    DB1 --> T1
    T1 --> DB3

    DB1 --> P1
    DB3 --> P1
    DB1 --> P2
    DB3 --> P2
    S2 --> P1   %% live risk enrichment

    DB1 --> D1
    DB3 --> D1
    S2 --> D1

    D1 --> V1
    D1 --> R1
    P1 --> D1
    P2 --> D1
    V1 --> R1

    style Inputs fill:#e3f2fd
    style Processing fill:#e8f5e9
    style ML_Prep_Train fill:#fefce8
    style User_Interface fill:#fef3c7
    style Prediction_Risk fill:#fce7f3
    style Outputs fill:#f3e5f5
```

## Data Flow Explanation
1. **Raw Inputs**: TN district crime CSVs (2022-2023) + text for sentiment (or auto-synthetic).
2. **Cleaning + Features**: Standardize, merge views, add year_centered / is_latest_year / population / ratios.
3. **Sentiment Path (parallel)**: DistilBERT primary scoring → per-record scores → district-year aggregates (polarity, negative_share, crime_intensity).
4. **Fusion (in clean)**: Sentiment aggregates merged into ML-ready (sentiment_* cols, fillna 0). This is the key fusion step.
5. **Training**: Temporal (past→latest year) model selection on the fused data. Saves models.
6. **Prediction + Risk**: predict.py loads latest template row (for 2026 override year features), applies model, then blends risk using predicted volume + negative sentiment.
7. **Consumption**: **Dashboard is primary UI**. Loads prebuilt artifacts + can trigger live predict_many() and score_text() without full retrain. CLI drives the full pipeline (sentiment first).
8. **Outputs**: Dashboard interactive + saved CSVs, figures, reports.

**Key Points**:
- Sentiment fusion happens before training (enrich_with_sentiment in clean_data).
- No training from the dashboard (training via app.py option 1 or --full).
- Risk index is computed post-prediction (see predict.compute_risk_index).
- Consistent with DFD Level 0/1 and system_flow_diagram.md.

**How to Render**: Paste Mermaid into mermaid.live or compatible viewer.
