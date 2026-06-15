from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from train_model import ML_READY_FILE, OUTPUT_DIR, train_models


FIGURE_DIR = OUTPUT_DIR / "figures"
PREDICTIONS_FILE = OUTPUT_DIR / "fitted_predictions.csv"

sns.set_theme(style="whitegrid", context="notebook")


def ensure_inputs(data_path: Path, predictions_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not data_path.exists() or not predictions_path.exists():
        train_models(data_path=data_path)

    return pd.read_csv(data_path), pd.read_csv(predictions_path)


def save_bar_chart(
    df: pd.DataFrame,
    value_column: str,
    title: str,
    output_file: Path,
    top_n: int = 12,
) -> Path:
    plot_df = df.nlargest(top_n, value_column).sort_values(value_column)
    plot_df = plot_df.assign(area_year=plot_df["district_city"] + " (" + plot_df["year"].astype(str) + ")")

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=plot_df, x=value_column, y="area_year", hue="area_type", dodge=False, ax=ax)
    ax.set_title(title)
    ax.set_xlabel(value_column.replace("_", " ").title())
    ax.set_ylabel("")
    ax.legend(title="Area type", loc="lower right")
    fig.tight_layout()
    fig.savefig(output_file, dpi=160)
    plt.close(fig)
    return output_file


def save_share_chart(df: pd.DataFrame, output_file: Path, top_n: int = 12) -> Path:
    columns = ["district_city", "year", "complaints_total_complaints", "complaints_oral_share", "complaints_written_share"]
    plot_df = df.dropna(subset=["complaints_oral_share", "complaints_written_share"]).nlargest(
        top_n,
        "complaints_total_complaints",
    )[columns].copy()
    plot_df = plot_df.sort_values("complaints_total_complaints")
    plot_df = plot_df.assign(area_year=plot_df["district_city"] + " (" + plot_df["year"].astype(str) + ")")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(plot_df["area_year"], plot_df["complaints_oral_share"], label="Oral")
    ax.barh(
        plot_df["area_year"],
        plot_df["complaints_written_share"],
        left=plot_df["complaints_oral_share"],
        label="Written",
    )
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of total complaints")
    ax.set_ylabel("")
    ax.set_title("Complaint Mode Share in Highest Complaint Areas")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(output_file, dpi=160)
    plt.close(fig)
    return output_file


def save_actual_vs_predicted(predictions: pd.DataFrame, output_file: Path) -> Path:
    target_labels = predictions["target_label"].drop_duplicates().to_list()
    fig, axes = plt.subplots(1, len(target_labels), figsize=(6 * len(target_labels), 5))
    if len(target_labels) == 1:
        axes = [axes]

    for ax, target_label in zip(axes, target_labels):
        target_df = predictions[predictions["target_label"] == target_label]
        sns.scatterplot(data=target_df, x="actual", y="predicted", hue="area_type", ax=ax)
        max_value = max(float(target_df["actual"].max()), float(target_df["predicted"].max()))
        ax.plot([0, max_value], [0, max_value], color="black", linewidth=1, linestyle="--")
        ax.set_title(target_label)
        ax.set_xlabel("Actual")
        ax.set_ylabel("Predicted")

    fig.suptitle("Actual vs Predicted Crime Counts", y=1.02)
    fig.tight_layout()
    fig.savefig(output_file, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return output_file


def write_visual_report(created_files: list[Path], output_dir: Path) -> Path:
    report_file = output_dir / "visual_report.md"
    lines = [
        "# Visual Analysis Report",
        "",
        "Generated chart files:",
        "",
    ]

    for path in created_files:
        lines.append(f"- `{path.name}`")

    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_file


def create_visualizations(
    data_path: Path = ML_READY_FILE,
    predictions_path: Path = PREDICTIONS_FILE,
    output_dir: Path = FIGURE_DIR,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    df, predictions = ensure_inputs(data_path, predictions_path)

    created_files = [
        save_bar_chart(
            df,
            "complaints_total_complaints",
            "Top Areas by Total Complaints",
            output_dir / "top_total_complaints.png",
        ),
        save_bar_chart(
            df,
            "murder_homicide_murder_incidence",
            "Top Areas by Murder Incidence",
            output_dir / "top_murder_incidence.png",
        ),
        save_bar_chart(
            df,
            "women_crimes_rape_sec_376_i",
            "Top Areas by Rape Incidents",
            output_dir / "top_rape_incidents.png",
        ),
        save_share_chart(df, output_dir / "complaint_mode_share.png"),
        save_actual_vs_predicted(predictions, output_dir / "actual_vs_predicted.png"),
    ]
    report_file = write_visual_report(created_files, output_dir)

    return {
        "figure_dir": output_dir,
        "report": report_file,
        **{path.stem: path for path in created_files},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create CRIMECAST analysis and model evaluation charts.")
    parser.add_argument("--data-path", type=Path, default=ML_READY_FILE)
    parser.add_argument("--predictions-path", type=Path, default=PREDICTIONS_FILE)
    parser.add_argument("--output-dir", type=Path, default=FIGURE_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = create_visualizations(args.data_path, args.predictions_path, args.output_dir)
    print(f"Charts written to: {outputs['figure_dir']}")
    print(f"Visual report: {outputs['report']}")


if __name__ == "__main__":
    main()
