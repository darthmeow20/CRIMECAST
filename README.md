# CRIMECAST

**College project** — usable TN district crime **prototype**: SCRB-style tables + news media + ML forecasts + Streamlit dashboard.

Not a live police system. **Official rates** (when tagged SCRB/NCRB) vs **media** (current affairs support). Predictions are research estimates, not legal evidence.

### Who can “use” it (realistically)

| Audience | Usable as |
|----------|-----------|
| **You / viva / examiners** | End-to-end demo: maps, feed, predict, 2026 |
| **Study / research cell (concept)** | District compare + media radar idea |
| **Police ops (production)** | No — needs official CCTNS/SCRB feed + security |

### Demo path (usable)

1. `START_DASHBOARD.bat` or `streamlit run dashboard.py`
2. **Live Feed** — news window + district ranking  
3. **District Map & Scoreboard** — pick district, compare  
4. **Predict** — murder / rape / cognizable rate  
5. **2026 Forecasts** — trend map  


## Fastest path (usable demo)

```bash
pip install -r requirements.txt
python health_check.py          # fix any FAIL first
# Windows: double-click START_DASHBOARD.bat
streamlit run dashboard.py
```

Usability / reliability guide: **[docs/MAKING_IT_USABLE.md](docs/MAKING_IT_USABLE.md)**.

## How to run

```bash
# Install
pip install -r requirements.txt

# Health (models, data, news age)
python health_check.py

# Interactive CLI menu
python app.py

# Web dashboard
streamlit run dashboard.py
# or START_DASHBOARD.bat

# Full pipeline (clean → train → visualize → sentiment)
python main.py
# or: python app.py  → option 1

# News refresh (NEW headlines only)
python acquire_news_signals.py --refresh-new

# Option 7 — 2026 rape forecasts (all districts)
python predict_2026_rape_all_districts.py
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
| `acquire_scrb_ncrb.py` | SCRB/NCRB official tables (pre-2022 + 2025/2026 drop-ins) |
| `tn_map.py` | TN map helpers |
| `health_check.py` | System health before demos |
| `db.py` | SQLite local store |

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
