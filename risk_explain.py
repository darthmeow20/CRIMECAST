# -*- coding: utf-8 -*-
"""
CRIMECAST — risk explainability (SHAP / LIME-style + feature importances).

Works without optional packages when possible:
  - Tree/linear model feature_importances_ / coef_ always
  - Local LIME-style: perturb numeric features, fit Ridge on Δprediction
  - Optional real SHAP if `shap` is installed
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _artifact_and_row(target: str, area: str, year: int | None = None):
    from predict import (
        load_best_models,
        load_dataset,
        load_model_for_target,
        resolve_area,
        resolve_target,
        series_to_feature_frame,
        predict_with_artifact,
    )

    resolved = resolve_target(target)
    df = load_dataset()
    best = load_best_models()
    artifact = load_model_for_target(resolved, best)
    row = resolve_area(df, area, year)
    feats = [str(c) for c in artifact["feature_columns"]]
    x = series_to_frame_safe(row, feats)
    return resolved, df, artifact, row, feats, x


def series_to_frame_safe(row: pd.Series, feats: list[str]) -> pd.DataFrame:
    from predict import series_to_feature_frame

    return series_to_feature_frame(row, feats)


def _unwrap_estimator(model: Any) -> Any:
    """Get final estimator from Pipeline / TransformedTargetRegressor / dict artifact."""
    if isinstance(model, dict):
        model = model.get("model", model)
    # TransformedTargetRegressor
    if hasattr(model, "regressor_"):
        model = model.regressor_
    elif type(model).__name__ == "TransformedTargetRegressor" and hasattr(model, "regressor"):
        model = model.regressor
    if hasattr(model, "named_steps"):
        # prefer named "model" step, else last step
        steps = model.named_steps
        if "model" in steps:
            return steps["model"]
        vals = list(steps.values())
        if vals:
            return vals[-1]
    if hasattr(model, "steps") and model.steps:
        return model.steps[-1][1]
    return model


def _feature_names_after_preprocess(pipeline: Any, input_feats: list[str]) -> list[str]:
    """Best-effort feature names after ColumnTransformer / Pipeline."""
    try:
        if hasattr(pipeline, "named_steps") and "preprocess" in pipeline.named_steps:
            pre = pipeline.named_steps["preprocess"]
            if hasattr(pre, "get_feature_names_out"):
                names = list(pre.get_feature_names_out())
                return [str(n).replace("numeric__", "").replace("categorical__", "") for n in names]
    except Exception:
        pass
    return list(input_feats)


def global_feature_importances(target: str, top_n: int = 15) -> pd.DataFrame:
    """
    Global model importance (tree feature_importances_ or |coef_|).
    Returns DataFrame: feature, importance, method
    """
    from predict import load_best_models, load_model_for_target, resolve_target

    resolved = resolve_target(target)
    best = load_best_models()
    artifact = load_model_for_target(resolved, best)
    feats = [str(c) for c in artifact["feature_columns"]]
    raw = artifact["model"] if isinstance(artifact, dict) else artifact
    est = _unwrap_estimator(raw)

    method = "unknown"
    imp = None
    names = feats

    if hasattr(est, "feature_importances_"):
        imp = np.asarray(est.feature_importances_, dtype=float)
        method = "tree_feature_importances"
        # length may match post-preprocess features
        if len(imp) != len(feats):
            names = _feature_names_after_preprocess(raw, feats)
            if len(names) != len(imp):
                names = [f"f{i}" for i in range(len(imp))]
    elif hasattr(est, "coef_"):
        coef = np.asarray(est.coef_, dtype=float).ravel()
        imp = np.abs(coef)
        method = "abs_linear_coef"
        if len(imp) != len(feats):
            names = _feature_names_after_preprocess(raw, feats)
            if len(names) != len(imp):
                names = [f"f{i}" for i in range(len(imp))]
    else:
        return pd.DataFrame(columns=["feature", "importance", "method"])

    out = pd.DataFrame({"feature": names[: len(imp)], "importance": imp, "method": method})
    out = out.sort_values("importance", ascending=False).head(top_n).reset_index(drop=True)
    s = out["importance"].sum()
    if s > 0:
        out["share"] = out["importance"] / s
    else:
        out["share"] = 0.0
    return out


def lime_local_explain(
    target: str,
    area: str,
    year: int | None = 2026,
    n_samples: int = 80,
    top_n: int = 12,
) -> dict[str, Any]:
    """
    LIME-style local explanation without the lime package:
    perturb numeric features around the district row, re-predict, fit Ridge on Δy.
    """
    from sklearn.linear_model import Ridge

    from predict import predict_with_artifact

    resolved, df, artifact, row, feats, x0 = _artifact_and_row(target, area, year)
    raw = artifact["model"] if isinstance(artifact, dict) else artifact

    base_pred = float(predict_with_artifact(raw, x0))
    x0 = x0.copy()

    # Numeric columns only for perturbation
    num_cols = []
    for c in feats:
        v = x0.iloc[0][c]
        try:
            float(v)
            num_cols.append(c)
        except Exception:
            continue
    if not num_cols:
        return {
            "area": area,
            "target": resolved,
            "base_prediction": base_pred,
            "method": "lime_style",
            "contributions": pd.DataFrame(),
            "note": "No numeric features to perturb.",
        }

    # Background stats from ML data for scale
    scales = {}
    for c in num_cols:
        if c in df.columns:
            s = pd.to_numeric(df[c], errors="coerce").std()
            scales[c] = float(s) if pd.notna(s) and s > 1e-9 else 1.0
        else:
            scales[c] = 1.0

    rng = np.random.default_rng(42)
    X_pert = []
    y_pert = []
    for _ in range(n_samples):
        row_p = x0.copy()
        for c in num_cols:
            noise = rng.normal(0.0, 0.35 * scales[c])
            try:
                row_p.loc[row_p.index[0], c] = float(x0.iloc[0][c]) + noise
            except Exception:
                pass
        try:
            yp = float(predict_with_artifact(raw, row_p))
        except Exception:
            continue
        X_pert.append([float(row_p.iloc[0][c]) - float(x0.iloc[0][c]) for c in num_cols])
        y_pert.append(yp - base_pred)

    if len(X_pert) < 10:
        return {
            "area": area,
            "target": resolved,
            "base_prediction": base_pred,
            "method": "lime_style",
            "contributions": pd.DataFrame(),
            "note": "Too few successful perturbations.",
        }

    Xa = np.asarray(X_pert, dtype=float)
    ya = np.asarray(y_pert, dtype=float)
    # weight samples closer to original more (LIME kernel)
    dist = np.linalg.norm(Xa / (np.array([scales[c] for c in num_cols]) + 1e-9), axis=1)
    w = np.exp(-(dist ** 2) / 2.0)
    model = Ridge(alpha=1.0)
    model.fit(Xa, ya, sample_weight=w)
    coefs = model.coef_

    # Contribution ≈ coef * (x_i - mean_background) or local value relative to 0 delta
    # Report: importance of moving this feature = |coef| * |local z|
    local_vals = np.array([float(x0.iloc[0][c]) for c in num_cols])
    bg = []
    for c in num_cols:
        if c in df.columns:
            m = pd.to_numeric(df[c], errors="coerce").mean()
            bg.append(float(m) if pd.notna(m) else 0.0)
        else:
            bg.append(0.0)
    bg = np.array(bg)
    delta = local_vals - bg
    contrib = coefs * delta

    contr = pd.DataFrame(
        {
            "feature": num_cols,
            "coefficient": coefs,
            "local_value": local_vals,
            "background_mean": bg,
            "contribution": contrib,
            "abs_contribution": np.abs(contrib),
        }
    ).sort_values("abs_contribution", ascending=False).head(top_n).reset_index(drop=True)

    return {
        "area": str(row.get("district_city", area)),
        "target": resolved,
        "base_prediction": base_pred,
        "method": "lime_style_ridge",
        "contributions": contr,
        "note": (
            "Local linear model on feature perturbations (LIME-style). "
            "Positive contribution → pushes prediction up for this district."
        ),
    }


def shap_or_proxy_explain(
    target: str,
    area: str,
    year: int | None = 2026,
    top_n: int = 12,
) -> dict[str, Any]:
    """
    Prefer real SHAP TreeExplainer / LinearExplainer if installed;
    otherwise importance × (local − mean) proxy.
    """
    from predict import predict_with_artifact

    resolved, df, artifact, row, feats, x0 = _artifact_and_row(target, area, year)
    raw = artifact["model"] if isinstance(artifact, dict) else artifact
    base_pred = float(predict_with_artifact(raw, x0))

    # --- Try real SHAP ---
    try:
        import shap  # type: ignore

        est = _unwrap_estimator(raw)
        # Build background of ~40 rows
        bg_rows = []
        for _, r in df.sample(min(40, len(df)), random_state=0).iterrows():
            bg_rows.append(series_to_frame_safe(r, feats).iloc[0])
        X_bg = pd.DataFrame(bg_rows)
        X_loc = x0

        # Transform if pipeline
        if hasattr(raw, "named_steps") and "preprocess" in raw.named_steps:
            pre = raw.named_steps["preprocess"]
            X_bg_t = pre.transform(X_bg)
            X_loc_t = pre.transform(X_loc)
            names = _feature_names_after_preprocess(raw, feats)
            if hasattr(est, "feature_importances_") or "Forest" in type(est).__name__ or "Boost" in type(est).__name__ or "Tree" in type(est).__name__:
                explainer = shap.TreeExplainer(est)
                sv = explainer.shap_values(X_loc_t)
            else:
                explainer = shap.LinearExplainer(est, X_bg_t)
                sv = explainer.shap_values(X_loc_t)
            vals = np.asarray(sv).ravel()
            if len(names) != len(vals):
                names = [f"f{i}" for i in range(len(vals))]
            contr = pd.DataFrame(
                {"feature": names[: len(vals)], "contribution": vals, "abs_contribution": np.abs(vals)}
            ).sort_values("abs_contribution", ascending=False).head(top_n)
            return {
                "area": str(row.get("district_city", area)),
                "target": resolved,
                "base_prediction": base_pred,
                "method": "shap",
                "contributions": contr.reset_index(drop=True),
                "note": "SHAP values from installed `shap` package.",
            }
    except Exception:
        pass

    # --- Proxy: global importance × local z-score ---
    gimp = global_feature_importances(target, top_n=50)
    if gimp.empty:
        return {
            "area": area,
            "target": resolved,
            "base_prediction": base_pred,
            "method": "proxy_unavailable",
            "contributions": pd.DataFrame(),
            "note": "Could not extract model importances.",
        }

    rows = []
    for _, gr in gimp.iterrows():
        f = str(gr["feature"])
        # map back to original feature if possible
        src = f
        for cand in feats:
            if cand in f or f.endswith(cand) or f == cand:
                src = cand
                break
        if src not in x0.columns:
            continue
        try:
            loc = float(pd.to_numeric(x0.iloc[0][src], errors="coerce"))
        except Exception:
            continue
        if src in df.columns:
            ser = pd.to_numeric(df[src], errors="coerce")
            mu = float(ser.mean()) if ser.notna().any() else 0.0
            sd = float(ser.std()) if ser.notna().any() and ser.std() > 1e-9 else 1.0
        else:
            mu, sd = 0.0, 1.0
        z = (loc - mu) / sd
        # signed proxy: importance * z (high feature + high importance → pushes risk up)
        contrib = float(gr["importance"]) * z
        rows.append(
            {
                "feature": src,
                "importance": float(gr["importance"]),
                "local_value": loc,
                "state_mean": mu,
                "z_score": z,
                "contribution": contrib,
                "abs_contribution": abs(contrib),
            }
        )

    contr = pd.DataFrame(rows)
    if not contr.empty:
        contr = contr.sort_values("abs_contribution", ascending=False).head(top_n).reset_index(drop=True)

    return {
        "area": str(row.get("district_city", area)),
        "target": resolved,
        "base_prediction": base_pred,
        "method": "importance_x_zscore_proxy",
        "contributions": contr,
        "note": (
            "SHAP not installed — using feature-importance × local z-score proxy. "
            "Install `shap` for true SHAP values. Positive ≈ feature above state mean "
            "with high model weight (associated with higher predicted risk)."
        ),
    }


def composite_risk_factors(
    area: str,
    card: dict[str, Any],
    *,
    state_medians: dict[str, float] | None = None,
) -> pd.DataFrame:
    """
    Human-readable multi-source risk factors (not pure ML SHAP):
    crime rates, 2026 forecast, news, sentiment vs state medians.
    """
    state_medians = state_medians or {}
    factors = []

    def add(name, value, median, weight, higher_worse=True):
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return
        try:
            v = float(value)
        except Exception:
            return
        med = float(median) if median is not None and not (isinstance(median, float) and np.isnan(median)) else None
        if med is not None and med > 0:
            ratio = v / med
            elev = (ratio - 1.0) if higher_worse else (1.0 - ratio)
        else:
            elev = 0.0
            ratio = None
        score = weight * max(0.0, elev if higher_worse else elev)
        factors.append(
            {
                "factor": name,
                "value": round(v, 3),
                "state_median": None if med is None else round(med, 3),
                "vs_median": None if ratio is None else round(ratio, 2),
                "risk_push": round(float(score), 4),
                "weight": weight,
            }
        )

    add("Murder rate", card.get("murder_rate"), state_medians.get("murder_rate"), 0.22)
    add("Rape rate", card.get("rape_rate"), state_medians.get("rape_rate"), 0.22)
    add("Rape incidents", card.get("rape_incidents"), state_medians.get("rape_incidents"), 0.12)
    add("Total complaints", card.get("complaints"), state_medians.get("complaints"), 0.10)
    add("2026 rape forecast", card.get("forecast_2026_rape"), state_medians.get("forecast_2026_rape"), 0.18)
    add("News heat (90d)", card.get("news_90d"), state_medians.get("news_90d"), 0.10)
    # Negative polarity is worse → invert
    pol = card.get("sentiment_polarity")
    if pol is not None:
        try:
            # more negative → higher push
            elev = max(0.0, -float(pol))  # 0..1-ish
            factors.append(
                {
                    "factor": "Sentiment (negative polarity)",
                    "value": round(float(pol), 3),
                    "state_median": state_medians.get("sentiment_polarity"),
                    "vs_median": None,
                    "risk_push": round(0.06 * elev, 4),
                    "weight": 0.06,
                }
            )
        except Exception:
            pass
    if card.get("rape_risk_index") is not None:
        try:
            ri = float(card["rape_risk_index"])
            factors.append(
                {
                    "factor": "2026 rape risk index",
                    "value": round(ri, 3),
                    "state_median": 0.35,
                    "vs_median": round(ri / 0.35, 2) if ri else None,
                    "risk_push": round(0.12 * ri, 4),
                    "weight": 0.12,
                }
            )
        except Exception:
            pass

    out = pd.DataFrame(factors)
    if not out.empty:
        out = out.sort_values("risk_push", ascending=False).reset_index(drop=True)
    return out
