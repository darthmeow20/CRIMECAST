# Hard-copy project report (submission)

## Index structure (from your screenshot)

Matches `WhatsApp Image 2026-07-19 at 2.58.51 PM.jpeg`:

1. Introduction (Company profile, Project overview)  
2. System analysis (Feasibility, Existing, Proposed)  
3. System configuration (Hardware, Software, About software)  
4. System design (Normalization, Table design, Input design, SFD/DFD)  
5. System description  
6. Testing and implementation  
7. Conclusion and future scope  
8. Forms and report  
9. Bibliography  

## Generate Word document (with NEW figures + screenshots)

Double-click:

```
project_docs\GENERATE_FULL_REPORT.bat
```

This runs **two** steps:

1. `regenerate_report_figures.py` → fresh charts from **current** CSVs/DB  
2. `generate_full_report_docx.py` → Word report using those assets  

Or manually:

```powershell
cd "C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST"
py -3 -m pip install python-docx pillow matplotlib pandas numpy
py -3 project_docs\regenerate_report_figures.py
py -3 project_docs\generate_full_report_docx.py
```

**Outputs:**

| Path | Content |
|------|---------|
| `project_docs\figures\results\` | Ch.06 result snapshot (NEW, not legacy) |
| `project_docs\figures\screenshots\` | Ch.08 forms (Live, Map, Accuracy, 2026, Compare, …) |
| `project_docs\CRIMECAST_FULL_PROJECT_REPORT.docx` | Full Word report |

Legacy `model_outputs/figures/*` is only used if a new file is missing.

## Testing evidence (formal cases + terminal)

```powershell
py -3 run_tests.py
py -3 project_docs\capture_test_terminal.py
```

| File | Use in report |
|------|----------------|
| `docs/FORMAL_TEST_CASES.md` | Chapter 06 table TC-01…TC-08 |
| `project_docs/figures/screenshots/shot_08_run_tests_terminal.png` | Forms/Report + Testing figure |
| `project_docs/figures/screenshots/run_tests_output.txt` | Annex log |

## Before print / binding

1. Open the `.docx` in Microsoft Word.  
2. Replace placeholders:
   - `[STUDENT NAME]`
   - `[REGISTER NUMBER]`
   - `[DEGREE / DEPARTMENT]`
   - `[GUIDE NAME]`
   - `[COLLEGE / UNIVERSITY]`
3. Insert → Page Number (if needed); update INDEX page numbers.  
4. Optional: paste 2–3 **live dashboard screenshots** (Live Feed, Map, 2026) into chapter 08.  
5. File → Print, or Export → PDF, then print hard copy.

## Figures auto-included (if present)

- `reports/diagrams/dfd_level_0.png`, `dfd_level_1.png`, `system_flow_diagram.png`
- `model_outputs/figures/actual_vs_predicted.png`, top murder, rape 2026, sentiment
- Your index photo from `project_docs/`

## Annex printouts (recommended)

- `model_outputs/training_report.md`
- `model_outputs/rape_predictions_2026_report.txt`
- One **district brief HTML** from District Compare (browser Ctrl+P)
- Health check: `py -3 health_check.py`
