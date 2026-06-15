"""Tamil Nadu district-wise sentiment analysis module."""

from pathlib import Path

import pandas as pd

from sentiment_analysis import DEFAULT_OUTPUT_FILE
from train_model import OUTPUT_DIR

TAMIL_NADU_DISTRICTS = {
    "Chennai", "Thiruvallur", "Kanchipuram", "Ranipet",
    "Vellore", "Tiruppattur", "Chengalpattu",
    "Cuddalore", "Villupuram",
    "Tiruvannamalai", "Kallakurichi",
    "Perambalur", "Ariyalur",
    "Namakkal", "Salem", "Krishnagiri",
    "Dharmapuri",
    "Erode", "Nilgiri", "Coimbatore",
    "Tiruppur",
    "Madurai", "Theni", "Dindigul",
    "Ramanathapuram", "Sivaganga",
    "Virudhunagar", "Tuticorin", "Tenkasi",
    "Tirunelveli", "Kanniyakumari",
    "Puducherry", "Karaikal", "Yanam", "Mahe",  # Union territories
    "Tiruchirapalli", "Ariyalur", "Perambalur",
}

TN_REPORT_DIR = OUTPUT_DIR / "tn_district_sentiment_reports"


def get_tamil_nadu_data(scores_file: Path = DEFAULT_OUTPUT_FILE) -> pd.DataFrame:
    """Extract Tamil Nadu records from sentiment scores."""
    if not scores_file.exists():
        raise FileNotFoundError(f"Sentiment scores file not found: {scores_file}")

    df = pd.read_csv(scores_file)
    if df.empty or "district_city" not in df.columns:
        raise ValueError("No sentiment data or 'district_city' column found")

    tn_df = df[df["district_city"].isin(TAMIL_NADU_DISTRICTS)]
    return tn_df


def analyze_tn_sentiment_by_district(scores_file: Path = DEFAULT_OUTPUT_FILE) -> dict:
    """Analyze sentiment metrics for each Tamil Nadu district."""
    tn_df = get_tamil_nadu_data(scores_file)
    
    if tn_df.empty:
        raise ValueError("No Tamil Nadu data found in sentiment scores")

    TN_REPORT_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    summary_lines = ["=" * 80, "TAMIL NADU DISTRICT-WISE SENTIMENT ANALYSIS", "=" * 80, ""]
    summary_lines.append(f"Total Records Analyzed: {len(tn_df)} (from {tn_df['district_city'].nunique()} districts)\n")

    for district in sorted(tn_df["district_city"].unique()):
        district_data = tn_df[tn_df["district_city"] == district]

        district_results = {
            "total_records": len(district_data),
            "sentiment_distribution": district_data["sentiment_label"].value_counts().to_dict(),
            "avg_polarity": round(district_data["polarity"].mean(), 3),
            "avg_subjectivity": round(district_data["subjectivity"].mean(), 3),
            "avg_confidence": round(district_data["confidence"].mean(), 3),
            "avg_crime_intensity": round(district_data["crime_intensity"].mean(), 2),
            "max_crime_intensity": int(district_data["crime_intensity"].max()),
            "crime_count": int((district_data["crime_intensity"] > 0).sum()),
        }

        results[district] = district_results

        summary_lines.append(f"\n{district.upper()}")
        summary_lines.append("-" * 80)
        summary_lines.append(f"  Total Records: {district_results['total_records']}")
        summary_lines.append(f"  Sentiment Distribution:")
        for label, count in sorted(district_results["sentiment_distribution"].items(), key=lambda x: x[1], reverse=True):
            pct = (count / district_results["total_records"]) * 100
            summary_lines.append(f"    {label.capitalize()}: {count} ({pct:.1f}%)")
        summary_lines.append(f"  Average Polarity: {district_results['avg_polarity']}")
        summary_lines.append(f"  Average Subjectivity: {district_results['avg_subjectivity']}")
        summary_lines.append(f"  Average Crime Intensity: {district_results['avg_crime_intensity']}")
        summary_lines.append(f"  Records with Crime Keywords: {district_results['crime_count']}/{district_results['total_records']}")

        create_tn_district_report(district, district_data)

    summary_lines.append("\n" + "=" * 80)
    summary_lines.append("\nKEY INSIGHTS:")
    
    top_negative = max(results.items(), key=lambda x: x[1]["sentiment_distribution"].get("negative", 0))[0] if results else None
    top_safe = max(results.items(), key=lambda x: x[1]["sentiment_distribution"].get("positive", 0))[0] if results else None
    top_crime = max(results.items(), key=lambda x: x[1]["avg_crime_intensity"])[0] if results else None

    if top_negative:
        summary_lines.append(f"  Highest Concern (Most Negative): {top_negative}")
    if top_safe:
        summary_lines.append(f"  Safest Feeling (Most Positive): {top_safe}")
    if top_crime:
        summary_lines.append(f"  Highest Crime Intensity: {top_crime}")

    with open(TN_REPORT_DIR / "tn_district_summary.txt", "w") as f:
        f.write("\n".join(summary_lines))

    return results


def create_tn_district_report(district: str, district_data: pd.DataFrame) -> None:
    """Create individual report for a Tamil Nadu district."""
    report_lines = ["=" * 70, f"TAMIL NADU - {district.upper()}", "=" * 70, ""]

    report_lines.append(f"Total Records: {len(district_data)}")
    report_lines.append(f"Year Range: {district_data['year'].min()}-{district_data['year'].max()}" if 'year' in district_data.columns else "")
    report_lines.append("")

    report_lines.append("SENTIMENT DISTRIBUTION:")
    for label, count in district_data["sentiment_label"].value_counts().items():
        pct = (count / len(district_data)) * 100
        report_lines.append(f"  {label.capitalize()}: {count} ({pct:.1f}%)")
    report_lines.append("")

    report_lines.append("SENTIMENT METRICS:")
    report_lines.append(f"  Average Polarity: {district_data['polarity'].mean():.3f}")
    report_lines.append(f"  Average Subjectivity: {district_data['subjectivity'].mean():.3f}")
    report_lines.append(f"  Average Confidence: {district_data['confidence'].mean():.3f}")
    report_lines.append(f"  Average Crime Intensity: {district_data['crime_intensity'].mean():.2f}")
    report_lines.append(f"  Max Crime Intensity: {district_data['crime_intensity'].max()}")
    report_lines.append("")

    report_lines.append("SOURCE DISTRIBUTION:")
    if "source" in district_data.columns:
        for source, count in district_data["source"].value_counts().items():
            pct = (count / len(district_data)) * 100
            report_lines.append(f"  {source}: {count} ({pct:.1f}%)")
    report_lines.append("")

    report_lines.append("CRIME TYPES DETECTED:")
    crime_data = district_data[district_data["crime_intensity"] > 0]
    if not crime_data.empty:
        crimes = crime_data["crime_types"].value_counts().head(10)
        for crime, count in crimes.items():
            report_lines.append(f"  {crime}: {count}")
    else:
        report_lines.append("  No crime keywords found")
    report_lines.append("")

    report_lines.append("SENTIMENT BY SOURCE:")
    if "source" in district_data.columns:
        for source in sorted(district_data["source"].unique()):
            source_data = district_data[district_data["source"] == source]
            sentiment_dist = source_data["sentiment_label"].value_counts().to_dict()
            avg_intensity = source_data["crime_intensity"].mean()
            report_lines.append(f"  {source}: {sentiment_dist} | Avg Intensity: {avg_intensity:.2f}")
    report_lines.append("")

    report_lines.append("SENTIMENT STATUS:")
    avg_polarity = district_data["polarity"].mean()
    avg_intensity = district_data["crime_intensity"].mean()
    
    if avg_polarity > 0.3:
        status = "[SAFE] Positive sentiment, low concern"
    elif avg_polarity > -0.3:
        status = "[MIXED] Balanced sentiment"
    else:
        status = "[CONCERN] Negative sentiment, high concern"
    
    report_lines.append(f"  {status}")
    report_lines.append("")

    report_lines.append("=" * 70)

    file_name = f"tn_{district.lower().replace(' ', '_')}_sentiment.txt"
    with open(TN_REPORT_DIR / file_name, "w") as f:
        f.write("\n".join(report_lines))


def get_tn_district_comparison() -> pd.DataFrame:
    """Create comparison table across Tamil Nadu districts."""
    df = get_tamil_nadu_data()
    
    if df.empty:
        raise ValueError("No Tamil Nadu data found")

    comparison = []
    for district in sorted(df["district_city"].unique()):
        district_data = df[df["district_city"] == district]
        comparison.append({
            "District": district,
            "Records": len(district_data),
            "Positive %": round((district_data["sentiment_label"] == "positive").sum() / len(district_data) * 100, 1),
            "Negative %": round((district_data["sentiment_label"] == "negative").sum() / len(district_data) * 100, 1),
            "Neutral %": round((district_data["sentiment_label"] == "neutral").sum() / len(district_data) * 100, 1),
            "Avg Polarity": round(district_data["polarity"].mean(), 3),
            "Avg Intensity": round(district_data["crime_intensity"].mean(), 2),
            "Max Intensity": int(district_data["crime_intensity"].max()),
        })

    comparison_df = pd.DataFrame(comparison).sort_values("Avg Intensity", ascending=False)
    comparison_df.to_csv(TN_REPORT_DIR / "tn_district_comparison.csv", index=False)
    return comparison_df


if __name__ == "__main__":
    print("🔍 Analyzing Tamil Nadu district-wise sentiment...\n")
    
    try:
        results = analyze_tn_sentiment_by_district()
        print(f"✓ Analyzed {len(results)} Tamil Nadu districts\n")
        
        print("📊 Generating comparison table...\n")
        comparison = get_tn_district_comparison()
        print(comparison.to_string(index=False))
        
        print(f"\n✓ Reports saved to: {TN_REPORT_DIR}")
        print(f"  - tn_district_summary.txt (overall summary)")
        print(f"  - tn_district_comparison.csv (excel-ready comparison)")
        print(f"  - tn_{{district}}_sentiment.txt (individual district reports)")
    except Exception as e:
        print(f"Error: {e}")
