# Model Training Report

- Dataset: `C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST\dataset\cleaned\crimecast_ml_ready.csv`
- Dataset rows: 99
- Dataset years: 2022, 2023
- Models directory: `C:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST\models`
- Trained targets: 3

## Notes

- Each target excludes its own source family to reduce direct leakage.
- `district_city` is excluded so the model does not simply memorize area names.
- More years make the model more useful, but this is still a prototype until the dataset covers several years consistently.
- Sentiment features were not used because the available CSVs do not contain free-text records yet.

## Best Models

| Target | Best model | CV MAE | CV RMSE | CV R2 | Test MAE | Test RMSE | Test R2 |
|---|---|---:|---:|---:|---:|---:|---:|
| Total complaints | random_forest_log | 10574.102 | 28605.056 | 0.472 | 4685.702 | 7233.808 | 0.879 |
| Murder incidence | gradient_boosting_log | 9.216 | 12.568 | 0.632 | 7.601 | 9.645 | 0.717 |
| Rape incidents | random_forest_log | 3.387 | 4.988 | 0.313 | 3.298 | 4.954 | 0.339 |

## All Candidate Metrics

Full metrics are saved in `training_metrics.csv`.
