# -*- coding: utf-8 -*-
"""
Generate simple-English project explanation PDF for viva.

  py -3 project_docs/generate_simple_explain_pdf.py

Output: project_docs/CRIMECAST_SIMPLE_EXPLAIN.pdf
Also always writes: project_docs/CRIMECAST_SIMPLE_EXPLAIN.html (print → PDF)
"""
from __future__ import annotations

from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
PDF = OUT_DIR / "CRIMECAST_SIMPLE_EXPLAIN.pdf"
HTML = OUT_DIR / "CRIMECAST_SIMPLE_EXPLAIN.html"


def write_html() -> Path:
    HTML.write_text(
        r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>CRIMECAST — How the Project Works (Simple English)</title>
<style>
  @page { size: A4; margin: 14mm; }
  body { font-family: "Segoe UI", Calibri, Arial, sans-serif; color: #111;
         max-width: 820px; margin: 0 auto; padding: 18px 14px 36px; font-size: 10.5pt; line-height: 1.45; }
  h1 { color: #991b1b; font-size: 1.4rem; border-bottom: 2px solid #991b1b; padding-bottom: 4px; }
  h1.cover { text-align: center; border: none; font-size: 1.55rem; margin-top: 1.5rem; }
  h2 { color: #1e3a5f; font-size: 1.08rem; margin-top: 1.1em; }
  .sub { text-align: center; color: #4b5563; margin: 0.2em 0; }
  .box { background: #f8fafc; border-left: 4px solid #991b1b; padding: 10px 12px; margin: 12px 0; }
  .say { color: #0f766e; font-style: italic; margin: 4px 0 10px 6px; font-size: 10pt; }
  table { width: 100%; border-collapse: collapse; font-size: 9.2pt; margin: 8px 0 12px; }
  th, td { border: 1px solid #cbd5e1; padding: 5px 7px; vertical-align: top; text-align: left; }
  th { background: #1e293b; color: #fff; }
  tr:nth-child(even) td { background: #f1f5f9; }
  pre.flow { background: #0f172a; color: #e2e8f0; padding: 12px 14px; border-radius: 6px;
             font-size: 9pt; overflow-x: auto; line-height: 1.4; }
  ul, ol { margin: 4px 0 10px 1.15em; }
  li { margin: 2px 0; }
  .muted { color: #6b7280; font-size: 9pt; text-align: center; margin-top: 1.5rem; }
  .page-break { page-break-before: always; }
  @media print { body { padding: 0; max-width: none; } table, .box, pre { page-break-inside: avoid; } }
</style>
</head>
<body>

<h1 class="cover">CRIMECAST</h1>
<p class="sub"><b>How the Project Works — Simple English</b></p>
<p class="sub">What it does · Modules · Algorithms · Data · Tools</p>
<p class="sub muted">College prototype · Not a live police system · Not an official SCRB forecast</p>

<div class="box">
  <b>30-second summary:</b><br/>
  CRIMECAST is a Python Streamlit app for Tamil Nadu districts. We clean multi-year crime CSVs into
  one table, train classical machine-learning models (Ridge, Random Forest, Gradient Boosting),
  predict rates and counts with a history blend, add news sentiment for live context, and show 2026
  as a <b>scenario</b> with maps, compare, and simple explanations.
</div>

<h1>1. What is this project?</h1>
<p><b>CRIMECAST</b> helps people:</p>
<ul>
  <li>Look at <b>crime-related numbers</b> for Tamil Nadu districts</li>
  <li><b>Predict</b> rates/counts with machine learning</li>
  <li>Sketch a <b>2026 scenario</b> (not an official forecast)</li>
  <li>See what the <b>news</b> is saying (sentiment / heat)</li>
  <li>Use one <b>web dashboard</b> for maps, compare, and explain</li>
</ul>
<p><b>It is not</b> a live police system and <b>not</b> an official government forecast.</p>

<h1>2. What does it do?</h1>
<table>
  <tr><th>Feature</th><th>In simple words</th></tr>
  <tr><td>Load crime tables</td><td>Reads CSV files (complaints, murder, crimes against women)</td></tr>
  <tr><td>Clean data</td><td>Fixes names, removes TOTAL rows, standardises districts</td></tr>
  <tr><td>Train models</td><td>Learns patterns from past official numbers</td></tr>
  <tr><td>Predict</td><td>Estimates a district value for a chosen year</td></tr>
  <tr><td>2026 scenarios</td><td>Simple trends for possible 2026 numbers + uncertainty</td></tr>
  <tr><td>News + sentiment</td><td>Headlines marked more positive or negative</td></tr>
  <tr><td>Dashboard</td><td>Maps, lists, compare, explain in the browser</td></tr>
  <tr><td>Tests</td><td>Automated checks via <code>run_tests.py</code></td></tr>
</table>

<h1>3. How it works (pipeline)</h1>
<pre class="flow">1. DATA          Official CSVs + news headlines
       ↓
2. CLEAN         One neat table (ML-ready)
       ↓
3. TRAIN         Models learn from official years
       ↓
4. PREDICT       Model + past history → district number
       ↓
5. FORECAST      Simple trend → 2026 scenario (with range)
       ↓
6. NEWS          Headlines → sentiment / map heat
       ↓
7. DASHBOARD     User sees everything in the browser</pre>
<p class="say"><b>Key idea:</b> Official tables train the models. News is for live awareness — not “this many FIRs.”</p>

<div class="page-break"></div>

<h1>4. Modules (main files)</h1>
<table>
  <tr><th>File / module</th><th>What it does</th></tr>
  <tr><td><code>clean_data.py</code></td><td>Finds yearly CSVs, fixes columns, drops totals, builds ML-ready table</td></tr>
  <tr><td><code>train_model.py</code></td><td>Trains several models, picks best per target, saves <code>.joblib</code></td></tr>
  <tr><td><code>predict.py</code></td><td>Predicts for one area/year; blends with district history</td></tr>
  <tr><td><code>forecast_engine.py</code> / <code>predict_2026_*</code></td><td>2026 linear / last-year / blend scenarios</td></tr>
  <tr><td><code>sentiment_analysis.py</code></td><td>Scores text (DistilBERT if available, else lexicon)</td></tr>
  <tr><td><code>acquire_news_signals.py</code></td><td>Updates news / media harvest files</td></tr>
  <tr><td><code>district_entities.py</code></td><td>Maps cities → 38 official TN districts (TN38)</td></tr>
  <tr><td><code>tn_map.py</code></td><td>Tamil Nadu district map (Plotly)</td></tr>
  <tr><td><code>db.py</code></td><td>SQLite store for headlines, alerts, tables</td></tr>
  <tr><td><code>dashboard.py</code></td><td>Streamlit website UI</td></tr>
  <tr><td><code>risk_explain.py</code></td><td>Simple “why high risk” explanations</td></tr>
  <tr><td><code>run_tests.py</code></td><td>Runs unit / integration / data-quality tests</td></tr>
  <tr><td><code>health_check.py</code></td><td>Checks if models and data files exist</td></tr>
</table>

<h1>5. Algorithms used (simple English)</h1>
<h2>5.1 Crime number prediction (main ML)</h2>
<table>
  <tr><th>Algorithm</th><th>Type</th><th>Simple meaning</th></tr>
  <tr><td><b>Dummy (median)</b></td><td>Baseline</td><td>Always guess the middle value — a simple bar to beat</td></tr>
  <tr><td><b>Ridge Regression</b></td><td>Linear model</td><td>Fits a stable straight-ish link; good for rates</td></tr>
  <tr><td><b>Random Forest</b></td><td>Many trees</td><td>Trees vote; handles mixed patterns</td></tr>
  <tr><td><b>Gradient Boosting</b></td><td>Trees in sequence</td><td>Each tree fixes previous errors</td></tr>
</table>
<p>We often train on a <b>log scale</b> for large counts, then convert back. Best model is chosen using error metrics (MAE, RMSE, R²) and a <b>temporal</b> check (train older years, test newer official year).</p>

<h2>5.2 History blend</h2>
<p>Final answer ≈ <b>part model</b> + <b>part past official value for that district</b>.</p>
<ul>
  <li><b>Rates</b> → trust history more (rates change slowly)</li>
  <li><b>Counts</b> → trust the model a bit more</li>
</ul>

<h2>5.3 2026 scenario methods</h2>
<table>
  <tr><th>Method</th><th>Simple meaning</th></tr>
  <tr><td>Linear trend</td><td>Straight line through past years → extend to 2026</td></tr>
  <tr><td>Last year carry</td><td>Assume next period looks like the last known year</td></tr>
  <tr><td>Blend</td><td>Average of linear + last year</td></tr>
  <tr><td>Uncertainty band</td><td>Low / mid / high range around the middle guess</td></tr>
</table>
<p class="say">We do <b>not</b> rely on LSTM/Prophet for the main demo: yearly district series are too short.</p>

<h2>5.4 Sentiment</h2>
<table>
  <tr><th>Method</th><th>Simple meaning</th></tr>
  <tr><td>DistilBERT (optional)</td><td>Small language model for positive/negative text</td></tr>
  <tr><td>Lexicon / keywords</td><td>Fallback using crime-related words</td></tr>
  <tr><td>Word cloud</td><td>Bigger words = more frequent in headlines</td></tr>
</table>

<h2>5.5 Explainability</h2>
<table>
  <tr><th>Method</th><th>Simple meaning</th></tr>
  <tr><td>Composite factors</td><td>Compare rates, news, forecast vs state median</td></tr>
  <tr><td>LIME-style</td><td>Slightly change inputs; see what pushes the score</td></tr>
  <tr><td>SHAP (optional)</td><td>Feature importance if the library is installed</td></tr>
</table>

<div class="page-break"></div>

<h1>6. What data it uses</h1>
<table>
  <tr><th>Data</th><th>Example</th><th>Used for</th></tr>
  <tr><td>Complaints tables</td><td>Total complaints, cognizable rate</td><td>Train / predict</td></tr>
  <tr><td>Murder / homicide</td><td>Incidence, rate</td><td>Train / predict</td></tr>
  <tr><td>Crimes against women</td><td>Rape Sec. 376, rates</td><td>Train / predict / 2026</td></tr>
  <tr><td>Media harvest</td><td>Headline, date, district, source</td><td>Live feed, heat, sentiment</td></tr>
  <tr><td>TN38 districts</td><td>38 official names</td><td>Maps, rollups, fair compare</td></tr>
  <tr><td>Population estimates</td><td>Lakhs per district</td><td>Per-lakh ranking</td></tr>
  <tr><td>SQLite DB</td><td>Headlines, alerts</td><td>Optional local store</td></tr>
</table>

<h1>7. Dashboard screens</h1>
<table>
  <tr><th>Screen</th><th>Purpose</th></tr>
  <tr><td>Live Feed</td><td>Latest news-style items + news heat</td></tr>
  <tr><td>District Map</td><td>Coloured TN map + scoreboard</td></tr>
  <tr><td>Accuracy</td><td>How models score (honest metrics)</td></tr>
  <tr><td>Predict</td><td>Pick district / crime type / year → number</td></tr>
  <tr><td>Sentiment</td><td>News mood + word cloud</td></tr>
  <tr><td>2026 Forecasts</td><td>Scenario map + ranking + uncertainty</td></tr>
  <tr><td>District Compare</td><td>2–4 districts side by side</td></tr>
  <tr><td>Risk Explain</td><td>Simple “why this looks high”</td></tr>
  <tr><td>Health</td><td>Are files and models present?</td></tr>
</table>

<h1>8. Technologies (what it uses)</h1>
<table>
  <tr><th>Layer</th><th>Tools</th></tr>
  <tr><td>Language</td><td>Python</td></tr>
  <tr><td>Data tables</td><td>pandas, numpy</td></tr>
  <tr><td>Machine learning</td><td>scikit-learn, joblib</td></tr>
  <tr><td>Charts &amp; maps</td><td>Plotly, matplotlib, seaborn</td></tr>
  <tr><td>Web app</td><td>Streamlit</td></tr>
  <tr><td>Database</td><td>SQLite</td></tr>
  <tr><td>Optional NLP</td><td>transformers + torch (DistilBERT) — not required for cloud</td></tr>
  <tr><td>Testing</td><td>unittest via <code>run_tests.py</code></td></tr>
  <tr><td>Deploy options</td><td>Local PC, Streamlit Cloud, Render.com</td></tr>
</table>

<h1>9. What it does not claim</h1>
<ul>
  <li>Not real-time police dispatch</li>
  <li>Not “this will definitely happen in 2026”</li>
  <li>News volume ≠ registered crime cases</li>
  <li>Short official history → forecasts are discussion scenarios only</li>
</ul>

<h1>10. Simple diagram (draw if asked)</h1>
<pre class="flow">[Official CSV] ──► Clean ──► Train (RF / GB / Ridge) ──► Predict + blend
                                                              │
[News] ─────────► Sentiment / heat ──────────────────────────┤
                                                              ▼
                                                    Streamlit Dashboard
                                                              │
[History series] ► Linear / last-year / blend ──► 2026 scenario map</pre>

<div class="box">
  <b>Viva one-liner:</b> We clean multi-table TN crime data, train classical ML models, blend predictions
  with district history, use news only as support (not FIRs), and show 2026 as a scenario with maps and simple explanations.
</div>

<p class="muted">
  CRIMECAST · Simple English project explain · Print: Ctrl+P → Save as PDF<br/>
  Or: <code>py -3 project_docs/generate_simple_explain_pdf.py</code>
</p>
</body>
</html>
""",
        encoding="utf-8",
    )
    return HTML


def build_pdf() -> Path | None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            ListFlowable,
            ListItem,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        return None

    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=A4,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="CRIMECAST Simple Explain",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CT", parent=styles["Title"], fontSize=16, textColor=colors.HexColor("#991b1b"), alignment=TA_CENTER, spaceAfter=6))
    styles.add(ParagraphStyle(name="CS", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor("#4b5563"), spaceAfter=3))
    styles.add(ParagraphStyle(name="H1x", parent=styles["Heading1"], fontSize=13, textColor=colors.HexColor("#111827"), spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontSize=11, textColor=colors.HexColor("#1e3a5f"), spaceBefore=8, spaceAfter=4))
    styles.add(ParagraphStyle(name="Bx", parent=styles["Normal"], fontSize=9, leading=12, alignment=TA_JUSTIFY, spaceAfter=5))
    styles.add(ParagraphStyle(name="Cell", parent=styles["Normal"], fontSize=7.5, leading=10))
    styles.add(ParagraphStyle(name="CellB", parent=styles["Normal"], fontSize=7.5, leading=10, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Box", parent=styles["Normal"], fontSize=9, leading=12, leftIndent=4, spaceBefore=4, spaceAfter=8))

    story = []

    def h1(t):
        story.append(Paragraph(t, styles["H1x"]))

    def h2(t):
        story.append(Paragraph(t, styles["H2x"]))

    def p(t):
        story.append(Paragraph(t, styles["Bx"]))

    def bullets(items):
        lis = [ListItem(Paragraph(i, styles["Bx"]), leftIndent=10) for i in items]
        story.append(ListFlowable(lis, bulletType="bullet", start="•", leftIndent=12))
        story.append(Spacer(1, 3))

    def tbl(headers, rows, widths):
        data = [[Paragraph(str(h), styles["CellB"]) for h in headers]]
        for r in rows:
            data.append([Paragraph(str(c), styles["Cell"]) for c in r])
        t = Table(data, colWidths=widths, repeatRows=1)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#eef2ff")]),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph("CRIMECAST", styles["CT"]))
    story.append(Paragraph("<b>How the Project Works — Simple English</b>", styles["CS"]))
    story.append(Paragraph("What it does · Modules · Algorithms · Data · Tools", styles["CS"]))
    story.append(Paragraph("College prototype · Not police system · Not official SCRB forecast", styles["CS"]))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "<b>30-second summary:</b> CRIMECAST cleans multi-year TN crime CSVs, trains classical ML "
            "(Ridge, Random Forest, Gradient Boosting), predicts with history blend, uses news for live "
            "context (not FIRs), and shows 2026 as a <b>scenario</b> with maps, compare, and simple explanations.",
            styles["Box"],
        )
    )

    h1("1. What is this project?")
    p("CRIMECAST is a student dashboard that helps people look at district crime numbers, "
      "make ML predictions, sketch a 2026 scenario, and see news sentiment for Tamil Nadu.")
    bullets([
        "Look at crime-related numbers by district",
        "Predict rates/counts with machine learning",
        "Sketch 2026 scenarios (not official forecasts)",
        "See news headlines and sentiment",
        "Use one Streamlit website for maps and compare",
    ])
    p("<b>Not</b> a live police system. <b>Not</b> an official government forecast.")

    h1("2. What does it do?")
    tbl(
        ["Feature", "In simple words"],
        [
            ["Load crime tables", "Reads CSVs (complaints, murder, crimes against women)"],
            ["Clean data", "Fixes names, removes TOTAL rows, standardises districts"],
            ["Train models", "Learns patterns from past official numbers"],
            ["Predict", "Estimates a district value for a chosen year"],
            ["2026 scenarios", "Simple trends + uncertainty range"],
            ["News + sentiment", "Headlines more positive or negative"],
            ["Dashboard", "Maps, lists, compare, explain in browser"],
            ["Tests", "Automated checks via run_tests.py"],
        ],
        [4.5 * cm, 12.5 * cm],
    )

    h1("3. How it works (pipeline)")
    p("<b>Data → Clean → Train → Predict → News/Sentiment → Dashboard</b> (+ 2026 trend branch)")
    bullets([
        "DATA — Official CSVs + news headlines",
        "CLEAN — One ML-ready table; TN38 district names",
        "TRAIN — Ridge / RF / GB; pick best per target",
        "PREDICT — Model + district history blend",
        "FORECAST — Linear / last-year / blend for 2026",
        "NEWS — Headlines → sentiment / map heat",
        "DASHBOARD — Streamlit UI for the user",
    ])
    p("<b>Key idea:</b> Official tables train models. News is for live awareness only.")

    story.append(PageBreak())

    h1("4. Modules (main files)")
    tbl(
        ["File", "What it does"],
        [
            ["clean_data.py", "Clean CSVs → ML-ready table"],
            ["train_model.py", "Train models; save .joblib"],
            ["predict.py", "Predict + history blend"],
            ["forecast_engine.py", "2026 multi-target scenarios"],
            ["sentiment_analysis.py", "Text polarity (DistilBERT or lexicon)"],
            ["acquire_news_signals.py", "Refresh media harvest"],
            ["district_entities.py", "City → TN38 parent district"],
            ["tn_map.py", "TN choropleth maps"],
            ["db.py", "SQLite headlines / alerts"],
            ["dashboard.py", "Streamlit website"],
            ["risk_explain.py", "Why high risk (simple + LIME-style)"],
            ["run_tests.py", "Unit / integration / data tests"],
        ],
        [4.8 * cm, 12.2 * cm],
    )

    h1("5. Algorithms (simple English)")
    h2("5.1 Main ML for crime numbers")
    tbl(
        ["Algorithm", "Meaning"],
        [
            ["Dummy (median)", "Baseline: always guess the middle value"],
            ["Ridge Regression", "Stable linear model; good for rates"],
            ["Random Forest", "Many decision trees vote"],
            ["Gradient Boosting", "Trees fix errors one after another"],
        ],
        [4.5 * cm, 12.5 * cm],
    )
    p("Best model chosen using MAE / RMSE / R² and temporal holdout when possible.")

    h2("5.2 History blend")
    p("Final ≈ part model + part past official district value. Rates trust history more; counts trust model more.")

    h2("5.3 2026 scenario")
    tbl(
        ["Method", "Meaning"],
        [
            ["Linear trend", "Straight line through past years → 2026"],
            ["Last year carry", "Next looks like last known year"],
            ["Blend", "Average of linear + last year"],
            ["Uncertainty band", "Low / mid / high range"],
        ],
        [4.5 * cm, 12.5 * cm],
    )
    p("LSTM/Prophet not used for main demo — yearly series are too short.")

    h2("5.4 Sentiment &amp; explain")
    p("DistilBERT (optional) or lexicon keywords; word clouds; composite risk + LIME-style explanations.")

    h1("6. Data used")
    tbl(
        ["Data", "Used for"],
        [
            ["Complaints / murder / women-crime CSVs", "Train &amp; predict"],
            ["Media harvest headlines", "Live feed, heat, sentiment"],
            ["TN38 district list", "Maps and fair rollups"],
            ["Population estimates", "Per-lakh ranking"],
            ["SQLite (optional)", "Headlines &amp; alerts store"],
        ],
        [7 * cm, 10 * cm],
    )

    h1("7. Dashboard screens")
    tbl(
        ["Screen", "Purpose"],
        [
            ["Live Feed", "Latest news-style items + heat"],
            ["District Map", "TN map + scoreboard"],
            ["Accuracy", "Honest model metrics"],
            ["Predict", "District / target / year → number"],
            ["Sentiment", "Mood map + word cloud"],
            ["2026 Forecasts", "Scenario map + bands"],
            ["District Compare", "2–4 districts side by side"],
            ["Risk Explain", "Why it looks high"],
            ["Health", "Files and models present?"],
        ],
        [4.5 * cm, 12.5 * cm],
    )

    h1("8. Technologies")
    p("<b>Python</b> · pandas · numpy · scikit-learn · joblib · Plotly · Streamlit · SQLite · optional transformers/torch")

    h1("9. What it does not claim")
    bullets([
        "Not real-time police dispatch",
        "Not a guaranteed 2026 fact",
        "News volume is not registered crime",
        "Short history → scenarios for discussion only",
    ])

    story.append(
        Paragraph(
            "<b>Viva one-liner:</b> We clean multi-table TN crime data, train classical ML models, "
            "blend predictions with district history, use news only as support (not FIRs), and show "
            "2026 as a scenario with maps and simple explanations.",
            styles["Box"],
        )
    )

    def footer(canvas, d):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6b7280"))
        canvas.drawString(1.7 * cm, 1.0 * cm, "CRIMECAST · Simple English Explain")
        canvas.drawRightString(A4[0] - 1.7 * cm, 1.0 * cm, f"Page {d.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return PDF


def main() -> int:
    write_html()
    print(f"[OK] HTML → {HTML}")
    pdf = build_pdf()
    if pdf and pdf.exists():
        print(f"[OK] PDF  → {pdf}")
    else:
        print("[INFO] Install reportlab for PDF:  py -3 -m pip install reportlab")
        print(f"       Then re-run this script. Or open HTML and Ctrl+P → Save as PDF.")
        print(f"       HTML: {HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
