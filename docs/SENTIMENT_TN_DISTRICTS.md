# Tamil Nadu District-Wise Sentiment Analysis

## Overview

Analyze sentiment data broken down by **Tamil Nadu districts** to identify regional patterns in crime sentiment, public concern levels, and sentiment distribution across different TN districts.

## Supported Tamil Nadu Districts

- **Chennai** - Metropolitan
- **Thiruvallur, Kanchipuram, Ranipet, Chengalpattu** - Chennai suburbs
- **Vellore, Tiruppattur** - Northern region
- **Tiruvannamalai, Kallakurichi** - Western region
- **Cuddalore, Villupuram** - Eastern region
- **Perambalur, Ariyalur** - Central region
- **Namakkal, Salem, Krishnagiri** - Northeast region
- **Dharmapuri** - Northwest region
- **Erode, Nilgiri, Coimbatore, Tiruppur** - Western region
- **Madurai, Theni, Dindigul** - Central region
- **Ramanathapuram, Sivaganga** - Southern region
- **Virudhunagar, Tuticorin, Tenkasi** - South-central region
- **Tirunelveli, Kanniyakumari** - Southern tip

## Features

### 1. **District-Wise Reports**
- Individual sentiment report for each TN district
- Customized metrics per district
- Source-wise sentiment breakdown
- Crime type analysis by district

### 2. **Comparison Analysis**
- Sentiment distribution across all TN districts
- Average polarity rankings
- Crime intensity by district
- Positive/Negative/Neutral percentages

### 3. **Visualizations**
- District sentiment distribution charts
- Crime intensity rankings (best to worst)
- Heatmap comparison of metrics
- Polarity distribution across districts

### 4. **Automated Reports**
- `tn_district_summary.txt` - Overall TN summary
- `tn_district_comparison.csv` - Excel-ready comparison
- Individual `tn_{district}_sentiment.txt` files

---

## Quick Start

### Option 1: Interactive Menu
```bash
python app.py
# Choose new option for TN district analysis
```

### Option 2: Direct Command
```bash
python sentiment_tn_districts.py
```

### Option 3: With Visualizations
```bash
python sentiment_visualize_tn_districts.py
```

---

## Output Structure

### Directory: `model_outputs/tn_district_sentiment_reports/`

```
tn_district_sentiment_reports/
├── tn_district_summary.txt              # Overall TN summary
├── tn_district_comparison.csv           # Comparison table
├── tn_chennai_sentiment.txt             # Chennai report
├── tn_madurai_sentiment.txt             # Madurai report
├── tn_coimbatore_sentiment.txt          # Coimbatore report
├── tn_salem_sentiment.txt               # Salem report
├── tn_erode_sentiment.txt               # Erode report
├── tn_vellore_sentiment.txt             # Vellore report
└── ... (other districts)
```

### Visualizations in `model_outputs/figures/`
- `tn_sentiment_by_district.png` - Grid of sentiment charts
- `tn_crime_intensity_ranking.png` - Ranked intensity chart
- `tn_district_sentiment_heatmap.png` - Comparison heatmap
- `tn_district_polarities.png` - Polarity distribution

---

## Report Examples

### TN District Summary (tn_district_summary.txt)
```
================================================================================
TAMIL NADU DISTRICT-WISE SENTIMENT ANALYSIS
================================================================================

Total Records Analyzed: 10 (from 3 districts)

KEY INSIGHTS:
  Highest Concern (Most Negative): Chennai
  Safest Feeling (Most Positive): Chennai
  Highest Crime Intensity: Chennai

CHENNAI
  Total Records: 5
  Sentiment Distribution:
    Negative: 3 (60.0%)
    Positive: 2 (40.0%)
  Average Polarity: -0.145
  Average Subjectivity: 0.689
  Average Crime Intensity: 6.40
  Records with Crime Keywords: 5/5

MADURAI
  Total Records: 3
  Sentiment Distribution:
    Neutral: 2 (66.7%)
    Positive: 1 (33.3%)
  Average Polarity: 0.156
  Average Subjectivity: 0.512
  Average Crime Intensity: 5.67
  Records with Crime Keywords: 2/3
```

### TN District Comparison (tn_district_comparison.csv)
```
District,Records,Positive %,Negative %,Neutral %,Avg Polarity,Avg Intensity,Max Intensity
Chennai,5,40.0,60.0,0.0,-0.145,6.40,10
Madurai,3,33.3,0.0,66.7,0.156,5.67,8
Coimbatore,2,50.0,50.0,0.0,-0.234,6.50,7
```

### Individual District Report (tn_chennai_sentiment.txt)
```
======================================================================
TAMIL NADU - CHENNAI
======================================================================

Total Records: 5

SENTIMENT DISTRIBUTION:
  Negative: 3 (60.0%)
  Positive: 2 (40.0%)

SENTIMENT METRICS:
  Average Polarity: -0.145
  Average Subjectivity: 0.689
  Average Confidence: 0.456
  Average Crime Intensity: 6.40
  Max Crime Intensity: 10

SOURCE DISTRIBUTION:
  complaint: 2 (40.0%)
  news: 2 (40.0%)
  social_media: 1 (20.0%)

CRIME TYPES DETECTED:
  violence: 2
  robbery: 2
  murder: 1

SENTIMENT BY SOURCE:
  complaint: {'negative': 2} | Avg Intensity: 7.50
  news: {'positive': 2} | Avg Intensity: 5.50
  social_media: {'negative': 1} | Avg Intensity: 6.00

SENTIMENT STATUS:
  ⚠ CONCERN - Negative sentiment, high concern
```

---

## Key Metrics

| Metric | Meaning | Range |
|--------|---------|-------|
| **Records** | Number of sentiment records | 1+ |
| **Positive %** | % with positive sentiment | 0-100 |
| **Negative %** | % with negative sentiment | 0-100 |
| **Neutral %** | % with neutral sentiment | 0-100 |
| **Avg Polarity** | Average sentiment polarity | -1.0 to 1.0 |
| **Avg Intensity** | Average crime intensity | 0-10 |
| **Max Intensity** | Highest crime intensity | 0-10 |

---

## Usage Examples

### Example 1: Basic Analysis
```bash
python sentiment_tn_districts.py
```
**Output**: TN district reports, comparison table, summary

### Example 2: With Visualizations
```bash
python sentiment_visualize_tn_districts.py
```
**Output**: Charts saved to `model_outputs/figures/`

### Example 3: Both (Recommended)
```bash
python sentiment_tn_districts.py
python sentiment_visualize_tn_districts.py
```

### Example 4: Interactive Menu
```bash
python app.py
# Select Tamil Nadu district analysis option
```

---

## Visualizations Explained

### 1. Sentiment by District (tn_sentiment_by_district.png)
Grid of bar charts showing sentiment distribution for each district
- Green bars = Positive
- Red bars = Negative
- Gray bars = Neutral

### 2. Crime Intensity Ranking (tn_crime_intensity_ranking.png)
Horizontal bar chart ranked by intensity (highest to lowest)
- Red bars (7-10) = High concern
- Orange bars (4-7) = Moderate concern
- Green bars (0-4) = Low concern

### 3. District Sentiment Heatmap (tn_district_sentiment_heatmap.png)
Heatmap showing all metrics normalized
- Red = Negative/High crime
- Yellow = Moderate
- Green = Positive/Low crime

### 4. Polarity Distribution (tn_district_polarities.png)
Shows which districts feel safest to residents
- Green bars = Positive polarity (feel safe)
- Red bars = Negative polarity (feel unsafe)

---

## Interpreting Results

### Safe Districts
- High positive sentiment (50%+)
- High polarity (+0.5 to +1.0)
- Low crime intensity (0-3)

### Concern Districts
- High negative sentiment (50%+)
- Low polarity (-0.5 to -1.0)
- High crime intensity (7-10)

### Mixed Districts
- Balanced sentiment
- Mixed polarity
- Moderate crime intensity

---

## Workflow

### Step 1: Run Overall Sentiment
```bash
python sentiment_analysis.py
```
Creates: `sentiment_scores.csv`

### Step 2: Analyze Tamil Nadu Districts
```bash
python sentiment_tn_districts.py
```
Creates: TN district reports in `tn_district_sentiment_reports/`

### Step 3: Generate Visualizations
```bash
python sentiment_visualize_tn_districts.py
```
Creates: Charts in `figures/`

### Step 4: Review and Analyze
- Open `tn_district_summary.txt` for overview
- Open `tn_district_comparison.csv` in Excel for comparison
- Read individual district `.txt` files for details
- View `.png` charts for quick visualization

---

## Customization

### Change Tamil Nadu Districts List
Edit `sentiment_tn_districts.py`:
```python
TAMIL_NADU_DISTRICTS = {
    "Chennai", "Madurai",  # Add/remove districts
    "Coimbatore",
}
```

### Focus on Specific Districts
```python
# Filter to specific districts
tn_df = df[df["district_city"].isin(["Chennai", "Madurai", "Coimbatore"])]
```

### Filter by Year
```python
# Analyze only 2023 data
tn_df = tn_df[tn_df["year"] == 2023]
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No Tamil Nadu data found" | Ensure sentiment_text_template.csv has TN districts |
| "No sentiment data" | Run `python sentiment_analysis.py` first |
| "district_city column error" | Add `district_city` column to input data |
| "Empty reports" | Check that records have `district_city` value |
| "Charts not rendering" | Install matplotlib: `pip install matplotlib` |

---

## Sample Commands

```bash
# Full TN analysis workflow
python sentiment_analysis.py                          # Step 1
python sentiment_tn_districts.py                      # Step 2
python sentiment_visualize_tn_districts.py            # Step 3

# Quick check
python sentiment_tn_districts.py | head -30

# Interactive exploration
python app.py
# Select TN district analysis
```

---

## Integration with CRIMECAST

Part of the complete CRIMECAST workflow:

```
Raw Data → Cleaning → ML Training → Prediction → Sentiment Analysis → TN District Analysis
```

Fully integrated into the interactive menu and pipeline automation.

---

## File Reference

| File | Purpose |
|------|---------|
| `sentiment_tn_districts.py` | Main TN district analysis |
| `sentiment_visualize_tn_districts.py` | TN visualizations |
| `app.py` | Interactive menu (updated with TN option) |
| `sentiment_analysis.py` | Overall sentiment (prerequisite) |

---

## Next Steps

1. **Prepare Data**: Ensure sentiment input has Tamil Nadu districts
2. **Run Analysis**: `python sentiment_tn_districts.py`
3. **Create Charts**: `python sentiment_visualize_tn_districts.py`
4. **Review Results**: Open reports in `tn_district_sentiment_reports/`
5. **Plan Actions**: Identify priority districts for intervention
6. **Track Changes**: Re-run periodically to monitor sentiment changes
