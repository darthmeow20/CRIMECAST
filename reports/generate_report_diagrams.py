from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Rectangle


OUTPUT_DIR = Path(__file__).resolve().parent / "diagrams"

COLORS = {
    "navy": "#17324D",
    "blue": "#2F6B9A",
    "teal": "#1F8A70",
    "green": "#4C956C",
    "orange": "#E58E26",
    "red": "#C94C4C",
    "gray": "#E9EEF2",
    "dark_gray": "#475569",
    "white": "#FFFFFF",
}


def add_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    text: str,
    color: str,
    fontsize: int = 10,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.012",
        facecolor=color,
        edgecolor=COLORS["navy"],
        linewidth=1.5,
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        color=COLORS["white"] if color != COLORS["gray"] else COLORS["navy"],
        fontsize=fontsize,
        fontweight="bold",
        wrap=True,
    )


def add_entity(ax: plt.Axes, x: float, y: float, width: float, height: float, text: str) -> None:
    patch = Rectangle(
        (x, y),
        width,
        height,
        facecolor=COLORS["gray"],
        edgecolor=COLORS["navy"],
        linewidth=1.8,
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        color=COLORS["navy"],
        fontsize=10,
        fontweight="bold",
    )


def add_process(ax: plt.Axes, x: float, y: float, width: float, height: float, text: str, color: str) -> None:
    patch = Ellipse(
        (x + width / 2, y + height / 2),
        width,
        height,
        facecolor=color,
        edgecolor=COLORS["navy"],
        linewidth=1.6,
    )
    ax.add_patch(patch)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        color=COLORS["white"],
        fontsize=9,
        fontweight="bold",
    )


def add_store(ax: plt.Axes, x: float, y: float, width: float, height: float, text: str) -> None:
    patch = Rectangle(
        (x, y),
        width,
        height,
        facecolor=COLORS["white"],
        edgecolor=COLORS["teal"],
        linewidth=2.0,
    )
    ax.add_patch(patch)
    ax.plot([x, x + width], [y + height * 0.72, y + height * 0.72], color=COLORS["teal"], linewidth=1.4)
    ax.text(
        x + width / 2,
        y + height / 2,
        text,
        ha="center",
        va="center",
        color=COLORS["navy"],
        fontsize=9,
        fontweight="bold",
    )


def add_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    label: str = "",
    curve: float = 0.0,
    label_offset: tuple[float, float] = (0.0, 0.018),
) -> None:
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=13,
        linewidth=1.5,
        color=COLORS["dark_gray"],
        connectionstyle=f"arc3,rad={curve}",
        shrinkA=2,
        shrinkB=2,
    )
    ax.add_patch(arrow)
    if label:
        ax.text(
            (start[0] + end[0]) / 2 + label_offset[0],
            (start[1] + end[1]) / 2 + label_offset[1],
            label,
            ha="center",
            va="center",
            fontsize=8,
            color=COLORS["dark_gray"],
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.5, "alpha": 0.9},
        )


def new_canvas(title: str, figsize: tuple[int, int] = (16, 9)) -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(
        0.5,
        0.965,
        title,
        ha="center",
        va="top",
        fontsize=19,
        fontweight="bold",
        color=COLORS["navy"],
    )
    return fig, ax


def save_figure(fig: plt.Figure, filename: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / filename
    fig.savefig(output_file, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_file


def generate_sfd() -> Path:
    fig, ax = new_canvas("System Flow Diagram (SFD) - CRIMECAST")

    top_boxes = [
        (0.03, "Crime CSVs\n2022-2023", COLORS["blue"]),
        (0.22, "File Discovery\nand Validation", COLORS["teal"]),
        (0.41, "Cleaning and\nStandardisation", COLORS["green"]),
        (0.60, "Multi-Year\nML Dataset", COLORS["orange"]),
        (0.79, "EDA and Feature\nEngineering", COLORS["blue"]),
    ]
    for x, text, color in top_boxes:
        add_box(ax, x, 0.72, 0.15, 0.12, text, color)

    for left, right in zip(top_boxes, top_boxes[1:]):
        add_arrow(ax, (left[0] + 0.15, 0.78), (right[0], 0.78))

    add_box(ax, 0.42, 0.45, 0.16, 0.12, "Model Comparison\nRF, GB, Ridge", COLORS["teal"])
    add_box(ax, 0.63, 0.45, 0.16, 0.12, "Evaluation and\nSaved Models", COLORS["green"])
    add_box(ax, 0.82, 0.45, 0.15, 0.12, "Predictions, Charts\nand Reports", COLORS["orange"])
    add_arrow(ax, (0.865, 0.72), (0.50, 0.57), "numeric features", curve=0.16)
    add_arrow(ax, (0.58, 0.51), (0.63, 0.51))
    add_arrow(ax, (0.79, 0.51), (0.82, 0.51))

    add_box(ax, 0.05, 0.16, 0.15, 0.12, "Complaint, News\nand Social Text", COLORS["red"])
    add_box(ax, 0.27, 0.16, 0.15, 0.12, "Text Cleaning and\nLabel Validation", COLORS["blue"])
    add_box(ax, 0.49, 0.16, 0.17, 0.12, "TF-IDF and Logistic\nRegression", COLORS["teal"])
    add_box(ax, 0.73, 0.16, 0.19, 0.12, "State and District\nSentiment Reports", COLORS["green"])
    add_arrow(ax, (0.20, 0.22), (0.27, 0.22))
    add_arrow(ax, (0.42, 0.22), (0.49, 0.22))
    add_arrow(ax, (0.66, 0.22), (0.73, 0.22))

    ax.text(0.03, 0.62, "CRIME PREDICTION FLOW", fontsize=11, fontweight="bold", color=COLORS["navy"])
    ax.text(0.03, 0.34, "SENTIMENT ANALYSIS FLOW", fontsize=11, fontweight="bold", color=COLORS["navy"])
    ax.text(
        0.5,
        0.04,
        "Outputs are accessed through main.py, app.py, prediction utilities, dashboard modules, and generated reports.",
        ha="center",
        fontsize=9,
        color=COLORS["dark_gray"],
    )
    return save_figure(fig, "system_flow_diagram.png")


def generate_dfd_level_0() -> Path:
    fig, ax = new_canvas("Data Flow Diagram - Level 0 (Context Diagram)")

    add_entity(ax, 0.05, 0.65, 0.19, 0.12, "Crime Data Sources")
    add_entity(ax, 0.05, 0.20, 0.19, 0.12, "Text Data Sources")
    add_process(ax, 0.37, 0.32, 0.28, 0.34, "0\nCRIMECAST\nSystem", COLORS["navy"])
    add_entity(ax, 0.77, 0.43, 0.18, 0.14, "User / Analyst")

    add_arrow(ax, (0.24, 0.71), (0.37, 0.58), "crime CSV files", curve=-0.06)
    add_arrow(ax, (0.24, 0.26), (0.37, 0.40), "labeled text", curve=0.06)
    add_arrow(ax, (0.77, 0.50), (0.65, 0.54), "analysis request", curve=0.08, label_offset=(0.0, 0.035))
    add_arrow(ax, (0.65, 0.43), (0.77, 0.47), "predictions and reports", curve=-0.08, label_offset=(0.0, -0.035))

    ax.text(
        0.5,
        0.10,
        "The Level 0 DFD treats CRIMECAST as one process and shows only external data exchange.",
        ha="center",
        fontsize=10,
        color=COLORS["dark_gray"],
    )
    return save_figure(fig, "dfd_level_0.png")


def generate_dfd_level_1() -> Path:
    fig, ax = new_canvas("Data Flow Diagram - Level 1")

    add_entity(ax, 0.02, 0.73, 0.14, 0.10, "Crime Data\nSources")
    add_entity(ax, 0.02, 0.18, 0.14, 0.10, "Text Data\nSources")
    add_entity(ax, 0.84, 0.42, 0.14, 0.12, "User / Analyst")

    add_process(ax, 0.20, 0.70, 0.14, 0.13, "1.0\nIngest Data", COLORS["blue"])
    add_process(ax, 0.40, 0.70, 0.15, 0.13, "2.0\nClean and\nIntegrate", COLORS["teal"])
    add_process(ax, 0.61, 0.70, 0.15, 0.13, "3.0\nTrain and\nEvaluate ML", COLORS["green"])
    add_process(ax, 0.79, 0.70, 0.16, 0.13, "4.0\nPredict and\nVisualise", COLORS["orange"])
    add_process(ax, 0.39, 0.16, 0.18, 0.14, "5.0\nAnalyse\nSentiment", COLORS["red"])

    add_store(ax, 0.20, 0.46, 0.15, 0.11, "D1  Raw Data")
    add_store(ax, 0.42, 0.46, 0.16, 0.11, "D2  Cleaned Data")
    add_store(ax, 0.64, 0.46, 0.15, 0.11, "D3  Model Store")
    add_store(ax, 0.69, 0.17, 0.16, 0.11, "D4  Results")

    add_arrow(ax, (0.16, 0.78), (0.20, 0.77), "CSV files")
    add_arrow(ax, (0.27, 0.70), (0.27, 0.57), "raw records")
    add_arrow(ax, (0.35, 0.515), (0.42, 0.515), "validated data")
    add_arrow(ax, (0.475, 0.70), (0.50, 0.57), "clean rows")
    add_arrow(ax, (0.58, 0.515), (0.64, 0.515), "features")
    add_arrow(ax, (0.685, 0.70), (0.715, 0.57), "trained model")
    add_arrow(ax, (0.79, 0.515), (0.87, 0.70), "model")
    add_arrow(ax, (0.95, 0.76), (0.98, 0.52), "outputs", curve=0.2)
    add_arrow(ax, (0.87, 0.70), (0.77, 0.28), "save outputs", curve=0.08, label_offset=(-0.025, -0.01))
    add_arrow(ax, (0.16, 0.23), (0.39, 0.23), "text records")
    add_arrow(ax, (0.48, 0.30), (0.50, 0.46), "sentiment data")
    add_arrow(ax, (0.57, 0.23), (0.69, 0.23), "scores and summaries")
    add_arrow(ax, (0.91, 0.54), (0.89, 0.70), "request", curve=-0.08, label_offset=(0.025, 0.0))
    add_arrow(ax, (0.85, 0.23), (0.91, 0.42), "reports")

    ax.text(
        0.5,
        0.055,
        "D1-D4 represent persistent CSV datasets, trained joblib models, predictions, metrics, figures, and reports.",
        ha="center",
        fontsize=9,
        color=COLORS["dark_gray"],
    )
    return save_figure(fig, "dfd_level_1.png")


def main() -> None:
    files = [generate_sfd(), generate_dfd_level_0(), generate_dfd_level_1()]
    for path in files:
        print(path)


if __name__ == "__main__":
    main()
