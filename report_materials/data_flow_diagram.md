# CRIMECAST - Data Flow Diagram

```mermaid
flowchart LR
    subgraph Inputs
        R1[Raw TN Crime CSVs<br/>2022/2023<br/>complaints, women_crimes, murder]
        R2[Sentiment Text Template<br/>or Auto-Generated Text]
    end

    subgraph Processing
        C1[Cleaning & Normalization<br/>clean_data.py]
        C2[ML Feature Engineering<br/>year_centered, population, ratios]
        S1[DistilBERT Sentiment Scoring<br/>+ Crime Lexicon Intensity]
        S2[Aggregate Sentiment per District-Year<br/>polarity, negative_share, intensity]
    end

    subgraph Fusion & Storage
        M1[Merge Sentiment into ML Data<br/>Optional Features]
        DB1[(crimecast_ml_ready.csv)]
        DB2[(sentiment_scores.csv)]
        DB3[(best_models.json + .joblib Models)]
    end

    subgraph User_Interface
        D1[Web Dashboard<br/>streamlit run dashboard.py]
        D2[CLI / Reports]
    end

    subgraph Outputs
        P1[Predictions + Risk Index<br/>crime_predictions.csv]
        P2[2026 Forecasts<br/>rape_predictions_2026_all_districts.csv]
        V1[Interactive Charts<br/>Plotly + Matplotlib]
        R1[Reports & CSVs]
    end

    R1 --> C1
    R2 --> S1
    C1 --> C2
    C2 --> M1
    S1 --> S2
    S2 --> M1

    M1 --> DB1
    S2 --> DB2
    C2 --> DB3

    DB1 --> D1
    DB2 --> D1
    DB3 --> D1

    DB1 --> P1
    DB1 --> P2
    DB2 --> P1
    DB2 --> P2
    DB3 --> P1
    DB3 --> P2

    D1 --> V1
    D1 --> R1
    P1 --> D1
    P2 --> D1

    style Inputs fill:#e3f2fd
    style Processing fill:#e8f5e9
    style Fusion_Storage fill:#fff3e0
    style User_Interface fill:#fef3c7
    style Outputs fill:#f3e5f5
```

## Data Flow Explanation
1. **Raw Inputs**: Three categories of TN crime statistics + optional free-text for sentiment.
2. **Cleaning**: Standardize names, handle missing values, add derived columns (year, area_type).
3. **Sentiment Path**: Text → DistilBERT (or fallback) → polarity, confidence, crime_intensity, keywords.
4. **Fusion**: Sentiment aggregates are joined to the numeric ML table as predictive features.
5. **Model Storage**: Trained pipelines saved with feature metadata.
6. **Main Consumption**: The **Web Dashboard** now acts as the primary interface, pulling from DB1, DB2, and DB3 to deliver live predictions, sentiment scoring, and 2026 forecasts.
7. **Outputs**: Interactive visualizations (via dashboard), CSVs, and generated reports.

**Key Innovation**: Sentiment is actively fused into ML features. The dashboard provides the main interactive layer for end users.

**How to Render**: Paste Mermaid into mermaid.live or compatible viewer.
