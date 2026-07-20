# CRIMECAST — Formal test case table  
## (Chapter 06 · Testing and Implementation)

**How to run automated cases:** `py -3 run_tests.py`  
**Terminal screenshot:** `project_docs/figures/screenshots/shot_08_run_tests_terminal.png`  
**Log file:** `project_docs/figures/screenshots/run_tests_output.txt`  

Fill **Actual** after your run (or keep the sample Actual if your run matches).

---

### Formal test cases (8)

| ID | Module / type | Steps | Expected | Actual | Status |
|----|---------------|--------|----------|--------|--------|
| **TC-01** | Unit · District entities | 1. Run `py -3 run_tests.py tests.test_unit_core.TestDistrictEntities` 2. Observe city→parent and junk rules | Madurai City→Madurai; Avadi→Chennai; Cyber Cell→None; TN38 count = 38 | Matches expected (unit asserts pass) | **Pass** |
| **TC-02** | Unit · Data cleaning | 1. Use fixture `tests/fixtures/mini_complaints_2023.csv` 2. Call `clean_dataset` 3. Check rows | TOTAL DISTRICT(S) row dropped; year column present; cleaned rows ≥ 1 | TOTAL removed; year=2023; districts retained | **Pass** |
| **TC-03** | Unit · Prediction blend | 1. Call `_blend_with_history(10, 2, murder_rate)` and count target 2. Compare weights | Rate: 62% history / 38% model; count: 35% history / 65% model; result ≥ 0 | Rate blend = 5.04; count blend = 7.2; non-negative | **Pass** |
| **TC-04** | Unit · Alert rules | 1. Build mini ML table Thoothukudi murder rate 4.5 > Madurai 2.0 2. Call `compute_alert_rules` with HIGH 2026 rows | At least one HIGH alert; title mentions Thoothukudi>Madurai and/or 2026 HIGH risk | HIGH alerts raised as designed | **Pass** |
| **TC-05** | Integration · Predict | 1. Ensure models + ML-ready exist 2. `predict_for_area("murder_rate", "Chennai", year=2026)` | Returns dict with prediction ≥ 0, target, area, model_name | Numeric prediction ≥ 0; fields present *(or Skip if models missing)* | **Pass / Skip** |
| **TC-06** | Integration · 2026 forecast | 1. `forecast_districts("rape_incidents", method="linear", save=False)` 2. Inspect columns | Columns: district, predicted_value, pred_low, pred_high, risk_level, rank; pred_high ≥ pred_low; values ≥ 0; ~38 districts | Schema and non-negative values OK | **Pass** |
| **TC-07** | Data quality · ML-ready | 1. Load `dataset/cleaned/crimecast_ml_ready.csv` 2. Run P3 quality tests | No TOTAL aggregates; years 2015–2030; key crime columns not all-null; counts ≥ 0 | Quality asserts pass on current ML-ready | **Pass** |
| **TC-08** | System / UI · Dashboard smoke | 1. `START_DASHBOARD.bat` or `streamlit run dashboard.py` 2. Open Live, Map, Predict, 2026, Compare 3. Optional: `py -3 run_tests.py tests.test_p4_ui` | Pages load without traceback; forecast/predict maps use no news fill; checklist U1–U18 can be marked Pass | UI loads; automated P4 checks on source/checklist pass | **Pass** |

---

### Summary table (for report)

| Category | Test IDs | Tool |
|----------|----------|------|
| Unit | TC-01 … TC-04 | `unittest` / `run_tests.py` |
| Integration | TC-05, TC-06 | `unittest` + live models/data |
| Data quality | TC-07 | `test_p3_data_quality.py` |
| System / UI | TC-08 | Manual checklist + optional AppTest |

| Metric | Value (fill after run) |
|--------|-------------------------|
| Command | `py -3 run_tests.py` |
| Tests run | ________ |
| Failures | ________ |
| Errors | ________ |
| Skipped | ________ |
| Overall | **Pass** if failures=0 and errors=0 |

---

### Notes for examiner

1. Skipped integration tests occur when `.joblib` models or fitted history are not present; unit and data-quality tests still validate core logic.  
2. Forecasts are **scenarios**, not official SCRB publications.  
3. Full UI walkthrough: `docs/MANUAL_UI_CHECKLIST.md` (U1–U24).  
4. Terminal evidence figure: **Figure — run_tests.py output** (`shot_08_run_tests_terminal.png`).

---

### Sign-off

| Field | |
|-------|--|
| Prepared by | [STUDENT NAME] |
| Date | |
| Reviewed by | [GUIDE NAME] |
