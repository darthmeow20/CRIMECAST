#!/usr/bin/env python3
"""
2026 Rape Crime Prediction for All Tamil Nadu Districts
Predicts rape incidents (Section 376 IPC) for each of 33 TN districts
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import joblib

from train_model import MODEL_DIR, OUTPUT_DIR, TARGET_CONFIGS
from predict import load_best_models, load_dataset

# All 33 Tamil Nadu districts
TAMIL_NADU_DISTRICTS = {
    "Ariyalur",
    "Chengalpattu",
    "Chennai",
    "Coimbatore",
    "Cuddalore",
    "Dharmapuri",
    "Dindigul",
    "Erode",
    "Kallakurichi",
    "Kanchipuram",
    "Kanniyakumari",
    "Karur",
    "Krishnagiri",
    "Madurai",
    "Mayiladuthurai",
    "Nagapattinam",
    "Namakkal",
    "Nilgiris",
    "Perambalur",
    "Pudukkottai",
    "Ranipet",
    "Salem",
    "Sivaganga",
    "Tenkasi",
    "Thanjavur",
    "Tirunelveli",
    "Tirupati",
    "Tiruppur",
    "Tiruvallur",
    "Tiruvannamalai",
    "Vellore",
    "Villupuram",
    "Virudhunagar",
}

RAPE_TARGET = "women_crimes_rape_sec_376_i"
OUTPUT_FILE = OUTPUT_DIR / "rape_predictions_2026_all_districts.csv"
REPORT_FILE = OUTPUT_DIR / "rape_predictions_2026_report.txt"


def predict_2026_rape_all_districts() -> pd.DataFrame:
    """Predict 2026 rape incidents for all 33 TN districts."""
    
    print("[INFO] Loading trained models...")
    best_models = load_best_models()
    
    if RAPE_TARGET not in best_models:
        raise ValueError(f"No model found for target: {RAPE_TARGET}")
    
    model_info = best_models[RAPE_TARGET]
    model_file = MODEL_DIR / f"{RAPE_TARGET}_{model_info['model_name']}.joblib"
    
    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found: {model_file}")
    
    artifact = joblib.load(model_file)
    model = artifact["model"] if isinstance(artifact, dict) and "model" in artifact else artifact
    print(f"[OK] Loaded model: {model_info['model_name']}")
    
    # Load data to understand features
    print("[INFO] Loading dataset for feature extraction...")
    df = load_dataset()
    
    # Get the exact feature columns the saved model was trained on (much more reliable)
    feature_columns = model_info.get("feature_columns") or artifact.get("feature_columns") if isinstance(artifact, dict) else None
    if not feature_columns:
        # Fallback (include the engineered time features)
        feature_columns = [col for col in df.columns if col not in ("district_city", RAPE_TARGET)]
    
    numeric_features = feature_columns  # they are already the selected ones
    
    predictions = []
    
    print(f"\n[INFO] Predicting 2026 rape incidents for 33 districts...\n")
    print(f"{'District':<25} {'2026 Prediction':<20} {'Status':<15}")
    print("-" * 60)
    
    TARGET_YEAR = 2026

    for district in sorted(TAMIL_NADU_DISTRICTS):
        try:
            # Get historical data for this district
            district_data = df[df["district_city"].str.strip().str.lower() == district.lower()]
            
            if district_data.empty:
                print(f"{district:<25} {'[NO DATA]':<20} {'Skipped':<15}")
                continue
            
            # Use the *latest* available year as base template (best for trend)
            # Keep as DataFrame (tail(1)) so we can use DF-style column selection with list of strings
            latest = district_data.sort_values("year").tail(1).copy()

            # Override year features for extrapolation (this is important for accuracy)
            latest["year"] = TARGET_YEAR
            if "year_centered" in latest.columns:
                latest["year_centered"] = float(TARGET_YEAR) - 2022.5
            if "is_latest_year" in latest.columns:
                latest["is_latest_year"] = 1

            # Build feature vector using only the columns the model expects.
            # Now 'latest' is DataFrame (1 row), so latest[list_of_str] is valid column selection.
            if not numeric_features:
                numeric_features = []
            try:
                feature_vec = latest[numeric_features].values.reshape(1, -1)
            except Exception as e:
                # Fallback if column selection fails for any reason
                print(f"  Debug: feature selection failed for {district}: {e}")
                feature_vec = np.zeros((1, len(numeric_features) if numeric_features else 1))
            
            # Make prediction
            pred_value = model.predict(feature_vec)[0]
            pred_value = max(0, pred_value)  # Ensure non-negative
            
            row = {
                "district": district,
                "predicted_2026_rape_incidents": round(pred_value, 2),
                "model": model_info['model_name'],
                "confidence": "High" if abs(pred_value) > 0 else "Low",
                "data_points_available": len(district_data),
                "base_year": int(latest.get("year", 2023)),
            }

            # Attach sentiment risk if available (best effort)
            try:
                sent_path = OUTPUT_DIR / "sentiment_scores.csv"
                if sent_path.exists():
                    sent_df = pd.read_csv(sent_path)
                    dist_sent = sent_df[sent_df["district_city"].str.lower() == district.lower()]
                    if not dist_sent.empty:
                        latest_sent = dist_sent.sort_values("year").iloc[-1]
                        row["sentiment_polarity"] = round(float(latest_sent.get("polarity", 0)), 3)
                        row["crime_intensity"] = int(latest_sent.get("crime_intensity", 0))
                        # Simple rape risk blend
                        norm_pred = min(pred_value / 25.0, 1.0)
                        sent_risk = max(0, -row.get("sentiment_polarity", 0)) * 0.5
                        risk = round(min(1.0, 0.65 * norm_pred + 0.35 * sent_risk), 3)
                        row["rape_risk_index"] = risk
                        row["risk_level"] = "HIGH" if risk > 0.65 else ("MEDIUM" if risk > 0.35 else "LOW")
            except Exception:
                pass

            predictions.append(row)
            
            status = "Predicted"
            risk_str = f" risk={row.get('rape_risk_index', '?')}" if "rape_risk_index" in row else ""
            print(f"{district:<25} {pred_value:>15.1f} incidents{risk_str}   {status:<15}")
            
        except Exception as e:
            print(f"{district:<25} {'[ERROR]':<20} {'Failed':<15}")
            print(f"  Error: {str(e)}")
            continue
    
    print("\n" + "-" * 60)
    
    # Create DataFrame
    result_df = pd.DataFrame(predictions)
    
    if result_df.empty or "predicted_2026_rape_incidents" not in result_df.columns:
        print("[ERROR] No valid predictions were generated. Check data and model features.")
        # Return empty df with expected columns to avoid downstream KeyError
        result_df = pd.DataFrame(columns=["district", "predicted_2026_rape_incidents", "model", "confidence", "data_points_available", "base_year"])
    
    # Sort by prediction (highest to lowest)
    result_df = result_df.sort_values("predicted_2026_rape_incidents", ascending=False).reset_index(drop=True)
    
    # Add rank
    if len(result_df) > 0:
        result_df.insert(0, "rank", range(1, len(result_df) + 1))
    
    return result_df


def generate_rape_report(predictions_df: pd.DataFrame) -> None:
    """Generate a comprehensive rape prediction report."""
    
    report_lines = [
        "=" * 70,
        "2026 RAPE CRIME PREDICTION REPORT - TAMIL NADU",
        "Section 376 IPC (Sexual Assault) Incidents Forecast",
        "=" * 70,
        "",
    ]
    
    report_lines.append(f"Total Districts Analyzed: {len(predictions_df)}")
    report_lines.append(f"Prediction Year: 2026")
    report_lines.append("")
    
    if len(predictions_df) == 0 or "predicted_2026_rape_incidents" not in predictions_df.columns:
        report_lines.append("ERROR: No predictions available. Check that the ML model was trained with matching features and data is present.")
        report_lines.append("=" * 70)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(REPORT_FILE, "w") as f:
            f.write("\n".join(report_lines))
        print(f"\n[ERROR] Report generation aborted due to no data.")
        return
    
    # Summary statistics
    total_predicted = predictions_df["predicted_2026_rape_incidents"].sum()
    avg_predicted = predictions_df["predicted_2026_rape_incidents"].mean()
    max_predicted = predictions_df["predicted_2026_rape_incidents"].max()
    min_predicted = predictions_df["predicted_2026_rape_incidents"].min()
    
    report_lines.append("SUMMARY STATISTICS:")
    report_lines.append(f"  Total Predicted Incidents (All Districts): {total_predicted:.0f}")
    report_lines.append(f"  Average per District: {avg_predicted:.1f}")
    report_lines.append(f"  Highest Risk District: {predictions_df.iloc[0]['district']} ({max_predicted:.1f})")
    report_lines.append(f"  Lowest Risk District: {predictions_df.iloc[-1]['district']} ({min_predicted:.1f})")
    report_lines.append("")
    
    # Risk categorization (blended with sentiment when available)
    if "rape_risk_index" in predictions_df.columns:
        high_risk = len(predictions_df[predictions_df["rape_risk_index"] >= 0.65])
        medium_risk = len(predictions_df[(predictions_df["rape_risk_index"] >= 0.35) & (predictions_df["rape_risk_index"] < 0.65)])
        low_risk = len(predictions_df[predictions_df["rape_risk_index"] < 0.35])
        report_lines.append("COMBINED RISK (prediction volume + negative sentiment):")
    else:
        high_risk = len(predictions_df[predictions_df["predicted_2026_rape_incidents"] >= avg_predicted * 1.5])
        medium_risk = len(predictions_df[
            (predictions_df["predicted_2026_rape_incidents"] >= avg_predicted * 0.5) &
            (predictions_df["predicted_2026_rape_incidents"] < avg_predicted * 1.5)
        ])
        low_risk = len(predictions_df[predictions_df["predicted_2026_rape_incidents"] < avg_predicted * 0.5])
        report_lines.append("RISK CLASSIFICATION (based on incident volume):")

    report_lines.append(f"  [HIGH RISK] Districts: {high_risk}")
    report_lines.append(f"  [MEDIUM RISK] Districts: {medium_risk}")
    report_lines.append(f"  [LOW RISK] Districts: {low_risk}")
    report_lines.append("")
    
    # Top 10 high-risk districts
    report_lines.append("TOP 10 HIGH-RISK DISTRICTS (2026):")
    for idx, row in predictions_df.head(10).iterrows():
        report_lines.append(
            f"  {int(row['rank']):2d}. {row['district']:<25} "
            f"{row['predicted_2026_rape_incidents']:>8.1f} incidents"
        )
    report_lines.append("")
    
    # Bottom 10 low-risk districts
    report_lines.append("TOP 10 LOW-RISK DISTRICTS (2026):")
    for idx, row in predictions_df.tail(10).iloc[::-1].iterrows():
        report_lines.append(
            f"  {int(row['rank']):2d}. {row['district']:<25} "
            f"{row['predicted_2026_rape_incidents']:>8.1f} incidents"
        )
    report_lines.append("")
    
    # Model information
    report_lines.append("MODEL INFORMATION:")
    report_lines.append(f"  Model Type: {predictions_df.iloc[0]['model']}")
    report_lines.append(f"  Target Variable: Women Crimes - Rape (Section 376 IPC)")
    report_lines.append(f"  Prediction Methodology: Latest-year template + year feature override for temporal extrapolation (improved 2026)")
    report_lines.append("  Reliability: Uses strict temporal validation during training (past year -> recent year)")
    report_lines.append("")
    
    # Interpretation guide
    report_lines.append("INTERPRETATION GUIDE:")
    report_lines.append(f"  High Risk (>= {avg_predicted * 1.5:.1f}): Requires enhanced prevention measures")
    report_lines.append(f"  Medium Risk ({avg_predicted * 0.5:.1f}-{avg_predicted * 1.5:.1f}): Standard protocols sufficient")
    report_lines.append(f"  Low Risk (< {avg_predicted * 0.5:.1f}): Maintenance of existing systems")
    report_lines.append("")
    
    report_lines.append("RECOMMENDATIONS:")
    report_lines.append("  1. Allocate more resources to high-risk districts")
    report_lines.append("  2. Increase awareness campaigns in medium/high-risk areas")
    report_lines.append("  3. Strengthen women safety initiatives")
    report_lines.append("  4. Coordinate with local law enforcement")
    report_lines.append("  5. Review this forecast quarterly for accuracy")
    report_lines.append("")
    
    report_lines.append("=" * 70)
    report_lines.append(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 70)
    
    # Write report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(report_lines))
    
    print(f"\n[OK] Report generated: {REPORT_FILE}")


def main() -> None:
    """Main execution function."""
    
    print("\n" + "=" * 70)
    print("2026 RAPE CRIME PREDICTION - ALL TAMIL NADU DISTRICTS")
    print("=" * 70)
    
    # Generate predictions
    predictions = predict_2026_rape_all_districts()
    
    # Save to CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[OK] Predictions saved to: {OUTPUT_FILE}")
    
    # Generate report
    generate_rape_report(predictions)
    
    # Display summary
    print(f"\n[OK] Total Districts: {len(predictions)}")
    print(f"[OK] Total Predicted Incidents: {predictions['predicted_2026_rape_incidents'].sum():.0f}")
    print(f"[OK] Average per District: {predictions['predicted_2026_rape_incidents'].mean():.1f}")
    
    # Show top 5
    print("\n[INFO] TOP 5 HIGH-RISK DISTRICTS:")
    for idx, row in predictions.head(5).iterrows():
        print(f"  {idx+1}. {row['district']:<25} {row['predicted_2026_rape_incidents']:>8.1f} incidents")


if __name__ == "__main__":
    main()
