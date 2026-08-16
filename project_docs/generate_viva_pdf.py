# -*- coding: utf-8 -*-
"""
Generate CRIMECAST viva prep PDF.

  py -3 project_docs/generate_viva_pdf.py

Output: project_docs/CRIMECAST_VIVA_PREP.pdf
"""
from __future__ import annotations

import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "CRIMECAST_VIVA_PREP.pdf"


def build_with_reportlab() -> Path:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
        ListFlowable,
        ListItem,
        KeepTogether,
    )

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="CRIMECAST Viva Prep",
        author="CRIMECAST",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontSize=18,
            spaceAfter=8,
            textColor=colors.HexColor("#991b1b"),
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverSub",
            parent=styles["Normal"],
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=4,
            textColor=colors.HexColor("#374151"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1c",
            parent=styles["Heading1"],
            fontSize=14,
            spaceBefore=14,
            spaceAfter=8,
            textColor=colors.HexColor("#111827"),
            borderPadding=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2c",
            parent=styles["Heading2"],
            fontSize=11.5,
            spaceBefore=10,
            spaceAfter=5,
            textColor=colors.HexColor("#1e3a5f"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyJ",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Say",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0f766e"),
            leftIndent=8,
            spaceAfter=8,
            spaceBefore=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Pitch",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1f2937"),
            spaceBefore=6,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#4b5563"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Cell",
            parent=styles["Normal"],
            fontSize=8,
            leading=10.5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CellB",
            parent=styles["Normal"],
            fontSize=8,
            leading=10.5,
            fontName="Helvetica-Bold",
        )
    )

    story = []

    def h1(t):
        story.append(Paragraph(t, styles["H1c"]))

    def h2(t):
        story.append(Paragraph(t, styles["H2c"]))

    def body(t):
        story.append(Paragraph(t, styles["BodyJ"]))

    def say(t):
        story.append(Paragraph(f"<b>Say:</b> <i>{t}</i>", styles["Say"]))

    def bullets(items):
        lis = [ListItem(Paragraph(i, styles["Body"]), leftIndent=12, value="•") for i in items]
        story.append(ListFlowable(lis, bulletType="bullet", start="•", leftIndent=15))
        story.append(Spacer(1, 4))

    def tbl(headers, rows, col_widths=None):
        data = [[Paragraph(str(h), styles["CellB"]) for h in headers]]
        for row in rows:
            data.append([Paragraph(str(c), styles["Cell"]) for c in row])
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#eef2ff")]),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 8))

    # Cover
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("CRIMECAST", styles["CoverTitle"]))
    story.append(
        Paragraph(
            "Crime Analysis, Prediction &amp; Sentiment Analysis<br/>Using Machine Learning (Tamil Nadu Districts)",
            styles["CoverSub"],
        )
    )
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>VIVA PREPARATION GUIDE</b>", styles["CoverSub"]))
    story.append(Paragraph("How the project works · Expected examiner questions", styles["CoverSub"]))
    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            "College prototype · Not a live police system · Not an official SCRB forecast",
            styles["Small"],
        )
    )
    story.append(PageBreak())

    # Elevator
    h1("1. Elevator pitch (memorise)")
    story.append(
        Paragraph(
            "“CRIMECAST cleans multi-table Tamil Nadu crime stats, trains classical ML for "
            "district rates and counts with honest temporal metrics, adds news sentiment for "
            "live context, and shows 2026 as a <b>scenario</b> with maps, compare, and "
            "explainability — not as official SCRB output.”",
            styles["Pitch"],
        )
    )

    # Blocks
    h1("2. How it works — block by block")
    body(
        "Pipeline: <b>Data → Clean → Train → Predict → News/Sentiment → Dashboard</b>, "
        "with a parallel <b>2026 trend scenario</b> branch."
    )

    h2("Block 1 — Data (inputs)")
    tbl(
        ["Source", "Role"],
        [
            ["Official-style CSVs (complaints, murder, women crimes)", "Numbers for ML; train mainly on official-era years ≤2023"],
            ["News harvest (Tamil + English)", "Live heat, sentiment, word clouds — <b>not FIRs</b>"],
            ["SQLite (data/crimecast.db)", "Headlines, alerts, optional migrated tables"],
        ],
        [6.5 * cm, 10.5 * cm],
    )
    say("We separate official labels used for training from media used for live awareness.")

    h2("Block 2 — Clean (clean_data.py)")
    bullets(
        [
            "Discover yearly CSVs; fix headers (e.g. muder → murder)",
            "Drop TOTAL aggregate rows (no double counting)",
            "Merge into crimecast_ml_ready.csv (district × year)",
            "Map cities to 38 TN districts (Madurai City→Madurai, Avadi→Chennai)",
        ]
    )
    say("One ML-ready table, consistent districts.")

    h2("Block 3 — Train (train_model.py)")
    bullets(
        [
            "Targets: complaints, murder count/rate, rape count/rate, cognizable rate",
            "Models: Dummy, Ridge, Random Forest, Gradient Boosting (often log targets)",
            "Select best via CV + temporal holdout where possible",
            "Save models/*.joblib + training_metrics.csv",
        ]
    )
    say("We don’t claim perfect forecasting; we show temporal metrics honestly.")

    h2("Block 4 — Predict (predict.py)")
    bullets(
        [
            "Resolve district (TN38) → build features for year",
            "Model raw prediction → blend with district history",
            "Rates lean more on history so rankings stay realistic",
            "Optional: populate all 38 districts; map has no news fill",
        ]
    )
    say("Blend keeps sticky rates (e.g. high murder-rate districts) from going wild.")

    h2("Block 5 — 2026 scenario (forecast_engine)")
    bullets(
        [
            "Per-district trend on history (not Prophet / LSTM)",
            "Methods: linear · last year · blend",
            "Uncertainty bands (low–mid–high)",
            "Scenario only — not SCRB official",
        ]
    )
    say("Short time series → simple trend + bands, more honest than black-box deep models.")

    h2("Block 6 — News + sentiment")
    bullets(
        [
            "Harvest headlines → DistilBERT if available, else lexicon",
            "District concern score + word clouds",
            "Live Feed = news volume in a time window",
        ]
    )
    say("Media tone and volume, not crime registration.")

    h2("Block 7 — Dashboard (demo UI)")
    tbl(
        ["Tab", "One line"],
        [
            ["Live Feed", "News heat + alerts"],
            ["District Map", "Choropleth / heat / per-lakh scoreboard"],
            ["Accuracy", "Metrics, claim/don’t claim, blend check"],
            ["Predict", "One district + all-district map"],
            ["Sentiment", "Map + word cloud"],
            ["2026", "Multi-target scenario map + bands"],
            ["District Compare", "Side-by-side + carve maps + brief"],
            ["Risk Explain", "Why high risk (composite + LIME-style)"],
            ["Health", "Files/models ready?"],
        ],
        [4.5 * cm, 12.5 * cm],
    )
    story.append(PageBreak())

    # Demo path
    h1("3. Five-minute demo path")
    numbered = [
        "<b>Live</b> — “This is news heat, not FIRs.”",
        "<b>Map</b> — official rates / density; per-lakh ranking.",
        "<b>Accuracy</b> — test R², temporal limits, what we claim.",
        "<b>Predict</b> — one district + drivers.",
        "<b>2026</b> — scenario + uncertainty.",
        "<b>Compare</b> — e.g. Thoothukudi vs Madurai.",
        "<b>Explain</b> — risk factors.",
    ]
    for i, t in enumerate(numbered, 1):
        story.append(Paragraph(f"{i}. {t}", styles["Body"]))

    # Questions
    h1("4. Expected examiner questions")

    h2("A. Problem &amp; scope")
    tbl(
        ["Question", "Short answer"],
        [
            ["What is CRIMECAST?", "TN district crime analysis + ML prediction + news sentiment + Streamlit demo."],
            ["Is this a police system?", "No — academic prototype only."],
            ["Out of scope?", "Real-time FIR system, causal policy proof, official 2026 SCRB authority."],
        ],
        [5.5 * cm, 11.5 * cm],
    )

    h2("B. Data")
    tbl(
        ["Question", "Short answer"],
        [
            ["Data sources?", "SCRB/NCRB-style tables + news harvest."],
            ["Why remove TOTAL rows?", "Avoid double counting state aggregates."],
            ["What is TN38?", "38 official districts; cities rolled into parents."],
            ["News = crime?", "No. Volume/tone support only."],
            ["Training years?", "Mainly official-era ≤2023; later years thinner/proxy for maps."],
        ],
        [5.5 * cm, 11.5 * cm],
    )

    h2("C. Machine learning")
    tbl(
        ["Question", "Short answer"],
        [
            ["Which algorithms?", "Ridge, RF, GB (+ dummy); best per target."],
            ["Evaluation?", "CV MAE/RMSE/R² + temporal holdout."],
            ["Why weak temporal R² sometimes?", "Few official years → hard year-to-year generalisation (we show it)."],
            ["What is blend?", "Model + district history; rates weight history more."],
            ["Why not LSTM/Prophet?", "Short yearly series; simple models more honest."],
            ["Leakage control?", "Exclude target’s own source family from features."],
        ],
        [5.5 * cm, 11.5 * cm],
    )

    h2("D. 2026 forecast")
    tbl(
        ["Question", "Short answer"],
        [
            ["How is 2026 made?", "District trend: linear / last-year / blend + bands."],
            ["Official SCRB?", "No — scenario for discussion."],
            ["Uncertainty?", "Residual/horizon-style low–mid–high band."],
        ],
        [5.5 * cm, 11.5 * cm],
    )

    h2("E. Sentiment &amp; explainability")
    tbl(
        ["Question", "Short answer"],
        [
            ["DistilBERT role?", "Headline polarity when available; lexicon fallback."],
            ["Word cloud?", "Frequent terms in district headlines."],
            ["SHAP/LIME?", "Importance×z or local linear (LIME-style); optional real SHAP."],
        ],
        [5.5 * cm, 11.5 * cm],
    )

    h2("F. Engineering &amp; testing")
    tbl(
        ["Question", "Short answer"],
        [
            ["Why Streamlit?", "Fast interactive maps/tables for demo."],
            ["Why SQLite?", "Zero-server local store; CSVs remain backup."],
            ["Postgres?", "Future only — not full production path yet."],
            ["Testing?", "Unit + integration + data quality + UI checklist; py -3 run_tests.py."],
            ["No news fill on predict/2026 maps?", "Colours mean model/forecast, not media volume."],
        ],
        [5.5 * cm, 11.5 * cm],
    )

    h2("G. Ethics &amp; limits")
    tbl(
        ["Question", "Short answer"],
        [
            ["Bias?", "Under-reporting, media bias, uneven district reporting."],
            ["Misuse?", "Must not drive arrests/policing automatically."],
            ["Limitations?", "Short series; media ≠ crime; scenario forecasts."],
            ["Future work?", "More official years, monthly data, multi-user DB, deeper Tamil NLP."],
        ],
        [5.5 * cm, 11.5 * cm],
    )
    story.append(PageBreak())

    # Stuck lines
    h1("5. If stuck — safe lines")
    bullets(
        [
            "“That’s a scenario, not an official forecast.”",
            "“That’s news volume, not registered crime.”",
            "“With only a few official years we prefer simple, interpretable methods.”",
            "“We blend with history so rate rankings stay realistic.”",
            "“We report temporal metrics honestly — even when they are weak.”",
        ]
    )

    h1("6. Day-of checklist")
    bullets(
        [
            "Restart Streamlit; open http://localhost:8501",
            "Walk demo path (Section 3) in ~5 minutes",
            "Know one Accuracy number if asked (e.g. temporal R² for a rate target)",
            "Know unit vs integration vs UI testing (run_tests.py + checklist)",
            "Stay calm on limitations — honesty scores well",
        ]
    )

    h1("7. Quick commands")
    body("<b>Dashboard:</b>  py -3 -m streamlit run dashboard.py --server.port 8501")
    body("<b>Tests:</b>  py -3 run_tests.py")
    body("<b>Health:</b>  py -3 health_check.py")

    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            "— End of viva prep —  ·  CRIMECAST academic prototype",
            styles["CoverSub"],
        )
    )

    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawString(1.8 * cm, 1.0 * cm, "CRIMECAST · Viva Prep")
        canvas.drawRightString(A4[0] - 1.8 * cm, 1.0 * cm, f"Page {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return OUT


def build_with_fpdf() -> Path:
    from fpdf import FPDF

    class PDF(FPDF):
        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, f"CRIMECAST Viva Prep  |  Page {self.page_no()}", align="C")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, "CRIMECAST — Viva Preparation Guide", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(4)
    pdf.multi_cell(
        0,
        5,
        "How the project works block-by-block and expected examiner questions.\n"
        "Prototype only — not a live police system / not official SCRB forecast.",
        align="C",
    )
    pdf.ln(6)

    sections = [
        (
            "Elevator pitch",
            "CRIMECAST cleans multi-table TN crime stats, trains classical ML for district "
            "rates/counts with honest temporal metrics, adds news sentiment for live context, "
            "and shows 2026 as a scenario with maps, compare, and explainability — not SCRB official.",
        ),
        (
            "Blocks",
            "1 Data (official CSVs + news)\n"
            "2 Clean (ML-ready, TN38, drop TOTAL)\n"
            "3 Train (Ridge/RF/GB, temporal metrics)\n"
            "4 Predict (model + history blend, no news fill on map)\n"
            "5 2026 scenario (linear/last-year/blend + bands)\n"
            "6 News/sentiment (not FIRs)\n"
            "7 Dashboard (Live, Map, Accuracy, Predict, Sentiment, 2026, Compare, Explain, Health)",
        ),
        (
            "Demo path (5 min)",
            "Live (news not FIRs) -> Map -> Accuracy -> Predict -> 2026 scenario -> Compare -> Explain",
        ),
        (
            "Key Q&A",
            "Police system? No, academic prototype.\n"
            "News = crime? No.\n"
            "2026 official? No, scenario.\n"
            "Why blend? Sticky rates / realistic ranking.\n"
            "Why not Prophet/LSTM? Short yearly series.\n"
            "Weak temporal R2? Few official years; we report honestly.\n"
            "Testing? py -3 run_tests.py + UI checklist.\n"
            "Ethics? No automated policing; media bias; under-reporting.",
        ),
        (
            "Safe lines",
            "Scenario not official forecast. / News volume not registered crime. / "
            "Simple interpretable methods. / Blend with history. / Honest metrics.",
        ),
    ]
    for title, text in sections:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 58, 95)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(20, 20, 20)
        pdf.multi_cell(0, 5, text)
        pdf.ln(3)

    pdf.output(str(OUT))
    return OUT


def build_html_fallback() -> Path:
    """Write HTML if no PDF lib; user can Print → PDF."""
    html_path = OUT.with_suffix(".html")
    html_path.write_text(
        """<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>CRIMECAST Viva Prep</title>
<style>
 body{font-family:Segoe UI,Arial,sans-serif;max-width:800px;margin:24px auto;color:#111;line-height:1.45}
 h1{color:#991b1b} h2{color:#1e3a5f;border-bottom:1px solid #ddd;padding-bottom:4px}
 table{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0}
 th,td{border:1px solid #ccc;padding:6px 8px;vertical-align:top}
 th{background:#1e293b;color:#fff;text-align:left}
 .say{color:#0f766e;font-style:italic;margin:6px 0 12px}
 .pitch{background:#f8fafc;border-left:4px solid #991b1b;padding:12px;margin:12px 0}
 @media print{body{margin:12mm}}
</style></head><body>
<h1>CRIMECAST — Viva Preparation Guide</h1>
<p><b>How the project works · Expected examiner questions</b><br/>
College prototype · Not a live police system · Not an official SCRB forecast</p>

<div class="pitch"><b>Elevator pitch:</b> CRIMECAST cleans multi-table TN crime stats, trains classical ML
for district rates/counts with honest temporal metrics, adds news sentiment for live context,
and shows 2026 as a <b>scenario</b> with maps, compare, and explainability — not SCRB official.</div>

<h2>1. Pipeline</h2>
<p><b>Data → Clean → Train → Predict → News/Sentiment → Dashboard</b> (+ 2026 trend branch)</p>
<ol>
<li><b>Data</b> — Official-style CSVs (train ≤2023 era); news harvest (not FIRs); SQLite.</li>
<li><b>Clean</b> — Fix headers, drop TOTAL, ML-ready table, TN38 city rollup.</li>
<li><b>Train</b> — Ridge/RF/GB per target; CV + temporal metrics; joblib models.</li>
<li><b>Predict</b> — Model + history blend; all-district map without news fill.</li>
<li><b>2026</b> — Linear / last-year / blend + uncertainty; scenario only.</li>
<li><b>Sentiment</b> — DistilBERT/lexicon; concern map; word clouds.</li>
<li><b>UI</b> — Live, Map, Accuracy, Predict, Sentiment, 2026, Compare, Explain, Health.</li>
</ol>

<h2>2. Demo path (5 min)</h2>
<p>Live (news ≠ FIRs) → Map → Accuracy → Predict → 2026 scenario → Compare → Explain</p>

<h2>3. Expected questions (short answers)</h2>
<table>
<tr><th>Topic</th><th>Q</th><th>A</th></tr>
<tr><td>Scope</td><td>Police system?</td><td>No — academic prototype.</td></tr>
<tr><td>Data</td><td>News = crime?</td><td>No — volume/tone only.</td></tr>
<tr><td>Data</td><td>TN38?</td><td>38 districts; cities → parents.</td></tr>
<tr><td>ML</td><td>Models?</td><td>Ridge, RF, GB; best per target.</td></tr>
<tr><td>ML</td><td>Blend?</td><td>Model + history; rates lean on history.</td></tr>
<tr><td>ML</td><td>Prophet/LSTM?</td><td>Short yearly series; simple methods.</td></tr>
<tr><td>2026</td><td>Official SCRB?</td><td>No — scenario + bands.</td></tr>
<tr><td>Eng</td><td>Testing?</td><td>py -3 run_tests.py + UI checklist.</td></tr>
<tr><td>Ethics</td><td>Limits?</td><td>Short series; media bias; no auto-policing.</td></tr>
</table>

<h2>4. Safe lines</h2>
<ul>
<li>Scenario, not official forecast.</li>
<li>News volume, not registered crime.</li>
<li>Simple, interpretable methods.</li>
<li>Blend with history for realistic ranks.</li>
<li>Honest temporal metrics.</li>
</ul>

<p style="color:#666;font-size:12px">Print this page (Ctrl+P → Save as PDF) if reportlab/fpdf is unavailable.</p>
</body></html>
""",
        encoding="utf-8",
    )
    return html_path


def main() -> int:
    try:
        path = build_with_reportlab()
        print(f"[OK] PDF → {path}")
        return 0
    except ImportError:
        print("[INFO] reportlab not installed, trying fpdf…")
    except Exception as e:
        print(f"[WARN] reportlab failed: {e}; trying fpdf…")

    try:
        path = build_with_fpdf()
        print(f"[OK] PDF → {path}")
        return 0
    except ImportError:
        print("[INFO] fpdf not installed")
    except Exception as e:
        print(f"[WARN] fpdf failed: {e}")

    html = build_html_fallback()
    print(f"[OK] HTML fallback → {html}")
    print("Open in browser → Ctrl+P → Save as PDF")
    print("Or:  py -3 -m pip install reportlab  &&  py -3 project_docs/generate_viva_pdf.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
