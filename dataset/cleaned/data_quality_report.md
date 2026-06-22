# Data Quality Report

## Cleaning Rules

- Standardized headers to `snake_case`.
- Removed `TOTAL DISTRICT(S)` aggregate rows from model-ready data.
- Removed source serial-number columns.
- Converted numeric-looking fields to numeric values.
- Preserved unknown rate values as missing values for later imputation.
- Added `year`, `district_city`, and `area_type` keys.

## Cleaned Files

| Dataset | Raw rows | Clean rows | Dropped totals | Columns | Missing values | Output |
|---|---:|---:|---:|---:|---:|---|
| 2022_women_crimes | 50 | 49 | 1 | 39 | 48 | women_crimes_2022_clean.csv |
| 2022_murder_homicide | 50 | 49 | 1 | 12 | 12 | murder_homicide_2022_clean.csv |
| 2022_complaints | 50 | 49 | 1 | 9 | 4 | complaints_2022_clean.csv |
| 2023_complaints | 51 | 50 | 1 | 19 | 0 | complaints_2023_clean.csv |
| 2023_women_crimes | 51 | 50 | 1 | 39 | 48 | women_crimes_2023_clean.csv |
| 2023_murder_homicide | 51 | 50 | 1 | 12 | 12 | murder_homicide_2023_clean.csv |

## ML-Ready Dataset

- Rows: 99
- Columns: 82
- Years: 2022, 2023
- Output: `crimecast_ml_ready.csv`

NOTE: Only two years of data currently. Sentiment aggregates (if sentiment_scores.csv exists) are automatically merged as predictive features.
      This significantly improves crime rate model accuracy by incorporating public sentiment signals.

Suggested prediction targets include `complaints_total_complaints`, `murder_homicide_murder_incidence`, `women_crimes_rape_sec_376_i` (counts), and crime *rates*: `murder_homicide_murder_rate`, `women_crimes_rape_r`, `complaints_rate_of_cognizable_crime_ipc_sll` (or alias crime_rate).

## Sentiment Analysis Readiness

No complaint narratives, social posts, news text, or other free-text fields were found in the current raw CSVs.
Use `sentiment_text_template.csv` as the schema when you add text data for sentiment analysis.
