# Model Training Report

- Dataset: `C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST\dataset\cleaned\crimecast_ml_ready.csv`
- Dataset rows: 203
- Dataset years: 2022, 2023, 2024, 2025
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
| Total complaints | gradient_boosting_log | 11366.919 | 25650.227 | 0.435 | 10379.897 | 12406.154 | 0.413 | temporal holdout used |
| Murder incidence | gradient_boosting_log | 7.055 | 13.623 | 0.645 | 11.250 | 6.293 | 0.516 | temporal holdout used |
| Rape incidents | gradient_boosting_log | 2.410 | 4.087 | 0.589 | 2.052 | 1.031 | 0.919 | temporal holdout used |
| Murder rate | gradient_boosting_log | 0.408 | 0.690 | 0.887 | 0.370 | 0.201 | 0.968 | temporal holdout used |
| Rape rate | gradient_boosting_log | 0.326 | 0.493 | 0.638 | 0.309 | 0.162 | 0.880 | temporal holdout used |
| Cognizable crime rate (IPC+SLL) | gradient_boosting_log | 205.615 | 361.770 | 0.290 | 105.184 | nan | nan | random holdout only |

## All Candidate Metrics

Full metrics are saved in `training_metrics.csv`.
