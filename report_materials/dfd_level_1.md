# CRIMECAST - Level 1 DFD

```mermaid
flowchart TB
    subgraph External_Entities
        E1[Crime Data Sources]
        E2[User / Analyst]
        E3[Text Data Sources]
    end

    subgraph Processes
        P1[1.0\nClean &amp; Prepare Data]
        P2[2.0\nPerform Sentiment Analysis]
        P3[3.0\nEngineer Features &amp; Fuse Data]
        P4[4.0\nTrain ML Models]
        P5[5.0\nGenerate Predictions &amp; Risk Index]
        P6[6.0\nProduce Outputs &amp; Dashboard]
    end

    subgraph Data_Stores
        D1[(D1: Raw Crime Data)]
        D2[(D2: Cleaned ML Data)]
        D3[(D3: Sentiment Scores)]
        D4[(D4: Trained Models)]
        D5[(D5: Prediction Results)]
    end

    E1 -->|Raw CSVs| P1
    E3 -->|Text Data| P2
    E2 -->|Prediction Requests / Parameters| P5
    E2 -->|View Dashboard / Reports| P6

    P1 -->|Cleaned Data| D2
    P2 -->|Sentiment Scores| D3

    D2 --> P3
    D3 --> P3
    P3 -->|Fused Feature Data| D2

    D2 --> P4
    P4 -->|Trained Models| D4

    D2 --> P5
    D4 --> P5
    D3 --> P5
    P5 -->|Predictions + Risk Index| D5

    D5 --> P6
    P6 -->|Reports, CSVs, Visuals| E2
    P6 -->|Interactive Dashboard| E2

    style P1 fill:#e0f2fe
    style P2 fill:#e0f2fe
    style P3 fill:#e0f2fe
    style P4 fill:#e0f2fe
    style P5 fill:#e0f2fe
    style P6 fill:#e0f2fe
    style D1 fill:#fefce8
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
| **1.0 Clean & Prepare Data** | Ingest raw CSVs, standardize columns, remove aggregate rows, convert types, add year/area_type. |
| **2.0 Perform Sentiment Analysis** | Score text using DistilBERT (primary) + rule-based fallback. Extract polarity, confidence, crime intensity and keywords. |
| **3.0 Engineer Features & Fuse Data** | Add time-based features (year_centered, is_latest_year) and merge sentiment aggregates into numeric data. |
| **4.0 Train ML Models** | Train multiple models with temporal validation (past year → latest year). Save best models for each target (including rates). |
| **5.0 Generate Predictions & Risk Index** | Use latest data + trained models to predict for selected area/year. Calculate blended Risk Index (prediction volume + negative sentiment). |
| **6.0 Produce Outputs & Dashboard** | Generate CSVs, reports, visualizations. Power the Streamlit interactive dashboard for user interaction. |

## Data Stores

- **D1**: Raw Crime Data (original source files)
- **D2**: Cleaned & Engineered Data (`crimecast_ml_ready.csv`)
- **D3**: Sentiment Scores (`sentiment_scores.csv`)
- **D4**: Trained Models (`.joblib` + metadata)
- **D5**: Prediction Results (including 2026 forecasts and risk scores)

## Balancing Note
All external flows from Level 0 (Raw Crime Data, Text Data, Predictions/Risk, etc.) are preserved and decomposed in Level 1. The User now explicitly sends requests to trigger predictions and dashboard views.
