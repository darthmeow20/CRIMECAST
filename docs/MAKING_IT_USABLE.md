# Making CRIMECAST usable, reliable, and useful

**Framing for college:** a **usable prototype** (maps, feed, ranks, predict) you can demo and explain —
not a replacement for police SCRB/CCTNS. Usable = clear workflow + honest data labels + works offline after setup.

Honest assessment + practical ops guide for demos, academic submission, and light real-world *concept* use.

## What the project is good at today

| Strength | Why it matters |
|----------|----------------|
| **TN district focus** | Maps, scoreboards, 2026 rape trend, murder/rape/cognizable rates |
| **Official + media hybrid** | Official stats lag; news harvest bridges current affairs |
| **Streamlit ops UI** | Live Feed, Map & Scoreboard, Predict, Sentiment, 2026 |
| **SQLite local store** | Headlines + sentiment aggregates without a server |
| **Health check** | `python health_check.py` before demos |

## What limits “truthfulness” (be transparent)

1. **Official labels lag** — training/trust for rates is best ≤ **2023**. Years 2024–2026 may be thinner or proxy-filled.
2. **Media ≠ crime counts** — headline volume reflects attention, not FIR totals.
3. **TVK / party media scores** — association in news, not “who ruled better” on official rates alone.
4. **News RSS** — Google News can change, rate-limit, or miss Tamil sources.
5. **Models** — district predictions blend model + history; not courtroom evidence.

Always show **data year / source** next to numbers in demos.

---

## Reliability checklist (weekly)

```bash
python health_check.py
python acquire_news_signals.py --refresh-new
# optional full rebuild:
python app.py   # option 1 pipeline; option 7 for 2026
```

| Item | Action if fail |
|------|----------------|
| ML-ready missing | `python clean_data.py` or app option 1 |
| No models | app option 1 / `train_model.py` |
| Stale news (>7d) | dashboard 🔄 or `--refresh-new` |
| No 2026 file | option 7 / Forecasts tab |
| Map blank | first load online; caches `assets/tamil_nadu_districts.geojson` |

Schedule: `SCHEDULE_NEWS_REFRESH.bat` (Windows Task Scheduler).

---

## Usability — how to demo in 5 minutes

1. Double-click **`START_DASHBOARD.bat`** (runs health check + Streamlit).
2. **Live Feed** — high alerts + heat + headlines (current affairs).
3. **District Map & Scoreboard** — media volume or murder/rape; pick district high→low.
4. **Predict** — Murder / Rape / Cognizable rate + map.
5. **Sentiment** — score news → map; select one district.
6. **2026 Forecasts** — interactive map + uncertainty.

Do **not** open hidden tabs (Admin / Analytics removed from nav).

---

## Useful product directions (priority)

### P0 — do these for a serious deliverable
- [x] Health check + one-click dashboard start
- [x] Clear official vs media labels in UI
- [ ] Freeze a **demo snapshot** date (export CSV + db copy) for viva
- [ ] One-page **limitations** slide in report materials

### P1 — reliability
- [ ] Unit tests for district name normalization (`district_entities`)
- [ ] Pin `requirements.txt` + `requirements-minimal.txt` (no torch if lexicon-only demo)
- [ ] Log every news refresh timestamp in SQLite `meta` (already partially done)
- [ ] Fail soft when DistilBERT missing (TextBlob path — already partial)

### P2 — usefulness for users
- [ ] Export “district brief PDF” without print (weasyprint / reportlab)
- [ ] Alert email/Telegram when HIGH rules fire after refresh
- [ ] Compare two districts side-by-side export
- [x] Historical official years pre-2022 + SCRB/NCRB for 2025/2026 (`acquire_scrb_ncrb.py`)

### P3 — scale later
- [ ] PostgreSQL via `CRIMECAST_DATABASE_URL` for multi-user
- [ ] Auth + read-only public demo mode
- [ ] Scheduled scoring of full harvest (not only 120 headlines)

---

## Design principles that keep it trustworthy

1. **Never hide uncertainty** — show pred_low / pred_high on 2026.
2. **Separate layers** — official rates vs news heat vs model forecast.
3. **Rank with a stated metric** — scoreboard “rank by” must match the story.
4. **Refresh is incremental** — bulk populate once; daily = NEW only.
5. **One path to run** — `START_DASHBOARD.bat` / `python health_check.py`.

---

## Quick commands

```bash
# Health
python health_check.py

# Dashboard
streamlit run dashboard.py
# or START_DASHBOARD.bat

# News (new only)
python acquire_news_signals.py --refresh-new

# 2026
python predict_2026_rape_all_districts.py
```

Data locations: see conversation / README — `dataset/`, `model_outputs/`, `models/`, `data/crimecast.db`.
