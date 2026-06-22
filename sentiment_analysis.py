from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

PROJECT_ROOT = Path(__file__).resolve().parent
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

from clean_data import DEFAULT_OUTPUT_DIR
from train_model import MODEL_DIR, OUTPUT_DIR


DEFAULT_INPUT_FILE = DEFAULT_OUTPUT_DIR / "sentiment_text_template.csv"
DEFAULT_OUTPUT_FILE = OUTPUT_DIR / "sentiment_scores.csv"
DEFAULT_MODEL_FILE = MODEL_DIR / "sentiment_tfidf_logistic.joblib"
DEFAULT_METRICS_FILE = OUTPUT_DIR / "sentiment_metrics.json"
SENTIMENT_REPORT = OUTPUT_DIR / "sentiment_analysis_report.txt"

HAS_DISTILBERT = False
HAS_TEXTBLOB = False

try:
    import transformers  # noqa: F401
    HAS_DISTILBERT = True
except ImportError:
    HAS_DISTILBERT = False

try:
    import textblob as _textblob  # noqa: F401
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False

_distilbert_pipeline = None  # lazy loaded

VALID_LABELS = {"positive", "negative", "neutral"}
LABEL_ALIASES = {
    "pos": "positive",
    "good": "positive",
    "neg": "negative",
    "bad": "negative",
    "mixed": "neutral",
}

POSITIVE_WORDS = {
    "calm",
    "decreased",
    "effective",
    "good",
    "helpful",
    "improved",
    "justice",
    "peace",
    "protected",
    "quick",
    "resolved",
    "responsive",
    "safe",
    "safer",
    "secure",
    "support",
    "supported",
    "trusted",
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
    "increased",
    "murder",
    "panic",
    "rape",
    "robbery",
    "stolen",
    "unsafe",
    "violence",
    "violent",
    "worried",
}

NEGATIONS = {"no", "not", "never", "neither", "without", "hardly"}
INTENSIFIERS = {"extremely", "highly", "really", "so", "too", "very"}
DIMINISHERS = {"barely", "little", "slightly", "somewhat"}

CRIME_KEYWORDS = {
    "assault": "assault",
    "attack": "attack",
    "crime": "crime",
    "fraud": "fraud",
    "gunshot": "gunshot",
    "harassment": "harassment",
    "murder": "murder",
    "rape": "rape",
    "robbery": "robbery",
    "theft": "theft",
    "violence": "violence",
}


def normalize_label(value: object) -> str | None:
    if pd.isna(value):
        return None

    label = str(value).strip().lower()
    label = LABEL_ALIASES.get(label, label)
    return label if label in VALID_LABELS else None


def normalize_text(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"@[A-Za-z0-9_]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: object) -> list[str]:
    return re.findall(r"[a-z]+", normalize_text(text).lower())


def crime_features(tokens: list[str]) -> tuple[int, str]:
    detected = [crime_type for token, crime_type in CRIME_KEYWORDS.items() if token in tokens]
    return len(detected), ", ".join(sorted(detected)) if detected else "none"


def rule_score_text(text: object) -> dict[str, object]:
    tokens = tokenize(text)
    raw_score = 0.0
    positive_terms = 0
    negative_terms = 0

    for index, token in enumerate(tokens):
        polarity = 0.0
        if token in POSITIVE_WORDS:
            polarity = 1.0
            positive_terms += 1
        elif token in NEGATIVE_WORDS:
            polarity = -1.0
            negative_terms += 1
        else:
            continue

        context = tokens[max(0, index - 3) : index]
        if any(word in NEGATIONS for word in context):
            polarity *= -1
        if context and context[-1] in INTENSIFIERS:
            polarity *= 1.5
        elif context and context[-1] in DIMINISHERS:
            polarity *= 0.5

        raw_score += polarity

    sentiment_terms = positive_terms + negative_terms
    normalized_score = raw_score / max(sentiment_terms, 1)
    crime_intensity, crime_types = crime_features(tokens)

    if normalized_score > 0.15:
        label = "positive"
    elif normalized_score < -0.15:
        label = "negative"
    else:
        label = "neutral"

    confidence = min(0.99, 0.5 + min(abs(normalized_score), 1.0) * 0.49)
    if sentiment_terms == 0:
        confidence = 0.5

    return {
        "sentiment_score": round(normalized_score, 4),
        "sentiment_confidence": round(confidence, 4),
        "polarity": round(normalized_score, 4),
        "subjectivity": round(min(1.0, sentiment_terms / max(len(tokens), 1) * 3), 4),
        "confidence": round(confidence, 4),
        "positive_terms": positive_terms,
        "negative_terms": negative_terms,
        "crime_intensity": crime_intensity,
        "crime_types": crime_types,
        "sentiment_label": label,
        "sentiment_method": "rule_fallback",
    }


def get_distilbert_pipeline():
    """Lazy load the DistilBERT sentiment pipeline (downloads ~268MB on first use)."""
    global _distilbert_pipeline
    if _distilbert_pipeline is not None:
        return _distilbert_pipeline
    if not HAS_DISTILBERT:
        return None
    try:
        from transformers import pipeline as _hf_pipeline
        # Use CPU by default for broad compatibility (including Windows)
        _distilbert_pipeline = _hf_pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            tokenizer="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1,  # CPU
        )
        return _distilbert_pipeline
    except Exception as e:
        print(f"[WARN] Could not load DistilBERT pipeline: {e}")
        return None


def score_with_distilbert(text: object) -> dict[str, object]:
    """Score a single text using DistilBERT. Falls back to rule-based if unavailable."""
    pipeline = get_distilbert_pipeline()
    if pipeline is None:
        return rule_score_text(text)

    cleaned = normalize_text(text)
    if not cleaned:
        return rule_score_text(text)

    try:
        result = pipeline(cleaned[:512])[0]  # truncate long text
        label = result["label"].lower()  # "POSITIVE" or "NEGATIVE"
        confidence = float(result["score"])

        # Map to our polarity scale (-1 to +1)
        if label == "positive":
            polarity = confidence
            sentiment_label = "positive"
        else:
            polarity = -confidence
            sentiment_label = "negative"

        # Blend with lexicon for crime intensity and extra features
        lexicon = rule_score_text(text)

        # Combine: use DistilBERT for label/polarity/confidence, lexicon for crime details
        return {
            "sentiment_score": round(polarity, 4),
            "sentiment_confidence": round(confidence, 4),
            "polarity": round(polarity, 4),
            "subjectivity": round(lexicon["subjectivity"], 4),
            "confidence": round(confidence, 4),
            "positive_terms": lexicon["positive_terms"],
            "negative_terms": lexicon["negative_terms"],
            "crime_intensity": lexicon["crime_intensity"],
            "crime_types": lexicon["crime_types"],
            "sentiment_label": sentiment_label,
            "sentiment_method": "distilbert",
        }
    except Exception:
        return rule_score_text(text)


def build_sentiment_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.98,
                    max_features=15000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=2.0,
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ]
    )


def evaluate_training_data(texts: pd.Series, labels: pd.Series) -> dict[str, Any]:
    class_counts = labels.value_counts()
    minimum_class_count = int(class_counts.min())

    metrics: dict[str, Any] = {
        "labeled_rows": int(len(labels)),
        "class_counts": {str(key): int(value) for key, value in class_counts.items()},
        "evaluation_available": minimum_class_count >= 2,
    }

    if minimum_class_count < 2:
        metrics["message"] = "At least two examples per sentiment class are required for cross-validation."
        return metrics

    folds = min(5, minimum_class_count)
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
    predictions = cross_val_predict(build_sentiment_pipeline(), texts, labels, cv=cv)

    metrics.update(
        {
            "cross_validation_folds": folds,
            "accuracy": float(accuracy_score(labels, predictions)),
            "macro_f1": float(f1_score(labels, predictions, average="macro")),
            "classification_report": classification_report(
                labels,
                predictions,
                labels=sorted(VALID_LABELS),
                output_dict=True,
                zero_division=0,
            ),
            "confusion_matrix_labels": sorted(VALID_LABELS),
            "confusion_matrix": confusion_matrix(
                labels,
                predictions,
                labels=sorted(VALID_LABELS),
            ).tolist(),
        }
    )
    return metrics


def train_sentiment_model(
    df: pd.DataFrame,
    text_column: str,
    label_column: str,
    model_file: Path,
    metrics_file: Path,
) -> tuple[Pipeline | None, dict[str, Any]]:
    labels = df[label_column].map(normalize_label)
    texts = df[text_column].map(normalize_text)
    labeled_mask = labels.notna() & texts.ne("")
    labeled_texts = texts.loc[labeled_mask]
    labeled_labels = labels.loc[labeled_mask].astype(str)

    if len(labeled_labels) < 6 or labeled_labels.nunique() < 2:
        metrics = {
            "labeled_rows": int(len(labeled_labels)),
            "class_counts": {
                str(key): int(value)
                for key, value in labeled_labels.value_counts().items()
            },
            "evaluation_available": False,
            "message": "Add at least six labeled rows covering two or more sentiment classes to train the ML model.",
        }
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        metrics_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return None, metrics

    metrics = evaluate_training_data(labeled_texts, labeled_labels)
    model = build_sentiment_pipeline()
    model.fit(labeled_texts, labeled_labels)

    model_file.parent.mkdir(parents=True, exist_ok=True)
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "text_column": text_column,
            "label_column": label_column,
            "classes": model.named_steps["classifier"].classes_.tolist(),
            "training_rows": int(len(labeled_labels)),
        },
        model_file,
    )
    metrics_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return model, metrics


def load_sentiment_model(model_file: Path) -> Pipeline | None:
    if not model_file.exists():
        return None
    artifact = joblib.load(model_file)
    return artifact["model"]


def predict_with_model(model: Pipeline, texts: pd.Series) -> pd.DataFrame:
    predictions = model.predict(texts)
    probabilities = model.predict_proba(texts)
    confidence = probabilities.max(axis=1)
    classes = model.named_steps["classifier"].classes_.tolist()
    if "neutral" not in classes:
        predictions = np.where(confidence < 0.55, "neutral", predictions)

    class_probabilities = {
        label: probabilities[:, classes.index(label)] if label in classes else np.zeros(len(texts))
        for label in VALID_LABELS
    }
    polarity = class_probabilities["positive"] - class_probabilities["negative"]
    if "neutral" in classes:
        subjectivity = 1.0 - class_probabilities["neutral"]
    else:
        subjectivity = np.minimum(1.0, np.abs(polarity) + 0.2)

    lexical_rows = [rule_score_text(text) for text in texts]
    return pd.DataFrame(
        {
            "sentiment_score": polarity,
            "sentiment_confidence": confidence,
            "polarity": polarity,
            "subjectivity": subjectivity,
            "confidence": confidence,
            "positive_terms": [row["positive_terms"] for row in lexical_rows],
            "negative_terms": [row["negative_terms"] for row in lexical_rows],
            "crime_intensity": [row["crime_intensity"] for row in lexical_rows],
            "crime_types": [row["crime_types"] for row in lexical_rows],
            "sentiment_label": predictions,
            "sentiment_method": "tfidf_logistic_regression",
        }
    )


def score_text(text: object) -> dict[str, object]:
    """Score a single piece of text. Prefers DistilBERT when available."""
    # Primary: DistilBERT (best accuracy, no labels needed)
    if HAS_DISTILBERT:
        pipeline = get_distilbert_pipeline()
        if pipeline is not None:
            return score_with_distilbert(text)

    # Secondary: trained TF-IDF model
    model = load_sentiment_model(DEFAULT_MODEL_FILE)
    if model is not None:
        return predict_with_model(model, pd.Series([normalize_text(text)])).iloc[0].to_dict()

    # Fallback: rule-based lexicon (always works)
    return rule_score_text(text)


def empty_scored_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        sentiment_score=pd.Series(dtype="float64"),
        sentiment_confidence=pd.Series(dtype="float64"),
        polarity=pd.Series(dtype="float64"),
        subjectivity=pd.Series(dtype="float64"),
        confidence=pd.Series(dtype="float64"),
        positive_terms=pd.Series(dtype="Int64"),
        negative_terms=pd.Series(dtype="Int64"),
        crime_intensity=pd.Series(dtype="Int64"),
        crime_types=pd.Series(dtype="string"),
        sentiment_label=pd.Series(dtype="string"),
        sentiment_method=pd.Series(dtype="string"),
    )


def write_sentiment_report(
    scored: pd.DataFrame,
    method: str,
    training_metrics: dict[str, Any] | None,
    report_file: Path = SENTIMENT_REPORT,
) -> Path:
    distribution = scored["sentiment_label"].value_counts()
    method_display = {
        "distilbert": "DistilBERT (transformer) + crime lexicon",
        "tfidf_logistic_regression": "TF-IDF + Logistic Regression (trained)",
        "rule_fallback": "Rule-based lexicon (fallback)",
    }.get(method, method)

    lines = [
        "CRIMECAST SENTIMENT ANALYSIS REPORT",
        "=" * 45,
        f"Records scored: {len(scored)}",
        f"Method: {method_display}",
        f"Average polarity: {scored['polarity'].mean():.4f}",
        f"Average confidence: {scored['confidence'].mean():.4f}",
        f"Average crime intensity: {scored['crime_intensity'].mean():.4f}",
        "",
        "Sentiment distribution:",
    ]

    for label, count in distribution.items():
        lines.append(f"- {label}: {count} ({count / len(scored) * 100:.1f}%)")

    if training_metrics:
        lines.extend(["", "Supervised model evaluation:"])
        if training_metrics.get("evaluation_available"):
            lines.append(f"- Accuracy: {training_metrics['accuracy']:.4f}")
            lines.append(f"- Macro F1: {training_metrics['macro_f1']:.4f}")
            lines.append(f"- Cross-validation folds: {training_metrics['cross_validation_folds']}")
        elif training_metrics.get("message"):
            lines.append(f"- {training_metrics['message']}")

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_file


def analyze_sentiment(
    input_file: Path = DEFAULT_INPUT_FILE,
    output_file: Path = DEFAULT_OUTPUT_FILE,
    text_column: str = "text",
    label_column: str = "sentiment_label",
    model_file: Path = DEFAULT_MODEL_FILE,
    metrics_file: Path = DEFAULT_METRICS_FILE,
    train_if_labeled: bool = True,
) -> dict[str, object]:
    if not input_file.exists():
        raise FileNotFoundError(f"Text input file was not found: {input_file}")

    df = pd.read_csv(input_file)
    if text_column not in df.columns:
        raise ValueError(f"Input file must contain a '{text_column}' column")

    # Auto-generate synthetic text if the template is nearly empty (great for first-time users)
    if len(df) < 3:
        print("[INFO] Template nearly empty — generating synthetic crime-related text for demo...")
        generate_synthetic_text_from_crime_data()
        df = pd.read_csv(input_file)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    if df.empty:
        empty_scored_frame(df).to_csv(output_file, index=False)
        return {
            "rows": 0,
            "output_file": output_file,
            "method": "none",
            "message": "No text rows found. Add labeled complaint/news/social text rows before training sentiment analysis.",
        }

    source_labels = df[label_column].copy() if label_column in df.columns else None
    model: Pipeline | None = None
    training_metrics: dict[str, Any] | None = None

    if train_if_labeled and label_column in df.columns:
        model, training_metrics = train_sentiment_model(
            df,
            text_column,
            label_column,
            model_file,
            metrics_file,
        )

    # Note: DistilBERT branch below takes priority (best accuracy)
    normalized_texts = df[text_column].map(normalize_text)

    # Determine scoring method. DistilBERT is preferred for accuracy when available.
    distilbert_pipe = get_distilbert_pipeline() if HAS_DISTILBERT else None

    if distilbert_pipe is not None:
        # Primary: DistilBERT (best accuracy + context for crime narratives)
        scores = pd.DataFrame([score_with_distilbert(text) for text in normalized_texts])
        method = "distilbert"
    elif model is not None:
        scores = predict_with_model(model, normalized_texts)
        method = "tfidf_logistic_regression"
    else:
        scores = pd.DataFrame([rule_score_text(text) for text in normalized_texts])
        method = "rule_fallback"

    base = df.drop(columns=[label_column], errors="ignore").reset_index(drop=True)
    if source_labels is not None:
        base["provided_sentiment_label"] = source_labels.map(normalize_label).reset_index(drop=True)
    scored = pd.concat([base, scores.reset_index(drop=True)], axis=1)
    scored.to_csv(output_file, index=False)
    report_file = write_sentiment_report(scored, method, training_metrics)

    result: dict[str, object] = {
        "rows": len(scored),
        "output_file": output_file,
        "report_file": report_file,
        "method": method,
        "label_counts": scored["sentiment_label"].value_counts().to_dict(),
        "distilbert_available": HAS_DISTILBERT and get_distilbert_pipeline() is not None,
    }
    if training_metrics is not None:
        result["training_metrics"] = training_metrics
        result["model_file"] = model_file if model_file.exists() else None
        result["metrics_file"] = metrics_file
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train or run sentiment analysis for complaint/news/social text.")
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT_FILE)
    parser.add_argument("--output-file", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--text-column", default="text")
    parser.add_argument("--label-column", default="sentiment_label")
    parser.add_argument("--model-file", type=Path, default=DEFAULT_MODEL_FILE)
    parser.add_argument("--metrics-file", type=Path, default=DEFAULT_METRICS_FILE)
    parser.add_argument("--no-train", action="store_true", help="Use an existing model or the rule fallback without retraining.")
    return parser.parse_args()


def generate_synthetic_text_from_crime_data(
    ml_ready_path: Path | None = None,
    output_template: Path = DEFAULT_INPUT_FILE,
    num_samples: int = 20,
) -> Path:
    """Generate plausible complaint/news style text from the numeric crime data.
    This lets sentiment analysis work immediately even without manual text entry.
    """
    if ml_ready_path is None:
        ml_ready_path = PROJECT_ROOT / "dataset" / "cleaned" / "crimecast_ml_ready.csv"  # type: ignore
    if not ml_ready_path.exists():
        print("[INFO] No ML data found for synthetic text generation.")
        return output_template

    try:
        df = pd.read_csv(ml_ready_path)
        # Pick high crime rows for interesting text
        if "complaints_total_complaints" in df.columns:
            df = df.nlargest(30, "complaints_total_complaints")

        samples = []
        for i, row in df.head(num_samples).iterrows():
            district = row.get("district_city", "Area")
            year = int(row.get("year", 2023))
            rape = int(row.get("women_crimes_rape_sec_376_i", 0))
            murder = int(row.get("murder_homicide_murder_incidence", 0))
            complaints = int(row.get("complaints_total_complaints", 0))

            if rape > 10 or murder > 5:
                text = f"Residents in {district} are worried after recent incidents including {rape} rape cases and {murder} murders in {year}. People feel unsafe and demand better policing."
                label = "negative"
            else:
                text = f"Police in {district} have shown improvement. {complaints} complaints were handled efficiently in {year} with quick responses and community support."
                label = "positive"

            samples.append({
                "record_id": i + 1,
                "year": year,
                "district_city": district,
                "source": "synthetic",
                "text": text,
                "sentiment_label": label,
            })

        out_df = pd.DataFrame(samples)
        out_df.to_csv(output_template, index=False)
        print(f"[OK] Generated {len(samples)} synthetic text rows for sentiment analysis.")
        return output_template
    except Exception as e:
        print(f"[WARN] Could not generate synthetic text: {e}")
        return output_template


def main() -> None:
    args = parse_args()
    result = analyze_sentiment(
        input_file=args.input_file,
        output_file=args.output_file,
        text_column=args.text_column,
        label_column=args.label_column,
        model_file=args.model_file,
        metrics_file=args.metrics_file,
        train_if_labeled=not args.no_train,
    )
    print(f"Rows scored: {result['rows']}")
    print(f"Method: {result.get('method', 'unknown')}")
    if result.get("distilbert_available"):
        print("[OK] Using DistilBERT for high-accuracy sentiment scoring")
    print(f"Sentiment output: {result['output_file']}")
    if "message" in result:
        print(result["message"])
    if "label_counts" in result:
        print(f"Label counts: {result['label_counts']}")
    if result.get("model_file"):
        print(f"Saved sentiment model: {result['model_file']}")
        print(f"Sentiment metrics: {result['metrics_file']}")


if __name__ == "__main__":
    main()
