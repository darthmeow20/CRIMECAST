# CRIMECAST — 5-minute demo script (viva)

Use this path for viva / project demo. **Restart Streamlit** before demos so BUILD_ID matches.

```powershell
cd CRIMECAST
streamlit run dashboard.py
```

Optional: `python health_check.py` then `python train_model.py` if models missing.

---

## Opening (30s) — How it works

1. Open **🔴 Live Feed**.
2. Expand **How CRIMECAST works**.
3. Point to **health strip** (models · ML data · news age · GeoJSON · DB).

**Say:**  
“Pipeline: official SCRB-style tables + Tamil/English news → clean → train on official years ≤2023 → predict rates → map. Media is support, not training labels. 2026 is a scenario, not an official forecast.”

---

## Minute 1 — Live Feed + alerts

1. **HIGH alerts** banners.
2. News **time window** 30d / 90d / YTD.
3. **Alert log** expander — SQLite persistence over time.
4. Feed controls → language split (Tamil vs English).

**Say:**  
“Live heat is news volume in a window — not FIRs. Alerts are rule-based and logged.”

---

## Minute 2 — Map, scoreboard, brief

1. **🗺️ District Map & Scoreboard**.
2. Choropleth · colour by **murder rate** or density.
3. **Scoreboard** tab — rank by **murder_per_lakh** or **news_per_lakh** (fair compare).
4. Compare tab · pick Thoothukudi vs Madurai.
5. Download **district brief HTML** → “print to PDF for the report.”

**Say:**  
“Per-lakh metrics avoid Chennai always looking highest just because it is large.”

---

## Minute 3 — Accuracy + claims

1. **✅ Accuracy Check**.
2. Show **training metrics** (test R² / MAE) for best models.
3. **What we claim / don’t claim**.
4. **Build accuracy** table → blend vs raw error chart.
5. Optional **Backtest** (linear trend holdout).

**Say:**  
“We train on official years. Blend keeps sticky rates ranked realistically. Temporal R² can be weak — we show it honestly.”

---

## Minute 4 — Predict, 2026, multi-target

1. **🔮 Predict** → district → Murder rate → 2026 → drivers.
2. **📅 2026 Forecasts**:
   - Target: rape / murder / complaints  
   - Method: **linear · last year · blend**  
   - Map (no news fill) · uncertainty bands  
3. **⚖️ District Compare** side-by-side.

**Say:**  
“Three simple methods — no black-box Prophet. Uncertainty bands widen as we go further out.”

---

## Minute 5 — Sentiment + explain + health

1. **💬 Sentiment** → map + **word cloud** for one district.
2. **🔍 Risk Explain** → composite + SHAP proxy / LIME-style.
3. **🩺 Health** tab → green/yellow/red checks.

**Say:**  
“Sentiment is media narrative. Explainability shows *why* a district looks elevated. Health proves the demo is reproducible.”

---

## Screenshot checklist (3 fixed)

Save under `reports/screenshots/` or `report_materials/screenshots/`:

| # | File idea | Tab |
|---|-----------|-----|
| 1 | `01_live_feed.png` | Live Feed + HIGH alerts + map |
| 2 | `02_accuracy_or_scoreboard.png` | Accuracy metrics or Map scoreboard |
| 3 | `03_forecast_2026.png` | 2026 map + uncertainty |

See `docs/REPORTS_SCREENSHOTS_README.md`.

---

## Backup one-liners

| Question | Answer |
|----------|--------|
| Why not only social media? | News/e-papers only. |
| Why 2024–26 numbers? | Media proxies for maps; train on official ≤2023. |
| Why blend? | Rates sticky by district. |
| What is Live map? | News heat, not FIR map. |
| Prophet? | Skipped — annual series too short; linear/last-year/blend is honest. |
| SHAP? | Optional package; we always ship importance×z + LIME-style. |

---

## CLI backup

```powershell
python health_check.py
python app.py --news
python train_model.py
python predict_2026_rape_all_districts.py
streamlit run dashboard.py
```
