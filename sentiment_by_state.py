"""State/District-wise sentiment analysis module for CRIMECAST."""

from pathlib import Path

import pandas as pd

from sentiment_analysis import DEFAULT_OUTPUT_FILE, SENTIMENT_REPORT
from train_model import OUTPUT_DIR

STATE_REPORT_DIR = OUTPUT_DIR / "state_sentiment_reports"


def analyze_sentiment_by_state(scores_file: Path = DEFAULT_OUTPUT_FILE) -> dict:
    """Analyze sentiment metrics grouped by state/district."""
    if not scores_file.exists():
        raise FileNotFoundError(f"Sentiment scores file not found: {scores_file}")

    df = pd.read_csv(scores_file)
    if df.empty or "district_city" not in df.columns:
        raise ValueError("No sentiment data or 'district_city' column found")

    STATE_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    summary_lines = ["=" * 80, "STATE/DISTRICT-WISE SENTIMENT ANALYSIS", "=" * 80, ""]

    for state, group in df.groupby("district_city"):
        state_results = {
            "total_records": len(group),
            "sentiment_distribution": group["sentiment_label"].value_counts().to_dict(),
            "avg_polarity": round(group["polarity"].mean(), 3),
            "avg_subjectivity": round(group["subjectivity"].mean(), 3),
            "avg_confidence": round(group["confidence"].mean(), 3),
            "avg_crime_intensity": round(group["crime_intensity"].mean(), 2),
            "max_crime_intensity": int(group["crime_intensity"].max()),
            "crime_count": int((group["crime_intensity"] > 0).sum()),
        }

        results[state] = state_results

        summary_lines.append(f"\n{state.upper()}")
        summary_lines.append("-" * 80)
        summary_lines.append(f"  Total Records: {state_results['total_records']}")
        summary_lines.append(f"  Sentiment Distribution:")
        for label, count in state_results["sentiment_distribution"].items():
            pct = (count / state_results["total_records"]) * 100
            summary_lines.append(f"    {label.capitalize()}: {count} ({pct:.1f}%)")
        summary_lines.append(f"  Average Polarity: {state_results['avg_polarity']}")
        summary_lines.append(f"  Average Subjectivity: {state_results['avg_subjectivity']}")
        summary_lines.append(f"  Average Crime Intensity: {state_results['avg_crime_intensity']}")
        summary_lines.append(f"  Records with Crime: {state_results['crime_count']}/{state_results['total_records']}")

        create_state_report(state, group)

    summary_lines.append("\n" + "=" * 80)

    with open(STATE_REPORT_DIR / "state_summary.txt", "w") as f:
        f.write("\n".join(summary_lines))

    return results


def create_state_report(state: str, state_data: pd.DataFrame) -> None:
    """Create individual report for a state."""
    report_lines = ["=" * 70, f"SENTIMENT ANALYSIS: {state.upper()}", "=" * 70, ""]

    report_lines.append(f"Total Records: {len(state_data)}")
    report_lines.append("")

    report_lines.append("SENTIMENT DISTRIBUTION:")
    for label, count in state_data["sentiment_label"].value_counts().items():
        pct = (count / len(state_data)) * 100
        report_lines.append(f"  {label.capitalize()}: {count} ({pct:.1f}%)")
    report_lines.append("")

    report_lines.append("DETAILED METRICS:")
    report_lines.append(f"  Average Polarity: {state_data['polarity'].mean():.3f}")
    report_lines.append(f"  Average Subjectivity: {state_data['subjectivity'].mean():.3f}")
    report_lines.append(f"  Average Confidence: {state_data['confidence'].mean():.3f}")
    report_lines.append(f"  Average Crime Intensity: {state_data['crime_intensity'].mean():.2f}")
    report_lines.append(f"  Max Crime Intensity: {state_data['crime_intensity'].max()}")
    report_lines.append("")

    report_lines.append("SOURCE DISTRIBUTION:")
    if "source" in state_data.columns:
        for source, count in state_data["source"].value_counts().items():
            pct = (count / len(state_data)) * 100
            report_lines.append(f"  {source}: {count} ({pct:.1f}%)")
    report_lines.append("")

    report_lines.append("TOP CRIME TYPES:")
    crime_data = state_data[state_data["crime_intensity"] > 0]
    if not crime_data.empty:
        crimes = crime_data["crime_types"].value_counts().head(5)
        for crime, count in crimes.items():
            report_lines.append(f"  {crime}: {count}")
    else:
        report_lines.append("  No crime keywords found")
    report_lines.append("")

    report_lines.append("SENTIMENT BY SOURCE:")
    if "source" in state_data.columns:
        for source in state_data["source"].unique():
            source_data = state_data[state_data["source"] == source]
            sentiment_dist = source_data["sentiment_label"].value_counts().to_dict()
            avg_intensity = source_data["crime_intensity"].mean()
            report_lines.append(f"  {source}: {sentiment_dist} | Avg Intensity: {avg_intensity:.2f}")
    report_lines.append("")

    report_lines.append("=" * 70)

    file_name = f"{state.lower().replace(' ', '_')}_sentiment.txt"
    with open(STATE_REPORT_DIR / file_name, "w") as f:
        f.write("\n".join(report_lines))


def get_state_comparison() -> pd.DataFrame:
    """Create comparison table across all states."""
    if not (OUTPUT_DIR / "sentiment_scores.csv").exists():
        raise FileNotFoundError("Sentiment scores file not found")

    df = pd.read_csv(OUTPUT_DIR / "sentiment_scores.csv")

    comparison = []
    for state, group in df.groupby("district_city"):
        comparison.append({
            "State/District": state,
            "Total Records": len(group),
            "Positive %": (group["sentiment_label"] == "positive").sum() / len(group) * 100,
            "Negative %": (group["sentiment_label"] == "negative").sum() / len(group) * 100,
            "Neutral %": (group["sentiment_label"] == "neutral").sum() / len(group) * 100,
            "Avg Polarity": round(group["polarity"].mean(), 3),
            "Avg Intensity": round(group["crime_intensity"].mean(), 2),
            "Max Intensity": int(group["crime_intensity"].max()),
        })

    comparison_df = pd.DataFrame(comparison)
    comparison_df.to_csv(STATE_REPORT_DIR / "state_comparison.csv", index=False)
    return comparison_df


if __name__ == "__main__":
    print("Generating state-wise sentiment analysis...")
    results = analyze_sentiment_by_state()
    print(f"Analyzed {len(results)} states/districts")
    
    print("\nGenerating comparison table...")
    comparison = get_state_comparison()
    print(f"\nState Comparison:\n{comparison.to_string(index=False)}")
    
    print(f"\nReports saved to: {STATE_REPORT_DIR}")
