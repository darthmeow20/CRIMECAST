# -*- coding: utf-8 -*-
"""
CRIMECAST — 2026 rape prediction (ALL districts)
================================================
VERSION MARKER: FIXED-NO-SKLEARN-v5-TN38

THIS FILE DOES NOT USE sklearn / joblib / ColumnTransformer.
If you still see:
  "Specifying the columns using strings is only supported for dataframes"
you are NOT running THIS file. Close all terminals and run:

  python predict_2026_rape_all_districts.py

from folder:
  machine_learning\\CRIMECAST

Output is always the official 38 TN districts (city units rolled up:
Madurai City→Madurai, Avadi/Tambaram→Chennai, etc.). Junk units dropped.
"""
from __future__ import annotations

import csv
import math
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ---- unmistakable banner (if missing, wrong file is running) ----
SCRIPT_VERSION = "FIXED-NO-SKLEARN-v5-TN38"
print("=" * 70)
print(f"  CRIMECAST OPTION-7 ENGINE: {SCRIPT_VERSION}")
print("  sklearn model.predict: DISABLED")
print("  Output: TN38 only (cities rolled into parents)")
print("=" * 70)

RAPE_TARGET = "women_crimes_rape_sec_376_i"
TARGET_YEAR = 2026
ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "model_outputs"
FITTED = OUT_DIR / "fitted_predictions.csv"
OUTPUT_FILE = OUT_DIR / "rape_predictions_2026_all_districts.csv"
REPORT_FILE = OUT_DIR / "rape_predictions_2026_report.txt"


def _to_tn38(name: str) -> str | None:
    """Map free-text unit → TN38 district, or None if junk/unknown."""
    try:
        from district_entities import to_tn38

        return to_tn38(str(name), default=None)
    except Exception:
        # Minimal fallback aliases if district_entities missing
        key = str(name or "").strip().lower()
        aliases = {
            "chennai": "Chennai",
            "avadi": "Chennai",
            "tambaram": "Chennai",
            "madurai": "Madurai",
            "madurai city": "Madurai",
            "salem": "Salem",
            "salem city": "Salem",
            "coimbatore": "Coimbatore",
            "coimbatore city": "Coimbatore",
            "trichy": "Tiruchirappalli",
            "trichy city": "Tiruchirappalli",
            "tiruchirappalli": "Tiruchirappalli",
            "thirunelveli": "Tirunelveli",
            "thirunelveli city": "Tirunelveli",
            "tirunelveli": "Tirunelveli",
            "kanyakumari": "Kanniyakumari",
            "nilgiris": "The Nilgiris",
            "the nilgiris": "The Nilgiris",
            "villupuram": "Viluppuram",
            "thoothukudi": "Thoothukkudi",
            "ramnathapuram": "Ramanathapuram",
            "sivagangai": "Sivaganga",
            "pudukottai": "Pudukkottai",
            "thiruvannamalai": "Tiruvannamalai",
            "thiruvallur": "Tiruvallur",
            "thiruvarur": "Tiruvarur",
            "tiruppattur": "Tirupathur",
            "tiruppur city": "Tiruppur",
        }
        return aliases.get(key)


def _tn38_list() -> list[str]:
    try:
        from district_entities import TN38

        return list(TN38)
    except Exception:
        return [
            "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore",
            "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kanchipuram",
            "Kanniyakumari", "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai",
            "Nagapattinam", "Namakkal", "The Nilgiris", "Perambalur", "Pudukkottai",
            "Ramanathapuram", "Ranipet", "Salem", "Sivaganga", "Tenkasi",
            "Thanjavur", "Theni", "Thoothukkudi", "Tiruchirappalli", "Tirunelveli",
            "Tirupathur", "Tiruppur", "Tiruvallur", "Tiruvannamalai", "Tiruvarur",
            "Vellore", "Viluppuram", "Virudhunagar",
        ]


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
    half = max(0.5, 0.15 * mid, rmse * math.sqrt(1.0 + years_ahead))
    low = max(0.0, mid - half)
    high = mid + half
    return low, mid, high


def _load_hist():
    """
    Load rape history and roll city / alias units into TN38 parents.
    Same calendar year from city+district is summed (e.g. Madurai + Madurai City).
    Junk (Railway, Cyber Cell, Other Units) is dropped.
    """
    # district -> year -> total value
    year_totals: dict[str, dict[float, float]] = defaultdict(lambda: defaultdict(float))
    year_counts: dict[str, dict[float, int]] = defaultdict(lambda: defaultdict(int))
    dropped = []

    if not FITTED.exists():
        print(f"[ERROR] Missing {FITTED}")
        return {}

    with FITTED.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("target") or "").strip() != RAPE_TARGET:
                continue
            d = (row.get("district_city") or "").strip()
            if not d:
                continue
            canon = _to_tn38(d)
            if not canon:
                dropped.append(d)
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
                year_totals[canon][year] += val
                year_counts[canon][year] += 1

    if dropped:
        uniq = sorted(set(dropped))
        print(f"[INFO] Dropped {len(uniq)} non-TN38 units: {', '.join(uniq[:12])}"
              + ("…" if len(uniq) > 12 else ""))

    hist: dict[str, list[tuple[float, float]]] = {}
    for dist, ymap in year_totals.items():
        pts = sorted((y, ymap[y]) for y in ymap)
        hist[dist] = pts
    return hist


def _risk_from_pred(pred: float) -> tuple[float, str]:
    risk = round(min(1.0, 0.7 * min(max(pred, 0.0) / 25.0, 1.0)), 3)
    level = "HIGH" if risk > 0.65 else ("MEDIUM" if risk > 0.35 else "LOW")
    return risk, level


def predict_2026_rape_all_districts():
    """Public API — returns pandas DataFrame for all 38 TN districts. Never uses sklearn."""
    import pandas as pd

    hist = _load_hist()
    tn38 = _tn38_list()

    if not hist:
        if OUTPUT_FILE.exists():
            print(f"[WARN] No fitted history — reloading existing {OUTPUT_FILE.name}")
            try:
                existing = pd.read_csv(OUTPUT_FILE)
                return _normalize_to_tn38_df(existing)
            except Exception:
                pass
        print("[ERROR] No rape history and no existing CSV.")
        return pd.DataFrame(
            columns=["rank", "district", "predicted_2026_rape_incidents", "model"]
        )

    latest = [pts[-1][1] for pts in hist.values() if pts]
    gmed = sorted(latest)[len(latest) // 2] if latest else 0.0

    print(f"[OK] TN38 areas with history: {len(hist)} / {len(tn38)} | median floor: {gmed:.2f}")
    print()
    print(f"{'District':<30} {'2026 Prediction':>16}  Status")
    print("-" * 60)

    rows = []
    for district in tn38:
        pts = hist.get(district) or []
        if pts:
            years = [p[0] for p in pts]
            vals = [p[1] for p in pts]
            low, pred, high = _forecast_band(years, vals)
            if not math.isfinite(pred):
                pred, low, high = gmed, max(0.0, gmed * 0.7), gmed * 1.3
                method, conf = "Global median", "Low"
            else:
                method = "Trend (fitted-actual · TN38)"
                conf = "High" if len(pts) >= 2 else "Medium"
            n_pts = len(pts)
        else:
            # No history for this district — neutral floor, not news
            pred, low, high = 0.0, 0.0, 0.5
            method, conf = "No history (zero)", "Low"
            n_pts = 0

        risk, level = _risk_from_pred(pred)
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
                "data_points_available": n_pts,
                "base_year": TARGET_YEAR,
                "is_fallback": method != "Trend (fitted-actual · TN38)",
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
    print(f"[OK] Saved {len(rows)} TN38 predictions → {OUTPUT_FILE}")
    print(f"[OK] Engine {SCRIPT_VERSION} finished with ZERO sklearn errors")
    return pd.DataFrame(rows)


def _normalize_to_tn38_df(raw) -> "pd.DataFrame":
    """Roll any saved city/junk rows into TN38 for display / reload."""
    import pandas as pd

    if raw is None or (hasattr(raw, "empty") and raw.empty):
        return pd.DataFrame()
    df = raw.copy() if hasattr(raw, "copy") else pd.DataFrame(raw)
    rnc = "district" if "district" in df.columns else (
        "district_city" if "district_city" in df.columns else None
    )
    if not rnc:
        return df

    df["_d38"] = df[rnc].astype(str).map(lambda x: _to_tn38(x))
    df = df[df["_d38"].notna()].copy()
    if df.empty:
        return pd.DataFrame()

    metric = "predicted_2026_rape_incidents"
    sum_keys = ("incident", "pred_low", "pred_high", "width", "data_point")
    num_cols = [
        c
        for c in df.columns
        if c not in (rnc, "district", "district_city", "_d38", "risk_level",
                     "method", "model", "confidence", "rank")
        and pd.api.types.is_numeric_dtype(df[c])
    ]
    agg = {}
    for c in num_cols:
        cl = c.lower()
        agg[c] = "sum" if any(k in cl for k in sum_keys) else "mean"
    keep = [c for c in ("method", "model", "confidence") if c in df.columns]
    g = df.groupby("_d38", as_index=False)
    if agg:
        out = g.agg({**agg, **{c: "first" for c in keep}}) if keep else g.agg(agg)
    else:
        out = df.drop_duplicates(subset=["_d38"], keep="first")[["_d38"] + keep]
    out = out.rename(columns={"_d38": "district"})

    # Full TN38 frame
    base = pd.DataFrame({"district": _tn38_list()})
    out = base.merge(out, on="district", how="left")

    if metric in out.columns:
        out[metric] = pd.to_numeric(out[metric], errors="coerce")
        # Recompute risk from rolled-up mid
        risks, levels = [], []
        for v in out[metric].fillna(0.0):
            r, lv = _risk_from_pred(float(v) if pd.notna(v) else 0.0)
            risks.append(r)
            levels.append(lv)
        out["rape_risk_index"] = risks
        out["risk_level"] = levels
        out = out.sort_values(metric, ascending=False, na_position="last").reset_index(drop=True)
        out["rank"] = range(1, len(out) + 1)
    return out


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
    avg = total / len(rows) if rows else 0.0
    top = sorted(
        rows,
        key=lambda r: float(r.get("predicted_2026_rape_incidents") or 0),
        reverse=True,
    )
    lines = [
        "=" * 70,
        "2026 RAPE CRIME PREDICTION REPORT - TAMIL NADU",
        f"Engine: {SCRIPT_VERSION} (NO sklearn · TN38 only)",
        "=" * 70,
        f"Total districts (TN38): {len(rows)}",
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
        "City units rolled into parent districts (Madurai City→Madurai, Avadi→Chennai).",
        "Junk units (Railway / Cyber Cell / Other) excluded.",
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
