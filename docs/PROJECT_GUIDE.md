# CRIMECAST Project Guide

## Main Commands

Run the full project pipeline:

```powershell
.\.venv\Scripts\python.exe main.py
```

Open the console app menu:

```powershell
.\.venv\Scripts\python.exe app.py
```

**New: Interactive Web Dashboard** (recommended for users):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
streamlit run dashboard.py
```

Train only the ML models:

```powershell
.\.venv\Scripts\python.exe train_model.py
```

Create charts only:

```powershell
.\.venv\Scripts\python.exe visualize.py
```

Predict for Chennai:

```powershell
.\.venv\Scripts\python.exe predict.py --area Chennai
```

Predict using a specific year's area data:

```powershell
.\.venv\Scripts\python.exe predict.py --area Chennai --year 2022
```

Predict one target:

```powershell
.\.venv\Scripts\python.exe predict.py --area Chennai --target murder
```

Run sentiment scoring after adding text rows:

```powershell
.\.venv\Scripts\python.exe sentiment_analysis.py
```

For ML-based sentiment training, fill the `text` and `sentiment_label` columns in
`dataset/cleaned/sentiment_text_template.csv`. Labels must be `positive`, `negative`,
or `neutral`. Use at least six labeled rows across two classes to train; substantially
more balanced examples are recommended for reliable results.

## Output Folders

- `dataset/cleaned`: cleaned and ML-ready datasets.
- `models`: saved `.joblib` model files.
- `model_outputs`: metrics, reports, predictions, sentiment scores.
- `model_outputs/figures`: chart images.
- `models/sentiment_tfidf_logistic.joblib`: trained sentiment model, created after labeled text is added.
- `model_outputs/sentiment_metrics.json`: sentiment cross-validation metrics.

## Current Limitation (Data)

The project now discovers supported year files automatically and writes the combined ML table to `dataset/cleaned/crimecast_ml_ready.csv`.

**Current data: only 2022 + 2023** (99 rows total).

**Recent improvements for better accuracy & reliability**:
- Time + population + **sentiment features** (DistilBERT polarity + crime intensity) are fused into ML models.
- Automatic correlation pruning + temporal validation (past year → latest year) for honest forecasting.
- Future predictions (e.g. 2026) correctly extrapolate using year + sentiment.
- **Blended Risk Index** = crime volume + negative public sentiment.
- DistilBERT is now the real primary sentiment engine.
- Auto-generates demo text from your numeric data so sentiment "just works".

**Yes — you almost certainly need more years** for reliable crime *rate* forecasting:
- With only two years the models are mostly cross-sectional. Year-over-year trends, policy effects, and real forecasting power are very limited.
- 2026 predictions (see the rape 2026 scripts) are basically extrapolation on a tiny time series — they can be useful for prototyping but have high uncertainty.
- Adding even one more consistent year (2023 full district tables + 2024) would be a big improvement.

### Recommended Data Sources
1. **Best immediate addition (2023 district-level, matches your files almost exactly)**:
   - https://data.opencity.in/dataset/tamil-nadu-crime-data-2023
   - Direct CSVs you can drop in `dataset/`:
     - `tn_2023_total_complaints.csv`
     - `tn_2023_muder_homicide_negligence.csv` (note the "muder" spelling)
     - `tn_2023_crimes_against_women.csv`
   - The cleaner (`clean_data.py`) auto-discovers any CSV containing a 4-digit year + "complaint"/"women"/"muder|murder|homicide".

2. **NCRB "Crime in India" reports** (national + state tables, usually PDF):
   - https://ncrb.gov.in/ (Crime in India section)
   - 2023 and 2024 reports have been released as of mid-2026.
   - District tables are often in annexures. You may need to extract tables (use tabula, camelot, or manual copy for key categories).

3. **Tamil Nadu Police / SCRB**:
   - Official site: https://tnpolice.gov.in or e-services portals
   - They publish "Crime Review Tamil Nadu" annually (full district breakdowns are gold when available).
   - News outlets sometimes publish summaries from TN Police data for 2024 (e.g. murder counts).

4. Other:
   - data.gov.in / tn.data.gov.in (various crime tables, often state-level)
   - Kaggle "Indian Crimes Dataset" (up to 2024 in some versions)

**How to add new data**:
1. Download the matching CSV files.
2. Place them in the `dataset/` folder (keep your existing 2022/2023 files).
3. Re-run cleaning: `python clean_data.py` or full pipeline via `app.py` option 1 / `main.py`.
4. Re-train models.

If column names or structure changed slightly in newer releases, let me know and I'll update the cleaner.

Sentiment analysis needs text data such as complaint narratives, news text, posts, or public comments. The current CSVs are numeric tables, so `sentiment_text_template.csv` is the starting format for adding text.
