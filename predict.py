from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from train_model import ML_READY_FILE, MODEL_DIR, OUTPUT_DIR, TARGET_CONFIGS, train_models


def load_risk_weights() -> dict[str, float]:
    """Load configurable weights for risk index. Allows tuning volume / sentiment / news importance."""
    default = {"volume": 0.50, "sentiment": 0.30, "news": 0.20}
    cfg_path = Path("config/risk_weights.json")
    if cfg_path.exists():
        try:
            with open(cfg_path, encoding="utf-8") as f:
                user = json.load(f)
            # Only take numeric keys we care about
            for k in default:
                if k in user and isinstance(user[k], (int, float)):
                    default[k] = float(user[k])
            # Normalize if they don't sum close to 1
            total = sum(default.values())
            if total > 0 and abs(total - 1.0) > 0.05:
                for k in default:
                    default[k] /= total
        except Exception as e:
            print(f"[WARN] Could not load risk weights: {e}")
    return default


BEST_MODELS_FILE = OUTPUT_DIR / "best_models.json"
PREDICTION_OUTPUT_FILE = OUTPUT_DIR / "crime_predictions.csv"

TARGET_ALIASES = {
    "complaints": "complaints_total_complaints",
    "total_complaints": "complaints_total_complaints",
    "murder": "murder_homicide_murder_incidence",
    "murder_incidence": "murder_homicide_murder_incidence",
    "rape": "women_crimes_rape_sec_376_i",
    "rape_incidents": "women_crimes_rape_sec_376_i",
    # Rate aliases for crime rate prediction
    "murder_rate": "murder_homicide_murder_rate",
    "rape_rate": "women_crimes_rape_r",
    "rate": "women_crimes_rape_r",  # default generic rate -> rape rate
    "crime_rate": "complaints_rate_of_cognizable_crime_ipc_sll",
    "cognizable_rate": "complaints_rate_of_cognizable_crime_ipc_sll",
}


def load_dataset(data_path: Path = ML_READY_FILE) -> pd.DataFrame:
    if not data_path.exists():
        train_models(data_path=data_path)
    return pd.read_csv(data_path)


def load_best_models(best_models_file: Path = BEST_MODELS_FILE) -> dict[str, dict[str, Any]]:
    if not best_models_file.exists():
        train_models()

    rows = json.loads(best_models_file.read_text(encoding="utf-8"))
    return {row["target"]: row for row in rows}


def resolve_target(target: str) -> str:
    normalized = target.strip().lower().replace("-", "_").replace(" ", "_")
    resolved = TARGET_ALIASES.get(normalized, normalized)

    if resolved not in TARGET_CONFIGS:
        valid = ", ".join(sorted(TARGET_CONFIGS))
        aliases = ", ".join(sorted(TARGET_ALIASES))
        raise ValueError(f"Unknown target '{target}'. Use one of: {valid}. Aliases: {aliases}")

    return resolved


def resolve_area(df: pd.DataFrame, area: str, year: int | None = None) -> pd.Series:
    normalized_area = area.strip().casefold()
    matches = df[df["district_city"].astype(str).str.casefold() == normalized_area]

    if matches.empty:
        available = ", ".join(df["district_city"].sort_values().head(12).to_list())
        raise ValueError(f"Area '{area}' was not found. Example available areas: {available}")

    if year is not None:
        matches = matches[matches["year"].astype(int) == year]
        if matches.empty:
            # For future years (e.g. 2026), fall back to most recent data as template
            # We will override the year feature below
            if year > int(matches["year"].max() if not matches.empty else 0):
                matches = df[df["district_city"].astype(str).str.casefold() == normalized_area]
            else:
                raise ValueError(f"Area '{area}' was found, but not for year {year}")

    if year is None or year <= int(df["year"].max()):
        matches = matches[matches["year"] == matches["year"].max()]

    row = matches.sort_values("year").iloc[-1].copy()

    # --- Key accuracy fix for forecasting ---
    # Always set the year features to the requested year so models that learned
    # time trends (year_centered, is_latest_year) can extrapolate to future.
    if year is not None:
        row["year"] = int(year)
        if "year_centered" in row.index:
            row["year_centered"] = float(year) - 2022.5
        if "is_latest_year" in row.index:
            # When predicting future, treat as "latest" in spirit for the model
            row["is_latest_year"] = 1

    return row


def parse_overrides(values: list[str] | None) -> dict[str, str]:
    overrides: dict[str, str] = {}

    for value in values or []:
        if "=" not in value:
            raise ValueError(f"Override '{value}' must use COLUMN=VALUE format")
        column, override_value = value.split("=", 1)
        overrides[column.strip()] = override_value.strip()

    return overrides


def apply_overrides(row: pd.Series, overrides: dict[str, str], feature_columns: list[str]) -> pd.Series:
    updated = row.copy()
    allowed = set(feature_columns)

    for column, value in overrides.items():
        if column not in allowed:
            raise ValueError(f"Cannot override '{column}'. It is not a feature for this model.")

        existing = updated[column]
        if pd.api.types.is_number(existing):
            updated[column] = float(value)
        else:
            updated[column] = value

    return updated


def load_model_for_target(target: str, best_models: dict[str, dict[str, Any]]) -> dict[str, Any]:
    metadata = best_models.get(target)
    if metadata is None:
        raise ValueError(f"No trained model metadata found for target '{target}'")

    model_path = Path(metadata["model_path"])
    if not model_path.exists():
        train_models(targets=[target])
        best_models = load_best_models()
        metadata = best_models[target]
        model_path = Path(metadata["model_path"])

    return joblib.load(model_path)


def series_to_feature_frame(source_row: pd.Series, feature_columns: list[str]) -> pd.DataFrame:
    """Build a 1-row DataFrame for model input. Never use Series[list_of_str] (Pandas 3)."""
    import numpy as np

    row: dict[str, Any] = {}
    idx = source_row.index
    for col in feature_columns:
        col = str(col)
        if col not in idx:
            row[col] = 0.0
            continue
        val = source_row.loc[col]
        # Duplicate index labels → Series; take first scalar
        if isinstance(val, (pd.Series, pd.DataFrame)):
            try:
                val = val.iloc[0] if len(val) else 0.0
            except Exception:
                val = 0.0
        if isinstance(val, (list, tuple, np.ndarray)):
            val = val[0] if len(val) else 0.0
        try:
            if val is None or (isinstance(val, float) and np.isnan(val)) or pd.isna(val):
                row[col] = 0.0
            elif isinstance(val, (int, float, np.integer, np.floating)):
                row[col] = float(val)
            else:
                # keep strings for possible categorical features
                row[col] = val
        except Exception:
            row[col] = 0.0
    return pd.DataFrame([row], columns=[str(c) for c in feature_columns])


def _select_columns_as_array(X_df: pd.DataFrame, cols: Any, *, as_numeric: bool = True) -> Any:
    """Select columns by name/position without sklearn string-index path; return 2D array-like."""
    import numpy as np

    n = len(X_df)
    if cols is None or cols == "drop":
        return np.zeros((n, 0), dtype=float)
    if isinstance(cols, slice):
        arr = X_df.iloc[:, cols].to_numpy()
        return arr.astype(float) if as_numeric else arr
    if isinstance(cols, str):
        cols = [cols]
    if not hasattr(cols, "__iter__"):
        cols = [cols]
    cols = list(cols)
    if not cols:
        return np.zeros((n, 0), dtype=float)
    if isinstance(cols[0], (bool, np.bool_)):
        arr = X_df.loc[:, cols].to_numpy()
        return arr.astype(float) if as_numeric else arr
    if isinstance(cols[0], (int, np.integer)):
        arr = X_df.iloc[:, cols].to_numpy()
        return arr.astype(float) if as_numeric else arr

    # string column names — select one at a time (DataFrame only)
    pieces = []
    for c in cols:
        c = str(c)
        if c in X_df.columns:
            col = X_df[c]
            if as_numeric:
                pieces.append(pd.to_numeric(col, errors="coerce").fillna(0.0).to_numpy().reshape(n, 1))
            else:
                # categorical: keep as object strings
                pieces.append(col.astype(object).fillna("unknown").astype(str).to_numpy().reshape(n, 1))
        else:
            if as_numeric:
                pieces.append(np.zeros((n, 1), dtype=float))
            else:
                pieces.append(np.full((n, 1), "unknown", dtype=object))
    if not pieces:
        return np.zeros((n, 0), dtype=float)
    return np.hstack(pieces)


def _column_transform_manual(col_transformer: Any, X_df: pd.DataFrame) -> Any:
    """
    Apply a fitted ColumnTransformer without sklearn string-column indexing.
    Avoids: ValueError: Specifying the columns using strings is only supported for dataframes.
    """
    import numpy as np

    transformers = getattr(col_transformer, "transformers_", None)
    if not transformers:
        X_plain = pd.DataFrame(
            {str(c): X_df[c].to_numpy() for c in X_df.columns},
            index=range(len(X_df)),
        )
        return col_transformer.transform(X_plain)

    parts: list[Any] = []
    n = len(X_df)
    for name, trans, cols in transformers:
        if name == "remainder" and trans == "drop":
            continue
        if trans == "drop" or cols == "drop":
            continue

        # Heuristic: categorical branch names / presence of OneHotEncoder
        is_categorical = False
        name_l = str(name).lower()
        if "cat" in name_l or "categor" in name_l:
            is_categorical = True
        else:
            try:
                steps = getattr(trans, "named_steps", {}) or {}
                if "onehot" in steps or any("OneHot" in type(s).__name__ for s in steps.values()):
                    is_categorical = True
            except Exception:
                pass

        if trans == "passthrough":
            sub = _select_columns_as_array(X_df, cols, as_numeric=not is_categorical)
            parts.append(np.asarray(sub, dtype=float) if not is_categorical else np.asarray(sub))
            continue

        sub = _select_columns_as_array(X_df, cols, as_numeric=not is_categorical)
        if hasattr(trans, "transform"):
            try:
                out = trans.transform(sub)
            except Exception:
                try:
                    out = trans.transform(np.asarray(sub, dtype=float))
                except Exception:
                    # last resort for categoricals
                    out = trans.transform(np.asarray(sub, dtype=object))
            if hasattr(out, "toarray"):
                out = out.toarray()
            parts.append(np.asarray(out, dtype=float))
        else:
            parts.append(np.asarray(sub, dtype=float))

    if not parts:
        return np.zeros((n, 0), dtype=float)
    shaped = []
    for p in parts:
        p = np.asarray(p, dtype=float)
        if p.ndim == 1:
            p = p.reshape(n, -1)
        shaped.append(p)
    return np.hstack(shaped)


def predict_with_artifact(model: Any, X_df: pd.DataFrame) -> float:
    """
    Robust single-row (or multi-row first) prediction for CRIMECAST artifacts.

    Handles TransformedTargetRegressor + Pipeline(ColumnTransformer, estimator).
    Bypasses sklearn ColumnTransformer string-column selection which fails when
    the input is not recognized as a dataframe (Pandas 3 / narwhals edge cases).
    """
    import numpy as np

    # Normalize to a plain DataFrame with string column names
    X = pd.DataFrame(
        {str(c): X_df[c].to_numpy() if c in X_df.columns else np.zeros(len(X_df)) for c in X_df.columns},
        index=range(len(X_df)),
    )

    inv_func = None
    est = model

    # Fitted TransformedTargetRegressor
    if hasattr(est, "regressor_"):
        inv_func = getattr(est, "inverse_func_", None) or getattr(est, "inverse_func", None)
        est = est.regressor_
    elif type(est).__name__ == "TransformedTargetRegressor":
        inv_func = getattr(est, "inverse_func", None)
        if hasattr(est, "regressor"):
            est = est.regressor

    pred: Any
    if hasattr(est, "named_steps") and "preprocess" in getattr(est, "named_steps", {}):
        pre = est.named_steps["preprocess"]
        final = est.named_steps.get("model")
        if final is None:
            # last step
            final = est.steps[-1][1]
        Xt = _column_transform_manual(pre, X)
        pred = final.predict(Xt)
    else:
        try:
            pred = est.predict(X)
        except Exception:
            # last resort: pure numpy
            try:
                pred = est.predict(X.to_numpy(dtype=float))
            except Exception:
                pred = est.predict(np.nan_to_num(X.apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)))

    pred_arr = np.asarray(pred, dtype=float).ravel()
    if inv_func is not None:
        pred_arr = np.asarray(inv_func(pred_arr), dtype=float).ravel()
    return float(pred_arr[0])


def _official_history_baseline(
    df: pd.DataFrame,
    area: str,
    target: str,
    *,
    prefer_max_year: int = 2023,
) -> float | None:
    """Mean of official-era values (prefer is_official_year or year<=prefer_max_year).

    Example: Thoothukudi murder rate ~4.0–4.5 vs Madurai ~2.9–3.0 should stay ordered.
    """
    if "district_city" not in df.columns or target not in df.columns:
        return None
    mask = df["district_city"].astype(str).str.strip().str.casefold() == str(area).strip().casefold()
    sub = df.loc[mask]
    if sub.empty:
        return None
    if "is_official_year" in sub.columns and sub["is_official_year"].astype(bool).any():
        sub = sub.loc[sub["is_official_year"].astype(bool)]
    elif "year" in sub.columns:
        years = pd.to_numeric(sub["year"], errors="coerce")
        official = sub.loc[years <= prefer_max_year]
        if not official.empty:
            sub = official
    vals = pd.to_numeric(sub[target], errors="coerce").dropna()
    if vals.empty:
        return None
    return float(vals.mean())


def _blend_with_history(
    model_pred: float,
    history: float | None,
    target: str,
) -> float:
    """Blend model output with district history so rates/ranks stay realistic.

    Crime *rates* (e.g. murder rate) are sticky by district — lean harder on history.
    Counts lean more on the model for trend flexibility.
    """
    import math

    if history is None or not math.isfinite(float(history)):
        return max(0.0, model_pred)
    t = target.lower()
    is_rate = "rate" in t or t.endswith("_r")
    # History weight higher for rates so Thoothukudi (high murder rate) stays above Madurai
    w_hist = 0.62 if is_rate else 0.35
    w_model = 1.0 - w_hist
    blended = w_model * float(model_pred) + w_hist * float(history)
    return max(0.0, float(blended))


def predict_for_area(
    target: str,
    area: str,
    data_path: Path = ML_READY_FILE,
    best_models_file: Path = BEST_MODELS_FILE,
    year: int | None = None,
    overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    resolved_target = resolve_target(target)
    df = load_dataset(data_path)
    best_models = load_best_models(best_models_file)
    artifact = load_model_for_target(resolved_target, best_models)

    source_row = resolve_area(df, area, year)
    feature_columns = [str(c) for c in artifact["feature_columns"]]
    prediction_row = apply_overrides(source_row, overrides or {}, feature_columns)
    x = series_to_feature_frame(prediction_row, feature_columns)
    raw_model = artifact["model"] if isinstance(artifact, dict) else artifact
    model_pred = max(predict_with_artifact(raw_model, x), 0.0)

    # Stabilize with official multi-year district baseline (esp. murder rate rankings)
    history = _official_history_baseline(df, str(source_row.get("district_city", area)), resolved_target)
    prediction = _blend_with_history(model_pred, history, resolved_target)

    actual = source_row.get(resolved_target, pd.NA)
    return {
        "area": source_row["district_city"],
        "year": int(source_row["year"]) if year is None else int(year),
        "area_type": source_row["area_type"],
        "target": resolved_target,
        "target_label": artifact.get("target_label", TARGET_CONFIGS[resolved_target]["label"]),
        "model_name": artifact["metrics"]["model_name"],
        "prediction": prediction,
        "model_raw": round(model_pred, 4),
        "history_baseline": None if history is None else round(history, 4),
        "actual": None if pd.isna(actual) else float(actual),
        "overrides": overrides or {},
    }


def compute_risk_index(
    prediction_row: dict,
    sentiment_polarity: float | None = None,
    crime_intensity: float | None = None,
    news_negative_share: float | None = None,
    news_count: float | None = None,
    news_intensity: float | None = None,
    weights: dict[str, float] | None = None,
) -> dict:
    """Compute a blended risk index from predicted crime volume + negative sentiment + public media/news signals.
    Higher = worse (more crime + more negative public feeling + media buzz).
    News signals act as a leading proxy when official data is sparse.

    Weights are configurable via config/risk_weights.json
    """
    if weights is None:
        weights = load_risk_weights()

    pred = max(prediction_row.get("prediction", 0), 0)
    target = prediction_row.get("target", "")

    # Normalize roughly by rough scale (crude but useful for ranking)
    if "rape" in target or "women" in target:
        norm_pred = min(pred / 30.0, 1.0)
    elif "murder" in target:
        norm_pred = min(pred / 100.0, 1.0)
    else:
        norm_pred = min(pred / 100000.0, 1.0)

    sent_component = 0.0
    if sentiment_polarity is not None:
        sent_component = max(0.0, -sentiment_polarity) * 0.5
    if crime_intensity is not None:
        sent_component = max(sent_component, min(crime_intensity / 10.0, 1.0) * 0.4)

    news_component = 0.0
    if news_negative_share is not None:
        news_component = max(news_component, news_negative_share * 0.6)
    if news_count is not None:
        norm_news_count = min(news_count / 25.0, 1.0)
        news_component = max(news_component, norm_news_count * 0.35)
    if news_intensity is not None:
        news_component = max(news_component, min(news_intensity / 10.0, 1.0) * 0.35)

    w_vol = weights.get("volume", 0.5)
    w_sent = weights.get("sentiment", 0.3)
    w_news = weights.get("news", 0.2)

    risk = min(1.0, w_vol * norm_pred + w_sent * sent_component + w_news * news_component)
    risk_label = "HIGH" if risk > 0.7 else ("MEDIUM" if risk > 0.4 else "LOW")

    return {
        **prediction_row,
        "risk_index": round(risk, 3),
        "risk_label": risk_label,
        "sentiment_polarity_used": sentiment_polarity,
        "news_negative_share_used": news_negative_share,
        "news_count_used": news_count,
    }


def predict_many(
    area: str,
    targets: list[str] | None = None,
    data_path: Path = ML_READY_FILE,
    output_file: Path = PREDICTION_OUTPUT_FILE,
    year: int | None = None,
    overrides: dict[str, str] | None = None,
) -> pd.DataFrame:
    selected_targets = targets or list(TARGET_CONFIGS)
    rows = [
        predict_for_area(
            target=target,
            area=area,
            data_path=data_path,
            year=year,
            overrides=overrides,
        )
        for target in selected_targets
    ]

    output_file.parent.mkdir(parents=True, exist_ok=True)
    predictions = pd.DataFrame(rows)

    # Enrich with risk using latest sentiment + news/media signals (hybrid proxy approach)
    try:
        sent_path = Path("model_outputs/sentiment_scores.csv")
        news_path = Path("model_outputs/news_signals.csv")

        sent_latest = None
        if sent_path.exists():
            sent_df = pd.read_csv(sent_path)
            sent_latest = (
                sent_df.sort_values("year")
                .groupby("district_city")
                .tail(1)[["district_city", "polarity", "crime_intensity"]]
                .rename(columns={"polarity": "sentiment_polarity", "crime_intensity": "crime_intensity"})
            )
            predictions = predictions.merge(sent_latest, left_on="area", right_on="district_city", how="left")

        news_latest = None
        if news_path.exists():
            news_df = pd.read_csv(news_path)
            news_latest = (
                news_df.sort_values("year")
                .groupby("district_city")
                .tail(1)[["district_city", "negative_news_share", "news_count", "avg_news_crime_intensity"]]
                .rename(columns={
                    "negative_news_share": "news_negative_share",
                    "news_count": "news_count",
                    "avg_news_crime_intensity": "news_intensity"
                })
            )
            predictions = predictions.merge(news_latest, left_on="area", right_on="district_city", how="left", suffixes=("", "_news"))

        weights = load_risk_weights()
        risk_rows = []
        for _, r in predictions.iterrows():
            risk_rows.append(
                compute_risk_index(
                    r.to_dict(),
                    r.get("sentiment_polarity"),
                    r.get("crime_intensity"),
                    r.get("news_negative_share"),
                    r.get("news_count"),
                    r.get("news_intensity"),
                    weights=weights,
                )
            )
        if risk_rows:
            predictions = pd.DataFrame(risk_rows)
    except Exception:
        pass

    predictions.to_csv(output_file, index=False)
    return predictions


def list_areas(data_path: Path = ML_READY_FILE) -> list[str]:
    df = load_dataset(data_path)
    return df["district_city"].sort_values().to_list()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict crime counts with saved CRIMECAST models.")
    parser.add_argument("--area", default="Chennai", help="Existing district/city to use as the feature template.")
    parser.add_argument(
        "--target",
        nargs="+",
        default=None,
        help="Target(s) to predict. Use complaints, murder, rape, murder_rate, rape_rate, crime_rate, or exact target column names.",
    )
    parser.add_argument("--data-path", type=Path, default=ML_READY_FILE)
    parser.add_argument("--output-file", type=Path, default=PREDICTION_OUTPUT_FILE)
    parser.add_argument("--year", type=int, default=None, help="Template year or target future year (e.g. 2026). Year features will be adjusted for extrapolation.")
    parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=None,
        help="Override one feature with COLUMN=VALUE. Can be used multiple times.",
    )
    parser.add_argument("--list-areas", action="store_true")
    parser.add_argument("--list-targets", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list_targets:
        for key, config in TARGET_CONFIGS.items():
            print(f"{key}: {config['label']}")
        return

    if args.list_areas:
        for area in list_areas(args.data_path):
            print(area)
        return

    targets = [resolve_target(target) for target in args.target] if args.target else None
    predictions = predict_many(
        area=args.area,
        targets=targets,
        data_path=args.data_path,
        output_file=args.output_file,
        year=args.year,
        overrides=parse_overrides(args.overrides),
    )

    cols = ["area", "year", "target_label", "model_name", "prediction", "actual"]
    if "risk_index" in predictions.columns:
        cols = ["area", "year", "target_label", "prediction", "risk_index", "risk_label"]
    print(predictions[cols].to_string(index=False))
    print(f"Saved predictions: {args.output_file}")

    # Helpful note for users doing future forecasts
    if args.year and args.year > 2023:
        print("\n[INFO] Future-year prediction: year features were overridden for extrapolation.")
        print("       For crime *rates*, try --target crime_rate or rape_rate for often more stable results.")


if __name__ == "__main__":
    main()
