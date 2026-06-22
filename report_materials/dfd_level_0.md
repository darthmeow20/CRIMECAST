# CRIMECAST - Level 0 DFD (Context Diagram)

```mermaid
flowchart LR
    E1[Crime Data Sources<br/>Raw CSVs - TN Police] -->|Raw Crime Data| P0((0<br/>CRIMECAST System))
    E3[Text Data Sources<br/>Complaints, News, Social Media] -->|Unstructured Text Data| P0

    P0 -->|Crime Predictions + Risk Index| E2[User / Analyst]
    P0 -->|Sentiment Analysis Results| E2
    P0 -->|2026 Forecasts & Reports| E2
    P0 -->|Interactive Dashboard| E2

    style P0 fill:#e0f2fe,stroke:#0369a1,stroke-width:3px
    style E1 fill:#fef3c7
    style E2 fill:#fef3c7
    style E3 fill:#fef3c7
```

## Description

**Process 0: CRIMECAST System**
- The entire system represented as one single process.
- Receives raw crime data and text data.
- Produces predictions, risk scores, forecasts, reports, and the interactive dashboard.

**External Entities:**
- **Crime Data Sources**: Tamil Nadu Police / NCRB raw data (2022-2023).
- **User / Analyst**: The person who uses the system for analysis and forecasting.
- **Text Data Sources**: Provider of narrative text (complaints, news, social media) for sentiment analysis.

**Rules Applied:**
- Only **one process** (numbered 0).
- No data stores shown at Level 0.
- All inputs and outputs must balance with Level 1.
- This diagram defines the scope of the system.
