# Model Training Report

- Dataset: `C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST\dataset\cleaned\crimecast_ml_ready.csv`
- Dataset rows: 253
- Dataset years (full table): 2022, 2023, 2024, 2025, 2026
- **Training labels**: `is_official_year==1` (SCRB/NCRB any year, incl. pre-2022 & 2025–2026) — media-proxy excluded; legacy cap if no flags: ≤ 2023
- Models directory: `C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST\models`
- Trained targets: 6

RELIABILITY NOTE: Best model is chosen primarily by 'temporal_mae' (train on past year(s), test on most recent *official* year).
This is a much stricter and more honest measure of how well the model would perform on future/unseen years.

## Official vs media-proxy years

- **Official labels** (used for y): year ≤ 2023 (real TN crime tables).
- **Media-proxy years** (2024+): may exist in `ml_ready` for maps/news features/templates, but are **not** used as training targets.
- News/sentiment columns remain available as **features** when present on official-year rows.
- Prediction still blends model output with district official history for rate ranking (see `predict.py`).

## Notes

- **Temporal evaluation** (train earlier year, test latest official year) is primary for realistic accuracy.
- Each target excludes its own source family to reduce direct leakage.
- `district_city` is excluded so the model does not simply memorize area names.
- Highly correlated features are pruned (corr > 0.95) for more stable models.
- `year` / `year_centered` / `is_latest_year`, population, and **sentiment features** are used when available.
- More official years of data will still give the biggest gains.
- Rate targets (e.g. murder_rate, rape_rate) + risk_index give the most reliable view.

## Best Models

| Target | Best model | Train years | Rows | CV MAE | Temporal MAE | Temporal R2 | Notes |
|---|---|---|---:|---:|---:|---:|---|
| Total complaints | gradient_boosting_log | 2022,2023 | 99 | 9836.549 | 44760.442 | -0.866 | official + temporal holdout |
| Murder incidence | gradient_boosting_log | 2022,2023 | 99 | 9.537 | 11.521 | 0.438 | official + temporal holdout |
| Rape incidents | random_forest_log | 2022,2023 | 99 | 3.262 | 3.152 | 0.357 | official + temporal holdout |
| Murder rate | gradient_boosting_log | 2022,2023 | 91 | 0.710 | 0.735 | 0.502 | official + temporal holdout |
| Rape rate | ridge_log | 2022,2023 | 91 | 0.544 | 0.392 | 0.563 | official + temporal holdout |
| Cognizable crime rate (IPC+SLL) | gradient_boosting_log | 2022 | 49 | 203.998 | nan | nan | official labels only |

## All Candidate Metrics

Full metrics are saved in `training_metrics.csv`.
