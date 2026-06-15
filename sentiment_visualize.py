"""Optional visualization module for sentiment analysis results."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from sentiment_analysis import DEFAULT_OUTPUT_FILE
from train_model import OUTPUT_DIR

FIGURE_DIR = OUTPUT_DIR / "figures"


def plot_sentiment_distribution(scores_file: Path = DEFAULT_OUTPUT_FILE) -> Path:
    """Create sentiment distribution chart."""
    if not scores_file.exists():
        raise FileNotFoundError(f"Sentiment scores file not found: {scores_file}")

    df = pd.read_csv(scores_file)
    if df.empty:
        raise ValueError("No sentiment data to visualize")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    label_counts = df["sentiment_label"].value_counts()
    colors = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}
    label_colors = [colors.get(label, "#34495e") for label in label_counts.index]

    ax1.bar(label_counts.index, label_counts.values, color=label_colors)
    ax1.set_title("Sentiment Distribution", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Number of Records")
    ax1.set_xlabel("Sentiment")
    for i, v in enumerate(label_counts.values):
        ax1.text(i, v + 0.1, str(v), ha="center", va="bottom")

    crime_intensity = df["crime_intensity"].value_counts().sort_index()
    ax2.bar(crime_intensity.index, crime_intensity.values, color="#3498db")
    ax2.set_title("Crime Intensity Distribution", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Number of Records")
    ax2.set_xlabel("Intensity Score (0-10)")

    plt.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURE_DIR / "sentiment_distribution.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return output_path


def plot_polarity_subjectivity(scores_file: Path = DEFAULT_OUTPUT_FILE) -> Path:
    """Create polarity vs subjectivity scatter plot."""
    if not scores_file.exists():
        raise FileNotFoundError(f"Sentiment scores file not found: {scores_file}")

    df = pd.read_csv(scores_file)
    if df.empty:
        raise ValueError("No sentiment data to visualize")

    fig, ax = plt.subplots(figsize=(10, 6))

    label_colors = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}
    colors = [label_colors.get(label, "#34495e") for label in df["sentiment_label"]]

    ax.scatter(df["polarity"], df["subjectivity"], c=colors, alpha=0.6, s=100)
    ax.set_xlabel("Polarity (Objectivity ← → Negativity)", fontsize=11)
    ax.set_ylabel("Subjectivity (Factual ← → Opinion)", fontsize=11)
    ax.set_title("Sentiment Analysis: Polarity vs Subjectivity", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3)

    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="#2ecc71", label="Positive"),
        Patch(facecolor="#e74c3c", label="Negative"),
        Patch(facecolor="#95a5a6", label="Neutral"),
    ]
    ax.legend(handles=legend_elements, loc="best")

    fig.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURE_DIR / "polarity_subjectivity.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return output_path


def generate_sentiment_visualizations(scores_file: Path = DEFAULT_OUTPUT_FILE) -> dict:
    """Generate all sentiment analysis visualizations."""
    figures = {
        "distribution": plot_sentiment_distribution(scores_file),
        "polarity_subjectivity": plot_polarity_subjectivity(scores_file),
    }
    return figures


if __name__ == "__main__":
    figs = generate_sentiment_visualizations()
    for name, path in figs.items():
        print(f"{name}: {path}")
