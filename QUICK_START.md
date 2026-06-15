# CRIMECAST Quick Start Guide

## 30-Second Setup

```bash
cd c:\Users\ya allah\python_visual_code\machine_learning\CRIMECAST
pip install -r requirements.txt
python app.py
```

Then choose from menu:
- **Option 4**: Sentiment Analysis (DistilBERT)
- **Option 6**: Tamil Nadu District Analysis ⭐
- **Option 1**: Full Pipeline (clean → train → predict → sentiment)

---

## Common Commands

| Command | What it does |
|---------|------------|
| `python app.py` | Open interactive menu |
| `python app.py --tn-district` | Run TN district analysis directly |
| `python app.py --state` | Run state-wise analysis |
| `python sentiment_analysis.py` | Score sentiment on data |
| `python test_project.py` | Check project health |

---

## What You Get

✅ **Sentiment Analysis**
- Text: "Crime rate increased, fear among citizens"
- Result: NEGATIVE (polarity: -0.95, confidence: 0.95)
- Method: DistilBERT (91% accurate)

✅ **Crime Intensity Scoring**
- Detects: murder, rape, assault, robbery, theft, etc.
- Intensity: 0-10 scale
- Example: "Murder in Chennai" → intensity: 10

✅ **Tamil Nadu District Breakdown**
- All 33 districts analyzed separately
- Individual reports per district
- Comparison table (CSV)
- 4 visualization charts

✅ **Crime Predictions**
- Area: Chennai, Coimbatore, etc.
- Target: Total Complaints, Murder, Rape, etc.
- ML model prediction + historical actual

---

## Output Files

After running analysis, find results in `model_outputs/`:

```
├── sentiment_scores.csv                          # Sentiment results
├── sentiment_report.txt                          # Summary report
├── crime_predictions.csv                         # ML predictions
├── tn_district_sentiment_reports/
│   ├── tn_district_comparison.csv               # District comparison
│   ├── tn_ariyalur_sentiment.txt                # District 1 report
│   ├── tn_chengalpattu_sentiment.txt            # District 2 report
│   └── ... (33 total district files)
└── figures/
    ├── sentiment_by_district.png                # All districts
    ├── crime_intensity_ranking.png              # Intensity chart
    ├── district_sentiment_heatmap.png           # Heatmap
    └── ... (4 total visualization charts)
```

---

## Example Usage

### 1. Run Sentiment Analysis
```bash
python app.py
# Select: 4 (Run sentiment scoring)
```
Output: `sentiment_scores.csv` + `sentiment_report.txt`

### 2. Analyze Tamil Nadu Districts
```bash
python app.py
# Select: 6 (Tamil Nadu district-wise sentiment)
```
Output: 33 district reports + visualizations + comparison CSV

### 3. Make Predictions
```bash
python app.py
# Select: 2 (Predict for an area)
# Enter: Chennai
# Enter: (leave blank for all targets)
```
Output: Predictions displayed in console

### 4. Full Pipeline
```bash
python app.py
# Select: 1 (Full pipeline)
```
Runs: clean → train → visualize → sentiment

---

## Sentiment Score Interpretation

| Label | Range | Meaning |
|-------|-------|---------|
| **POSITIVE** | +0.5 to +1.0 | Good news, safe sentiment |
| **NEUTRAL** | -0.1 to +0.1 | Balanced or unclear |
| **NEGATIVE** | -1.0 to -0.5 | Bad news, crime-related |

**Confidence**: Higher is more certain (0.5-1.0)

---

## First Run Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run health check: `python test_project.py`
- [ ] Open menu: `python app.py`
- [ ] Try option 4: Sentiment analysis
- [ ] Try option 6: TN districts
- [ ] Check outputs in `model_outputs/`
- [ ] Read reports in `model_outputs/sentiment_report.txt`

---

## Troubleshooting

**Q: "No module named transformers"**
A: Install dependencies → `pip install -r requirements.txt`

**Q: Slow first run**
A: Normal. Downloads DistilBERT model (~268MB, 5 min). Future runs are fast.

**Q: Different sentiment scores than before**
A: Expected. DistilBERT is more accurate than old TextBlob method.

**Q: Character encoding errors**
A: Fixed! All Unicode removed. Should work on Windows console now.

---

## Key Features

🧠 **DistilBERT Sentiment** - 91% accurate, context-aware  
📊 **TN Districts** - All 33 districts supported  
🔮 **Crime Predictions** - ML models for forecasting  
📈 **Visualizations** - Charts, heatmaps, comparisons  
💾 **Batch Processing** - Handle 1000s of records  
🎯 **Crime Scoring** - Intensity 0-10 scale  

---

## Next Steps

1. **Just starting?** → Run `python app.py` → Select option 4
2. **Want TN analysis?** → `python app.py --tn-district`
3. **Need full pipeline?** → `python app.py` → Select option 1
4. **Want to understand?** → Read `PROJECT_GUIDE.md`
5. **Need deep dive?** → Read `DISTILBERT_GUIDE.md` or `SENTIMENT_TN_DISTRICTS.md`

---

**Status**: ✅ Ready to use  
**Last Updated**: June 14, 2026  
**Method**: DistilBERT (Primary) + TextBlob (Fallback)
