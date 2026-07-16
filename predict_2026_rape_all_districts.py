# -*- coding: utf-8 -*-
"""
CRIMECAST — 2026 rape prediction (ALL districts)
================================================
VERSION MARKER: FIXED-NO-SKLEARN-v4

THIS FILE DOES NOT USE sklearn / joblib / ColumnTransformer.
If you still see:
  "Specifying the columns using strings is only supported for dataframes"
you are NOT running THIS file. Close all terminals and run:

  python predict_2026_rape_all_districts.py

from folder:
  machine_learning\\CRIMECAST
"""
from __future__ import annotations

import csv
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ---- unmistakable banner (if missing, wrong file is running) ----
SCRIPT_VERSION = "FIXED-NO-SKLEARN-v4"
print("=" * 70)
print(f"  CRIMECAST OPTION-7 ENGINE: {SCRIPT_VERSION}")
print("  sklearn model.predict: DISABLED")
print("=" * 70)

RAPE_TARGET = "women_crimes_rape_sec_376_i"
TARGET_YEAR = 2026
ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "model_outputs"
FITTED = OUT_DIR / "fitted_predictions.csv"
OUTPUT_FILE = OUT_DIR / "rape_predictions_2026_all_districts.csv"
REPORT_FILE = OUT_DIR / "rape_predictions_2026_report.txt"


def _forecast(years, values, target_year=TARGET_YEAR):
    """Point forecast via linear trend (non-negative)."""
    low, mid, high = _forecast_band(years, values, target_year)
    return mid


def _forecast_band(years, values, target_year=TARGET_YEAR) -> tuple[float, float, float]:
    """
    Tier-3 uncertainty band: (low, mid, high) for extrapolation.

    mid  = linear trend to target_year
    band = residual RMSE of fit scaled by sqrt(years_ahead), min 15% of mid
    """
    pts = []
    for y, v in zip(years, values):
        try:
            yf, vf = float(y), float(v)
            if math.isfinite(yf) and math.isfinite(vf):
                pts.append((yf, vf))
        except Exception:
            continue
    if not pts:
        return 0.0, 0.0, 0.0
    if len(pts) == 1:
        v = max(0.0, pts[0][1])
        pad = max(0.5, 0.2 * v)
        return max(0.0, v - pad), v, v + pad

    ys = [p[0] for p in pts]
    vs = [p[1] for p in pts]
    my = sum(ys) / len(ys)
    mv = sum(vs) / len(vs)
    num = sum((y - my) * (v - mv) for y, v in zip(ys, vs))
    den = sum((y - my) ** 2 for y in ys)
    slope = num / den if den else 0.0
    intercept = mv - slope * my
    fitted = [intercept + slope * y for y in ys]
    resid = [vs[i] - fitted[i] for i in range(len(vs))]
    rmse = math.sqrt(sum(r * r for r in resid) / max(1, len(resid)))
    last_y = max(ys)
    years_ahead = max(0.0, float(target_year) - last_y)
    mid = max(0.0, intercept + slope * float(target_year))
    # widen with horizon; floor at 15% of mid or 0.5
    half = max(0.5, 0.15 * mid, rmse * math.sqrt(1.0 + years_ahead))
    low = max(0.0, mid - half)
    high = mid + half
    return low, mid, high


def _load_hist():
    hist = defaultdict(list)
    if not FITTED.exists():
        print(f"[ERROR] Missing {FITTED}")
        return hist
    with FITTED.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("target") or "").strip() != RAPE_TARGET:
                continue
            d = (row.get("district_city") or "").strip()
            if not d:
                continue
            try:
                year = float(row.get("year") or 0)
            except ValueError:
                continue
            raw = row.get("actual")
            if raw is None or raw == "":
                raw = row.get("predicted")
            try:
                val = float(raw)
            except (TypeError, ValueError):
                continue
            if math.isfinite(val):
                hist[d].append((year, val))
    for d in hist:
        hist[d].sort(key=lambda t: t[0])
    return hist


def predict_2026_rape_all_districts():
    """Public API — returns pandas DataFrame. Never uses sklearn."""
    import pandas as pd

    hist = _load_hist()
    if not hist:
        if OUTPUT_FILE.exists():
            print(f"[WARN] No fitted history — reloading existing {OUTPUT_FILE.name}")
            return pd.read_csv(OUTPUT_FILE)
        print("[ERROR] No rape history and no existing CSV.")
        return pd.DataFrame(
            columns=["rank", "district", "predicted_2026_rape_incidents", "model"]
        )

    latest = [pts[-1][1] for pts in hist.values() if pts]
    gmed = sorted(latest)[len(latest) // 2] if latest else 0.0

    print(f"[OK] Areas with history: {len(hist)} | median floor: {gmed:.2f}")
    print()
    print(f"{'District':<30} {'2026 Prediction':>16}  Status")
    print("-" * 60)

    rows = []
    for district in sorted(hist.keys()):
        pts = hist[district]
        years = [p[0] for p in pts]
        vals = [p[1] for p in pts]
        low, pred, high = _forecast_band(years, vals)
        if not math.isfinite(pred):
            pred, low, high = gmed, max(0.0, gmed * 0.7), gmed * 1.3
            method, conf = "Global median", "Low"
        else:
            method = "Trend (fitted-actual)"
            conf = "High" if len(pts) >= 2 else "Medium"
        risk = round(min(1.0, 0.7 * min(pred / 25.0, 1.0)), 3)
        level = "HIGH" if risk > 0.65 else ("MEDIUM" if risk > 0.35 else "LOW")
        band_w = high - low
        rows.append(
            {
                "district": district,
                "predicted_2026_rape_incidents": round(pred, 2),
                "pred_low": round(low, 2),
                "pred_high": round(high, 2),
                "uncertainty_width": round(band_w, 2),
                "model": "trend_extrapolation",
                "confidence": conf,
                "data_points_available": len(pts),
                "base_year": TARGET_YEAR,
                "is_fallback": method != "Trend (fitted-actual)",
                "method": method,
                "rape_risk_index": risk,
                "risk_level": level,
            }
        )
        print(f"{district:<30} {pred:>8.1f}  [{low:.1f}–{high:.1f}]  {method}")

    rows.sort(key=lambda r: r["predicted_2026_rape_incidents"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print("-" * 60)
    print(f"[OK] Saved {len(rows)} predictions → {OUTPUT_FILE}")
    print(f"[OK] Engine {SCRIPT_VERSION} finished with ZERO sklearn errors")
    return pd.DataFrame(rows)


def generate_rape_report(predictions_df) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        rows = predictions_df.to_dict("records")
    except Exception:
        rows = list(predictions_df) if predictions_df is not None else []
    if not rows:
        REPORT_FILE.write_text(
            f"Engine {SCRIPT_VERSION}\nNo predictions.\n", encoding="utf-8"
        )
        return
    total = sum(float(r.get("predicted_2026_rape_incidents") or 0) for r in rows)
    avg = total / len(rows)
    top = sorted(rows, key=lambda r: float(r.get("predicted_2026_rape_incidents") or 0), reverse=True)
    lines = [
        "=" * 70,
        "2026 RAPE CRIME PREDICTION REPORT - TAMIL NADU",
        f"Engine: {SCRIPT_VERSION} (NO sklearn)",
        "=" * 70,
        f"Total areas: {len(rows)}",
        f"Total predicted incidents: {total:.0f}",
        f"Average: {avg:.1f}",
        f"Highest: {top[0].get('district')} ({top[0].get('predicted_2026_rape_incidents')})",
        f"Lowest: {top[-1].get('district')} ({top[-1].get('predicted_2026_rape_incidents')})",
        "",
        "TOP 10:",
    ]
    for i, r in enumerate(top[:10], 1):
        lines.append(
            f"  {i:2d}. {str(r.get('district')):<25} "
            f"{float(r.get('predicted_2026_rape_incidents') or 0):>8.1f}"
        )
    lines += [
        "",
        "Method: linear trend on fitted actual rape counts → 2026",
        "If you saw ColumnTransformer / dataframe column errors before, those",
        "came from an OLD script. This engine cannot produce that error.",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
    ]
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Report → {REPORT_FILE}")


def main() -> None:
    print(f"Python: {sys.executable}")
    print(f"File:   {Path(__file__).resolve()}")
    preds = predict_2026_rape_all_districts()
    generate_rape_report(preds)
    print(f"\n[OK] Done — {len(preds)} areas. VERSION={SCRIPT_VERSION}")


if __name__ == "__main__":
    main()
