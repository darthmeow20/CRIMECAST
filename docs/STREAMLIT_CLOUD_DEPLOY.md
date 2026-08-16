# Deploy CRIMECAST on Streamlit Community Cloud

## Why the previous deploy failed

1. **`requirements.txt` was a full local freeze** (Jupyter, torch, pinned `kiwisolve==1.5.0`, etc.).
2. Cloud used **Python 3.14**, which has **no wheel** for that kiwisolver pin.
3. **Absolute Windows paths** in `best_models.json` would break model load on Linux even after install.

## Fix applied in repo

| File | Change |
|------|--------|
| `requirements.txt` | Lean, flexible pins for cloud (no torch/jupyter) |
| `requirements-local-full.txt` | Old full freeze for local Windows reference |
| `runtime.txt` | `python-3.11` (supported on Streamlit Cloud) |
| `predict.py` | Resolves `models/<name>.joblib` if absolute path missing |
| `best_models.json` | Relative `models/...` paths |
| `train_model.py` | Saves relative model paths |

## Push and redeploy

```powershell
cd "C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST"
git add requirements.txt requirements-local-full.txt runtime.txt packages.txt
git add predict.py train_model.py model_outputs/best_models.json
git add models/*.joblib
git add dataset/cleaned/crimecast_ml_ready.csv model_outputs/*.csv
git status
git commit -m "Fix Streamlit Cloud deps (Python 3.11, lean requirements, relative model paths)"
git push origin main
```

Then on [share.streamlit.io](https://share.streamlit.io): **Reboot app** / wait for rebuild.

**Main file:** `dashboard.py`  
**Branch:** `main`

## Must be on GitHub (not gitignored)

- `dashboard.py` and all Python modules used by the dashboard  
- `requirements.txt` + `runtime.txt`  
- `models/*.joblib`  
- `model_outputs/best_models.json`  
- Key CSVs: `dataset/cleaned/crimecast_ml_ready.csv`, news/forecast CSVs under `model_outputs/`  
- `assets/tamil_nadu_districts.geojson` (or allow first-load download)

Check:

```powershell
git check-ignore -v models/*.joblib
```

If ignored, remove `models/` from `.gitignore` or force-add:

```powershell
git add -f models/*.joblib
```

## What is NOT installed on cloud (by design)

- **torch / transformers / DistilBERT** — too heavy; sentiment uses lexicon/TextBlob fallback  
- Jupyter, PDF OCR, tesseract  

Local full stack: `pip install -r requirements-local-full.txt` (optional).

## If install still fails

1. Confirm **runtime.txt** is `python-3.11` (not 3.14).  
2. In Streamlit Cloud app settings, Advanced → Python version **3.11** if available.  
3. Temporarily drop `wordcloud` from `requirements.txt`.  
4. Logs → clear “Could not find a version that satisfies…” package and loosen that pin.

## Smoke check after deploy

- Live Feed opens without traceback  
- Map loads (or GeoJSON warning)  
- Predict returns a number for Chennai  
- 2026 Forecasts generate or load CSV  
