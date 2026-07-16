# CRIMECAST - Level 0 DFD (Context Diagram)

```mermaid
---
id: 215f56fd-26ea-4185-b3a4-9d909f43c044
---
flowchart LR
    E1[Crime Data Sources<br/>Raw CSVs - TN Police / NCRB] -->|Raw Crime Data| P0((0<br/>CRIMECAST System))
    E3[Text Data Sources<br/>Complaints, News, Social Media] -->|Unstructured Text Data| P0

    P0 -->|Crime Predictions<br/>+ Risk Index| E2[User / Analyst]
    P0 -->|Sentiment Scores<br/>&amp; Analysis| E2
    P0 -->|2026 Forecasts<br/>&amp; Reports| E2
    P0 -->|Interactive Dashboard<br/>(Streamlit)| E2

    style P0 fill:#e0f2fe,stroke:#0369a1,stroke-width:3px
    style E1 fill:#fef3c7
    style E2 fill:#fef3c7
    style E3 fill:#fef3c7
```

## Description

**Process 0: CRIMECAST System**
- The entire system represented as one single process.
- Receives raw crime data (CSVs) and unstructured text data.
- Produces predictions (counts + rates), blended risk indices (volume + sentiment), 2026 forecasts, reports/CSVs, visualizations, and the interactive Streamlit dashboard.

**External Entities:**
- **Crime Data Sources**: Tamil Nadu Police / NCRB raw data (2022-2023 district files).
- **User / Analyst**: End user interacting via CLI or primarily the web dashboard for predictions and analysis.
- **Text Data Sources**: Complaints, news, social posts, or auto-generated text for sentiment analysis.

**Rules Applied:**
- Only **one process** (numbered 0).
- No data stores shown at Level 0.
- All inputs and outputs must balance with Level 1 (same external flows decomposed).
- This diagram defines the scope of the system.
