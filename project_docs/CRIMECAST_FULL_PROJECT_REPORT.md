# A PROJECT REPORT ON

# CRIMECAST: Crime Analysis, Prediction and Sentiment Analysis  
# Using Machine Learning for Tamil Nadu Districts

**Submitted by:** [STUDENT NAME]  
**Register No.:** [REGISTER NUMBER]  
**Degree / Department:** [DEGREE] / [DEPARTMENT]  
**Institution:** [COLLEGE / UNIVERSITY]  
**Guide:** [GUIDE NAME]  
**Academic Year:** 2025–2026  

---

# INDEX

| S.NO | CONTENTS | PAGE NO. |
|------|----------|----------|
| 01. | INTRODUCTION | |
| | 1.1 COMPANY / ORGANIZATION PROFILE | |
| | 1.2 PROJECT OVERVIEW | |
| 02. | SYSTEM ANALYSIS | |
| | 2.1 FEASIBILITY STUDY | |
| | 2.2 EXISTING SYSTEM | |
| | 2.3 PROPOSED SYSTEM | |
| 03. | SYSTEM CONFIGURATION | |
| | 3.1 HARDWARE SPECIFICATION | |
| | 3.2 SOFTWARE SPECIFICATION | |
| | 3.3 ABOUT THE SOFTWARE | |
| 04. | SYSTEM DESIGN | |
| | 4.1 NORMALIZATION | |
| | 4.2 TABLE DESIGN | |
| | 4.3 INPUT DESIGN | |
| | 4.4 SFD / DFD | |
| 05. | SYSTEM DESCRIPTION | |
| 06. | TESTING AND IMPLEMENTATION | |
| 07. | CONCLUSION AND FUTURE SCOPE | |
| 08. | FORMS AND REPORT | |
| 09. | BIBLIOGRAPHY | |

*(Structure matches the college INDEX template in `project_docs/` screenshot.)*

---

# CERTIFICATE

This is to certify that the project report entitled **“CRIMECAST: Crime Analysis, Prediction and Sentiment Analysis Using Machine Learning for Tamil Nadu Districts”** submitted by **[STUDENT NAME]** (Register No. **[NUMBER]**) is a bonafide record of work carried out under my supervision. The contents of this report, in full or in parts, have not been submitted to any other Institute or University for the award of any degree or diploma.

**Signature of the Guide** _________________ **Signature of the HOD** _________________  

Place: _______________ Date: _______________

---

# DECLARATION

I hereby declare that the project work entitled **“CRIMECAST…”** submitted to **[College Name]** is a record of original work done by me under the guidance of **[Guide Name]**. I further declare that this work has not been submitted elsewhere for any other degree or diploma.

Signature of the Candidate: _______________  
Name: [STUDENT NAME] Register No.: [NUMBER]

---

# ACKNOWLEDGEMENT

I express my sincere gratitude to my project guide **[Guide Name]** for continuous guidance. I thank the Head of the Department and faculty of **[Department]** for support. I acknowledge open data and public reporting that make academic study of crime statistics possible, and thank my family and friends.

---

# 01. INTRODUCTION

## 1.1 Company / Organization Profile

This project is developed in an **academic** setting as a **decision-support prototype** for district-level crime analysis in Tamil Nadu. The domain is public-safety analytics for students, researchers, and analysts who work with **SCRB/NCRB-style** tables and contemporaneous **news** coverage.

Official crime statistics are often:

- Published with lag  
- Split across tables (complaints, crimes against women, murder/homicide)  
- Inconsistent in headers and district spellings  

Media provides timely signals but is **not** a substitute for FIRs. CRIMECAST integrates both carefully:

- **Official-era numeric labels** train models  
- **News / sentiment** support live monitoring and explanation  

**Disclaimer:** College prototype only — not a live police system, not an official SCRB forecast product, not for automated enforcement.

## 1.2 Project Overview

**CRIMECAST** is an end-to-end **Python + Streamlit** system that:

1. Cleans multi-year Tamil Nadu district crime CSVs  
2. Trains regression models for counts and rates  
3. Scores news sentiment (DistilBERT / lexicon)  
4. Produces **2026 scenario forecasts** with uncertainty  
5. Explains district risk (composite + LIME-style / SHAP-proxy)  
6. Provides maps, scoreboards, district compare, and HTML briefs  

**Targets:** total complaints; murder incidence & rate; rape incidents (Sec. 376) & rate; cognizable crime rate (IPC+SLL).

**Key folders:**

| Path | Role |
|------|------|
| `dataset/cleaned/` | ML-ready tables |
| `models/` | Trained `.joblib` models |
| `model_outputs/` | Metrics, forecasts, figures, news |
| `data/crimecast.db` | SQLite (headlines, alerts, migrated CSVs) |
| `dashboard.py` | Interactive UI |

**Run dashboard:** `START_DASHBOARD.bat` → http://localhost:8501  

---

# 02. SYSTEM ANALYSIS

## 2.1 Feasibility Study

### 2.1.1 Technical feasibility  
Python, pandas, scikit-learn, Streamlit, Plotly, SQLite run on a student laptop. Optional DistilBERT needs more RAM. GeoJSON caches under `assets/`. **Feasible.**

### 2.1.2 Operational feasibility  
Sidebar dashboard + `.bat` helpers (start, kill old Streamlit, migrate CSV, health check). **Feasible for demos.**

### 2.1.3 Economic feasibility  
Open-source stack; no paid API required for core demo. **Low cost.**

### 2.1.4 Schedule feasibility  
Modular pipeline (clean → train → viz → dashboard) supports incremental delivery. **Feasible.**

## 2.2 Existing System

Manual spreadsheets per category/year → slow, error-prone, non-reproducible; no multi-model comparison; news disconnected from stats; no unified TN38 map.

## 2.3 Proposed System

Automated pipeline + Streamlit UI.

**Advantages:** reproducible ML-ready table; official vs media-proxy discipline; temporal validation; history blend for rates; TN38 rollups; explainability; SQLite persistence; district compare with carve maps and per-lakh metrics.

---

# 03. SYSTEM CONFIGURATION

## 3.1 Hardware Specification

| Component | Minimum / Recommended |
|-----------|----------------------|
| Processor | i5 / Ryzen 5+ |
| RAM | 8 GB min; 16 GB if DistilBERT |
| Storage | ~10 GB free |
| Display | 1366×768 min; FHD preferred |
| Network | Optional (GeoJSON once; news refresh) |

## 3.2 Software Specification

| Software | Purpose |
|----------|---------|
| Windows 10/11 | Host OS |
| Python 3.10+ | Runtime |
| pandas, numpy, scikit-learn | Data & ML |
| Streamlit, Plotly | Dashboard & charts |
| joblib | Model files |
| SQLite | Local DB |
| transformers/torch (optional) | DistilBERT |
| wordcloud (optional) | Word clouds |

## 3.3 About the Software

Python for scientific stack; Streamlit for rapid UI; scikit-learn for interpretable tabular models; Plotly for choropleths; SQLite for offline multi-table storage without a server.

---

# 04. SYSTEM DESIGN

## 4.1 Normalization

- Grain: **district × year**  
- Drop aggregate Total rows  
- Canonical **TN38** names (cities → parents; junk dropped)  
- Rates vs counts separated; population estimates for per-lakh  
- DB: operational tables + `ds_*` full frames  

## 4.2 Table Design

**Files:** `crimecast_ml_ready.csv`, `fitted_predictions.csv`, `training_metrics.csv`, `rape_predictions_2026_*.csv`, `media_harvest_*.csv`, `sentiment_scores.csv`

**SQLite:** `meta`, `news_headlines`, `district_sentiment`, `rape_2026`, `alert_log`, `dataset_registry`, `ds_ml_ready`, `ds_media_harvest`, …

## 4.3 Input Design

- Yearly CSVs under `dataset/`  
- Dashboard controls (district, target, year, method, news window)  
- News refresh; optional labeled sentiment text  
- Validation: aliases, TN38, numeric coercion  

## 4.4 SFD / DFD

**Level 0:** Crime sources + text/news → CRIMECAST → User (predictions, sentiment, 2026, dashboard).

**Level 1 processes:** Clean → Features → Train → Predict → News/Sentiment → Forecast → Present/Alert.

*(Insert figures from `reports/diagrams/dfd_level_0.png`, `dfd_level_1.png`, `system_flow_diagram.png`.)*

---

# 05. SYSTEM DESCRIPTION

### 5.1 Cleaning (`clean_data.py`)  
Discover years, standardise, merge → ML-ready; official vs proxy flags.

### 5.2 Training (`train_model.py`)  
Per-target pipelines; Dummy / Ridge / RF / GB; temporal holdout preference.

**Best models (current `training_report.md`):**

| Target | Best model | Temporal MAE | Temporal R² |
|--------|------------|--------------|-------------|
| Total complaints | gradient_boosting_log | 44760.44 | −0.87 |
| Murder incidence | gradient_boosting_log | 11.52 | 0.44 |
| Rape incidents | random_forest_log | 3.15 | 0.36 |
| Murder rate | gradient_boosting_log | 0.73 | 0.50 |
| Rape rate | ridge_log | 0.39 | 0.56 |
| Cognizable rate | gradient_boosting_log | — | — |

### 5.3 Prediction (`predict.py`)  
TN38 resolve; year override; **blend** with official history for rates.

### 5.4 Sentiment & news  
Harvest + DistilBERT/lexicon; district concern map; word clouds.

### 5.5 2026 engine  
Rape / murder / complaints; methods linear · last-year · blend; uncertainty bands; **scenario only**.

### 5.6 Dashboard tabs  
Live, Map, Accuracy, Predict, Sentiment, 2026, **District Compare** (merged), Risk Explain, Health.

### 5.7 Database  
`data/crimecast.db`; `migrate_csv_to_db.py` / Health → Migrate CSVs.

---

# 06. TESTING AND IMPLEMENTATION

This chapter describes **how CRIMECAST was implemented** (build steps, environment) and **how it was tested** (strategy, formal cases, automated runner, UI checklist, and result figures).

## 6.1 Implementation environment

| Item | Detail |
|------|--------|
| Language | Python 3.10+ |
| Core libraries | pandas, numpy, scikit-learn, joblib |
| UI | Streamlit, Plotly |
| Storage | CSV files + SQLite (`data/crimecast.db`) |
| Optional | transformers/torch (DistilBERT), wordcloud |
| OS (demo) | Windows 10/11 |
| Entry points | `run_tests.py`, `dashboard.py`, `train_model.py`, `predict.py` |

## 6.2 Implementation steps

The system was implemented and deployed for demo in the following order:

1. **Data preparation** — Place yearly SCRB/NCRB-style CSVs under `dataset/`; optional staged SCRB under `dataset/scrb_ncrb/`.  
2. **Cleaning** — Run `clean_data.py` / full pipeline to produce `dataset/cleaned/crimecast_ml_ready.csv` (drop TOTAL rows, normalise headers, merge families).  
3. **Model training** — Run `train_model.py`; review `model_outputs/training_report.md` and `training_metrics.csv`.  
4. **Prediction & blend** — Use `predict.py` for district targets; history blend stabilises rates.  
5. **News & sentiment** — Refresh media harvest; score headlines; optional word clouds.  
6. **2026 scenarios** — `forecast_engine` / `predict_2026_rape_all_districts.py` (linear / last-year / blend; TN38).  
7. **Database (optional)** — `py -3 migrate_csv_to_db.py` or Health tab → migrate CSVs into SQLite.  
8. **Dashboard** — `py -3 -m streamlit run dashboard.py --server.port 8501` (or `START_DASHBOARD.bat`).  
9. **Exports for report** — District brief HTML, accuracy CSV, regenerated figures, test terminal capture.  

**Dashboard launch:**

```text
cd CRIMECAST
py -3 -m streamlit run dashboard.py --server.port 8501
```

Browser: `http://localhost:8501`

## 6.3 Testing strategy

Testing is organised in four layers (P1–P4) plus core unit tests (P0):

| Layer | Name | Purpose |
|-------|------|---------|
| **P0** | Core unit | Districts, forecast math, layout, health structure |
| **P1** | Unit (fixtures) | `clean_data`, blend weights, alert rules, map aliases |
| **P2** | Integration | `predict_for_area`, `forecast_districts` column contracts |
| **P3** | Data quality | ML-ready / metrics / 2026 non-negativity & schema |
| **P4** | UI / system | Manual checklist U1–U24 + optional Streamlit AppTest |

**How automated tests are run (Python, no .bat required):**

```text
py -3 run_tests.py
```

**Capture terminal evidence for annex / Forms:**

```text
py -3 project_docs/capture_test_terminal.py
```

Outputs:

- `project_docs/figures/screenshots/shot_08_run_tests_terminal.png`  
- `project_docs/figures/screenshots/run_tests_output.txt`  

**Manual UI validation:** `docs/MANUAL_UI_CHECKLIST.md`  
**Detailed formal table:** `docs/FORMAL_TEST_CASES.md`

### Types of testing mapped to the project

| Type | What was checked in CRIMECAST |
|------|-------------------------------|
| Unit testing | Column normalisation, TOTAL-row drop, TN38 mapping, forecast bands, blend formula, alert rules |
| Integration testing | Predict + multi-district populate; 2026 multi-target forecast schema |
| Data-quality testing | Year range, no aggregates, non-negative counts, official flags, TN38 coverage |
| Model evaluation | CV / test / temporal MAE and R² in Accuracy tab and `training_metrics.csv` |
| System / UI testing | Dashboard pages load; forecast/predict maps use `fill_nulls_from_media=False` |
| Regression / self-test | Option-7 forecast engine remains sklearn-free; version marker present |

## 6.4 Formal test cases (ID · Steps · Expected · Actual)

| ID | Type | Steps (summary) | Expected | Actual / Status |
|----|------|-----------------|----------|-----------------|
| **TC-01** | Unit | Run district entity tests (`to_tn38`, TN38, junk) | Madurai City→Madurai; Avadi→Chennai; junk→None; 38 districts | **Pass** |
| **TC-02** | Unit | `clean_dataset` on fixture with TOTAL row | TOTAL DISTRICT(S) removed; year column set | **Pass** |
| **TC-03** | Unit | `_blend_with_history` for rate vs count targets | Rate: 62% history; count: 35% history; result ≥ 0 | **Pass** |
| **TC-04** | Unit | Alert rules with Thoothukudi rate > Madurai + 2026 HIGH rows | HIGH alerts for murder comparison and/or 2026 risk | **Pass** |
| **TC-05** | Integration | `predict_for_area("murder_rate", "Chennai", year=2026)` | Dict with prediction ≥ 0, area, target, model_name | **Pass / Skip*** |
| **TC-06** | Integration | `forecast_districts("rape_incidents", method="linear")` | Columns district, predicted_value, pred_low/high, risk_level, rank; values ≥ 0 | **Pass** |
| **TC-07** | Data quality | Asserts on `crimecast_ml_ready.csv` | No TOTAL rows; years sane; crime columns not all-null; counts ≥ 0 | **Pass** |
| **TC-08** | System / UI | Open Live, Map, Predict, 2026, Compare; run P4 automated checks | No traceback; no news-fill on forecast maps; checklist can be signed | **Pass** |

\*TC-05 may **Skip** if trained `.joblib` models are not present; unit and data-quality tests still validate core logic.

### Test execution summary (fill after your run)

| Metric | Value |
|--------|--------|
| Command | `py -3 run_tests.py` |
| Tests run | ________ |
| Failures | ________ |
| Errors | ________ |
| Skipped | ________ |
| Overall | **Pass** if failures = 0 and errors = 0 |

**Figure 6.0 — Terminal output of `py -3 run_tests.py`**  
Insert: `project_docs/figures/screenshots/shot_08_run_tests_terminal.png`

## 6.5 Implementation modules delivered

| Module | File(s) | Implementation outcome |
|--------|---------|------------------------|
| Cleaning | `clean_data.py` | Multi-year ML-ready table |
| Training | `train_model.py` | Best model per target + metrics |
| Prediction | `predict.py` | District predict + history blend |
| Forecast 2026 | `forecast_engine.py`, `predict_2026_*` | Multi-target scenarios + uncertainty |
| Sentiment / news | `sentiment_*`, harvest CSVs | Concern map + word clouds |
| Dashboard | `dashboard.py` | Live, Map, Accuracy, Predict, Sentiment, 2026, Compare, Explain, Health |
| Database | `db.py`, `migrate_csv_to_db.py` | SQLite + CSV migrate |
| Testing | `run_tests.py`, `tests/test_*.py` | P0–P4 automated suite |

## 6.6 Result snapshot figures (current data)

Regenerate with: `py -3 project_docs/regenerate_report_figures.py`  

Folder: **`project_docs/figures/results/`** (preferred over legacy `model_outputs/figures/`).

| Figure | File | Description |
|--------|------|-------------|
| 6.1 | `04_actual_vs_predicted.png` | Fitted actual vs predicted |
| 6.2 | `01_top_murder_incidence.png` | Top murder incidence (TN38) |
| 6.3 | `02_top_rape_incidents.png` | Top rape incidents (latest) |
| 6.4 | `05_training_test_r2.png` | Best models test R² |
| 6.5 | `06_rape_2026_top15.png` | 2026 rape scenario top 15 |
| 6.6 | `07_rape_2026_risk_pie.png` | 2026 risk categories |
| 6.7 | `09_news_volume_by_district.png` | News harvest volume (not FIRs) |

**Interpretation note:** 2026 charts are **scenario trends**, not official SCRB forecasts. News volume is a **media support** layer.

## 6.7 Limitations of testing

- Integration predict tests skip when models are not trained.  
- Streamlit AppTest is optional and may skip in heavy environments (torch).  
- Manual UI checklist remains the primary UI sign-off for viva.  
- Short official time series limits model temporal R² — reported honestly on Accuracy page.

---

# 07. CONCLUSION AND FUTURE SCOPE

## 7.1 Conclusion  
CRIMECAST delivers a complete academic pipeline from messy multi-table CSVs to models, news-aware monitoring, scenario forecasts, and explainable district comparison, with honest limits on short official histories.

## 7.2 Limitations  
Short time series; media ≠ FIRs; optional heavy NLP deps; Postgres multi-user not fully wired (SQLite is demo path).

## 7.3 Future scope  
More official years; monthly series; full Postgres; stronger causal designs; deeper Tamil NLP; auth/audit for institutional use.

---

# 08. FORMS AND REPORT

Streamlit pages act as forms/screens. **Print-ready form panels** (regenerated from live data):

Folder: **`project_docs/figures/screenshots/`**

| File | Form |
|------|------|
| `shot_01_live_feed.png` | Live Feed |
| `shot_02_district_map.png` | District Map & Scoreboard |
| `shot_03_accuracy.png` | Accuracy Check |
| `shot_04_forecast_2026.png` | 2026 Forecasts |
| `shot_05_district_compare.png` | District Compare |
| `shot_06_sentiment.png` | Sentiment |
| `shot_07_health.png` | Health |
| `shot_08_run_tests_terminal.png` | **run_tests.py terminal** (testing evidence) |
| `run_tests_output.txt` | Raw test log |

Generate terminal figure: `py -3 project_docs/capture_test_terminal.py`

Optional: replace UI panels with real browser capture (Win+Shift+S) while Streamlit is running.

**Annex:** training_report, 2026 report txt, district brief HTML, health_check, `figures/MANIFEST.md`.

*(INDEX template only: `project_docs/WhatsApp Image 2026-07-19 at 2.58.51 PM.jpeg`.)*

---

# 09. BIBLIOGRAPHY

[1] NCRB, *Crime in India* (various years), Ministry of Home Affairs, GoI.  
[2] SCRB / Tamil Nadu Police — district statistical tables (as available).  
[3] Open public TN crime CSV portals (e.g. OpenCity district releases).  
[4] Pedregosa et al., “Scikit-learn: Machine Learning in Python,” JMLR, 2011.  
[5] McKinney, pandas — Python for Data Analysis.  
[6] Streamlit documentation — https://docs.streamlit.io/  
[7] Plotly.py documentation — https://plotly.com/python/  
[8] Sanh et al., DistilBERT, arXiv:1910.01108, 2019.  
[9] Ribeiro et al., LIME, KDD 2016.  
[10] Lundberg & Lee, SHAP, NeurIPS 2017.  
[11] Python Software Foundation — https://docs.python.org/3/  
[12] SQLite documentation — https://www.sqlite.org/docs.html  

---

**— End of Report —**

*Replace all [PLACEHOLDERS] before final binding. Prefer Word version from `GENERATE_FULL_REPORT.bat` for print layout with embedded figures.*
