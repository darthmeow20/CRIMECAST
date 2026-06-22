# Model Training Report

- Dataset: `C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST\dataset\cleaned\crimecast_ml_ready.csv`
- Dataset rows: 99
- Dataset years: 2022, 2023
- Models directory: `C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST\models`
- Trained targets: 6

RELIABILITY NOTE: Best model is chosen primarily by 'temporal_mae' (train on past year(s), test on most recent year).
This is a much stricter and more honest measure of how well the model would perform on future/unseen years.

## Notes

- **Temporal evaluation** (train earlier year, test latest) is now primary for realistic future prediction accuracy.
- Each target excludes its own source family to reduce direct leakage.
- `district_city` is excluded so the model does not simply memorize area names.
- Highly correlated features are pruned (corr > 0.95) for more stable models.
- `year` / `year_centered` / `is_latest_year`, population, and **sentiment features** (polarity, intensity, negative share) are used when available.
- Sentiment signals from DistilBERT are fused to make crime rate predictions more accurate and context-aware.
- More years of data will still give the biggest gains.
- Rate targets (e.g. murder_rate, rape_rate, crime_rate) + risk_index give the most reliable view.

## Best Models

| Target | Best model | CV MAE | CV RMSE | CV R2 | Test MAE | Temporal MAE | Temporal R2 | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Total complaints | gradient_boosting_log | 9817.298 | 25544.344 | 0.579 | 3130.381 | 44776.511 | -0.872 | temporal holdout used |
| Murder incidence | gradient_boosting_log | 9.586 | 12.758 | 0.621 | 8.390 | 11.486 | 0.441 | temporal holdout used |
| Rape incidents | random_forest_log | 3.260 | 4.847 | 0.351 | 3.373 | 3.129 | 0.366 | temporal holdout used |
| Murder rate | gradient_boosting_log | 0.706 | 1.232 | 0.656 | 0.763 | 0.726 | 0.471 | temporal holdout used |
| Rape rate | gradient_boosting_log | 0.498 | 0.638 | 0.448 | 0.486 | 0.493 | 0.394 | temporal holdout used |
| Cognizable crime rate (IPC+SLL) | gradient_boosting_log | 208.365 | 370.690 | 0.255 | 98.301 | nan | nan | random holdout only |

## All Candidate Metrics

Full metrics are saved in `training_metrics.csv`.
