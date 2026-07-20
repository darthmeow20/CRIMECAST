# CRIMECAST — Manual UI checklist (P4)

Use this for viva / hard-copy **Testing** chapter.  
Run app: `START_DASHBOARD.bat` → http://localhost:8501  

Mark each row: **Pass / Fail / N/A**

| ID | Tab | Steps | Expected | Result |
|----|-----|--------|----------|--------|
| U1 | 🔴 Live Feed | Open page | News heat / map area loads; no red traceback | |
| U2 | Live Feed | Expand **How it works** | Pipeline text visible; health strip caption | |
| U3 | Live Feed | Feed controls → Alert log | Table or “empty” caption (no crash) | |
| U4 | 🗺️ District Map | Choropleth tab | TN map or clear warning if GeoJSON missing | |
| U5 | District Map | Heat map tab | District × metric grid or ranking | |
| U6 | District Map | Scoreboard | Rank by per-lakh options; table sorts | |
| U7 | District Map | Note about Compare | Points to **District Compare** sidebar | |
| U8 | ✅ Accuracy | Page load | Training metrics table or “run train” info | |
| U9 | Accuracy | Claims expander | Claim / don’t claim text | |
| U10 | Accuracy | Build accuracy (optional) | Table + blend metrics if models present | |
| U11 | Accuracy | Holdout backtest (optional) | Table or “no actuals” warning | |
| U12 | 🔮 Predict | Pick district + target + year → Predict | Numeric result + drivers | |
| U13 | Predict | Populate all districts | Map **without** news fill; CSV download | |
| U14 | 💬 Sentiment | Score / load map | Concern map or ranking | |
| U15 | Sentiment | Word cloud section | Bars and/or image; district picker | |
| U16 | 📅 2026 Forecasts | Choose target + method → Generate | TN38 table; map no news fill | |
| U17 | 2026 | Uncertainty bands | Top chart if pred_low/high present | |
| U18 | ⚖️ District Compare | Select 2–4 districts | Carve maps + metrics side-by-side | |
| U19 | Compare | Download brief HTML | File downloads for a district | |
| U20 | 🔍 Risk Explain | Pick district → Explain | Composite chart + SHAP/LIME tabs | |
| U21 | 🩺 Health | Open page | Green/yellow/red checks | |
| U22 | Health | Migrate CSVs (optional) | Success + dataset registry | |
| U23 | Sidebar | Refresh news (optional) | Success or fail toast; no crash | |
| U24 | Lang | Toggle EN/TA | Nav labels switch | |

## Notes for examiner

- **News heat ≠ FIRs.** Forecasts are **scenarios**, not official SCRB.  
- AppTest automated smoke is optional; this checklist is the primary UI validation.  
- Automated unit/integration/data-quality: `RUN_TESTS.bat`.

## Sign-off

| | |
|--|--|
| Tester | |
| Date | |
| Environment | Windows / Python / Streamlit |
| Overall | Pass / Fail with notes |
