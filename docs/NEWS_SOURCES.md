# CRIMECAST — Crime News Sources & NLP Strategy

## Goal
Collect **Tamil Nadu crime news** from **English + Tamil media outlets** to fill data gaps (**2024, 2025, and 2026**), drive **trends**, and feed **NLP** — **without relying on social media**.

---

## 1. Text sources (in scope)

| Layer | Examples | How we use them |
|-------|----------|-----------------|
| **Google News (English)** | The Hindu, TOI, DT Next, Indian Express, NIE, HT, News18 | RSS `hl=en-IN` + **English crime keywords** |
| **Google News (Tamil)** | Tamil-indexed headlines | RSS `hl=ta-IN` + **Tamil crime keywords** |
| **Tamil media (priority)** | **தினத்தந்தி**, **தினமலர்**, **தினமணி**, **தமிழ் முரசு**, **புதிய தலைமுறை**, **விகடன்**, **பிபிசி தமிழ்** | Brand + `site:` queries |
| **English TN press** | The Hindu, TOI, DT Next, Indian Express, Deccan Chronicle, HT | Brand + `site:` queries (equal priority to Tamil) |

Both languages always run in harvest/refresh — not Tamil-only.
| **English TN press** | The Hindu, DT Next, TOI, New Indian Express, Deccan Chronicle | `site:` queries |
| **Local news apps (aggregator)** | Daily Hunt, Lokal, Public | Open-web headlines only (not app scraping) |
| **Police / civic** | TN Police releases when structured | Prefer official CSVs when available |

### Crime keywords (Tamil harvest)

| Tamil | Meaning |
|-------|---------|
| கொலை | Murder |
| தாக்குதல் | Assault / attack |
| கடத்தல் | Abduction / kidnapping |
| லஞ்சம் | Bribery |
| இணைய வழி குற்றங்கள் | Cyber crimes |
| திருட்டு | Theft |
| பாலியல் வன்கொடுமை | Sexual violence |
| POCSO | POCSO Act cases |
| போதைப்பொருள் கடத்தல் | Drug trafficking |
| கைது | Arrest |
| முதல் தகவல் அறிக்கை | FIR |

Configured in `acquire_news_signals.py` as `TAMIL_CRIME_KEYWORDS` / `TAMIL_CRIME_OR`.

### Out of scope (by design)
- **Social media** as primary collection  
- User posts as ground truth for crime *counts*

> Official district statistics remain the gold standard. News volume is a **leading indicator / proxy**, not a substitute for FIRs.

---

## 2. Three LLM models (trends + NLP)

| # | Role | Model | Task |
|---|------|--------|------|
| **1** | Sentiment | DistilBERT SST-2 | Polarity on crime news |
| **2** | Crime-type | DistilBERT MNLI zero-shot | homicide, rape, theft, cyber, … |
| **3** | Trend | DistilBERT MNLI trend labels | rising / stable / isolated / … |

Implementation: `nlp_pipeline.py` → `analyze_crime_text(text)`

---

## 3. Pipeline integration

```
News harvest (Google News EN+TA + Tamil e-paper site queries)
        │
        ▼
  3-LLM NLP (sentiment · crime type · trend)
        │
        ▼
  news_signals.csv  +  media_harvest_*.csv
        │
        ▼
  Scale / fill 2024–2025–2026 district proxy CSVs
        │
        ▼
  clean_data → train_model → predict → dashboard
```

### Commands

```powershell
# ONE-TIME bulk (first setup only) — full 2024–2026 proxies
python acquire_news_signals.py --populate-2024-2026
# or: python app.py → n → mode 1

# Incremental NEW headlines only (dashboard 🔄 / full pipeline step 1)
python acquire_news_signals.py --refresh-new
# or: dashboard "Refresh new news" button

# Live fetch / CSV / demo
python acquire_news_signals.py --fetch "தமிழ்நாடு குற்றம்" --lang ta
python acquire_news_signals.py --csv my_epaper_headlines.csv
python acquire_news_signals.py --demo

# Full ML rebuild (uses existing news + pulls NEW only)
python app.py   # option 1
```

### Outputs
| File | Description |
|------|-------------|
| `dataset/tn_2024_*.csv` … `tn_2026_*.csv` | Media-scaled proxy tables |
| `model_outputs/media_harvest_tn_crime_2024_2026.csv` | Raw harvest log |
| `model_outputs/media_headlines_scored_{year}.csv` | NLP-scored sample |
| `model_outputs/news_signals.csv` | District-year aggregates for ML |

---

## 4. Manual export from apps (optional quality boost)

1. Export headlines from TN crime sections (date + district if known).
2. CSV columns: `date,district,headline,source`
3. `python acquire_news_signals.py --csv that_file.csv`
4. Re-run clean + train.

---

## 5. Ethics & limits
- Media bias and sensational crime over-reporting  
- Chennai over-representation  
- Tamil model scoring may be weaker on pure Tamil script (lexicon / EN models)  
- Always label proxy years clearly in reports  
- **2026 proxies** are early-year / forward media attention, not official statistics  
