#!/usr/bin/env python3
"""
2026 Rape Crime Prediction Visualizations - All Tamil Nadu Districts
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

OUTPUT_DIR = Path(__file__).parent / "model_outputs"
PREDICTION_FILE = OUTPUT_DIR / "rape_predictions_2026_all_districts.csv"
FIGURES_DIR = OUTPUT_DIR / "figures"


def create_top_districts_chart(predictions_df: pd.DataFrame) -> None:
    """Create bar chart of top 15 high-risk districts."""
    
    top_districts = predictions_df.nlargest(15, "predicted_2026_rape_incidents")
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = plt.cm.Reds([(x - top_districts["predicted_2026_rape_incidents"].min()) / 
                          (top_districts["predicted_2026_rape_incidents"].max() - 
                           top_districts["predicted_2026_rape_incidents"].min())
                          for x in top_districts["predicted_2026_rape_incidents"]])
    
    ax.barh(range(len(top_districts)), top_districts["predicted_2026_rape_incidents"], color=colors)
    ax.set_yticks(range(len(top_districts)))
    ax.set_yticklabels(top_districts["district"])
    ax.set_xlabel("Predicted Rape Incidents (2026)", fontsize=12, fontweight="bold")
    ax.set_title("Top 15 High-Risk Districts - 2026 Rape Crime Prediction", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    
    # Add value labels
    for i, v in enumerate(top_districts["predicted_2026_rape_incidents"]):
        ax.text(v + 0.5, i, f"{v:.0f}", va="center")
    
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    
    output_path = FIGURES_DIR / "rape_2026_top_districts.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"[OK] Chart saved: rape_2026_top_districts.png")
    plt.close()


def create_distribution_chart(predictions_df: pd.DataFrame) -> None:
    """Create distribution/histogram of predictions."""
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    avg_val = predictions_df["predicted_2026_rape_incidents"].mean()
    
    ax.hist(predictions_df["predicted_2026_rape_incidents"], bins=15, color="steelblue", edgecolor="black", alpha=0.7)
    ax.axvline(avg_val, color="red", linestyle="--", linewidth=2, label=f"Average: {avg_val:.1f}")
    ax.axvline(avg_val * 1.5, color="orange", linestyle="--", linewidth=2, label=f"High Risk Threshold: {avg_val*1.5:.1f}")
    ax.axvline(avg_val * 0.5, color="green", linestyle="--", linewidth=2, label=f"Low Risk Threshold: {avg_val*0.5:.1f}")
    
    ax.set_xlabel("Predicted Rape Incidents (2026)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Number of Districts", fontsize=12, fontweight="bold")
    ax.set_title("Distribution of 2026 Rape Crime Predictions Across Districts", fontsize=14, fontweight="bold")
    ax.legend()
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    
    output_path = FIGURES_DIR / "rape_2026_distribution.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"[OK] Chart saved: rape_2026_distribution.png")
    plt.close()


def create_risk_categories_chart(predictions_df: pd.DataFrame) -> None:
    """Create pie chart of risk categories."""
    
    avg_val = predictions_df["predicted_2026_rape_incidents"].mean()
    
    high_risk = len(predictions_df[predictions_df["predicted_2026_rape_incidents"] >= avg_val * 1.5])
    medium_risk = len(predictions_df[
        (predictions_df["predicted_2026_rape_incidents"] >= avg_val * 0.5) &
        (predictions_df["predicted_2026_rape_incidents"] < avg_val * 1.5)
    ])
    low_risk = len(predictions_df[predictions_df["predicted_2026_rape_incidents"] < avg_val * 0.5])
    
    sizes = [high_risk, medium_risk, low_risk]
    labels = [f"High Risk\n({high_risk} districts)", f"Medium Risk\n({medium_risk} districts)", f"Low Risk\n({low_risk} districts)"]
    colors = ["#d62728", "#ff7f0e", "#2ca02c"]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
    
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontweight("bold")
        autotext.set_fontsize(11)
    
    ax.set_title("2026 Rape Crime Risk Distribution by District", fontsize=14, fontweight="bold", pad=20)
    
    plt.tight_layout()
    
    output_path = FIGURES_DIR / "rape_2026_risk_categories.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"[OK] Chart saved: rape_2026_risk_categories.png")
    plt.close()


def create_comparison_chart(predictions_df: pd.DataFrame) -> None:
    """Create comparison chart with all districts sorted."""
    
    sorted_df = predictions_df.sort_values("predicted_2026_rape_incidents", ascending=False)
    avg_val = predictions_df["predicted_2026_rape_incidents"].mean()
    
    fig, ax = plt.subplots(figsize=(16, 10))
    
    colors = ["#d62728" if x >= avg_val * 1.5 else "#ff7f0e" if x >= avg_val * 0.5 else "#2ca02c"
              for x in sorted_df["predicted_2026_rape_incidents"]]
    
    ax.bar(range(len(sorted_df)), sorted_df["predicted_2026_rape_incidents"], color=colors)
    ax.set_xticks(range(len(sorted_df)))
    ax.set_xticklabels(sorted_df["district"], rotation=45, ha="right")
    ax.set_ylabel("Predicted Rape Incidents (2026)", fontsize=12, fontweight="bold")
    ax.set_title("All 33 Tamil Nadu Districts - 2026 Rape Crime Predictions", fontsize=14, fontweight="bold")
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#d62728", label="High Risk (>= 1.5x avg)"),
        Patch(facecolor="#ff7f0e", label="Medium Risk (0.5-1.5x avg)"),
        Patch(facecolor="#2ca02c", label="Low Risk (< 0.5x avg)"),
    ]
    ax.legend(handles=legend_elements, loc="upper right")
    
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    
    output_path = FIGURES_DIR / "rape_2026_all_districts.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"[OK] Chart saved: rape_2026_all_districts.png")
    plt.close()


def create_rank_comparison(predictions_df: pd.DataFrame) -> None:
    """Create table visualization of ranked predictions."""
    
    fig, ax = plt.subplots(figsize=(12, 14))
    ax.axis("off")
    
    # Select top 20 for table
    top_20 = predictions_df.head(20).copy()
    
    table_data = []
    for idx, row in top_20.iterrows():
        table_data.append([
            f"{int(row['rank'])}",
            row['district'],
            f"{row['predicted_2026_rape_incidents']:.1f}",
        ])
    
    table = ax.table(cellText=table_data,
                     colLabels=["Rank", "District", "2026 Prediction"],
                     cellLoc="center",
                     loc="center",
                     colWidths=[0.1, 0.5, 0.3])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Header styling
    for i in range(3):
        table[(0, i)].set_facecolor("#404040")
        table[(0, i)].set_text_props(weight="bold", color="white")
    
    # Alternate row colors
    for i in range(1, len(table_data) + 1):
        color = "#f0f0f0" if i % 2 == 0 else "white"
        for j in range(3):
            table[(i, j)].set_facecolor(color)
    
    plt.title("Top 20 High-Risk Districts - 2026 Rape Crime Predictions", 
              fontsize=14, fontweight="bold", pad=20)
    
    output_path = FIGURES_DIR / "rape_2026_top20_table.png"
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"[OK] Chart saved: rape_2026_top20_table.png")
    plt.close()


def main() -> None:
    """Generate all visualizations."""
    
    print("\n[INFO] Loading predictions...")
    if not PREDICTION_FILE.exists():
        print("[ERROR] Predictions file not found. Run predict_2026_rape_all_districts.py first.")
        return
    
    predictions = pd.read_csv(PREDICTION_FILE)
    
    print(f"[INFO] Creating visualizations ({len(predictions)} districts)...\n")
    
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    create_top_districts_chart(predictions)
    create_distribution_chart(predictions)
    create_risk_categories_chart(predictions)
    create_comparison_chart(predictions)
    create_rank_comparison(predictions)
    
    print(f"\n[OK] All visualizations saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
