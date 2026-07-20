# CRIMECAST — Testing guide (P0–P4)

## Run everything (preferred — Python file)

```powershell
cd CRIMECAST
python run_tests.py
```

or:

```powershell
py -3 run_tests.py
```

### Capture terminal screenshot for Forms/Report

```powershell
py -3 project_docs/capture_test_terminal.py
```

Creates:

- `project_docs/figures/screenshots/shot_08_run_tests_terminal.png`
- `project_docs/figures/screenshots/run_tests_output.txt`

### Formal test case table (print this)

See **`docs/FORMAL_TEST_CASES.md`** — TC-01 … TC-08 (ID, steps, expected, actual).

Other options:

```powershell
py -3 run_tests.py --list
py -3 run_tests.py -q
py -3 run_tests.py tests.test_p1_unit_clean_blend_alerts
py -3 run_tests.py tests.test_p2_integration
```

Also works:

```powershell
py -3 -m unittest discover -s tests -p "test_*.py" -v
.\RUN_TESTS.bat
```

Exit code **0** = success (skips are OK when optional data/models missing).

---

## Layers implemented

| Priority | Layer | Files |
|----------|--------|--------|
| **P0** | Core unit tests | `test_unit_core.py`, `test_forecast_math.py`, `test_option7_fix.py` |
| **P1** | Fixtures + clean_data + blend + alerts | `test_p1_unit_clean_blend_alerts.py`, `tests/fixtures/*` |
| **P2** | Integration predict + forecast columns | `test_p2_integration.py` |
| **P3** | Data quality on ML-ready / outputs | `test_p3_data_quality.py` |
| **P4** | UI checklist + optional AppTest | `test_p4_ui.py`, `docs/MANUAL_UI_CHECKLIST.md` |

---

## P1 — Unit (fixtures)

Fixtures in `tests/fixtures/`:

- `mini_complaints_2023.csv` — includes TOTAL row to drop  
- `mini_ml_ready.csv` — tiny multi-year table  
- `mini_rape_2026.csv` — HIGH risk rows  

Covers: column normalize, total-row drop, area classify, `_blend_with_history` weights, alert rules (Thoothukudi > Madurai, 2026 HIGH).

---

## P2 — Integration

- `predict_for_area` for murder rate / rape (skips if models missing)  
- `populate_all_district_predictions` shape  
- `forecast_districts` required columns for rape / murder / complaints  
- Methods linear / last_year / blend  
- `district_brief_html` contains district name  

---

## P3 — Data quality

On `dataset/cleaned/crimecast_ml_ready.csv` (if present):

- Not empty; year range; no TOTAL aggregates  
- Key crime columns present and not all-null  
- Non-negative counts  
- Official-year flags when present  
- TN38 coverage after `to_tn38`  

Also checks training_metrics, fitted_predictions, rape 2026 non-negative.

---

## P4 — UI

1. **Manual (primary for viva):** fill `docs/MANUAL_UI_CHECKLIST.md` (U1–U24).  
2. **Automated:**  
   - Checklist file exists & mentions core tabs  
   - `dashboard.py` contains main page names + `fill_nulls_from_media=False`  
   - Optional `streamlit.testing.v1.AppTest` smoke (skips if unstable/torch-heavy)  

---

## Report text (copy into Ch.06)

> Testing comprises (1) unit tests for pure logic (districts, cleaning, blend, alerts, forecast bands); (2) integration tests for prediction and 2026 forecast contracts when models/data exist; (3) data-quality asserts on the ML-ready table; (4) a 24-item manual UI checklist plus optional Streamlit AppTest smoke. Run: `RUN_TESTS.bat`.

---

## Tips

| Issue | Fix |
|-------|-----|
| Many skips | Run `train_model.py` + ensure `fitted_predictions.csv` |
| Dashboard import fails in P1 alerts | Install `streamlit` |
| AppTest timeout | Ignore — use manual checklist |
| DB tests | Write tiny `_unit_test_tiny` table in `data/crimecast.db` |
