# DistilBERT Sentiment Analysis Integration

## Overview
The CRIMECAST project now uses **DistilBERT** for advanced sentiment analysis. DistilBERT is a faster, lighter version of BERT (Bidirectional Encoder Representations from Transformers) that provides superior accuracy compared to TextBlob while maintaining reasonable inference speed.

## What is DistilBERT?
- **Model**: `distilbert-base-uncased-finetuned-sst-2-english`
- **Purpose**: Multi-class sentiment classification (POSITIVE/NEGATIVE)
- **Size**: ~268MB (smaller than BERT)
- **Speed**: ~2x faster than BERT
- **Accuracy**: Comparable to BERT on sentiment tasks
- **Training Data**: Fine-tuned on Stanford Sentiment Treebank v2 (SST-2)

## Key Improvements Over TextBlob

### 1. **Transformer-Based Context Understanding**
- TextBlob: Lexicon-based, doesn't understand context
- DistilBERT: Deep neural network understands word relationships and context

**Example**:
- Text: "I love the quick response but hate the slow investigation"
- TextBlob: May miss nuance (counts both positive/negative words)
- DistilBERT: Understands the contradictory sentiment structure

### 2. **Numerical Representation**
- TextBlob polarity: -1.0 to +1.0 (coarse-grained)
- DistilBERT confidence: 0.0 to 1.0 (fine-grained probability)

**Example**:
```
TextBlob: polarity=0.5, subjectivity=0.6
DistilBERT: polarity=0.87 (POSITIVE), confidence=0.95
```

### 3. **Reduced False Positives/Negatives**
- Handles negation better: "not good" vs "good"
- Understands intensifiers: "very bad" vs "bad"
- Recognizes sarcasm patterns (when trained on such data)

## Installation

### Step 1: Update Requirements
The `requirements.txt` file has been updated with:
```
transformers==4.40.0
torch==2.1.0
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

**Note**: First run will download the DistilBERT model (~268MB). This happens automatically when you run sentiment analysis.

### Step 3: Verify Installation
```bash
python -c "from transformers import pipeline; print('DistilBERT installed successfully!')"
```

## Usage

### Interactive Menu
```bash
python app.py
# Choose option 4: Run sentiment scoring
```

### Command-Line
```bash
python sentiment_analysis.py --input-file dataset/my_crimes.csv
```

### Python Script
```python
from sentiment_analysis import analyze_sentiment

result = analyze_sentiment()
print(f"Rows scored: {result['rows']}")
print(f"Method: DistilBERT (or fallback method if not available)")
```

## Output Format

### CSV Output (sentiment_scores.csv)
```
text,sentiment_score,positive_terms,negative_terms,sentiment_label,polarity,subjectivity,crime_types,crime_intensity,confidence
"Crime rate high in...",−2,1,3,negative,−0.985,0.5,robbery; theft,7,0.985
"Police response was...",3,4,1,positive,0.972,0.5,none,0,0.972
```

### Report Output (sentiment_report.txt)
```
SENTIMENT METRICS:
  Sentiment Method: DistilBERT
  Average Polarity: 0.145
  Average Subjectivity: 0.500
  Average Confidence: 0.896
```

## Fallback Hierarchy

The system automatically falls back if DistilBERT is unavailable:

1. **DistilBERT** (Primary) → Transformer-based, most accurate
2. **TextBlob** (Secondary) → Lexicon-based, ~70% accuracy
3. **Lexicon-Only** (Tertiary) → Custom word lists, basic accuracy

```python
if HAS_DISTILBERT:
    # Use DistilBERT pipeline
    result = pipeline("sentiment-analysis")(text)
elif HAS_TEXTBLOB:
    # Use TextBlob
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
else:
    # Use custom lexicon
    polarity = custom_score * 0.1
```

## Performance Characteristics

### Speed
- **First run**: ~5-10 seconds (model download + cache)
- **Subsequent runs**: ~0.1-0.2 seconds per record
- **Batch of 1000**: ~2-3 minutes

### Memory Usage
- **Model size**: ~268MB (on disk)
- **Runtime memory**: ~500MB-1GB during inference
- **Batch processing**: Handles texts up to 512 tokens (≈2000 words)

### Accuracy Metrics (SST-2 Benchmark)
- **Accuracy**: 91.3% (DistilBERT vs 94.9% BERT)
- **Precision**: ~91%
- **Recall**: ~91%

## Crime-Specific Tuning

The sentiment analysis combines DistilBERT with crime-specific features:

### Crime Intensity Score (0-10)
```python
CRIME_INTENSITY = {
    "murder": 10,      # Highest severity
    "rape": 10,
    "homicide": 9,
    "assault": 8,
    "robbery": 7,
    "harassment": 6,
    "theft": 5,
    "fraud": 5,
    "burglary": 7,
    "violence": 9,
}
```

### Combined Scoring Example
```
Input: "Murder suspects arrested in 2 hours"
DistilBERT: POSITIVE (confidence=0.92, polarity=0.92)
Crime Type: murder
Crime Intensity: 10
Combined Output:
  - sentiment_label: positive
  - polarity: 0.92
  - crime_intensity: 10
  - confidence: 0.92
```

## Troubleshooting

### Issue: "transformers module not found"
```bash
pip install transformers torch
# Or reinstall all requirements
pip install -r requirements.txt
```

### Issue: "CUDA out of memory"
The system automatically uses CPU. If you have GPU and want to enable:
```python
pipe = pipeline("sentiment-analysis", model="...", device=0)  # device 0 = first GPU
```

### Issue: Slow Performance
- First run downloads the model (~5 minutes)
- Subsequent runs are faster (~0.1s per record)
- Consider batch processing for large datasets

### Issue: Different Scores Than Before
This is expected! DistilBERT is more accurate than TextBlob:
- More nuanced understanding of context
- Better handling of negation and intensifiers
- May differ on ambiguous texts

## Comparing Methods

To compare sentiment methods on a dataset:

```python
# sentiment_analysis.py includes logic to automatically choose the best available method
# DistilBERT > TextBlob > Lexicon-based

# Check which method was used in your report
cat model_outputs/sentiment_report.txt | grep "Sentiment Method"
```

## Tamil Nadu District Analysis with DistilBERT

When running district-level analysis, DistilBERT will automatically be used:

```bash
python app.py --tn-district
# Reports will show "Sentiment Method: DistilBERT"
```

## Advanced Configuration

### Using Different DistilBERT Models
You can modify `sentiment_analysis.py` to use other models:

```python
# In get_distilbert_pipeline():
# Current: "distilbert-base-uncased-finetuned-sst-2-english"

# Alternative options:
# "distilbert-base-multilingual-uncased-distilled-sst-2-all-langs" (multilingual)
# "distilbert-base-uncased" (base model, requires fine-tuning)
```

### Batch Processing for Large Datasets
```python
# Process texts in batches for efficiency
def score_batch(texts, batch_size=32):
    pipe = pipeline("sentiment-analysis")
    results = pipe(texts, batch_size=batch_size)
    return results
```

## Model Details

| Aspect | Details |
|--------|---------|
| Model Name | distilbert-base-uncased-finetuned-sst-2-english |
| Model Type | Distilled BERT (6 layers instead of 12) |
| Vocabulary | 30,522 tokens |
| Parameters | ~67M (vs 110M for BERT) |
| Training Data | SST-2 (Stanford Sentiment Treebank) |
| Fine-tuned For | Binary sentiment classification |
| Output Classes | POSITIVE, NEGATIVE |
| Max Sequence Length | 512 tokens |

## References

- **DistilBERT Paper**: "DistilBERT, a distilled version of BERT" (Sanh et al., 2019)
- **Model Card**: https://huggingface.co/distilbert-base-uncased-finetuned-sst-2-english
- **Hugging Face Transformers**: https://huggingface.co/transformers/

## Quick Reference

| Task | Command |
|------|---------|
| Run sentiment analysis | `python sentiment_analysis.py` |
| Use in app menu | `python app.py` → Select option 4 |
| Tamil Nadu districts | `python app.py --tn-district` |
| Check method used | `grep "Sentiment Method" model_outputs/sentiment_report.txt` |
| Install dependencies | `pip install -r requirements.txt` |

---

**Updated**: 2024
**Model**: DistilBERT (distilbert-base-uncased-finetuned-sst-2-english)
**Status**: Active
