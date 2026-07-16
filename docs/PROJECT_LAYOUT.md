# CRIMECAST Project Layout

```
CRIMECAST/
├── README.md                 # Project entry (only .md outside docs/)
├── requirements.txt
├── RUN_OPTION7.bat
├── CLEANUP_ROOT.bat          # One-time: delete stubs / empty nested docs folders
│
├── app.py, dashboard.py, main.py, …
│
├── docs/                     # ★ ALL documentation (flat — no subfolders)
│   ├── README.md             # Index of every doc
│   ├── QUICK_START.md
│   ├── INSTALL_GUIDE.md
│   ├── PROJECT_GUIDE.md
│   ├── … (all other .md files)
│   ├── flowchart_LR.mmd
│   └── flowchart_TB.mmd
│
├── tests/
├── dataset/
├── models/
├── model_outputs/
├── config/
├── assets/
├── report_materials/         # Screenshots / diagram sources
└── reports/                  # Generated PNGs
```

## Documentation rule

- **One folder for all markdown:** `docs/`
- Files are **flat** (no `docs/guides/`, `docs/sentiment/`, …)
- Root keeps only `README.md` as the project homepage
