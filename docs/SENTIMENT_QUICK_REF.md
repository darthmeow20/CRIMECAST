# 🎯 CRIMECAST Sentiment Analysis - Quick Reference

## What's New?

✨ **Enhanced sentiment analysis** with multi-method scoring, crime detection, and automated reporting.

---

## 🚀 Quick Start (3 Steps)

### 1️⃣ Add Text Data
Edit: `dataset/cleaned/sentiment_text_template.csv`
```csv
record_id,year,district_city,source,text
1,2023,Chennai,complaint,We are afraid of violence here.
2,2023,Mumbai,news,Police resolved the murder case!
```

### 2️⃣ Run Analysis
```bash
python sentiment_analysis.py
```

### 3️⃣ View Results
- **Scores**: `model_outputs/sentiment_scores.csv` (all metrics)
- **Report**: `model_outputs/sentiment_report.txt` (summary)

---

## 📊 Output Columns

| Column | Meaning | Range |
|--------|---------|-------|
| `sentiment_label` | positive/negative/neutral | — |
| `sentiment_score` | keyword-based score | -N to +N |
| `polarity` | TextBlob sentiment | -1.0 to 1.0 |
| `subjectivity` | opinion vs fact | 0.0 to 1.0 |
| `crime_types` | detected crimes | text |
| `crime_intensity` | severity score | 0-10 |
| `confidence` | assessment confidence | 0.0 to 1.0 |

---

## 💬 Sentiment Interpretation

| Label | Meaning | Polarity | Typical Words |
|-------|---------|----------|----------------|
| **Positive** | Good, safe, supportive | > 0 | safe, justice, resolved, protected |
| **Negative** | Bad, dangerous, fearful | < 0 | afraid, violence, crime, danger |
| **Neutral** | Balanced or no sentiment | ≈ 0 | report, data, statistics |

---

## 🔴 Crime Intensity Scale

| Score | Category | Examples |
|-------|----------|----------|
| **10** | Most Severe | Murder, Rape, Homicide |
| **9** | Severe | Violence |
| **8** | Serious | Assault |
| **7** | Major | Robbery, Burglary |
| **6** | Moderate | Harassment |
| **5** | Minor | Theft, Fraud |
| **0** | None | No crime keywords |

---

## 🔧 Commands

### Analyze with Default Settings
```bash
python sentiment_analysis.py
```

### Custom Input File
```bash
python sentiment_analysis.py \
  --input-file path/to/data.csv \
  --text-column text_column_name
```

### From Console App
```bash
python app.py
# Choose: 4. Run sentiment scoring
```

### Full Pipeline (Clean + Train + Visualize + Sentiment)
```bash
python app.py --full
```

---

## 📈 Report Example

```
SENTIMENT ANALYSIS REPORT

Total Records: 10

SENTIMENT DISTRIBUTION:
  Negative: 5 (50.0%)
  Positive: 3 (30.0%)
  Neutral: 2 (20.0%)

SENTIMENT METRICS:
  Average Polarity: -0.245
  Average Subjectivity: 0.715
  Average Confidence: 0.432

CRIME ANALYSIS:
  Average Crime Intensity: 6.50
  Max Crime Intensity: 10
  Records with Crime Keywords: 8 (80.0%)
```

---

## 📚 Files Reference

| File | Purpose | Location |
|------|---------|----------|
| `sentiment_analysis.py` | Main analysis module | Root |
| `sentiment_visualize.py` | Visualization (optional) | Root |
| `SENTIMENT_GUIDE.md` | Full documentation | `docs/` |
| `sentiment_text_template.csv` | Input data template | `dataset/cleaned/` |
| `sentiment_scores.csv` | Detailed results | `model_outputs/` |
| `sentiment_report.txt` | Summary report | `model_outputs/` |

---

## ✅ Checklist

- ✅ Enhanced sentiment analysis module
- ✅ Multi-method scoring (lexicon + TextBlob)
- ✅ Crime detection & intensity scoring
- ✅ Automated report generation
- ✅ Sample data with 10 records
- ✅ Visualization module (optional)
- ✅ Fixed requirements.txt
- ✅ Comprehensive documentation

---

## 🎓 Key Concepts

### Polarity
- **-1.0** = Most negative (very bad)
- **0.0** = Neutral (balanced)
- **1.0** = Most positive (very good)

### Subjectivity
- **0.0** = Objective (factual, measurable)
- **1.0** = Subjective (opinion-based)

### Crime Intensity
- Automatically calculated from detected crime keywords
- Higher score = more severe crime
- 0 = No crime keywords found

### Confidence
- Measure of sentiment assessment reliability
- Based on TextBlob polarity and subjectivity
- Higher = more confident prediction

---

## 🆘 Troubleshooting

### Error: "Text input file not found"
→ Create `sentiment_text_template.csv` with sample data

### Error: "No text rows found"
→ Add data rows to the CSV file (at least 1 record)

### Error: Missing TextBlob/NLTK
→ Install: `pip install textblob nltk`

### Unexpected sentiment labels
→ Review your text for positive/negative keywords
→ Check `POSITIVE_WORDS`/`NEGATIVE_WORDS` sets

---

## 📖 Learn More

See **SENTIMENT_GUIDE.md** for:
- Detailed feature explanations
- Input/output formats
- Complete keyword lists
- Best practices
- Advanced customization
