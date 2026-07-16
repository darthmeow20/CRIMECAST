# CRIMECAST

Crime analysis, ML forecasting, and DistilBERT sentiment for Tamil Nadu districts.

## How to run

```bash
# Install
pip install -r requirements.txt

# Interactive CLI menu
python app.py

# Web dashboard
streamlit run dashboard.py

# Full pipeline (clean → train → visualize → sentiment)
python main.py
# or: python app.py  → option 1

# Option 7 — 2026 rape forecasts (all districts)
python predict_2026_rape_all_districts.py
# or: RUN_OPTION7.bat
# or: python app.py → option 7

# Tests
python tests/test_project.py
python tests/test_option7_fix.py
```

## Quick start

See **[docs/QUICK_START.md](docs/QUICK_START.md)**.

Full documentation index: **[docs/README.md](docs/README.md)**.

## Main Python modules (root)

| Module | Role |
|--------|------|
| `app.py` | Interactive CLI menu |
| `dashboard.py` | Streamlit web UI |
| `main.py` | Full pipeline entry |
| `clean_data.py` | Clean + feature enrich |
| `train_model.py` | Train ML models |
| `predict.py` | Area/target predictions + risk |
| `predict_2026_rape_all_districts.py` | 2026 rape all-district engine |
| `visualize.py` / `visualize_rape_2026.py` | Charts |
| `sentiment_analysis.py` | DistilBERT sentiment |
| `sentiment_by_state.py` / `sentiment_tn_districts.py` | Regional sentiment |
| `sentiment_visualize*.py` | Sentiment charts |
| `nlp_pipeline.py` | 3-LLM crime text NLP |
| `acquire_news_signals.py` | News/media signal harvest |
| `tn_map.py` | TN map helpers |

## Layout

- `docs/` — **all markdown flat** (see [docs/README.md](docs/README.md))
- `tests/` — health checks and option-7 self-test
- `dataset/` — raw + cleaned data
- `models/` — trained `.joblib` models
- `model_outputs/` — predictions, reports, figures
- `report_materials/` / `reports/` — report binary assets (md copies live in `docs/`)

See also [docs/PROJECT_LAYOUT.md](docs/PROJECT_LAYOUT.md).

### One-time cleanup

If nested `docs/` subfolders or root stubs remain:

1. Double-click **`FLATTEN_DOCS.bat`** to copy all markdown flat into `docs/`.
2. Double-click **`CLEANUP_ROOT.bat`** to delete root stubs and empty `docs/*` subdirs.
