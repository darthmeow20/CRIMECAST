# CRIMECAST - System Flow Diagram

```mermaid
flowchart TB
    subgraph User_Interface
        direction TB
        A1[Web Dashboard<br/>streamlit run dashboard.py]
        A2[CLI Menu<br/>python app.py]
    end

    subgraph Data_Pipeline
        B[Raw CSVs<br/>dataset/*.csv]
        C[Data Cleaning<br/>clean_data.py<br/>+ Sentiment Enrichment]
        D[ML-Ready Dataset<br/>crimecast_ml_ready.csv]
    end

    subgraph Sentiment_Module
        E[Sentiment Text Template<br/>or Auto-Generated Text]
        F[Sentiment Analysis<br/>sentiment_analysis.py<br/>DistilBERT Primary + Lexicon Fallback]
        G[Sentiment Scores<br/>+ Crime Intensity]
    end

    subgraph ML_Core
        H[Feature Engineering<br/>Time + Sentiment Features]
        I[Model Training<br/>train_model.py<br/>Temporal Validation + Risk Fusion]
        J[Trained Models<br/>.joblib + best_models.json]
    end

    subgraph Prediction_Engine
        K[Prediction Module<br/>predict.py<br/>+ 2026 Rape Predictor]
        L[Risk Index Calculation<br/>Crime Volume + Negative Sentiment]
        M[Batch Forecasts<br/>All Districts 2026]
    end

    subgraph Output_Layer
        N[Visualizations<br/>matplotlib / Plotly]
        O[Reports & CSVs<br/>crime_predictions.csv<br/>sentiment_scores.csv<br/>2026 reports]
    end

    A1 -->|Interactive UI| K
    A1 -->|Interactive UI| F
    A1 -->|Interactive UI| I
    A2 --> B

    B --> C
    C --> D
    D --> H

    E --> F
    F --> G
    G --> H
    G --> L

    H --> I
    I --> J
    J --> K

    K --> L
    L --> M
    M --> N
    M --> O
    M --> A1

    style A1 fill:#e0f2fe
    style A2 fill:#e0f2fe
    style J fill:#c8e6c9
    style L fill:#fef3c7
    style N fill:#f3e8ff
    style O fill:#f3e8ff
```

## Description
- **Primary Entry Point**: **Web Dashboard** (`dashboard.py`) — modern interactive interface (light theme).
- **Alternative**: **CLI Menu** (`app.py`) for script-based or full pipeline usage.
- **Core Flow**: Raw data → Cleaning + Sentiment Enrichment → ML Training with Risk Fusion.
- **Prediction Engine**: Generates predictions + blended Risk Index (prediction volume + negative sentiment).
- **Outputs**: Interactive views in dashboard, plus CSVs, reports and visualizations.

**Key Points**:
- The Streamlit dashboard is the main way users interact with the system.
- Sentiment analysis (DistilBERT) feeds into both standalone scoring and ML feature engineering.
- All diagrams maintain consistency with Level 0/1 DFDs.

**How to Render**: Copy the Mermaid code into https://mermaid.live , VS Code Mermaid extension, or export as image for your report.
