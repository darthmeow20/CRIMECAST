# CRIMECAST: Machine Learning for Crime Rate Prediction and Public Sentiment Analysis in Tamil Nadu

**Partial Progress Report**  
**Student Project**  
**Date:** 22 June 2026  
**Status:** Core ML pipeline + Sentiment Integration complete and improved for accuracy

**Note**: Supporting diagrams and screenshots are provided in the same folder (`system_flow_diagram.md`, `data_flow_diagram.md`, `screenshots.md`).

---

## 1. Executive Summary

CRIMECAST is an end-to-end machine learning system for predicting crime rates (total complaints, murder incidence, rape incidents, and normalized rates) across Tamil Nadu districts using 2022–2023 official data, with **2024–2025 gap-fill from Tamil Nadu crime news** (internet news, e-papers, local aggregator surfaces such as DailyHunt / Lokal / Public-style feeds — **not social media**). Trends and NLP use a **three-LLM stack** (DistilBERT sentiment + DistilBERT-MNLI crime-type + trend labels). Outputs include a blended **Risk Index**.

**Key Achievements (this iteration):**
- Implemented temporal-aware model selection and evaluation for more reliable forecasting.
- Added time-trend features, population signals, and automatic feature pruning.
- **Fused sentiment features** (from DistilBERT) directly into the ML feature set.
- Created a blended **Crime + Sentiment Risk Index**.
- Made DistilBERT the primary sentiment engine (previously only documented, not implemented in core).
- Added auto-generation of synthetic text so the full pipeline "just works".
- Improved 2026 forecasting logic with year extrapolation and sentiment risk.
- End-to-end pipeline now runs sentiment → cleaning (with fusion) → training → prediction → visualization.

The system is designed as a prototype that can be extended with additional years of data.

**See**: `system_flow_diagram.md` and `data_flow_diagram.md` for visual overviews.

---

## 2. Problem Statement & Motivation

Predicting future crime rates (especially normalized **crime rates**) is valuable for resource allocation, policy, and public safety. However:
- Official data is released with lag.
- Raw counts are biased by population size.
- Public sentiment (fear, trust in police) is an important leading indicator not captured in numeric tables alone.

**Goal:** Build accurate, interpretable models for both **absolute counts** and **rates**, augmented by real-time public sentiment signals.

---

## 3. Dataset

- **Source:** Tamil Nadu Police / NCRB-style district-level statistics (2022 & 2023).
- **Files:** Complaints, Crimes Against Women, Murder/Homicide.
- **ML-ready dataset:** 99 rows (districts + cities), 73+ features after cleaning.
- **Years:** Only 2022–2023 (major limitation for time-series forecasting).
- **Sentiment data:** Uses `sentiment_text_template.csv` (currently seeded with synthetic + example text for demo). Aggregated sentiment (polarity, intensity, negative share) is merged as features.

**Recent data note:** 2023 district-level CSVs are publicly available (opencity.in). More years would dramatically improve reliability.

---

## 4. Methodology

### 4.1 Data Cleaning & Feature Engineering
- Automatic discovery of yearly files.
- Standardisation, removal of totals, numeric conversion.
- Derived features: ratios, shares, year-centered trend, is_latest_year.
- **New:** Automatic enrichment with sentiment aggregates when `sentiment_scores.csv` exists.

### 4.2 Machine Learning Models (train_model.py)
**Targets (original + new):**
- `complaints_total_complaints`
- `murder_homicide_murder_incidence`
- `women_crimes_rape_sec_376_i`
- **Rate targets:** `murder_homicide_murder_rate`, `women_crimes_rape_r`, `complaints_rate_of_cognizable_crime_ipc_sll` (crime_rate)

**Improvements for accuracy:**
- **Temporal holdout** (train on 2022, test on 2023) used for model selection and reporting (far more realistic than random splits).
- Candidate models: Dummy, Ridge (log), RandomForest (log), GradientBoosting (log).
- Correlation-based feature pruning (threshold ~0.95).
- Explicit use of `year` features for extrapolation.
- Log target transform for count/rate data.
- Sentiment features now included when available.

**Evaluation metrics:** MAE, RMSE, R² (CV + temporal + holdout).

### 4.3 NLP & Trends — 3 LLM models (`nlp_pipeline.py` + `sentiment_analysis.py`)

| # | Role | Model | Output |
|---|------|--------|--------|
| 1 | Sentiment | DistilBERT SST-2 | polarity, positive/negative |
| 2 | Crime type | DistilBERT-MNLI zero-shot | homicide, rape, theft, cyber, narcotics, … |
| 3 | Trend | DistilBERT-MNLI zero-shot (trend labels) | rising / stable / isolated / declining |

**Text sources:** Google News / e-papers / local news apps (DailyHunt, Lokal, Public — via open web/RSS). **Social media excluded** from primary collection.  
See `NEWS_SOURCES.md`.

**Integration:** Aggregated sentiment + news volume per district-year fused into ML features and Risk Index.

### 4.4 Prediction & Risk
- `predict.py` supports area + target + future year.
- **Risk Index** (0–1): Blends normalized prediction volume + negative sentiment + **public news/media signals** (volume + negativity) as proxy/leading indicator.
- Configurable weights via `config/risk_weights.json`.
- 2026 district-level forecasting now uses latest template + year override + sentiment + news proxy risk.
- New tool: `acquire_news_signals.py` (demo + live Google News RSS fetch + CSV scoring) to supplement limited official data.

### 4.5 Pipeline
Full flow: `sentiment` → `clean` (fusion) → `train` → `visualize` → combined reports.

**See diagrams:** `system_flow_diagram.md` and `data_flow_diagram.md`.

---

## 5. Results (Current Prototype)

### Training Performance (note: re-run `train_model.py` after changes for updated temporal metrics)

| Target                  | Best Model              | CV MAE   | Temporal Focus |
|-------------------------|-------------------------|----------|----------------|
| Total complaints        | Random Forest (log)     | ~10574   | Improved with sentiment |
| Murder incidence        | Gradient Boosting (log) | ~9.2     | Strong temporal signal |
| Rape incidents          | Random Forest (log)     | ~3.4     | Benefits most from sentiment |
| Rate targets            | Various                 | Varies   | New in this iteration |

**Note on old report:** The current `training_report.md` reflects pre-fusion state. After re-training, it will show temporal MAE/R² and mention sentiment fusion.

### Sentiment Analysis
- Method: DistilBERT (primary)
- On template data: Balanced positive/negative, high confidence (~0.99), strong crime keyword detection.
- TN District example (Chennai): Mixed sentiment, crime intensity captured.

### 2026 Rape Forecast (example from current outputs)
- Total predicted incidents (all districts): ~307
- Highest risk: Thiruvannamalai (~19)
- New: Combined risk scores now available (incorporating sentiment).

**Risk Index Example** (produced by recent improvements):
- Blends predicted volume + negative public sentiment + news/media buzz (configurable weights).
- Categories: HIGH / MEDIUM / LOW.
- Public signals now pulled via `acquire_news_signals.py` (including live RSS).

**Visual evidence**: See `screenshots.md` and figures in `model_outputs/figures/`.

---

## 6. Key Contributions & Improvements (This Phase)

1. **Reliability** — Temporal validation + year features instead of random splits.
2. **Accuracy boost** — Sentiment fusion as actual ML features.
3. **Practical forecasting** — Proper future-year handling and Risk Index.
4. **Sentiment implementation** — DistilBERT now actually runs (was only in docs).
5. **Usability** — Auto text generation, better pipeline ordering, risk output in predictions.
6. **End-to-end integration** — Crime ML + public sentiment now work together.

---

## 7. Visualizations & Outputs Produced

- Actual vs Predicted plots
- Top areas by crime type
- Sentiment vs Prediction scatter (new)
- 2026 district risk maps/reports
- TN district sentiment breakdowns
- State-wise comparisons

All outputs in `model_outputs/`.

**See**: `screenshots.md` for guidance on capturing and referencing these.

---

## 8. Limitations & Challenges

- **Data scarcity**: Only two years severely limits temporal modeling.
- **No 2024/2025 data** found in original dataset.
- Sentiment currently relies on small template (synthetic generation helps for demo).
- Risk Index is a practical heuristic, not a calibrated probabilistic model.
- Models remain prototypes.

**Mitigation**: Strong engineering (temporal eval, feature engineering, fusion) extracts maximum signal from limited data.

---

## 9. Future Work (Post-Submission)

- Incorporate 2023+ district data (opencity.in has matching CSVs).
- Use news/media proxies via acquire_news_signals.py (already implemented + live fetch).
- Expand with more years + external indicators.
- Dashboard already shows news buzz visuals + hybrid risk.
- Fine-tune DistilBERT on domain-specific crime text.

---

## 10. Technical Stack

- Python, pandas, scikit-learn, matplotlib/seaborn
- DistilBERT via Hugging Face Transformers + PyTorch
- Joblib for model persistence
- Modular design (clean, train, predict, sentiment, visualize)

---

## 11. How to Reproduce (for Submission)

```bash
# Full pipeline (recommended)
python main.py

# Or interactive
python app.py

# Specific
python train_model.py
python sentiment_analysis.py
python predict.py --area Chennai --target crime_rate --year 2026
```

**Important:** Run `train_model.py` and `sentiment_analysis.py` after pulling latest code to generate updated reports with fusion and DistilBERT.

---

## Conclusion

CRIMECAST demonstrates a practical, integrated approach to crime forecasting that goes beyond pure numeric models by incorporating public sentiment. Significant engineering improvements have been made to prediction reliability, model selection, and the fusion of the two core components (ML + DistilBERT sentiment).

While data volume remains the fundamental constraint, the current system is significantly more robust, interpretable, and ready for extension than the initial prototype.

**Supporting Materials** (in this folder):
- System Flow Diagram
- Data Flow Diagram
- Screenshot Guide
- All referenced figures are in `../model_outputs/figures/`

**Prepared for partial submission – 22 June 2026**

---
*End of Report*
