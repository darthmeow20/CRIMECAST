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

## Output Folders

- `dataset/cleaned`: cleaned and ML-ready datasets.
- `models`: saved `.joblib` model files.
- `model_outputs`: metrics, reports, predictions, sentiment scores.
- `model_outputs/figures`: chart images.

## Current Limitation

The project now discovers supported year files automatically and writes the combined ML table to `dataset/cleaned/crimecast_ml_ready.csv`.

The current dataset has 2022 and 2023 rows. The models are more useful than a one-year prototype, but stronger forecasting needs several consistent years of crime data.

Sentiment analysis needs text data such as complaint narratives, news text, posts, or public comments. The current CSVs are numeric tables, so `sentiment_text_template.csv` is the starting format for adding text.
