# CRIMECAST - Report Materials

This folder contains documentation artifacts for the project report:

## Diagrams
- `system_flow_diagram.md` – High-level System Flow Diagram (updated for dashboard primary + DistilBERT + risk fusion + correct pipeline order)
- `data_flow_diagram.md` – General Data Flow Diagram (fixed fusion/training flows)
- `dfd_level_0.md` – **Level 0 DFD (Context Diagram)** — balanced external view
- `dfd_level_1.md` – **Level 1 DFD (Major Processes)** — 6 processes matching actual modules (sentiment before fusion, dashboard as P6)

**Note**: Run `python reports/generate_report_diagrams.py` (from project root) to regenerate matching PNGs in `reports/diagrams/`. Paste Mermaid code into https://mermaid.live for editing or screenshots.

## Reports
- `partial_report.md` – Partial project report

## Screenshots
- `screenshots/` – Folder for captured images + descriptions

## How to Use
- Open `.md` files in VS Code (with Mermaid extension recommended) or paste into https://mermaid.live
- All diagrams are created using Mermaid syntax for easy editing and rendering.

**Latest Update**: Added proper Level 0 and Level 1 Data Flow Diagrams.
