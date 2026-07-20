# -*- coding: utf-8 -*-
"""
Regenerate CURRENT (non-legacy) result figures + dashboard-style screenshots
for the hard-copy project report.

Output:
  project_docs/figures/results/     — result snapshot charts
  project_docs/figures/screenshots/ — forms & report UI panels

Run:
  py -3 project_docs/regenerate_report_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT_RES = Path(__file__).resolve().parent / "figures" / "results"
OUT_SCR = Path(__file__).resolve().parent / "figures" / "screenshots"
OUT_RES.mkdir(parents=True, exist_ok=True)
OUT_SCR.mkdir(parents=True, exist_ok=True)

ML = ROOT / "dataset" / "cleaned" / "crimecast_ml_ready.csv"
FITTED = ROOT / "model_outputs" / "fitted_predictions.csv"
RAPE26 = ROOT / "model_outputs" / "rape_predictions_2026_all_districts.csv"
METRICS = ROOT / "model_outputs" / "training_metrics.csv"
HARVEST = ROOT / "model_outputs" / "media_harvest_tn_crime_latest.csv"
SENT = ROOT / "model_outputs" / "sentiment_scores.csv"

# Dark ops style (match dashboard)
BG = "#0e0e12"
FG = "#e5e7eb"
ACCENT = "#38bdf8"
RED = "#ef4444"
BLUE = "#3b82f6"
GRID = "#27272a"


def _style(ax, title: str):
    ax.set_facecolor(BG)
    ax.figure.patch.set_facecolor(BG)
    ax.tick_params(colors=FG, labelsize=8)
    ax.xaxis.label.set_color(FG)
    ax.yaxis.label.set_color(FG)
    ax.title.set_color(FG)
    ax.set_title(title, fontsize=12, fontweight="bold", color=FG, pad=10)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    ax.grid(True, alpha=0.25, color=GRID)


def _save(fig, path: Path):
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"[OK] {path.relative_to(ROOT)}")


def _to_tn38_series(names: pd.Series) -> pd.Series:
    try:
        from district_entities import to_tn38

        return names.astype(str).map(lambda x: to_tn38(x, default=None))
    except Exception:
        return names.astype(str)


def fig_top_murder():
    if not ML.exists():
        return
    df = pd.read_csv(ML)
    col = "murder_homicide_murder_incidence"
    if col not in df.columns:
        return
    d = df.copy()
    d["district"] = _to_tn38_series(d.get("district_city", pd.Series(dtype=str)))
    d = d[d["district"].notna()]
    d[col] = pd.to_numeric(d[col], errors="coerce")
    # latest year per district
    if "year" in d.columns:
        d = d.sort_values("year").groupby("district", as_index=False).last()
    top = d.nlargest(12, col).sort_values(col)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    _style(ax, "Top districts · Murder incidence (latest)")
    ax.barh(top["district"], top[col], color=RED, alpha=0.9)
    ax.set_xlabel("Murder incidence")
    _save(fig, OUT_RES / "01_top_murder_incidence.png")


def fig_top_rape():
    if not ML.exists():
        return
    df = pd.read_csv(ML)
    col = "women_crimes_rape_sec_376_i"
    if col not in df.columns:
        return
    d = df.copy()
    d["district"] = _to_tn38_series(d.get("district_city", pd.Series(dtype=str)))
    d = d[d["district"].notna()]
    d[col] = pd.to_numeric(d[col], errors="coerce")
    if "year" in d.columns:
        d = d.sort_values("year").groupby("district", as_index=False).last()
    top = d.nlargest(12, col).sort_values(col)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    _style(ax, "Top districts · Rape incidents Sec.376 (latest)")
    ax.barh(top["district"], top[col], color="#f97316", alpha=0.9)
    ax.set_xlabel("Incidents")
    _save(fig, OUT_RES / "02_top_rape_incidents.png")


def fig_top_complaints():
    if not ML.exists():
        return
    df = pd.read_csv(ML)
    col = "complaints_total_complaints"
    if col not in df.columns:
        return
    d = df.copy()
    d["district"] = _to_tn38_series(d.get("district_city", pd.Series(dtype=str)))
    d = d[d["district"].notna()]
    d[col] = pd.to_numeric(d[col], errors="coerce")
    if "year" in d.columns:
        d = d.sort_values("year").groupby("district", as_index=False).last()
    top = d.nlargest(12, col).sort_values(col)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    _style(ax, "Top districts · Total complaints (latest)")
    ax.barh(top["district"], top[col], color=BLUE, alpha=0.9)
    ax.set_xlabel("Complaints")
    _save(fig, OUT_RES / "03_top_total_complaints.png")


def fig_actual_vs_predicted():
    if not FITTED.exists():
        return
    pred = pd.read_csv(FITTED)
    if "actual" not in pred.columns or "predicted" not in pred.columns:
        return
    # pick a few targets
    targets = pred["target"].dropna().unique().tolist()[:4] if "target" in pred.columns else [None]
    n = max(1, len(targets))
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 4.2))
    if n == 1:
        axes = [axes]
    fig.patch.set_facecolor(BG)
    for ax, t in zip(axes, targets):
        sub = pred if t is None else pred[pred["target"] == t]
        a = pd.to_numeric(sub["actual"], errors="coerce")
        p = pd.to_numeric(sub["predicted"], errors="coerce")
        m = a.notna() & p.notna()
        ax.scatter(a[m], p[m], s=18, alpha=0.65, c=ACCENT, edgecolors="none")
        if m.any():
            lo = min(a[m].min(), p[m].min())
            hi = max(a[m].max(), p[m].max())
            ax.plot([lo, hi], [lo, hi], "--", color=RED, lw=1.2)
        _style(ax, (str(t).split("_")[-1] if t else "All")[:28])
        ax.set_xlabel("Actual")
        ax.set_ylabel("Predicted")
    fig.suptitle("Actual vs Predicted (fitted)", color=FG, fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, OUT_RES / "04_actual_vs_predicted.png")


def fig_training_metrics():
    if not METRICS.exists():
        return
    m = pd.read_csv(METRICS)
    if "is_best" in m.columns:
        best = m[m["is_best"].astype(str).str.lower().isin(("true", "1", "yes"))]
    else:
        best = m
    if best.empty:
        best = m
    label_col = "target_label" if "target_label" in best.columns else "target"
    r2_col = "test_r2" if "test_r2" in best.columns else None
    if not r2_col:
        return
    best = best.copy()
    best[r2_col] = pd.to_numeric(best[r2_col], errors="coerce")
    best = best.dropna(subset=[r2_col]).sort_values(r2_col)
    fig, ax = plt.subplots(figsize=(9, 5))
    _style(ax, "Best models · Test R²")
    ax.barh(best[label_col].astype(str), best[r2_col], color=ACCENT, alpha=0.9)
    ax.set_xlabel("Test R²")
    ax.axvline(0, color=FG, lw=0.8)
    _save(fig, OUT_RES / "05_training_test_r2.png")


def fig_rape_2026():
    path = RAPE26
    if not path.exists():
        return
    df = pd.read_csv(path)
    ncol = "district" if "district" in df.columns else "district_city"
    vcol = (
        "predicted_2026_rape_incidents"
        if "predicted_2026_rape_incidents" in df.columns
        else "predicted_value"
    )
    if vcol not in df.columns:
        return
    d = df.copy()
    d["district"] = _to_tn38_series(d[ncol])
    d = d[d["district"].notna()]
    d[vcol] = pd.to_numeric(d[vcol], errors="coerce")
    # if multiple rows per district sum
    g = d.groupby("district", as_index=False)[vcol].sum()
    top = g.nlargest(15, vcol).sort_values(vcol)
    fig, ax = plt.subplots(figsize=(9, 6))
    _style(ax, "2026 scenario · Rape incidents (TN38)")
    colors = plt.cm.Blues(np.linspace(0.35, 0.95, len(top)))
    ax.barh(top["district"], top[vcol], color=colors)
    ax.set_xlabel("Predicted incidents (scenario)")
    for i, (v, name) in enumerate(zip(top[vcol], top["district"])):
        ax.text(v + 0.3, i, f"{v:.0f}", va="center", color=FG, fontsize=8)
    _save(fig, OUT_RES / "06_rape_2026_top15.png")

    # risk pie
    if "risk_level" in df.columns:
        counts = df["risk_level"].astype(str).value_counts()
    else:
        # derive
        r = g[vcol]
        risk = pd.cut(r, bins=[-0.1, 8, 16, 1e9], labels=["LOW", "MEDIUM", "HIGH"])
        counts = risk.value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    cols = {"HIGH": RED, "MEDIUM": "#f59e0b", "LOW": "#22c55e"}
    c = [cols.get(str(k).upper(), ACCENT) for k in counts.index]
    ax.pie(
        counts.values,
        labels=counts.index,
        colors=c,
        autopct="%1.0f%%",
        textprops={"color": FG, "fontsize": 10},
    )
    ax.set_title("2026 risk categories", color=FG, fontweight="bold")
    _save(fig, OUT_RES / "07_rape_2026_risk_pie.png")


def fig_murder_rate_compare():
    if not ML.exists():
        return
    df = pd.read_csv(ML)
    col = "murder_homicide_murder_rate"
    if col not in df.columns:
        return
    d = df.copy()
    d["district"] = _to_tn38_series(d["district_city"])
    d = d[d["district"].notna()]
    d[col] = pd.to_numeric(d[col], errors="coerce")
    if "year" in d.columns:
        d = d.sort_values("year").groupby("district", as_index=False).last()
    focus = ["Thoothukudi", "Madurai", "Chennai", "Salem", "Coimbatore", "Tiruchirappalli"]
    # alias map
    try:
        from district_entities import to_tn38

        focus = [to_tn38(x, default=x) for x in focus]
    except Exception:
        pass
    sub = d[d["district"].isin(focus)].dropna(subset=[col]).sort_values(col)
    if sub.empty:
        sub = d.nlargest(8, col).sort_values(col)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    _style(ax, "Murder rate comparison (selected TN38)")
    ax.barh(sub["district"], sub[col], color="#a78bfa")
    ax.set_xlabel("Murder rate")
    _save(fig, OUT_RES / "08_murder_rate_selected.png")


def fig_news_volume():
    path = HARVEST
    if not path.exists():
        cands = sorted((ROOT / "model_outputs").glob("media_harvest_tn_crime_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        path = cands[0] if cands else None
    if path is None or not path.exists():
        return
    h = pd.read_csv(path)
    dcol = "district" if "district" in h.columns else None
    if not dcol:
        return
    h["district"] = _to_tn38_series(h[dcol])
    h = h[h["district"].notna()]
    cnt = h.groupby("district").size().sort_values(ascending=True).tail(15)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    _style(ax, "News headlines by district (harvest)")
    ax.barh(cnt.index.astype(str), cnt.values, color=ACCENT)
    ax.set_xlabel("Headline count")
    _save(fig, OUT_RES / "09_news_volume_by_district.png")


# ---------- Dashboard-style screenshots (Forms & Reports) ----------

def _panel_header(ax, title: str, subtitle: str = ""):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_facecolor(BG)
    ax.add_patch(plt.Rectangle((0, 0), 10, 10, fill=True, color=BG, zorder=0))
    ax.text(0.3, 9.2, "CRIMECAST", color=RED, fontsize=11, fontweight="bold")
    ax.text(0.3, 8.5, title, color=FG, fontsize=14, fontweight="bold")
    if subtitle:
        ax.text(0.3, 7.9, subtitle, color="#9ca3af", fontsize=9)


def shot_live_feed():
    fig = plt.figure(figsize=(11, 6.2), facecolor=BG)
    gs = fig.add_gridspec(2, 3, height_ratios=[0.9, 2.2], hspace=0.35, wspace=0.3)
    ax0 = fig.add_subplot(gs[0, :])
    ax0.set_facecolor(BG)
    ax0.axis("off")
    ax0.text(0.01, 0.7, "🔴 LIVE FEED  ·  Tamil Nadu Live Intelligence", color=FG, fontsize=14, fontweight="bold", transform=ax0.transAxes)
    ax0.text(0.01, 0.25, "News heat · HIGH alerts · How it works · Health strip", color="#9ca3af", fontsize=9, transform=ax0.transAxes)

    # metrics
    for i, (lab, val) in enumerate([("MODELS", "6"), ("HIGH", "3"), ("NEWS 90d", "—"), ("STATUS", "OK")]):
        ax = fig.add_subplot(gs[1, 0] if i == 0 else gs[1, 0])
    axm = fig.add_subplot(gs[1, 0])
    axm.set_facecolor("#141418")
    axm.axis("off")
    axm.set_title("HIGH ALERTS", color=RED, fontsize=10, fontweight="bold")
    for j, t in enumerate(["Elevated murder rate districts", "2026 HIGH rape-risk set", "News spike watchlist"]):
        axm.text(0.08, 0.75 - j * 0.25, f"●  {t}", color=FG, fontsize=9, transform=axm.transAxes)

    # fake heat bars from real news if possible
    axb = fig.add_subplot(gs[1, 1:])
    _style(axb, "Live news heat (top districts)")
    districts, vals = ["Chennai", "Madurai", "Salem", "Coimbatore", "Tirunelveli", "Vellore"], [12, 9, 8, 7, 5, 4]
    if HARVEST.exists() or list((ROOT / "model_outputs").glob("media_harvest*.csv")):
        try:
            path = HARVEST if HARVEST.exists() else sorted((ROOT / "model_outputs").glob("media_harvest*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)[0]
            h = pd.read_csv(path)
            h["d"] = _to_tn38_series(h["district"] if "district" in h.columns else h.iloc[:, 1])
            h = h[h["d"].notna()]
            cnt = h.groupby("d").size().sort_values(ascending=False).head(8)
            districts = list(cnt.index.astype(str)[::-1])
            vals = list(cnt.values[::-1])
        except Exception:
            pass
    axb.barh(districts, vals, color=ACCENT)
    axb.set_xlabel("Headlines")
    _save(fig, OUT_SCR / "shot_01_live_feed.png")


def shot_district_map():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.5), facecolor=BG)
    # left: choropleth proxy as ranked bars
    ax = axes[0]
    _style(ax, "District Map · Murder rate ranking")
    if ML.exists():
        df = pd.read_csv(ML)
        col = "murder_homicide_murder_rate"
        if col in df.columns:
            d = df.copy()
            d["district"] = _to_tn38_series(d["district_city"])
            d = d[d["district"].notna()]
            d[col] = pd.to_numeric(d[col], errors="coerce")
            if "year" in d.columns:
                d = d.sort_values("year").groupby("district", as_index=False).last()
            top = d.nlargest(12, col).sort_values(col)
            ax.barh(top["district"], top[col], color="#fb923c")
            ax.set_xlabel("Murder rate")
    # right: scoreboard note
    ax2 = axes[1]
    ax2.set_facecolor("#141418")
    ax2.axis("off")
    ax2.text(0.05, 0.9, "📋 SCOREBOARD", color=FG, fontsize=12, fontweight="bold", transform=ax2.transAxes)
    ax2.text(0.05, 0.78, "Default rank: murder / lakh (fair compare)", color="#9ca3af", fontsize=9, transform=ax2.transAxes)
    lines = [
        "Tabs: Choropleth · Heat map · Scoreboard",
        "Compare → sidebar ⚖️ District Compare",
        "Per-lakh metrics preferred",
        "No news-fill on official-rate maps",
    ]
    for i, line in enumerate(lines):
        ax2.text(0.05, 0.62 - i * 0.1, "•  " + line, color=FG, fontsize=10, transform=ax2.transAxes)
    fig.suptitle("FORMS · District Map & Scoreboard", color=FG, fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, OUT_SCR / "shot_02_district_map.png")


def shot_accuracy():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), facecolor=BG)
    ax = axes[0]
    _style(ax, "Accuracy · Test R² (best models)")
    if METRICS.exists():
        m = pd.read_csv(METRICS)
        if "is_best" in m.columns:
            best = m[m["is_best"].astype(str).str.lower().isin(("true", "1", "yes"))]
        else:
            best = m
        lab = "target_label" if "target_label" in best.columns else "target"
        if "test_r2" in best.columns:
            best = best.copy()
            best["test_r2"] = pd.to_numeric(best["test_r2"], errors="coerce")
            best = best.dropna(subset=["test_r2"]).sort_values("test_r2")
            ax.barh(best[lab].astype(str).str[:28], best["test_r2"], color="#22c55e")
            ax.set_xlabel("Test R²")
    ax2 = axes[1]
    ax2.set_facecolor("#141418")
    ax2.axis("off")
    ax2.text(0.06, 0.88, "✅ ACCURACY CHECK", color=FG, fontsize=12, fontweight="bold", transform=ax2.transAxes)
    claims = [
        "Train on official-era labels (≤2023)",
        "Show temporal MAE / R² honestly",
        "Blend vs model raw vs history",
        "Holdout backtest (linear trend)",
        "What we claim / don’t claim panel",
    ]
    for i, c in enumerate(claims):
        ax2.text(0.06, 0.72 - i * 0.1, "✓  " + c, color=FG, fontsize=10, transform=ax2.transAxes)
    fig.suptitle("FORMS · Accuracy Check", color=FG, fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, OUT_SCR / "shot_03_accuracy.png")


def shot_forecast_2026():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.5), facecolor=BG)
    ax = axes[0]
    _style(ax, "2026 Forecast · top districts")
    if RAPE26.exists():
        df = pd.read_csv(RAPE26)
        vcol = "predicted_2026_rape_incidents" if "predicted_2026_rape_incidents" in df.columns else "predicted_value"
        ncol = "district" if "district" in df.columns else df.columns[0]
        if vcol in df.columns:
            d = df.copy()
            d["d"] = _to_tn38_series(d[ncol])
            d = d[d["d"].notna()]
            d[vcol] = pd.to_numeric(d[vcol], errors="coerce")
            g = d.groupby("d", as_index=False)[vcol].sum().nlargest(12, vcol).sort_values(vcol)
            ax.barh(g["d"], g[vcol], color=ACCENT)
            ax.set_xlabel("Scenario incidents")
            # error bars if present
            if "pred_low" in d.columns and "pred_high" in d.columns:
                pass
    ax2 = axes[1]
    ax2.set_facecolor("#141418")
    ax2.axis("off")
    ax2.text(0.06, 0.9, "📅 2026 FORECASTS", color=FG, fontsize=12, fontweight="bold", transform=ax2.transAxes)
    for i, line in enumerate([
        "Targets: rape · murder · complaints",
        "Methods: linear · last year · blend",
        "Map: forecast only (no news fill)",
        "TN38 rollup · uncertainty bands",
        "Scenario only — not SCRB fact",
    ]):
        ax2.text(0.06, 0.72 - i * 0.1, "•  " + line, color=FG, fontsize=10, transform=ax2.transAxes)
    fig.suptitle("FORMS · 2026 Forecasts", color=FG, fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, OUT_SCR / "shot_04_forecast_2026.png")


def shot_compare():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), facecolor=BG)
    ax = axes[0]
    _style(ax, "District Compare · murder rate")
    pairs = ["Thoothukudi", "Madurai", "Chennai", "Salem"]
    vals = [0, 0, 0, 0]
    if ML.exists():
        df = pd.read_csv(ML)
        col = "murder_homicide_murder_rate"
        if col in df.columns:
            d = df.copy()
            d["district"] = _to_tn38_series(d["district_city"])
            d[col] = pd.to_numeric(d[col], errors="coerce")
            if "year" in d.columns:
                d = d.sort_values("year").groupby("district", as_index=False).last()
            try:
                from district_entities import to_tn38
                pairs = [to_tn38(x, default=x) for x in pairs]
            except Exception:
                pass
            got = []
            for name in pairs:
                row = d[d["district"] == name]
                if not row.empty and pd.notna(row.iloc[0][col]):
                    got.append((name, float(row.iloc[0][col])))
            if got:
                pairs = [g[0] for g in got]
                vals = [g[1] for g in got]
    ax.bar(pairs, vals, color=[RED, BLUE, ACCENT, "#a855f7"][: len(pairs)])
    ax.set_ylabel("Murder rate")
    ax.tick_params(axis="x", rotation=15)
    ax2 = axes[1]
    ax2.set_facecolor("#141418")
    ax2.axis("off")
    ax2.text(0.06, 0.9, "⚖️ DISTRICT COMPARE", color=FG, fontsize=12, fontweight="bold", transform=ax2.transAxes)
    for i, line in enumerate([
        "Carved district outlines",
        "Rates + per-lakh metrics",
        "2026 forecast + ML row",
        "Murder history line chart",
        "HTML district brief download",
        "Radar relative profile",
    ]):
        ax2.text(0.06, 0.75 - i * 0.09, "•  " + line, color=FG, fontsize=10, transform=ax2.transAxes)
    fig.suptitle("FORMS · District Compare (merged)", color=FG, fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, OUT_SCR / "shot_05_district_compare.png")


def shot_sentiment():
    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
    _style(ax, "Sentiment / news concern proxy")
    # use news volume as proxy visual if sentiment empty
    labels, vals = ["Chennai", "Madurai", "Salem", "Coimbatore", "Vellore"], [0.6, 0.45, 0.4, 0.35, 0.3]
    path = HARVEST if HARVEST.exists() else None
    if path:
        try:
            h = pd.read_csv(path)
            h["d"] = _to_tn38_series(h["district"])
            cnt = h.groupby("d").size().sort_values(ascending=False).head(10)
            labels = list(cnt.index.astype(str)[::-1])
            mx = max(cnt.values.max(), 1)
            vals = list((cnt.values / mx)[::-1])
        except Exception:
            pass
    ax.barh(labels, vals, color="#e879f9")
    ax.set_xlabel("Relative concern / volume (normalized)")
    fig.suptitle("FORMS · Sentiment tab (map + word cloud source)", color=FG, fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, OUT_SCR / "shot_06_sentiment.png")


def shot_health():
    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor=BG)
    ax.set_facecolor("#141418")
    ax.axis("off")
    ax.text(0.03, 0.9, "🩺 HEALTH · Demo readiness", color=FG, fontsize=14, fontweight="bold", transform=ax.transAxes)
    checks = []
    checks.append(("ML-ready CSV", ML.exists()))
    checks.append(("Models folder", (ROOT / "models").exists() and any((ROOT / "models").glob("*.joblib"))))
    checks.append(("2026 forecasts", RAPE26.exists()))
    checks.append(("Training metrics", METRICS.exists()))
    checks.append(("SQLite DB", (ROOT / "data" / "crimecast.db").exists()))
    checks.append(("GeoJSON assets", (ROOT / "assets" / "tamil_nadu_districts.geojson").exists()))
    for i, (name, ok) in enumerate(checks):
        mark = "🟢 OK" if ok else "🔴 FAIL"
        ax.text(0.05, 0.72 - i * 0.1, f"{mark}   {name}", color=FG, fontsize=11, transform=ax.transAxes, family="monospace")
    ax.text(0.03, 0.05, "CRIMECAST health · migrate CSVs from this tab", color="#9ca3af", fontsize=9, transform=ax.transAxes)
    _save(fig, OUT_SCR / "shot_07_health.png")


def write_manifest():
    lines = [
        "# Report figures (results + form screenshots)",
        "",
        "## results/ (chapter 06 Result Snapshot)",
    ]
    for p in sorted(OUT_RES.glob("*.png")):
        lines.append(f"- `{p.name}`")
    lines += ["", "## screenshots/ (chapter 08 Forms and Report)"]
    for p in sorted(OUT_SCR.glob("*.png")):
        lines.append(f"- `{p.name}`")
    (Path(__file__).resolve().parent / "figures" / "MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")
    print("[OK] MANIFEST.md")


def main():
    sys.path.insert(0, str(ROOT))
    print("=" * 60)
    print("Regenerating CURRENT report figures")
    print("=" * 60)
    fig_top_murder()
    fig_top_rape()
    fig_top_complaints()
    fig_actual_vs_predicted()
    fig_training_metrics()
    fig_rape_2026()
    fig_murder_rate_compare()
    fig_news_volume()
    shot_live_feed()
    shot_district_map()
    shot_accuracy()
    shot_forecast_2026()
    shot_compare()
    shot_sentiment()
    shot_health()
    write_manifest()
    print("=" * 60)
    print(f"Results → {OUT_RES}")
    print(f"Screenshots → {OUT_SCR}")
    print("Next: GENERATE_FULL_REPORT.bat")
    print("=" * 60)


if __name__ == "__main__":
    main()
