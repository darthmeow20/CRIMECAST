from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from clean_data import DEFAULT_OUTPUT_DIR
from train_model import OUTPUT_DIR

try:
    from transformers import pipeline
    HAS_DISTILBERT = True
except ImportError:
    HAS_DISTILBERT = False
    print("Warning: transformers not installed. Install with: pip install transformers torch")

try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False


DEFAULT_INPUT_FILE = DEFAULT_OUTPUT_DIR / "sentiment_text_template.csv"
DEFAULT_OUTPUT_FILE = OUTPUT_DIR / "sentiment_scores.csv"
SENTIMENT_REPORT = OUTPUT_DIR / "sentiment_report.txt"

POSITIVE_WORDS = {
    "safe",
    "safer",
    "helpful",
    "quick",
    "resolved",
    "protected",
    "support",
    "supported",
    "calm",
    "secure",
    "improved",
    "peace",
    "justice",
    "trusted",
    "responsive",
    "justice served",
    "arrested",
    "caught",
    "patrolling",
    "vigilant",
}

NEGATIVE_WORDS = {
    "afraid",
    "angry",
    "attack",
    "crime",
    "danger",
    "dangerous",
    "delay",
    "fear",
    "fraud",
    "harassed",
    "harassment",
    "hate",
    "hurt",
    "murder",
    "panic",
    "rape",
    "robbery",
    "stolen",
    "unsafe",
    "violence",
    "violent",
    "worried",
    "assaulted",
    "threatened",
    "abused",
    "suspicious",
    "gunshot",
    "stabbed",
    "missing",
}

CRIME_INTENSITY = {
    "murder": 10,
    "rape": 10,
    "homicide": 9,
    "assault": 8,
    "robbery": 7,
    "theft": 5,
    "harassment": 6,
    "fraud": 5,
    "burglary": 7,
    "violence": 9,
}


def tokenize(text: object) -> list[str]:
    return re.findall(r"[a-z]+", str(text).lower())


def extract_crime_types(text: object) -> list[str]:
    """Extract crime-specific keywords from text."""
    text_lower = str(text).lower()
    found_crimes = [crime for crime in CRIME_INTENSITY if crime in text_lower]
    return found_crimes


def calculate_crime_intensity(text: object) -> int:
    """Calculate crime intensity based on keywords found."""
    crimes = extract_crime_types(text)
    if crimes:
        return max(CRIME_INTENSITY.get(crime, 0) for crime in crimes)
    return 0


def get_distilbert_pipeline():
    """Initialize DistilBERT sentiment pipeline once."""
    if not hasattr(get_distilbert_pipeline, 'pipe'):
        get_distilbert_pipeline.pipe = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
    return get_distilbert_pipeline.pipe


def score_text(text: object) -> dict[str, object]:
    """Score text using DistilBERT with fallback methods."""
    text_str = str(text)
    tokens = tokenize(text_str)
    
    positive_count = sum(token in POSITIVE_WORDS for token in tokens)
    negative_count = sum(token in NEGATIVE_WORDS for token in tokens)
    custom_score = positive_count - negative_count

    polarity = 0.0
    subjectivity = 0.5
    label = "neutral"
    confidence = 0.0
    
    if HAS_DISTILBERT:
        try:
            pipe = get_distilbert_pipeline()
            result = pipe(text_str[:512])[0]
            
            if result['label'] == 'POSITIVE':
                polarity = result['score']
                label = "positive"
            else:
                polarity = -result['score']
                label = "negative"
            
            confidence = result['score']
        except Exception as e:
            print(f"[WARNING] DistilBERT failed: {e}. Using fallback.")
            polarity = min(1.0, max(-1.0, custom_score * 0.1))
            confidence = abs(polarity) if polarity != 0 else 0.5
    elif HAS_TEXTBLOB:
        blob = TextBlob(text_str)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        confidence = abs(polarity) if polarity != 0 else (1 - subjectivity)
        
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
    else:
        polarity = min(1.0, max(-1.0, custom_score * 0.1))
        confidence = abs(polarity) if polarity != 0 else 0.5
    
    crimes = extract_crime_types(text_str)
    intensity = calculate_crime_intensity(text_str)
    
    return {
        "sentiment_score": custom_score,
        "positive_terms": positive_count,
        "negative_terms": negative_count,
        "sentiment_label": label,
        "polarity": round(polarity, 3),
        "subjectivity": round(subjectivity, 3),
        "crime_types": "; ".join(crimes) if crimes else "none",
        "crime_intensity": intensity,
        "confidence": round(confidence, 3),
    }


def analyze_sentiment(
    input_file: Path = DEFAULT_INPUT_FILE,
    output_file: Path = DEFAULT_OUTPUT_FILE,
    text_column: str = "text",
) -> dict[str, object]:
    if not input_file.exists():
        raise FileNotFoundError(f"Text input file was not found: {input_file}")

    df = pd.read_csv(input_file)
    if text_column not in df.columns:
        raise ValueError(f"Input file must contain a '{text_column}' column")

    if df.empty:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.assign(
            sentiment_score=pd.Series(dtype="int64"),
            positive_terms=pd.Series(dtype="int64"),
            negative_terms=pd.Series(dtype="int64"),
            sentiment_label=pd.Series(dtype="string"),
            polarity=pd.Series(dtype="float64"),
            subjectivity=pd.Series(dtype="float64"),
            crime_types=pd.Series(dtype="string"),
            crime_intensity=pd.Series(dtype="int64"),
            confidence=pd.Series(dtype="float64"),
        ).to_csv(output_file, index=False)
        return {
            "rows": 0,
            "output_file": output_file,
            "message": "No text rows found. Add complaint/news/social text rows before sentiment analysis.",
        }

    scores = pd.DataFrame([score_text(text) for text in df[text_column]])
    scored = pd.concat([df.reset_index(drop=True), scores], axis=1)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(output_file, index=False)

    generate_sentiment_report(scored)

    return {
        "rows": len(scored),
        "output_file": output_file,
        "label_counts": scored["sentiment_label"].value_counts().to_dict(),
        "avg_polarity": round(scored["polarity"].mean(), 3),
        "avg_crime_intensity": round(scored["crime_intensity"].mean(), 2),
        "report": SENTIMENT_REPORT,
    }


def generate_sentiment_report(df: pd.DataFrame) -> None:
    """Generate a sentiment analysis report."""
    report_lines = ["=" * 70, "SENTIMENT ANALYSIS REPORT", "=" * 70, ""]

    report_lines.append(f"Total Records Analyzed: {len(df)}")
    report_lines.append("")

    report_lines.append("SENTIMENT DISTRIBUTION:")
    for label, count in df["sentiment_label"].value_counts().items():
        percentage = (count / len(df)) * 100
        report_lines.append(f"  {label.capitalize()}: {count} ({percentage:.1f}%)")
    report_lines.append("")

    report_lines.append("SENTIMENT METRICS:")
    method = "DistilBERT" if HAS_DISTILBERT else ("TextBlob" if HAS_TEXTBLOB else "Lexicon-based")
    report_lines.append(f"  Sentiment Method: {method}")
    report_lines.append(f"  Average Polarity: {df['polarity'].mean():.3f}")
    report_lines.append(f"  Average Subjectivity: {df['subjectivity'].mean():.3f}")
    report_lines.append(f"  Average Confidence: {df['confidence'].mean():.3f}")
    report_lines.append("")

    report_lines.append("CRIME ANALYSIS:")
    report_lines.append(f"  Average Crime Intensity: {df['crime_intensity'].mean():.2f}")
    report_lines.append(f"  Max Crime Intensity: {df['crime_intensity'].max()}")
    crime_counts = df[df["crime_intensity"] > 0].shape[0]
    report_lines.append(f"  Records with Crime Keywords: {crime_counts} ({(crime_counts/len(df))*100:.1f}%)")
    report_lines.append("")

    top_crimes = df[df["crime_types"] != "none"]["crime_types"].value_counts().head(5)
    if not top_crimes.empty:
        report_lines.append("TOP CRIME TYPES MENTIONED:")
        for crime, count in top_crimes.items():
            report_lines.append(f"  {crime}: {count}")
        report_lines.append("")

    report_lines.append("=" * 70)

    SENTIMENT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(SENTIMENT_REPORT, "w") as f:
        f.write("\n".join(report_lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score sentiment for complaint/news/social text records.")
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT_FILE)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--text-column", default="text")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = analyze_sentiment(args.input_file, args.output_file, args.text_column)
    print(f"Rows scored: {result['rows']}")
    print(f"Sentiment output: {result['output_file']}")
    if "message" in result:
        print(result["message"])
    if "label_counts" in result:
        print(f"Label counts: {result['label_counts']}")
    if "avg_polarity" in result:
        print(f"Average polarity: {result['avg_polarity']}")
        print(f"Average crime intensity: {result['avg_crime_intensity']}")
        print(f"Report generated: {result['report']}")


if __name__ == "__main__":
    main()
