#!/usr/bin/env python3
"""
2026 Tamil Nadu Rape Crime Prediction
======================================
Standalone script: uses 2022-2023 historical data + ML trend extrapolation
to predict 2026 rape incidents (Section 376 IPC) for all TN districts.

Run:  python run_rape_2026_prediction.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
FITTED_CSV   = PROJECT_ROOT / "model_outputs" / "fitted_predictions.csv"
OUTPUT_DIR   = PROJECT_ROOT / "model_outputs"
FIGURES_DIR  = OUTPUT_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Load historical fitted predictions for rape
# ─────────────────────────────────────────────────────────────────────────────
def load_rape_history() -> pd.DataFrame:
    df = pd.read_csv(FITTED_CSV)
    rape = df[df["target"] == "women_crimes_rape_sec_376_i"].copy()
    # Include districts AND city commissionerates (e.g. Chennai, Madurai City)
    # Exclude only special units (Cyber Cell, Railway, etc.)
    rape = rape[rape["area_type"].isin(["district", "city"])].copy()
    return rape


# ─────────────────────────────────────────────────────────────────────────────
# Predict 2026 using linear trend (year-over-year slope)
# ─────────────────────────────────────────────────────────────────────────────
def predict_2026(rape: pd.DataFrame) -> pd.DataFrame:
    records = []
    for district, grp in rape.groupby("district_city"):
        grp = grp.sort_values("year")
        years = grp["year"].values
        preds = grp["predicted"].values
        actuals = grp["actual"].values

        if len(grp) == 1:
            # Only one year: carry forward with 0-change
            slope = 0.0
            base  = preds[-1]
        else:
            # Linear regression on PREDICTED values (model-smoothed)
            slope = np.polyfit(years, preds, 1)[0]
            base  = preds[-1]

        years_ahead = 2026 - years[-1]
        forecast_2026 = max(0.0, base + slope * years_ahead)

        # Confidence: based on model R² proxy (how close actual vs predicted)
        avg_err = np.mean(np.abs(actuals - preds))
        if avg_err < 2:
            confidence = "High"
        elif avg_err < 5:
            confidence = "Medium"
        else:
            confidence = "Low"

        records.append({
            "district": district,
            "actual_2022": grp[grp["year"] == 2022]["actual"].values[0] if 2022 in years else None,
            "predicted_2022": grp[grp["year"] == 2022]["predicted"].values[0] if 2022 in years else None,
            "actual_2023": grp[grp["year"] == 2023]["actual"].values[0] if 2023 in years else None,
            "predicted_2023": grp[grp["year"] == 2023]["predicted"].values[0] if 2023 in years else None,
            "slope_per_year": round(slope, 3),
            "predicted_2026": round(forecast_2026, 1),
            "confidence": confidence,
        })

    result = pd.DataFrame(records).sort_values("predicted_2026", ascending=False).reset_index(drop=True)
    result.insert(0, "rank", range(1, len(result) + 1))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Risk categorisation
# ─────────────────────────────────────────────────────────────────────────────
def categorise_risk(df: pd.DataFrame) -> pd.DataFrame:
    avg = df["predicted_2026"].mean()
    df["risk"] = pd.cut(
        df["predicted_2026"],
        bins=[-np.inf, avg * 0.5, avg * 1.5, np.inf],
        labels=["Low", "Medium", "High"],
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Visualisations
# ─────────────────────────────────────────────────────────────────────────────
PALETTE = {
    "High":   "#E74C3C",
    "Medium": "#F39C12",
    "Low":    "#27AE60",
}
BG_COLOR    = "#0D1117"
TEXT_COLOR  = "#E6EDF3"
GRID_COLOR  = "#21262D"
ACCENT      = "#58A6FF"


def style_ax(ax, title: str = "") -> None:
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax.title.set_color(TEXT_COLOR)
    ax.title.set_fontsize(11)
    ax.title.set_fontweight("bold")
    if title:
        ax.set_title(title)
    ax.grid(color=GRID_COLOR, linestyle="--", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)


def fig_top_districts(df: pd.DataFrame) -> Path:
    top = df.head(15).copy()
    colors = [PALETTE[r] for r in top["risk"]]

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(BG_COLOR)
    bars = ax.barh(
        top["district"][::-1],
        top["predicted_2026"][::-1],
        color=colors[::-1],
        edgecolor=GRID_COLOR,
        linewidth=0.4,
        height=0.65,
    )
    # Value labels
    for bar, val in zip(bars, top["predicted_2026"][::-1]):
        ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", ha="left", color=TEXT_COLOR, fontsize=8)

    style_ax(ax, "🔴  Top 15 High-Risk Districts — Predicted 2026 Rape Incidents (Section 376 IPC)")
    ax.set_xlabel("Predicted Incidents", color=TEXT_COLOR, fontsize=9)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    [t.set_color(TEXT_COLOR) for t in ax.get_yticklabels()]
    [t.set_color(TEXT_COLOR) for t in ax.get_xticklabels()]

    # Legend
    patches = [mpatches.Patch(color=v, label=k + " Risk") for k, v in PALETTE.items()]
    ax.legend(handles=patches, loc="lower right", facecolor="#161B22", edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, fontsize=8)

    plt.tight_layout(pad=1.5)
    out = FIGURES_DIR / "rape_2026_top_districts.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    return out


def fig_all_districts(df: pd.DataFrame) -> Path:
    colors = [PALETTE[r] for r in df["risk"]]

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor(BG_COLOR)
    ax.bar(df["district"], df["predicted_2026"], color=colors,
           edgecolor=GRID_COLOR, linewidth=0.3, width=0.7)

    style_ax(ax, "📊  All Districts — 2026 Predicted Rape Incidents (ranked highest → lowest)")
    ax.set_xlabel("District", color=TEXT_COLOR, fontsize=9)
    ax.set_ylabel("Predicted Incidents (2026)", color=TEXT_COLOR, fontsize=9)
    plt.xticks(rotation=60, ha="right", fontsize=7, color=TEXT_COLOR)
    plt.yticks(color=TEXT_COLOR)
    [t.set_color(TEXT_COLOR) for t in ax.get_xticklabels()]

    patches = [mpatches.Patch(color=v, label=k + " Risk") for k, v in PALETTE.items()]
    ax.legend(handles=patches, loc="upper right", facecolor="#161B22", edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, fontsize=8)

    plt.tight_layout(pad=1.5)
    out = FIGURES_DIR / "rape_2026_all_districts.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    return out


def fig_risk_pie(df: pd.DataFrame) -> Path:
    counts = df["risk"].value_counts()
    labels = counts.index.tolist()
    colors = [PALETTE[l] for l in labels]
    sizes  = counts.values

    fig, ax = plt.subplots(figsize=(7, 6))
    fig.patch.set_facecolor(BG_COLOR)
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.0f%%",
        startangle=140, pctdistance=0.75,
        wedgeprops={"edgecolor": BG_COLOR, "linewidth": 2},
    )
    for t in texts + autotexts:
        t.set_color(TEXT_COLOR)
        t.set_fontsize(10)

    ax.set_facecolor(BG_COLOR)
    ax.set_title("⚠️  Risk Category Distribution — 2026 TN Districts", color=TEXT_COLOR,
                 fontsize=11, fontweight="bold", pad=12)
    plt.tight_layout()
    out = FIGURES_DIR / "rape_2026_risk_pie.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    return out


def fig_trend_comparison(df: pd.DataFrame) -> Path:
    """Compare 2022 actual → 2023 actual → 2026 predicted for top 12 districts."""
    top12 = df.head(12).copy()
    x = np.arange(len(top12))
    width = 0.28

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(BG_COLOR)

    b1 = ax.bar(x - width, top12["actual_2022"].fillna(0), width, label="2022 Actual",
                color="#4CC9F0", edgecolor=GRID_COLOR, linewidth=0.3)
    b2 = ax.bar(x,          top12["actual_2023"].fillna(0), width, label="2023 Actual",
                color="#7209B7", edgecolor=GRID_COLOR, linewidth=0.3)
    b3 = ax.bar(x + width,  top12["predicted_2026"],        width, label="2026 Predicted",
                color="#E74C3C", edgecolor=GRID_COLOR, linewidth=0.3)

    style_ax(ax, "📈  Year-over-Year Trend: 2022 → 2023 → 2026 Forecast (Top 12 Districts)")
    ax.set_xticks(x)
    ax.set_xticklabels(top12["district"], rotation=35, ha="right", fontsize=8, color=TEXT_COLOR)
    [t.set_color(TEXT_COLOR) for t in ax.get_yticklabels()]
    ax.set_ylabel("Rape Incidents (Section 376 IPC)", color=TEXT_COLOR, fontsize=9)
    ax.legend(facecolor="#161B22", edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=9)

    plt.tight_layout(pad=1.5)
    out = FIGURES_DIR / "rape_2026_trend_comparison.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    return out


def fig_summary_table(df: pd.DataFrame) -> Path:
    """Professional table chart for top 20 districts."""
    top20 = df.head(20).copy()
    top20["Predicted 2026"] = top20["predicted_2026"].map("{:.1f}".format)
    top20["2022 Actual"]    = top20["actual_2022"].map(lambda v: f"{v:.0f}" if pd.notna(v) else "–")
    top20["2023 Actual"]    = top20["actual_2023"].map(lambda v: f"{v:.0f}" if pd.notna(v) else "–")

    col_labels = ["Rank", "District", "2022 Actual", "2023 Actual", "Predicted 2026", "Risk", "Confidence"]
    table_data = []
    for _, row in top20.iterrows():
        table_data.append([
            str(int(row["rank"])),
            row["district"],
            row["2022 Actual"],
            row["2023 Actual"],
            row["Predicted 2026"],
            row["risk"],
            row["confidence"],
        ])

    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.axis("off")

    table = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)

    # Style header
    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor(ACCENT)
        cell.set_text_props(color="black", fontweight="bold")

    # Style rows
    for i in range(1, len(table_data) + 1):
        risk_val = table_data[i - 1][5]
        row_color = {"High": "#3D1515", "Medium": "#3D2E0B", "Low": "#0F2D1A"}.get(risk_val, "#161B22")
        for j in range(len(col_labels)):
            cell = table[i, j]
            cell.set_facecolor(row_color)
            cell.set_text_props(color=TEXT_COLOR)

            # Highlight risk column
            if j == 5:
                cell.set_text_props(color=PALETTE.get(risk_val, TEXT_COLOR), fontweight="bold")

    ax.set_title("📋  Top 20 Districts — 2026 Tamil Nadu Rape Crime Forecast",
                 color=TEXT_COLOR, fontsize=12, fontweight="bold", pad=20)
    plt.tight_layout()
    out = FIGURES_DIR / "rape_2026_summary_table.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close()
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Text report
# ─────────────────────────────────────────────────────────────────────────────
def write_report(df: pd.DataFrame) -> Path:
    total   = df["predicted_2026"].sum()
    avg     = df["predicted_2026"].mean()
    hi_cnt  = (df["risk"] == "High").sum()
    med_cnt = (df["risk"] == "Medium").sum()
    lo_cnt  = (df["risk"] == "Low").sum()

    lines = [
        "=" * 72,
        "  2026 RAPE CRIME PREDICTION REPORT — TAMIL NADU",
        "  Section 376 IPC (Sexual Assault) | District-Level Forecast",
        "=" * 72,
        "",
        f"  Prediction Year   : 2026",
        f"  Historical Data   : 2022 – 2023",
        f"  Model             : RandomForest (log-transformed target)",
        f"  Method            : Linear trend extrapolation from fitted values",
        f"  Districts Covered : {len(df)}",
        "",
        "─" * 72,
        "  SUMMARY STATISTICS",
        "─" * 72,
        f"  Total Predicted Incidents (all districts) : {total:.0f}",
        f"  Average per District                      : {avg:.1f}",
        f"  Highest Risk District : {df.iloc[0]['district']} ({df.iloc[0]['predicted_2026']:.1f} incidents)",
        f"  Lowest Risk District  : {df.iloc[-1]['district']} ({df.iloc[-1]['predicted_2026']:.1f} incidents)",
        "",
        "─" * 72,
        "  RISK CLASSIFICATION",
        "─" * 72,
        f"  [HIGH   RISK]  > {avg * 1.5:.1f} incidents  → {hi_cnt} districts",
        f"  [MEDIUM RISK]  {avg * 0.5:.1f} – {avg * 1.5:.1f}  → {med_cnt} districts",
        f"  [LOW    RISK]  < {avg * 0.5:.1f} incidents  → {lo_cnt} districts",
        "",
        "─" * 72,
        "  TOP 15 HIGH-RISK DISTRICTS (2026)",
        "─" * 72,
    ]

    for _, row in df.head(15).iterrows():
        trend = "↑" if row["slope_per_year"] > 0.1 else ("↓" if row["slope_per_year"] < -0.1 else "→")
        lines.append(
            f"  {int(row['rank']):2d}. {row['district']:<22} "
            f"Predicted: {row['predicted_2026']:>6.1f}  "
            f"Risk: {str(row['risk']):<6}  Trend: {trend}"
        )

    lines += [
        "",
        "─" * 72,
        "  BOTTOM 10 LOWER-RISK DISTRICTS (2026)",
        "─" * 72,
    ]
    for _, row in df.tail(10).iloc[::-1].iterrows():
        lines.append(
            f"  {int(row['rank']):2d}. {row['district']:<22} "
            f"Predicted: {row['predicted_2026']:>6.1f}  "
            f"Risk: {str(row['risk']):<6}"
        )

    lines += [
        "",
        "─" * 72,
        "  RECOMMENDATIONS",
        "─" * 72,
        "  1. Prioritise resource allocation to HIGH RISK districts.",
        "  2. Strengthen women safety initiatives in MEDIUM RISK areas.",
        "  3. Coordinate with local law enforcement for rapid response.",
        "  4. Increase public awareness campaigns in high-incidence areas.",
        "  5. Re-evaluate this forecast quarterly as new data arrives.",
        "",
        "─" * 72,
        f"  Generated : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 72,
    ]

    out = OUTPUT_DIR / "rape_predictions_2026_report.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    print("\n" + "=" * 60)
    print("  2026 Tamil Nadu Rape Crime Prediction")
    print("  Section 376 IPC — All Districts")
    print("=" * 60)

    if not FITTED_CSV.exists():
        print(f"\n[ERROR] Could not find: {FITTED_CSV}")
        print("  Run: python app.py --full  (to train models first)")
        sys.exit(1)

    print("\n[1/4] Loading historical data...")
    rape_history = load_rape_history()
    print(f"      Loaded {len(rape_history)} rows for {rape_history['district_city'].nunique()} districts")

    print("[2/4] Computing 2026 predictions via trend extrapolation...")
    predictions = predict_2026(rape_history)
    predictions = categorise_risk(predictions)

    # Save CSV
    csv_out = OUTPUT_DIR / "rape_predictions_2026_all_districts.csv"
    predictions.to_csv(csv_out, index=False)
    print(f"      Saved: {csv_out}")

    print("[3/4] Generating visualisations (5 charts)...")
    f1 = fig_top_districts(predictions)
    f2 = fig_all_districts(predictions)
    f3 = fig_risk_pie(predictions)
    f4 = fig_trend_comparison(predictions)
    f5 = fig_summary_table(predictions)
    for p in [f1, f2, f3, f4, f5]:
        print(f"      ✓ {p.name}")

    print("[4/4] Writing text report...")
    report = write_report(predictions)
    print(f"      Saved: {report}")

    # ── Console summary ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  PREDICTION RESULTS — 2026 (Section 376 IPC)")
    print("=" * 60)
    print(f"  {'Rank':<5} {'District':<25} {'2022':>6} {'2023':>6} {'2026':>8}  Risk")
    print("  " + "─" * 55)
    for _, row in predictions.iterrows():
        a22 = f"{row['actual_2022']:.0f}" if pd.notna(row["actual_2022"]) else "–"
        a23 = f"{row['actual_2023']:.0f}" if pd.notna(row["actual_2023"]) else "–"
        print(f"  {int(row['rank']):<5} {row['district']:<25} {a22:>6} {a23:>6} "
              f"{row['predicted_2026']:>8.1f}  {row['risk']}")

    print("\n" + "=" * 60)
    print(f"  Total districts  : {len(predictions)}")
    print(f"  Total predicted  : {predictions['predicted_2026'].sum():.0f}")
    print(f"  Average / district: {predictions['predicted_2026'].mean():.1f}")
    hr = predictions[predictions["risk"] == "High"]
    print(f"  HIGH risk        : {len(hr)} districts → {', '.join(hr['district'].head(5).tolist())}")
    print("=" * 60)
    print("\n  ✅  Done! Check model_outputs/ for CSV, report, and figures.\n")


if __name__ == "__main__":
    main()
