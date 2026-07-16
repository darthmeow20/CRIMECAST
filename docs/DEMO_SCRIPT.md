# CRIMECAST — 3-minute demo script

Use this path for viva / project demo.

## Setup (once)

```powershell
cd CRIMECAST
streamlit run dashboard.py
```

Optional (if models old):

```powershell
python train_model.py
```

---

## Minute 1 — Live Feed (current affairs)

1. Open **🔴 Live Feed**.
2. Point to **alert banners** (e.g. Thoothukudi murder rate > Madurai, news spikes).
3. Show **Map metric** toggle:
   - News (time window)
   - Murder rate
   - Rape rate
   - 2026 rape forecast
4. Show **time window**: 30d / 90d / YTD / All time.
5. Show **Tamil vs English** pie (dual media pipeline).
6. Click small **🔄** to refresh **new** news only.

**Say:**  
“Live heat is news volume in a chosen window, not the 2026 model. Forecasts are a separate metric.”

---

## Minute 2 — Scorecard + accuracy

1. Open **📋 District Scorecard**.
2. Select **Thoothukudi**, compare with **Madurai**.
3. Highlight murder rate higher in Thoothukudi; news + 2026 forecast on one page.
4. Download **district brief HTML** → “print to PDF for the report.”
5. Open **✅ Accuracy Check** → Build table → show **official vs model raw vs blend**.
6. Spotlight rows: blend closer to official history.

**Say:**  
“We train only on official years ≤2023. Media proxies fill maps/news, not training labels. Blend keeps high-rate districts ranked correctly.”

---

## Minute 3 — Predict + 2026 + Tier-3

1. **🔮 Predict** → Thoothukudi → Murder rate → year 2026 → Predict.
2. Read **Why this prediction?** drivers.
3. **📅 2026 Forecasts** → regenerate if needed → show **uncertainty bands** chart.
4. Optional: **🗺️ Geographic** choropleth.
5. Mention weekly news: `SCHEDULE_NEWS_REFRESH.bat` / Task Scheduler (`docs/TIER3_OPS.md`).

**Say:**  
“End-to-end: Tamil+English news with entity cleanup, official-trained ML, explainable risk, uncertainty bands, and district briefs.”

---

## Backup one-liners

| Question | Answer |
|----------|--------|
| Why not only social media? | News/e-papers only; social not primary. |
| Why 2024–26 numbers? | Media proxies for gaps; train on official ≤2023. |
| Why blend? | Rates sticky by district; improves ranking (Thoothukudi > Madurai). |
| What is Live map? | Current affairs news heat, not crime FIR map. |

---

## CLI backup (if Streamlit fails)

```powershell
python app.py --news          # or n → mode 2 for new only
python train_model.py
python app.py --rape-2026
python app.py --predict --area Thoothukudi --target murder_rate --year 2026
```
