# -*- coding: utf-8 -*-
"""
CRIMECAST multi-target district forecasts (no Prophet / sklearn).

Methods:
  - linear   : linear trend → target year + uncertainty band
  - last_year: carry last observed value
  - blend    : 0.5 * linear + 0.5 * last_year

Targets map to columns in fitted_predictions.csv / ML-ready style names.
"""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "model_outputs"
FITTED = OUT_DIR / "fitted_predictions.csv"

# Public forecast targets (key → fitted target name, display label, risk scale)
FORECAST_TARGETS: dict[str, dict[str, Any]] = {
    "rape_incidents": {
        "fitted_target": "women_crimes_rape_sec_376_i",
        "label": "Rape incidents (Sec 376)",
        "metric_col": "predicted_value",
        "risk_scale": 25.0,
        "out_csv": "forecast_2026_rape_incidents.csv",
    },
    "murder_incidence": {
        "fitted_target": "murder_homicide_murder_incidence",
        "label": "Murder incidence",
        "metric_col": "predicted_value",
        "risk_scale": 40.0,
        "out_csv": "forecast_2026_murder_incidence.csv",
    },
    "total_complaints": {
        "fitted_target": "complaints_total_complaints",
        "label": "Total complaints",
        "metric_col": "predicted_value",
        "risk_scale": 25000.0,
        "out_csv": "forecast_2026_total_complaints.csv",
    },
}

METHODS = ("linear", "last_year", "blend")


def _to_tn38(name: str) -> str | None:
    try:
        from district_entities import to_tn38

        return to_tn38(str(name), default=None)
    except Exception:
        return str(name).strip() or None


def _tn38_list() -> list[str]:
    try:
        from district_entities import TN38

        return list(TN38)
    except Exception:
        return []


def _forecast_band(years, values, target_year: int) -> tuple[float, float, float]:
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
    return max(0.0, mid - half), mid, mid + half


def _load_hist(fitted_target: str) -> dict[str, list[tuple[float, float]]]:
    year_totals: dict[str, dict[float, float]] = defaultdict(lambda: defaultdict(float))
    if not FITTED.exists():
        return {}
    with FITTED.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("target") or "").strip() != fitted_target:
                continue
            d = (row.get("district_city") or "").strip()
            if not d:
                continue
            canon = _to_tn38(d)
            if not canon:
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
    hist = {}
    for dist, ymap in year_totals.items():
        hist[dist] = sorted((y, ymap[y]) for y in ymap)
    return hist


def _risk(pred: float, scale: float) -> tuple[float, str]:
    risk = round(min(1.0, 0.7 * min(max(pred, 0.0) / max(scale, 1e-6), 1.0)), 3)
    level = "HIGH" if risk > 0.65 else ("MEDIUM" if risk > 0.35 else "LOW")
    return risk, level


def forecast_districts(
    target_key: str = "rape_incidents",
    *,
    method: str = "linear",
    target_year: int = 2026,
    save: bool = True,
) -> pd.DataFrame:
    """
    Forecast all TN38 districts for one target with chosen method.
    Returns DataFrame with district, predicted_value, pred_low, pred_high, ...
    For rape_incidents also aliases predicted_2026_rape_incidents for dashboard compat.
    """
    if target_key not in FORECAST_TARGETS:
        raise ValueError(f"Unknown target_key {target_key}. Use {list(FORECAST_TARGETS)}")
    method = (method or "linear").strip().lower()
    if method not in METHODS:
        method = "linear"
    meta = FORECAST_TARGETS[target_key]
    hist = _load_hist(meta["fitted_target"])
    tn38 = _tn38_list() or sorted(hist.keys())
    scale = float(meta["risk_scale"])

    latest_vals = [pts[-1][1] for pts in hist.values() if pts]
    gmed = sorted(latest_vals)[len(latest_vals) // 2] if latest_vals else 0.0

    rows = []
    for district in tn38:
        pts = hist.get(district) or []
        if not pts:
            pred = low = 0.0
            high = 0.5
            n_pts = 0
            last_v = 0.0
            meth_label = f"{method} · no history"
        else:
            years = [p[0] for p in pts]
            vals = [p[1] for p in pts]
            last_v = float(vals[-1])
            n_pts = len(pts)
            low_l, mid_l, high_l = _forecast_band(years, vals, target_year)
            if method == "last_year":
                pred = max(0.0, last_v)
                pad = max(0.5, 0.15 * pred)
                low, high = max(0.0, pred - pad), pred + pad
                meth_label = "last_year carry"
            elif method == "blend":
                pred = max(0.0, 0.5 * mid_l + 0.5 * last_v)
                low = max(0.0, 0.5 * low_l + 0.5 * max(0.0, last_v * 0.85))
                high = 0.5 * high_l + 0.5 * (last_v * 1.15)
                meth_label = "blend 50% linear + 50% last_year"
            else:
                pred, low, high = mid_l, low_l, high_l
                if not math.isfinite(pred):
                    pred, low, high = gmed, max(0.0, gmed * 0.7), gmed * 1.3
                    meth_label = "linear · median floor"
                else:
                    meth_label = "linear trend"

        risk, level = _risk(pred, scale)
        row = {
            "district": district,
            "target_key": target_key,
            "target_label": meta["label"],
            "forecast_year": target_year,
            "forecast_method": method,
            "predicted_value": round(pred, 2),
            "pred_low": round(low, 2),
            "pred_high": round(high, 2),
            "uncertainty_width": round(high - low, 2),
            "last_observed": round(last_v, 2) if pts else None,
            "data_points_available": n_pts,
            "method": meth_label,
            "rape_risk_index": risk,
            "risk_level": level,
            "model": f"forecast_{method}",
            "confidence": "High" if n_pts >= 2 else ("Medium" if n_pts == 1 else "Low"),
        }
        # Compat for rape dashboard map
        if target_key == "rape_incidents":
            row["predicted_2026_rape_incidents"] = row["predicted_value"]
        rows.append(row)

    rows.sort(key=lambda r: r["predicted_value"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    df = pd.DataFrame(rows)
    if save and not df.empty:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / meta["out_csv"]
        df.to_csv(path, index=False)
        # Keep classic rape path in sync when rape + linear/blend
        if target_key == "rape_incidents":
            classic = OUT_DIR / "rape_predictions_2026_all_districts.csv"
            df.to_csv(classic, index=False)
    return df


def load_training_metrics_best() -> pd.DataFrame:
    path = OUT_DIR / "training_metrics.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "is_best" in df.columns:
        best = df[df["is_best"].astype(str).str.lower().isin(("true", "1", "yes"))]
        if not best.empty:
            return best.reset_index(drop=True)
    return df


def backtest_year(
    target: str,
    holdout_year: int = 2024,
    *,
    max_districts: int = 30,
) -> pd.DataFrame:
    """
    Simple backtest: use history years < holdout_year to forecast holdout_year
    via linear method; compare to actual if present in fitted or ML-ready.
    """
    # Map UI target to fitted name
    fitted = target
    for k, m in FORECAST_TARGETS.items():
        if k == target or m["fitted_target"] == target:
            fitted = m["fitted_target"]
            break

    hist_all = _load_hist(fitted)
    rows = []
    for dist, pts in hist_all.items():
        train = [(y, v) for y, v in pts if y < holdout_year]
        actual_pts = [v for y, v in pts if int(y) == int(holdout_year)]
        if not train:
            continue
        years = [p[0] for p in train]
        vals = [p[1] for p in train]
        _, pred, _ = _forecast_band(years, vals, holdout_year)
        actual = float(actual_pts[0]) if actual_pts else None
        err = abs(pred - actual) if actual is not None else None
        rows.append(
            {
                "district": dist,
                "holdout_year": holdout_year,
                "target": fitted,
                "n_train_years": len(train),
                "predicted": round(pred, 3),
                "actual": None if actual is None else round(actual, 3),
                "abs_error": None if err is None else round(err, 3),
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Prefer rows with actual
    with_act = df[df["actual"].notna()]
    if not with_act.empty:
        df = with_act.sort_values("abs_error", ascending=True)
    return df.head(max_districts).reset_index(drop=True)
