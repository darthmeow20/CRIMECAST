# CRIMECAST - System Flow Diagram

```mermaid
flowchart TB
    subgraph User_Interface
        direction TB
        A1[Primary: Web Dashboard<br/>streamlit run dashboard.py<br/>(Light theme)]
        A2[CLI / Full Pipeline<br/>python app.py or main.py]
    end

    subgraph Data_Ingestion
        B[Raw Crime CSVs<br/>dataset/ tn-2022/2023 *.csv]
    end

    subgraph Sentiment_Module
        E[Sentiment Text<br/>(template or synthetic)]
        F[Sentiment Analysis<br/>sentiment_analysis.py<br/>DistilBERT (primary) + Lexicon]
        G[Sentiment Scores<br/>polarity, intensity, labels<br/>sentiment_scores.csv]
    end

    subgraph Core_Pipeline
        C[Clean + Enrich<br/>clean_data.py<br/>(+ add_ml_features + enrich_with_sentiment)]
        D[ML-Ready Dataset<br/>crimecast_ml_ready.csv]
        H[Train Models<br/>train_model.py<br/>Temporal holdout + prune + log targets]
        J[Trained Models<br/>models/*.joblib<br/>+ best_models.json]
    end

    subgraph Prediction_Engine
        K[Predict + Risk<br/>predict.py<br/>(resolve_area handles 2026 template)]
        L[Compute Risk Index<br/>(pred volume + neg. sentiment)]
        M[2026 Batch Forecasts<br/>predict_2026_rape_all_districts.py]
    end

    subgraph Outputs
        N[Visualizations<br/>figures/*.png (plotly+mpl)]
        O[CSVs + Reports<br/>predictions, 2026, training_report]
        V[Interactive Views<br/>in Dashboard]
    end

    %% Full pipeline (offline / CLI)
    A2 --> B
    B --> C
    E --> F
    F --> G
    G --> C
    C --> D
    D --> H
    H --> J

    %% Live + batch paths (Dashboard primary)
    A1 -->|Live predict / 2026| K
    A1 -->|Live score text| F
    J --> K
    D --> K
    G --> K
    K --> L
    L --> V
    L --> O

    M --> O
    M --> V
    M --> N

    J --> V
    D --> V

    %% Output routing
    V --> N
    O --> V

    style A1 fill:#e0f2fe,stroke:#0369a1,stroke-width:2px
    style A2 fill:#e0f2fe
    style J fill:#c8e6c9
    style L fill:#fef3c7
    style G fill:#fefce8
    style D fill:#fefce8
    style N fill:#f3e8ff
    style O fill:#f3e8ff
    style V fill:#e0f2fe
```

## Description
- **Primary Entry Point**: **Web Dashboard** (`streamlit run dashboard.py`) — interactive light-theme UI for live predictions, sentiment scoring, 2026 forecasts, explorer.
- **Alternative / Batch**: **CLI** (`python app.py`) for full pipeline (recommended before first use) and scripted runs.
- **Pipeline Order (full run)**: Sentiment (DistilBERT) → Clean + Enrich (fuse sentiment + time feats) → Train (temporal) → Visuals.
- **Live Paths (Dashboard)**: Directly invokes predict_many() and score_text() without retraining.
- **Risk**: Blended after prediction using predicted volume + negative sentiment polarity/intensity.
- **Outputs**: Interactive dashboard views + persistent CSVs, figures, reports.

**Key Points**:
- Dashboard is the recommended user interface (no training from UI; training is via full pipeline).
- Sentiment (DistilBERT primary) is always computed before fusion in pipeline; live scoring available independently.
- All diagrams are consistent with DFD L0/L1 and actual module responsibilities (see app.py run_full_pipeline, dashboard main, predict, clean_data enrich_with_sentiment).

**How to Render**: Copy the Mermaid code into https://mermaid.live , VS Code Mermaid extension, or export as image for your report.
