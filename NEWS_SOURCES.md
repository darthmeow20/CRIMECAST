# CRIMECAST — Crime News Sources & NLP Strategy

## Goal
Collect **Tamil Nadu crime news** from internet news ecosystems to fill data gaps (especially 2024–2025), drive **trends**, and feed **NLP** — **without relying on social media**.

---

## 1. Text sources (in scope)

| Layer | Examples | How we use them |
|-------|----------|-----------------|
| **Web news / Google News** | The Hindu, TOI, DT Next, News18 Tamil, Indian Express | Google News RSS multi-query harvest (`acquire_news_signals.py`) |
| **E-papers / e-magazines** | Dinamalar, Maalai Malar, Vikatan (when indexed) | Headlines via News RSS / site: queries |
| **Local news apps (aggregator style)** | Daily Hunt, Lokal, Public app | Same public headlines often appear in aggregator feeds; we capture via open web/RSS, not app scraping |
| **Police / civic portals** | TN Police releases, OpenCity summaries | Prefer when structured CSVs exist |

### Out of scope (by design)
- **Social media** (X/Twitter, Facebook, Instagram, WhatsApp status) — **not** primary collection  
- User-generated posts as ground truth for crime *counts*

> Official district statistics remain the gold standard when available. News volume is a **leading indicator / proxy**, not a substitute for FIRs.

---

## 2. Three LLM models (trends + NLP)

| # | Role | Model | Task |
|---|------|--------|------|
| **1** | Sentiment LLM | `distilbert-base-uncased-finetuned-sst-2-english` | Polarity / public tone on crime news |
| **2** | Crime-type LLM | `typeform/distilbert-base-uncased-mnli` (zero-shot) | Classify: homicide, rape/sexual assault, theft, cybercrime, narcotics, assault, other |
| **3** | Trend LLM | Same MNLI backbone, **trend label set** | rising trend / stable / isolated incident / declining / public safety concern |

Implementation: `nlp_pipeline.py` → `analyze_crime_text(text)`

Lexicon fallbacks run if transformers/GPU models fail to load.

---

## 3. Pipeline integration

```
News harvest (Google News RSS + e-paper queries)
        │
        ▼
  3-LLM NLP (sentiment · crime type · trend)
        │
        ▼
  news_signals.csv  +  media_harvest_*.csv
        │
        ▼
  Scale / fill 2024–2025 district proxy CSVs
        │
        ▼
  clean_data (fuse sentiment + news features)
        │
        ▼
  train_model → predict → dashboard Live Feed
```

Commands:

```powershell
# Harvest news (no social) + fill 2024/2025 proxies
python acquire_news_signals.py --populate-2024-2025

# Score a CSV of e-paper headlines you exported (columns: date, district, headline, source)
python acquire_news_signals.py --csv my_epaper_headlines.csv

# Full ML rebuild
python app.py   # option 1
```

---

## 4. Manual export from apps (recommended for report quality)

DailyHunt / Lokal / Public app rarely offer open bulk APIs. For academic use:

1. Export or copy headlines from TN crime sections (date + district if known).
2. Save as CSV: `date,district,headline,source`
3. Run: `python acquire_news_signals.py --csv that_file.csv`
4. Re-run clean + train.

This keeps **news apps** in scope without reverse-engineering private APIs.

---

## 5. Report wording (suggested)

> CRIMECAST augments limited official TN district statistics with **crime-related news text** collected from internet news sources, e-papers, and local news aggregator surfaces (DailyHunt / Lokal / Public-style feeds via open web). **Social media is excluded** from primary collection. Trends and NLP use a **three-model LLM stack**: DistilBERT for sentiment, and DistilBERT-MNLI zero-shot for crime-type classification and temporal trend labelling.

---

## 6. Ethics & limits
- Media bias and over-reporting of sensational crimes
- Urban (Chennai) over-representation in English news
- Not a substitute for NCRB / TN Police official counts
- Always label proxy years (2024–2025) clearly in reports
