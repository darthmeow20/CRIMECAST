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
    "purple": "#7c3aed",
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

    # Top row: Data ingestion + clean + fuse
    top_boxes = [
        (0.02, "Raw Crime CSVs\n(2022-2023)", COLORS["blue"]),
        (0.18, "Clean + Standardize\n+ Time Features", COLORS["teal"]),
        (0.35, "DistilBERT\nSentiment", COLORS["red"]),
        (0.52, "Fuse Sentiment\n+ ML-Ready Data", COLORS["green"]),
        (0.70, "Train Models\n(Temporal + Risk)", COLORS["orange"]),
    ]
    for x, text, color in top_boxes:
        add_box(ax, x, 0.72, 0.14, 0.13, text, color)

    for i in range(len(top_boxes) - 1):
        add_arrow(ax, (top_boxes[i][0] + 0.14, 0.78), (top_boxes[i+1][0], 0.78))

    # Prediction / risk row
    add_box(ax, 0.18, 0.42, 0.16, 0.13, "Predict (any year)\n+ 2026 Batch", COLORS["blue"])
    add_box(ax, 0.40, 0.42, 0.18, 0.13, "Compute Risk Index\n(Volume + Neg. Sentiment)", COLORS["red"])
    add_box(ax, 0.64, 0.42, 0.16, 0.13, "Outputs: CSVs,\nFigures, Reports", COLORS["green"])

    add_arrow(ax, (0.59, 0.72), (0.26, 0.55), "fused data + models", curve=0.12)
    add_arrow(ax, (0.26, 0.55), (0.40, 0.55))
    add_arrow(ax, (0.49, 0.55), (0.64, 0.55))

    # Dashboard + CLI row (bottom)
    add_box(ax, 0.15, 0.15, 0.22, 0.12, "Primary UI:\nStreamlit Dashboard\n(live predict + sentiment)", "#7c3aed")
    add_box(ax, 0.45, 0.15, 0.22, 0.12, "CLI: Full Pipeline\n(app.py option 1)\n+ Individual steps", COLORS["teal"])
    add_box(ax, 0.75, 0.15, 0.18, 0.12, "Interactive\n+ Batch 2026\nForecasts", COLORS["orange"])

    add_arrow(ax, (0.72, 0.55), (0.26, 0.27), curve=-0.18)
    add_arrow(ax, (0.26, 0.27), (0.45, 0.27))
    add_arrow(ax, (0.56, 0.27), (0.75, 0.27))

    ax.text(0.03, 0.62, "CORE PIPELINE (sentiment first)", fontsize=11, fontweight="bold", color=COLORS["navy"])
    ax.text(0.03, 0.32, "PREDICTION + RISK", fontsize=11, fontweight="bold", color=COLORS["navy"])
    ax.text(
        0.5,
        0.03,
        "Primary user interface is the light-theme Streamlit dashboard. Full training via CLI pipeline. Risk blends prediction volume with negative sentiment.",
        ha="center",
        fontsize=9,
        color=COLORS["dark_gray"],
    )
    return save_figure(fig, "system_flow_diagram.png")


def generate_dfd_level_0() -> Path:
    fig, ax = new_canvas("Data Flow Diagram - Level 0 (Context Diagram)")

    add_entity(ax, 0.04, 0.68, 0.18, 0.11, "Crime Data Sources\n(Raw CSVs)")
    add_entity(ax, 0.04, 0.18, 0.18, 0.11, "Text Data Sources\n(Complaints/News)")
    add_process(ax, 0.36, 0.30, 0.28, 0.38, "0\nCRIMECAST\nSystem", COLORS["navy"])
    add_entity(ax, 0.78, 0.42, 0.18, 0.14, "User / Analyst\n(Dashboard + CLI)")

    add_arrow(ax, (0.22, 0.73), (0.36, 0.58), "Raw Crime Data", curve=-0.05)
    add_arrow(ax, (0.22, 0.24), (0.36, 0.38), "Unstructured Text", curve=0.05)
    add_arrow(ax, (0.78, 0.52), (0.64, 0.55), "Requests", curve=0.07, label_offset=(0.0, 0.03))
    add_arrow(ax, (0.64, 0.42), (0.78, 0.48), "Predictions + Risk,\nSentiment, 2026,\nDashboard UI", curve=-0.07, label_offset=(0.0, -0.03))

    ax.text(
        0.5,
        0.08,
        "Level 0: Single process. Inputs = raw CSVs + text. Outputs = predictions/risk, sentiment results, forecasts, interactive dashboard. Must balance at Level 1.",
        ha="center",
        fontsize=9,
        color=COLORS["dark_gray"],
    )
    return save_figure(fig, "dfd_level_0.png")


def generate_dfd_level_1() -> Path:
    fig, ax = new_canvas("Data Flow Diagram - Level 1")

    # External entities
    add_entity(ax, 0.02, 0.76, 0.12, 0.09, "Crime Data\nSources")
    add_entity(ax, 0.02, 0.16, 0.12, 0.09, "Text Data\nSources")
    add_entity(ax, 0.86, 0.45, 0.12, 0.11, "User / Analyst")

    # Level 1 processes (6 bubbles)
    add_process(ax, 0.17, 0.72, 0.12, 0.11, "1.0 Ingest\n& Clean", COLORS["blue"])
    add_process(ax, 0.34, 0.72, 0.12, 0.11, "2.0\nSentiment", COLORS["red"])
    add_process(ax, 0.51, 0.72, 0.12, 0.11, "3.0 Fuse\n+ ML Data", COLORS["teal"])
    add_process(ax, 0.68, 0.72, 0.12, 0.11, "4.0 Train\nModels", COLORS["green"])
    add_process(ax, 0.51, 0.38, 0.12, 0.11, "5.0 Predict\n+ Risk", COLORS["orange"])
    add_process(ax, 0.68, 0.38, 0.13, 0.11, "6.0 Dashboard\n& Outputs", "#7c3aed")

    # Data stores (open rectangles)
    add_store(ax, 0.17, 0.50, 0.12, 0.09, "D2 ML-Ready")
    add_store(ax, 0.34, 0.50, 0.12, 0.09, "D3 Sentiment")
    add_store(ax, 0.51, 0.50, 0.12, 0.09, "D4 Models")
    add_store(ax, 0.68, 0.20, 0.12, 0.09, "D5 Results")

    # Flows - crime data path (left to right top)
    add_arrow(ax, (0.14, 0.80), (0.17, 0.78), "raw CSVs")
    add_arrow(ax, (0.23, 0.72), (0.23, 0.59), "cleaned")
    add_arrow(ax, (0.29, 0.72), (0.29, 0.59), "text")

    # Sentiment path
    add_arrow(ax, (0.40, 0.72), (0.40, 0.59), "scores")
    add_arrow(ax, (0.40, 0.59), (0.51, 0.59), "agg")

    # Fuse to ML-ready store
    add_arrow(ax, (0.57, 0.72), (0.57, 0.59), "fused")
    add_arrow(ax, (0.23, 0.59), (0.23, 0.59))
    add_arrow(ax, (0.23, 0.50), (0.23, 0.59))  # from cleaned store area

    # To training
    add_arrow(ax, (0.23, 0.50), (0.51, 0.50), "features", curve=0.0)
    add_arrow(ax, (0.57, 0.72), (0.68, 0.72), "ml data")
    add_arrow(ax, (0.74, 0.72), (0.74, 0.59), "models")

    # Connect ML store + models + sentiment to Predict (P5)
    add_arrow(ax, (0.51, 0.50), (0.51, 0.49), "data")
    add_arrow(ax, (0.57, 0.50), (0.57, 0.49), "+ models")
    add_arrow(ax, (0.57, 0.38), (0.57, 0.49))

    # Predict to D5 Results
    add_arrow(ax, (0.57, 0.38), (0.68, 0.29), "pred + risk")

    # From stores and P5 to P6 (Dashboard)
    add_arrow(ax, (0.74, 0.59), (0.74, 0.49), "models")
    add_arrow(ax, (0.74, 0.38), (0.74, 0.29))

    # Output arrows from P6
    add_arrow(ax, (0.81, 0.38), (0.86, 0.50), "Interactive Dashboard\n+ Reports/CSVs", curve=0.06)

    # Sentiment aggregation and fusion connections
    add_arrow(ax, (0.40, 0.59), (0.51, 0.59), "sentiment agg")
    add_arrow(ax, (0.51, 0.72), (0.51, 0.59), "enrich")

    # User requests to P5/P6
    add_arrow(ax, (0.86, 0.52), (0.81, 0.44), "requests", curve=-0.08)
    add_arrow(ax, (0.81, 0.44), (0.68, 0.44))

    ax.text(
        0.5,
        0.03,
        "Balanced with Level 0. Sentiment (2.0) & cleaning (1.0) feed fusion (3.0). Training (4.0) produces models for prediction+ risk (5.0). P6 serves the interactive dashboard (primary) and static outputs. All external flows match context diagram.",
        ha="center",
        fontsize=8,
        color=COLORS["dark_gray"],
    )
    return save_figure(fig, "dfd_level_1.png")


def main() -> None:
    files = [generate_sfd(), generate_dfd_level_0(), generate_dfd_level_1()]
    for path in files:
        print(path)


if __name__ == "__main__":
    main()
