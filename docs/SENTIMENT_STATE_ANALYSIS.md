# State/District-Wise Sentiment Analysis Guide

## Overview

Analyze sentiment data broken down by state/district to identify regional patterns in crime sentiment, public concern levels, and sentiment distribution across different areas.

## Features

### 1. **State-Wise Reports**
- Individual sentiment reports for each state/district
- Customized metrics per location
- Source-wise sentiment breakdown
- Crime type analysis by region

### 2. **Comparison Metrics**
- Sentiment distribution comparison across states
- Average polarity rankings
- Crime intensity by state
- Positive/Negative/Neutral percentages

### 3. **Visualizations**
- State sentiment distribution charts
- Crime intensity rankings by state
- Heatmap comparison of all metrics
- Multi-state overview

### 4. **Automated Reports**
- Individual state reports (TXT files)
- Summary comparison table (CSV)
- Overall state summary (TXT)

---

## Quick Start

### Option 1: Interactive Menu
```bash
python app.py
# Choose: 5. Sentiment analysis by state/district
```

### Option 2: Direct Command
```bash
python sentiment_by_state.py
```

### Option 3: With Visualizations
```bash
python sentiment_visualize_states.py
```

---

## Output Structure

### Directory: `model_outputs/state_sentiment_reports/`

```
state_sentiment_reports/
├── state_summary.txt              # Overall summary across all states
├── state_comparison.csv           # Comparison table
├── delhi_sentiment.txt            # Individual state report
├── mumbai_sentiment.txt
├── chennai_sentiment.txt
└── bangalore_sentiment.txt
```

### Files Generated

| File | Content |
|------|---------|
| `state_summary.txt` | Summary for all states with key metrics |
| `state_comparison.csv` | Spreadsheet comparison (open in Excel) |
| `{state}_sentiment.txt` | Detailed report for each state |

---

## Report Examples

### State Summary (state_summary.txt)
```
================================================================================
STATE/DISTRICT-WISE SENTIMENT ANALYSIS
================================================================================

DELHI
--------------------------------------------------------------------------------
  Total Records: 2
  Sentiment Distribution:
    Negative: 1 (50.0%)
    Neutral: 1 (50.0%)
  Average Polarity: -0.245
  Average Subjectivity: 0.715
  Average Crime Intensity: 7.50
  Records with Crime: 2/2

MUMBAI
--------------------------------------------------------------------------------
  Total Records: 2
  Sentiment Distribution:
    Positive: 2 (100.0%)
  Average Polarity: 0.658
  Average Subjectivity: 0.412
  Average Crime Intensity: 5.50
  Records with Crime: 1/2

CHENNAI
--------------------------------------------------------------------------------
  Total Records: 3
  Sentiment Distribution:
    Negative: 2 (66.7%)
    Positive: 1 (33.3%)
  Average Polarity: -0.223
  Average Subjectivity: 0.689
  Average Crime Intensity: 6.67
  Records with Crime: 3/3

BANGALORE
--------------------------------------------------------------------------------
  Total Records: 2
  Sentiment Distribution:
    Negative: 2 (100.0%)
  Average Polarity: -0.645
  Average Subjectivity: 0.723
  Average Crime Intensity: 6.00
  Records with Crime: 2/2
```

### State Comparison (state_comparison.csv)
```
State/District,Total Records,Positive %,Negative %,Neutral %,Avg Polarity,Avg Intensity,Max Intensity
Delhi,2,0.0,50.0,50.0,-0.245,7.50,8
Mumbai,2,100.0,0.0,0.0,0.658,5.50,7
Chennai,3,33.3,66.7,0.0,-0.223,6.67,10
Bangalore,2,0.0,100.0,0.0,-0.645,6.00,7
```

### Individual State Report ({state}_sentiment.txt)
```
======================================================================
SENTIMENT ANALYSIS: DELHI
======================================================================

Total Records: 2

SENTIMENT DISTRIBUTION:
  Negative: 1 (50.0%)
  Neutral: 1 (50.0%)

DETAILED METRICS:
  Average Polarity: -0.245
  Average Subjectivity: 0.715
  Average Confidence: 0.432
  Average Crime Intensity: 7.50
  Max Crime Intensity: 8

SOURCE DISTRIBUTION:
  social_media: 1 (50.0%)
  news: 1 (50.0%)

TOP CRIME TYPES:
  assault: 1
  harassment: 1

SENTIMENT BY SOURCE:
  social_media: {'negative': 1} | Avg Intensity: 8.0
  news: {'neutral': 1} | Avg Intensity: 7.0
```

---

## Key Metrics Explained

### Sentiment Distribution %
- **Positive %**: Percentage of records with positive sentiment
- **Negative %**: Percentage of records with negative sentiment
- **Neutral %**: Percentage of records with neutral sentiment

### Average Polarity
- **-1.0 to 0**: Negative region (people concerned/afraid)
- **0.0**: Neutral
- **0 to 1.0**: Positive region (people feel safe)

### Average Crime Intensity
- **0-3**: Low concern
- **4-6**: Moderate concern
- **7-10**: High concern

### Sentiment by Source
Shows how different data sources (complaints, news, social media) perceive sentiment in each state.

---

## Usage Examples

### Example 1: Quick Analysis
```bash
python sentiment_by_state.py
```
**Output**: State reports, comparison table, and summary

### Example 2: With Visualizations
```bash
python sentiment_visualize_states.py
```
**Output**: Charts saved to `model_outputs/figures/`

### Example 3: Full Pipeline with State Analysis
```bash
python app.py
# Choose option 5
```

### Example 4: Custom Comparison
Edit `sentiment_by_state.py` and call:
```python
from sentiment_by_state import get_state_comparison
comparison_df = get_state_comparison()
print(comparison_df)
```

---

## Visualizations Generated

### 1. Sentiment by State (`sentiment_by_state.png`)
Bar charts showing sentiment distribution for top 4 states

### 2. Crime Intensity by State (`crime_intensity_by_state.png`)
Ranked bar chart of average crime intensity per state

### 3. State Comparison Heatmap (`state_sentiment_heatmap.png`)
Heatmap showing all metrics compared across states

---

## Interpreting Results

### High Positive Sentiment State
- Low crime intensity
- Safe feeling
- Confident in law enforcement
- Example: Mumbai (100% positive)

### High Negative Sentiment State
- High crime intensity
- Fear/concern present
- People report danger
- Example: Bangalore (100% negative)

### Mixed Sentiment State
- Balanced positive and negative
- Some areas safe, others not
- Varying public opinion
- Example: Chennai (67% negative, 33% positive)

---

## Analysis Tips

1. **Identify Problem Areas**: States with high negative sentiment and high crime intensity need attention

2. **Compare Trends**: Use state_comparison.csv to rank states by safety perception

3. **Source Analysis**: Check which data sources (complaints vs news) are most negative

4. **Regional Patterns**: Look for regional clusters of negative sentiment

5. **Action Planning**: High negative + high intensity = priority for law enforcement

---

## Customization

### Add Custom Analysis
Edit `sentiment_by_state.py`:
```python
# Add custom metric
for state, group in df.groupby("district_city"):
    custom_metric = group["crime_intensity"].std()  # Standard deviation
    results[state]["intensity_variance"] = custom_metric
```

### Change State Grouping
Currently groups by `district_city`. To group differently:
```python
# Change this line:
for state, group in df.groupby("district_city"):
    # To:
for state, group in df.groupby("year"):  # Or any other column
```

### Filter Specific States
```python
df_filtered = df[df["district_city"].isin(["Delhi", "Mumbai"])]
# Then analyze filtered data
```

---

## Troubleshooting

### Error: "district_city column not found"
- Ensure sentiment_text_template.csv has the `district_city` column
- Check for typos in column names

### Error: "No sentiment data found"
- Run sentiment analysis first: `python sentiment_analysis.py`
- Ensure sentiment_scores.csv exists

### Empty state reports
- Data may not have records for all states
- Only states with records will have reports

### Charts not generating
- Ensure matplotlib is installed: `pip install matplotlib`
- Check file permissions in model_outputs/figures/

---

## Integration with CRIMECAST

Works with the full pipeline:

```bash
python app.py --full
# Then:
python app.py
# Choose: 5. Sentiment analysis by state/district
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `sentiment_by_state.py` | State-wise sentiment analysis |
| `sentiment_visualize_states.py` | State comparison visualizations |
| `sentiment_analysis.py` | Overall sentiment (prerequisite) |
| `app.py` | Interactive menu (menu option 5) |

---

## Next Steps

1. **Run Overall Sentiment**: `python sentiment_analysis.py`
2. **Analyze by State**: `python sentiment_by_state.py`
3. **Create Visualizations**: `python sentiment_visualize_states.py`
4. **Review Reports**: Open files in `model_outputs/state_sentiment_reports/`
5. **Compare Metrics**: Open `state_comparison.csv` in Excel
6. **Plan Actions**: Identify high-priority states for intervention
