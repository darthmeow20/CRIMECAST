# CRIMECAST - Screenshots & Visual Evidence

## Recommended Screenshots to Capture

Run the following and capture screenshots (use Windows Snipping Tool or similar):

### 1. Interactive Menu
- Command: `python app.py`
- Capture the main menu showing options 1-9 + "c"
- File suggestion: `menu_main.png`

### 2. Full Pipeline Run (Option 1)
- Run option 1 or `python main.py`
- Capture console output showing:
  - Sentiment analysis (DistilBERT)
  - Cleaning + fusion
  - Training with temporal metrics
- File suggestion: `full_pipeline_output.png`

### 3. Prediction with Risk Index (Option 2 or CLI)
- Example: `python predict.py --area Chennai --target crime_rate --year 2026`
- Or from menu option 2
- Capture output showing `risk_index` and `risk_label`
- File suggestion: `prediction_with_risk.png`

### 4. 2026 Rape Predictions (Option 7)
- Run option 7
- Capture district table + risk levels (after fix)
- File suggestion: `2026_rape_predictions.png`

### 5. Sentiment Analysis (Option 4 or 6)
- Run sentiment scoring or TN district analysis
- Capture report output and any TN comparison table
- File suggestion: `sentiment_tn_districts.png`

### 6. Key Generated Visuals
Use the existing PNGs from `model_outputs/figures/` (copy into your report):
- `actual_vs_predicted.png`
- `sentiment_vs_prediction.png` (shows fusion benefit)
- `rape_2026_top_districts.png`
- `tn_district_sentiment_heatmap.png` or similar

## Placeholder / Example Descriptions

**Screenshot 1: Main Menu**
```
CRIMECAST PROJECT
1. Run full pipeline (sentiment → clean + fusion → train → charts)
...
c. Quick combined crime + sentiment risk (Chennai example)
```

**Screenshot 2: Risk-Enhanced Prediction**
```
area  year  target_label              prediction  risk_index  risk_label
Chennai  2026  Cognizable crime rate...  1234.5      0.72        HIGH
```

**Screenshot 3: 2026 Report Summary**
```
Highest Risk District: Thiruvannamalai (19.1)  Risk: HIGH
...
COMBINED RISK (prediction volume + negative sentiment)
```

## How to Include in Report
- Place actual screenshots in your Word/PDF document.
- Caption them as "Figure X: [Description]".
- Reference in the partial report under "Results" and "User Interface" sections.

**Tip**: After running the full pipeline and option 7, the best screenshots will be in:
- `model_outputs/figures/`
- Console output from `app.py`

If you need me to generate placeholder images or more descriptions, let me know.
