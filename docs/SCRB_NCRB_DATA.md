# SCRB / NCRB official data in CRIMECAST

## Policy

| Layer | Role |
|-------|------|
| **SCRB / NCRB / TN police tables** | **Official** — usable as training labels for **any year**, including **pre-2022** and **2025–2026** when files exist |
| **Media / news scaled proxies** | **Not** training labels — prediction templates + Live Feed only |

Configured in `config/official_data_policy.json`.

## What we ingest automatically

Public OpenCity TN district tables (SCRB-class):

- IPC cognizable counts **2019, 2020, 2021**
- Murder / culpable homicide / negligence (**2021**)
- Complaints detail (**2021**)
- Crimes against women / rape / assault (**2021**)

```bash
python acquire_scrb_ncrb.py --apply --rebuild-ml
python train_model.py
```

## 2025 & 2026 as SCRB/NCRB

NCRB “Crime in India” and TN SCRB PDFs lag; when you have official district CSVs:

### Option A — Drop-in (recommended)

Put files here (same naming as project raw tables):

```
dataset/scrb_ncrb/dropin/tn_2025_complaints.csv
dataset/scrb_ncrb/dropin/tn_2025_muder_homicide.csv
dataset/scrb_ncrb/dropin/tn_2025_crimes_against_women.csv
dataset/scrb_ncrb/dropin/tn_2026_....csv
```

Then:

```bash
python acquire_scrb_ncrb.py --apply --rebuild-ml
python train_model.py
```

### Option B — Tag existing project files

If `dataset/tn_2025_*.csv` / `tn_2026_*.csv` are **true** SCRB extracts (not media-scaled):

```bash
python acquire_scrb_ncrb.py --tag-years 2025 2026 --apply --rebuild-ml
python train_model.py
```

This sets `data_source=scrb_ncrb` so `is_official_year=1` and labels enter training.

## Columns that matter

After `clean_data`:

- `data_source` — `scrb_ncrb` | `media_proxy` | …
- `is_official_year` — 1 if SCRB/NCRB (or legacy ≤2023 without media tag)
- `is_media_proxy_year` — 1 if news-scaled fill only

Training uses **only** `is_official_year == 1` rows as **y**.

## Pre-2022

After apply you should see years **2019–2021** (and drop-ins) in `crimecast_ml_ready.csv` with official flags.

## Honesty

- OpenCity tables are compiled district stats (SCRB-class), not live FIR feeds.
- Until real SCRB 2025/2026 CSVs are dropped in, those years may still be media-proxy if they were filled from news.
- Always retrain after applying new official years.
