"""Visualizations for state-wise sentiment analysis."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from sentiment_analysis import DEFAULT_OUTPUT_FILE
from train_model import OUTPUT_DIR

FIGURE_DIR = OUTPUT_DIR / "figures"


def plot_sentiment_by_state(scores_file: Path = DEFAULT_OUTPUT_FILE) -> Path:
    """Create sentiment distribution chart for each state."""
    if not scores_file.exists():
        raise FileNotFoundError(f"Sentiment scores file not found: {scores_file}")

    df = pd.read_csv(scores_file)
    if df.empty or "district_city" not in df.columns:
        raise ValueError("No sentiment data found")

    states = df["district_city"].unique()
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()

    colors = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}

    for idx, state in enumerate(states):
        if idx >= 4:
            break

        state_data = df[df["district_city"] == state]
        sentiment_counts = state_data["sentiment_label"].value_counts()

        ax = axes[idx]
        label_colors = [colors.get(label, "#34495e") for label in sentiment_counts.index]
        ax.bar(sentiment_counts.index, sentiment_counts.values, color=label_colors)
        ax.set_title(f"{state}", fontsize=12, fontweight="bold")
        ax.set_ylabel("Number of Records")
        for i, v in enumerate(sentiment_counts.values):
            ax.text(i, v + 0.1, str(v), ha="center", va="bottom")

    plt.suptitle("Sentiment Distribution by State/District", fontsize=14, fontweight="bold")
    plt.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURE_DIR / "sentiment_by_state.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return output_path


def plot_crime_intensity_by_state(scores_file: Path = DEFAULT_OUTPUT_FILE) -> Path:
    """Create crime intensity comparison chart."""
    if not scores_file.exists():
        raise FileNotFoundError(f"Sentiment scores file not found: {scores_file}")

    df = pd.read_csv(scores_file)
    if df.empty or "district_city" not in df.columns:
        raise ValueError("No sentiment data found")

    state_intensity = df.groupby("district_city")["crime_intensity"].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(state_intensity.index, state_intensity.values, color="#e74c3c")
    ax.set_title("Average Crime Intensity by State/District", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average Crime Intensity (0-10)")
    ax.set_xlabel("State/District")
    ax.set_ylim(0, 10)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.2f}", ha="center", va="bottom")

    plt.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURE_DIR / "crime_intensity_by_state.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return output_path


def plot_state_comparison_heatmap(scores_file: Path = DEFAULT_OUTPUT_FILE) -> Path:
    """Create heatmap comparing sentiment metrics across states."""
    if not scores_file.exists():
        raise FileNotFoundError(f"Sentiment scores file not found: {scores_file}")

    df = pd.read_csv(scores_file)
    if df.empty or "district_city" not in df.columns:
        raise ValueError("No sentiment data found")

    metrics = []
    for state, group in df.groupby("district_city"):
        metrics.append({
            "State": state,
            "Positive %": (group["sentiment_label"] == "positive").sum() / len(group) * 100,
            "Negative %": (group["sentiment_label"] == "negative").sum() / len(group) * 100,
            "Avg Polarity": group["polarity"].mean() * 50 + 50,
            "Avg Intensity": group["crime_intensity"].mean() * 10,
        })

    metrics_df = pd.DataFrame(metrics).set_index("State")

    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(metrics_df.values, cmap="RdYlGn", aspect="auto")

    ax.set_xticks(range(len(metrics_df.columns)))
    ax.set_yticks(range(len(metrics_df.index)))
    ax.set_xticklabels(metrics_df.columns)
    ax.set_yticklabels(metrics_df.index)

    for i in range(len(metrics_df.index)):
        for j in range(len(metrics_df.columns)):
            text = ax.text(j, i, f"{metrics_df.values[i, j]:.1f}", ha="center", va="center", color="black")

    ax.set_title("Sentiment Metrics Comparison (Heatmap)", fontsize=12, fontweight="bold")
    plt.colorbar(im, ax=ax)
    plt.tight_layout()

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURE_DIR / "state_sentiment_heatmap.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return output_path


def generate_all_state_visualizations(scores_file: Path = DEFAULT_OUTPUT_FILE) -> dict:
    """Generate all state-wise visualizations."""
    figures = {
        "sentiment_by_state": plot_sentiment_by_state(scores_file),
        "crime_intensity_by_state": plot_crime_intensity_by_state(scores_file),
        "state_comparison_heatmap": plot_state_comparison_heatmap(scores_file),
    }
    return figures


if __name__ == "__main__":
    figs = generate_all_state_visualizations()
    for name, path in figs.items():
        print(f"{name}: {path}")
