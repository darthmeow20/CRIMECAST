# CRIMECAST - External & Proxy Data Guide (2026)

> **News + 3-LLM NLP:** see **`NEWS_SOURCES.md`** (same `docs/` folder)  
> TN crime news (web, e-paper, DailyHunt / Lokal / Public-style) · **not social media** · 3 LLMs for sentiment, crime type, trends.

## The Core Problem
We only have **2022 + 2023** official TN district-level counts. Predicting 2026 from 2 years of data is extremely weak for any time-series model.

## Recommended Strategy: Hybrid Official + Public Proxy

Use **two layers**:
1. **Official counts** (ground truth baseline when available) — extend with more years.
2. **Crime news media** (not social media): web news, e-papers, DailyHunt / Lokal / Public-style aggregators — volume + NLP for trends.

News volume and negative tone often spike **before or with** official reporting. Use as proxies when police data is lagged. See `NEWS_SOURCES.md`.

## 1. Official TN Data Sources (Priority #1)

### opencity.in (Best match for this project)
- Main historical collection: https://data.opencity.in/dataset/tamil-nadu-crime-data
  - Many years (2010–2021 at minimum) of district/city CSVs + PDF compendiums.
  - Direct CSVs for complaints, IPC crimes, murder/homicide, women crimes, etc.

- 2023 (and newer) specific: https://data.opencity.in/dataset/tamil-nadu-crime-data-2023
  Exact files that match current project naming:
  - `tn_2023_total_complaints.csv`
  - `tn_2023_crimes_against_women.csv`
  - `tn_2023_muder_homicide_negligence.csv`
  - Also: 2021-2023 totals, road accidents, suicides, etc.

**How to add more years**
1. Download the relevant CSVs from the links above.
2. Place them in `dataset/` using consistent naming:
   - `tn_2021_*.csv`, `tn_2024_*.csv`, etc.
3. Re-run `python app.py` → option 1 (or `python clean_data.py`).
4. The `discover_raw_datasets()` function will automatically pick them up by year in filename.

### NCRB "Crime in India" (national + state/district tables)
- Search data.gov.in or opencity for "Crime in India 2022", "2023", "2024".
- Reports contain state-level rates + some city breakdowns. Useful for normalization and broader trends.
- Latest reports appear mid-late the following year.

### Other
- Kaggle: "Indian Crimes Dataset" (2020-2024 across cities) — https://www.kaggle.com/datasets/sudhanvahg/indian-crimes-dataset

## 2. News & Social Proxies (Your Google News + Twitter idea)

These give you **time-series of attention and sentiment** without waiting for police releases.

### News Headlines (Google News style)
Recommended easy options:
- **NewsData.io** (has historical back to 2016, country=IN, keyword search, Google News integration): https://newsdata.io/
- **NewsAPI.org** — simple REST, good for recent + some archives.
- SerpApi / BrightData / HasData Google News scrapers (structured headlines, dates, sources).

Example query ideas:
- "Tamil Nadu crime" OR "Chennai rape" OR "TN police" district:Chennai after:2023
- Filter to Tamil sources + English.

You can store results as a simple CSV:
```
date,district,headline,source,url,sentiment_polarity,crime_intensity
2024-03-12,Chennai,"College student sexually assaulted in Adyar",NewsTamil24x7,https://...,-0.85,8
...
```

Then merge by year + district (like current sentiment_scores).

### Social (X / Twitter)
- Real incidents are discussed publicly (see recent examples of Chennai, Trichy, Namakkal cases).
- Use for:
  - Mention volume per week/month (proxy for "how much attention this crime is getting").
  - Sentiment on discussions.
- Limitation: API access is now paid for good historical search. Use for recent signals or sample collection.

**Example recent signals** (fetched 2026):
- Multiple reports of sexual assault cases in Chennai within 24h periods.
- Machete attacks, kidnappings, custodial deaths mentioned in short time windows.
- These can be turned into "media/social intensity" features.

### Simple Acquisition Ideas
- Run `python acquire_news_signals.py --demo` for starter data.
- Or `python acquire_news_signals.py --csv my_headlines.csv`
- **Live fetch**: `python acquire_news_signals.py --fetch "Tamil Nadu crime OR Chennai rape" --max-items 20`
  (uses Google News RSS via stdlib - no extra packages needed)
- **Populate 2024 & 2025 from media / Twitter / Google News** (recommended gap-fill):
  ```powershell
  python acquire_news_signals.py --populate-2024-2026
  python acquire_news_signals.py --populate-years 2024 2025 2026
  python acquire_news_signals.py --fetch "தமிழ்நாடு குற்றம்" --lang ta
  ```
  Multi-query Google News RSS + X volumes → full `tn_2024_*` / `tn_2025_*` for complaints, women crimes, murder (all 2023 districts, media-scaled). Updates `news_signals.csv`. Harvest log: `media_harvest_tn_crime_2024_2025.csv`. **Proxy only, not official FIRs.**
- For richer historical data: use NewsData.io / NewsAPI with queries like "Tamil Nadu crime" OR "Chennai rape" etc. Then score with the script.
- Reuse the existing `sentiment_analysis.py` (DistilBERT primary + crime lexicon) on any headlines.

## 3. How to Fuse in CRIMECAST (Now Implemented)

- `enrich_with_sentiment()` + new `enrich_with_news_signals()` in clean_data.py
  merge official + sentiment + `news_count`, `avg_news_polarity`, `negative_news_share`, `avg_news_crime_intensity`.
- `compute_risk_index()` in predict.py now blends:
  - 50% predicted volume
  - 30% negative sentiment
  - 20% news/media buzz (volume + negativity + intensity)
- Dashboard shows extra "News/Media Signals" metric + contribution in prediction results + bar chart of news negativity by district in Overview.
- Configurable risk weights: edit `config/risk_weights.json` (volume / sentiment / news).
- `acquire_news_signals.py --demo` or `--fetch` gives immediate usable proxy data.

This directly addresses limited official data by using abundant public discussion volume and tone as leading indicators.

## Practical Next Steps

1. **Fill 2024–2025 gaps from media/X/Google News**:
   `python acquire_news_signals.py --populate-2024-2026`

## Official vs media-proxy years (training)

| Years | Role |
|-------|------|
| **≤ 2023** | **Official** TN tables → used as **training labels** (y) |
| **2024+** | Media-proxy fills → for maps / news features / prediction templates only |

Retrain after clean so models ignore proxy years as labels:

```powershell
python clean_data.py   # or app option 1 clean step
python train_model.py  # trains on year ≤ 2023 only
# or: python app.py → option 1
```

Override if you later receive real 2024 FIRs:

```powershell
python train_model.py --official-max-year 2024
```
2. **Rebuild ML data + models**: `python app.py` → option 1
3. **2026 rape forecasts**: option 7
4. Optional: download more official years from opencity.in when available
5. Optional: add more X volumes to `media_twitter_volumes_2024_2025.csv` and re-populate

**Important disclaimers for reports**:
- Official numbers are always lagged and under-reported.
- News/social = attention/sentiment signals, **not** verified incident counts.
- Best used together: official base rates + public signal adjustments.

See also:
- `docs/SENTIMENT_GUIDE.md`
- Current `clean_data.py` (enrich_with_sentiment)
- `predict.py` (risk calculation)

Contributions welcome — especially a robust news collector that respects rate limits.
