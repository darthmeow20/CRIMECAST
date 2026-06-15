"""Visualizations for Tamil Nadu district-wise sentiment analysis."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from sentiment_analysis import DEFAULT_OUTPUT_FILE
from sentiment_tn_districts import get_tamil_nadu_data
from train_model import OUTPUT_DIR

FIGURE_DIR = OUTPUT_DIR / "figures"


def plot_tn_sentiment_by_district(scores_file: Path = DEFAULT_OUTPUT_FILE) -> Path:
    """Create sentiment distribution chart for TN districts."""
    tn_df = get_tamil_nadu_data(scores_file)
    
    if tn_df.empty:
        raise ValueError("No Tamil Nadu data found")

    districts = sorted(tn_df["district_city"].unique())
    num_districts = len(districts)
    cols = 3
    rows = (num_districts + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(16, rows * 4))
    if rows == 1 and cols > 1:
        axes = axes.flatten()
    elif rows == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    colors = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}

    for idx, district in enumerate(districts):
        if idx >= len(axes):
            break

        district_data = tn_df[tn_df["district_city"] == district]
        sentiment_counts = district_data["sentiment_label"].value_counts()

        ax = axes[idx]
        label_colors = [colors.get(label, "#34495e") for label in sentiment_counts.index]
        ax.bar(sentiment_counts.index, sentiment_counts.values, color=label_colors)
        ax.set_title(f"{district} (n={len(district_data)})", fontsize=10, fontweight="bold")
        ax.set_ylabel("Count")
        ax.set_ylim(0, max(sentiment_counts.values) * 1.2)
        for i, v in enumerate(sentiment_counts.values):
            ax.text(i, v + 0.05, str(v), ha="center", va="bottom", fontsize=9)

    for idx in range(len(districts), len(axes)):
        axes[idx].axis("off")

    plt.suptitle("Tamil Nadu - Sentiment Distribution by District", fontsize=14, fontweight="bold")
    plt.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURE_DIR / "tn_sentiment_by_district.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return output_path


def plot_tn_crime_intensity_ranking(scores_file: Path = DEFAULT_OUTPUT_FILE) -> Path:
    """Create crime intensity ranking chart for TN districts."""
    tn_df = get_tamil_nadu_data(scores_file)
    
    if tn_df.empty:
        raise ValueError("No Tamil Nadu data found")

    district_intensity = tn_df.groupby("district_city")["crime_intensity"].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(12, len(district_intensity) * 0.35))
    
    colors_intensity = ["#e74c3c" if x >= 7 else "#f39c12" if x >= 4 else "#2ecc71" for x in district_intensity.values]
    bars = ax.barh(range(len(district_intensity)), district_intensity.values, color=colors_intensity)
    
    ax.set_yticks(range(len(district_intensity)))
    ax.set_yticklabels(district_intensity.index)
    ax.set_xlabel("Average Crime Intensity (0-10)")
    ax.set_title("Tamil Nadu - Crime Intensity by District (Ranked)", fontsize=12, fontweight="bold")
    ax.set_xlim(0, 10)
    ax.axvline(x=7, color="red", linestyle="--", alpha=0.5, label="High Concern (7+)")
    ax.axvline(x=4, color="orange", linestyle="--", alpha=0.5, label="Moderate (4-7)")

    for i, (bar, value) in enumerate(zip(bars, district_intensity.values)):
        ax.text(value + 0.2, i, f"{value:.2f}", va="center", fontsize=9)

    ax.legend(loc="lower right")
    plt.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURE_DIR / "tn_crime_intensity_ranking.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return output_path


def plot_tn_district_comparison_heatmap(scores_file: Path = DEFAULT_OUTPUT_FILE) -> Path:
    """Create heatmap comparing sentiment metrics across TN districts."""
    tn_df = get_tamil_nadu_data(scores_file)
    
    if tn_df.empty:
        raise ValueError("No Tamil Nadu data found")

    metrics = []
    for district in sorted(tn_df["district_city"].unique()):
        district_data = tn_df[tn_df["district_city"] == district]
        metrics.append({
            "District": district,
            "Positive": (district_data["sentiment_label"] == "positive").sum() / len(district_data) * 100,
            "Negative": (district_data["sentiment_label"] == "negative").sum() / len(district_data) * 100,
            "Avg Polarity (Normalized)": (district_data["polarity"].mean() + 1) * 50,
            "Avg Intensity": district_data["crime_intensity"].mean() * 10,
        })

    metrics_df = pd.DataFrame(metrics).set_index("District")

    fig, ax = plt.subplots(figsize=(10, max(6, len(metrics_df) * 0.25)))
    im = ax.imshow(metrics_df.values, cmap="RdYlGn_r", aspect="auto")

    ax.set_xticks(range(len(metrics_df.columns)))
    ax.set_yticks(range(len(metrics_df.index)))
    ax.set_xticklabels(metrics_df.columns, rotation=45, ha="right")
    ax.set_yticklabels(metrics_df.index)

    for i in range(len(metrics_df.index)):
        for j in range(len(metrics_df.columns)):
            text = ax.text(j, i, f"{metrics_df.values[i, j]:.1f}", ha="center", va="center", 
                          color="white" if metrics_df.values[i, j] > 50 else "black", fontsize=8)

    ax.set_title("Tamil Nadu - District Sentiment Metrics Heatmap", fontsize=12, fontweight="bold")
    plt.colorbar(im, ax=ax, label="Metric Value")
    plt.tight_layout()

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURE_DIR / "tn_district_sentiment_heatmap.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return output_path


def plot_tn_district_polarities(scores_file: Path = DEFAULT_OUTPUT_FILE) -> Path:
    """Create polarity distribution chart for TN districts."""
    tn_df = get_tamil_nadu_data(scores_file)
    
    if tn_df.empty:
        raise ValueError("No Tamil Nadu data found")

    district_polarity = tn_df.groupby("district_city")["polarity"].mean().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(12, max(6, len(district_polarity) * 0.3)))
    
    colors_polarity = ["#2ecc71" if x > 0 else "#e74c3c" for x in district_polarity.values]
    bars = ax.barh(range(len(district_polarity)), district_polarity.values, color=colors_polarity)
    
    ax.set_yticks(range(len(district_polarity)))
    ax.set_yticklabels(district_polarity.index)
    ax.set_xlabel("Average Polarity (-1=Negative, +1=Positive)")
    ax.set_title("Tamil Nadu - Sentiment Polarity by District", fontsize=12, fontweight="bold")
    ax.set_xlim(-1, 1)
    ax.axvline(x=0, color="black", linestyle="-", linewidth=0.5)

    for i, (bar, value) in enumerate(zip(bars, district_polarity.values)):
        ax.text(value + 0.05 if value > 0 else value - 0.05, i, f"{value:.3f}", 
               va="center", ha="left" if value > 0 else "right", fontsize=9)

    plt.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = FIGURE_DIR / "tn_district_polarities.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    return output_path


def generate_all_tn_visualizations(scores_file: Path = DEFAULT_OUTPUT_FILE) -> dict:
    """Generate all Tamil Nadu district visualizations."""
    figures = {
        "tn_sentiment_by_district": plot_tn_sentiment_by_district(scores_file),
        "tn_crime_intensity_ranking": plot_tn_crime_intensity_ranking(scores_file),
        "tn_district_sentiment_heatmap": plot_tn_district_comparison_heatmap(scores_file),
        "tn_district_polarities": plot_tn_district_polarities(scores_file),
    }
    return figures


if __name__ == "__main__":
    print("📊 Generating Tamil Nadu district visualizations...\n")
    try:
        figs = generate_all_tn_visualizations()
        for name, path in figs.items():
            print(f"✓ {name}: {path}")
        print("\n✓ All visualizations created successfully!")
    except Exception as e:
        print(f"Error: {e}")
