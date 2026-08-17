# Deploy CRIMECAST on Render.com

## 1. Push code to GitHub

```bash
cd "/c/Users/ya allah/python_visual_code/machine_learning/CRIMECAST"
git add -A
git commit -m "Render deploy: streamlit start, lean requirements"
git push origin main
```

Include on GitHub:

- `dashboard.py` + Python modules  
- `requirements.txt`  
- `render.yaml` (optional Blueprint)  
- `.streamlit/config.toml`  
- `models/*.joblib`  
- `model_outputs/best_models.json` (relative paths)  
- `dataset/cleaned/crimecast_ml_ready.csv` + key CSVs  
- `assets/` GeoJSON if present  

**Do not** use a comment-filled `packages.txt` (that was for Streamlit Cloud apt only).

---

## 2. Create a Web Service on Render

1. Go to [https://dashboard.render.com](https://dashboard.render.com)  
2. **New → Web Service**  
3. Connect the **crimecast** GitHub repo  
4. Settings:

| Field | Value |
|--------|--------|
| **Name** | `crimecast` (or any) |
| **Region** | Oregon (or closest) |
| **Branch** | `main` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install --upgrade pip && pip install -r requirements.txt` |
| **Start Command** | `streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0 --server.headless true` |
| **Instance** | Free |

5. **Environment → Environment Variables** (critical)

| Key | Value |
|-----|--------|
| `PYTHON_VERSION` | `3.11.11` |
| `STREAMLIT_SERVER_HEADLESS` | `true` |
| `STREAMLIT_BROWSER_GATHER_USAGE_STATS` | `false` |

Also commit **`.python-version`** with `3.11.11` (repo already has this).

**If logs say `Using Python version 3.14.x`**, the build will hang/fail on pandas.  
Fix: set `PYTHON_VERSION=3.11.11` in the Render service → **Manual Deploy → Clear build cache & deploy**.

6. **Create Web Service** → wait for build + deploy.

URL will look like: `https://crimecast.onrender.com`

---

## 3. Or use Blueprint (`render.yaml`)

1. **New → Blueprint**  
2. Select repo (must contain `render.yaml` at root)  
3. Apply → Render creates the service from the file  

---

## 4. Free tier notes

- Service **sleeps** after ~15 min idle; first open can take 30–60s.  
- Disk is **ephemeral** — SQLite writes may reset on redeploy; ship data as CSVs in git.  
- Do **not** install `torch` on free tier (too heavy). Sentiment uses lexicon/TextBlob.  

---

## 5. If build fails

| Error | Fix |
|--------|-----|
| Python 3.14 / pandas “Preparing metadata still running” | Set `PYTHON_VERSION=3.11.11` + `.python-version`; clear build cache |
| Pillow build failed | Ensure Python 3.11 (wheels exist); or drop Pillow line |
| ModuleNotFoundError: plotly | Check `requirements.txt` on GitHub has `plotly` |
| Model not found | Commit `models/*.joblib` + relative paths in `best_models.json` |
| Wrong port | Start command **must** use `$PORT` |

---

## 6. Local smoke (same start style)

```bash
export PORT=8501   # Git Bash / Linux
streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

Windows PowerShell:

```powershell
$env:PORT=8501
streamlit run dashboard.py --server.port $env:PORT --server.address 0.0.0.0 --server.headless true
```
