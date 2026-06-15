# CRIMECAST Sentiment Analysis Guide

## Overview

The enhanced sentiment analysis module analyzes text data from crime-related sources (complaints, news, social media) to extract sentiment insights and crime-related information.

## Features

### 1. **Multi-Method Sentiment Scoring**
- **Custom Lexicon-Based**: Matches against crime-specific positive/negative word lists
- **TextBlob Polarity**: -1 (most negative) to 1 (most positive)
- **Subjectivity Scoring**: 0 (objective) to 1 (subjective)
- **Confidence Metrics**: Measures reliability of sentiment assessment

### 2. **Crime-Specific Analysis**
- **Crime Type Extraction**: Identifies crime keywords (murder, robbery, assault, theft, etc.)
- **Crime Intensity Scoring**: 
  - Murder/Rape: 10 (most severe)
  - Homicide: 9
  - Assault: 8
  - Robbery/Burglary: 7
  - Harassment: 6
  - Theft/Fraud: 5

### 3. **Output Metrics**
Each record produces:
- `sentiment_score`: Custom keyword-based score
- `sentiment_label`: positive/negative/neutral
- `polarity`: TextBlob polarity (-1 to 1)
- `subjectivity`: TextBlob subjectivity (0 to 1)
- `crime_types`: Detected crime keywords
- `crime_intensity`: Severity score (0-10)
- `confidence`: Confidence in sentiment assessment (0-1)

## Usage

### Run Sentiment Analysis
```bash
python sentiment_analysis.py
```

### With Custom Input/Output Files
```bash
python sentiment_analysis.py \
  --input-file path/to/text_data.csv \
  --output-file path/to/output.csv \
  --text-column your_text_column_name
```

### From the Console App
1. Run: `python app.py`
2. Choose option **4. Run sentiment scoring**

## Input Data Format

Required CSV with at least a `text` column:

```csv
record_id,year,district_city,source,text
1,2023,Chennai,complaint,"We are afraid of violence here. Need police support."
2,2023,Mumbai,news,"Police arrested murder suspects. Justice served!"
3,2023,Delhi,social_media,"Assault cases increasing. People feel unsafe."
```

### Column Details
- `record_id`: Unique identifier (optional)
- `year`: Year of record (optional)
- `district_city`: Area name (optional)
- `source`: Data source type - complaint/news/social_media (optional)
- `text`: **Required** - The text to analyze

## Output Files

### 1. **sentiment_scores.csv**
Complete scored dataset with all metrics:
```
record_id,year,district_city,source,text,sentiment_score,positive_terms,...,confidence
```

### 2. **sentiment_report.txt**
Summary statistics and insights:
```
======================================================================
SENTIMENT ANALYSIS REPORT
======================================================================

Total Records Analyzed: 10

SENTIMENT DISTRIBUTION:
  Negative: 5 (50.0%)
  Positive: 3 (30.0%)
  Neutral: 2 (20.0%)

SENTIMENT METRICS:
  Average Polarity (TextBlob): -0.245
  Average Subjectivity: 0.715
  Average Confidence: 0.432

CRIME ANALYSIS:
  Average Crime Intensity: 6.50
  Max Crime Intensity: 10
  Records with Crime Keywords: 8 (80.0%)

TOP CRIME TYPES MENTIONED:
  violence: 4
  robbery: 3
  murder: 2
```

## Keyword Lists

### Positive Words
- safe, safer, helpful, quick, resolved, protected, support
- calm, secure, improved, peace, justice, trusted, responsive
- arrested, caught, patrolling, vigilant

### Negative Words
- afraid, angry, attack, crime, danger, dangerous, delay
- fear, fraud, harassed, harassment, hate, hurt, murder, panic
- rape, robbery, stolen, unsafe, violence, violent, worried
- assaulted, threatened, abused, suspicious, gunshot, stabbed, missing

### Crime Types (with Intensity 0-10)
- murder: 10, rape: 10
- homicide: 9, violence: 9
- assault: 8
- robbery: 7, burglary: 7
- harassment: 6
- theft: 5, fraud: 5

## Example Workflow

### Step 1: Prepare Text Data
Add rows to `dataset/cleaned/sentiment_text_template.csv`:
```csv
record_id,year,district_city,source,text
1,2023,Chennai,complaint,Violence in our area makes people feel unsafe and afraid.
2,2023,Mumbai,news,Police quickly resolved the murder case. Justice served!
```

### Step 2: Run Analysis
```bash
python sentiment_analysis.py
```

### Step 3: Review Results
- Check `model_outputs/sentiment_scores.csv` for detailed scores
- Read `model_outputs/sentiment_report.txt` for summary

## Interpreting Metrics

### Sentiment Score (Custom Lexicon)
- **Positive (>0)**: More positive words than negative
- **Negative (<0)**: More negative words than positive
- **Neutral (0)**: Equal or no sentiment words

### Polarity (TextBlob)
- **Range**: -1.0 to 1.0
- **-1.0**: Most negative
- **0.0**: Neutral
- **1.0**: Most positive

### Subjectivity (TextBlob)
- **Range**: 0.0 to 1.0
- **0.0**: Objective (factual)
- **1.0**: Subjective (opinion-based)

### Crime Intensity
- **0**: No crime keywords
- **1-5**: Minor crimes (theft, fraud)
- **6-8**: Serious crimes (assault, harassment, robbery)
- **9-10**: Severe crimes (murder, rape, homicide, violence)

## Tips & Best Practices

1. **Data Quality**: Longer, more descriptive text yields better analysis
2. **Mixed Sources**: Include complaints, news, and social media for diverse perspectives
3. **Regular Updates**: Rerun analysis as new text data arrives
4. **Customization**: Modify `POSITIVE_WORDS`, `NEGATIVE_WORDS`, `CRIME_INTENSITY` in the code
5. **Context**: Review original text alongside scores for accuracy

## Integration with Pipeline

The sentiment analysis is part of the full CRIMECAST pipeline:

```bash
python app.py --full  # Runs data cleaning, ML training, visualization, AND sentiment analysis
```

## Troubleshooting

### "No text rows found" error
- Ensure `sentiment_text_template.csv` has data
- Verify the text column contains actual content

### Missing dependencies
- Install: `pip install textblob nltk`
- Download NLTK data: `python -m textblob.download_corpora`

### Unexpected sentiment labels
- Review the POSITIVE_WORDS and NEGATIVE_WORDS sets
- Consider adding domain-specific keywords
- Check TextBlob's polarity for additional context
