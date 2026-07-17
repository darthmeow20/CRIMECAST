from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from clean_data import DEFAULT_OUTPUT_DIR, ML_READY_FILENAME, run_cleaning


PROJECT_ROOT = Path(__file__).resolve().parent
ML_READY_FILE = DEFAULT_OUTPUT_DIR / ML_READY_FILENAME
MODEL_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "model_outputs"
RANDOM_STATE = 42

# Legacy fallback if is_official_year column missing.
# Prefer is_official_year==1 (SCRB/NCRB can include pre-2022 and 2025–2026).
OFFICIAL_LABEL_MAX_YEAR = 2023

IDENTIFIER_COLUMNS = {
    "district_city",
    "is_media_proxy_year",
    "is_official_year",
    "data_source",
}
TARGET_CONFIGS = {
    "complaints_total_complaints": {
        "label": "Total complaints",
        "exclude_prefixes": ("complaints_",),
        "log_target": True,
    },
    "murder_homicide_murder_incidence": {
        "label": "Murder incidence",
        "exclude_prefixes": ("murder_homicide_", "murder_"),
        "log_target": True,
    },
    "women_crimes_rape_sec_376_i": {
        "label": "Rape incidents",
        "exclude_prefixes": ("women_crimes_", "rape_"),
        "log_target": True,
    },
    # Crime *rate* targets (normalized per population / lakh) — rates often benefit from log too but we keep option
    "murder_homicide_murder_rate": {
        "label": "Murder rate",
        "exclude_prefixes": ("murder_homicide_", "murder_"),
        "log_target": True,
    },
    "women_crimes_rape_r": {
        "label": "Rape rate",
        "exclude_prefixes": ("women_crimes_", "rape_"),
        "log_target": True,
    },
    "complaints_rate_of_cognizable_crime_ipc_sll": {
        "label": "Cognizable crime rate (IPC+SLL)",
        "exclude_prefixes": ("complaints_",),
        "log_target": True,
    },
}


@dataclass(frozen=True)
class ModelSpec:
    name: str
    estimator: Any
    scale_numeric: bool = False
    log_target: bool = False


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def candidate_models() -> list[ModelSpec]:
    return [
        ModelSpec("dummy_median", DummyRegressor(strategy="median")),
        ModelSpec("ridge_log", Ridge(alpha=5.0), scale_numeric=True, log_target=True),
        ModelSpec(
            "random_forest_log",
            RandomForestRegressor(
                n_estimators=300,
                min_samples_leaf=3,   # slightly more conservative for small data
                max_depth=6,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
            log_target=True,
        ),
        ModelSpec(
            "gradient_boosting_log",
            GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.04,
                max_depth=3,
                subsample=0.8,
                random_state=RANDOM_STATE,
            ),
            log_target=True,
        ),
    ]


def ensure_training_data(data_path: Path) -> pd.DataFrame:
    if not data_path.exists():
        run_cleaning()

    if not data_path.exists():
        raise FileNotFoundError(f"Could not find ML-ready dataset at {data_path}")

    return pd.read_csv(data_path)


def select_feature_columns(df: pd.DataFrame, target: str, exclude_prefixes: tuple[str, ...]) -> list[str]:
    features: list[str] = []

    for column in df.columns:
        if column == target or column in IDENTIFIER_COLUMNS:
            continue
        if any(column.startswith(prefix) for prefix in exclude_prefixes):
            continue
        features.append(column)

    # Keep useful engineered time features even if they look generic
    time_features = {"year", "year_centered", "is_latest_year"}
    features = sorted(set(features) | (time_features & set(df.columns)))

    return features


def prune_correlated_features(df: pd.DataFrame, feature_columns: list[str], threshold: float = 0.95) -> list[str]:
    """Remove one of highly correlated numeric feature pairs to reduce multicollinearity."""
    if len(feature_columns) < 2:
        return feature_columns

    num_df = df[feature_columns].select_dtypes(include=[np.number]).copy()
    if num_df.shape[1] < 2:
        return feature_columns

    corr = num_df.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))

    to_drop = set()
    for column in upper.columns:
        if column in to_drop:
            continue
        high_corr = upper[column][upper[column] > threshold].index.tolist()
        for other in high_corr:
            if other not in to_drop:
                # Prefer keeping time/population features
                if "year" in other or "pop" in other.lower() or "rate" in other.lower():
                    to_drop.add(column)
                else:
                    to_drop.add(other)

    kept = [f for f in feature_columns if f not in to_drop]
    return kept if len(kept) >= 3 else feature_columns  # don't prune too aggressively


def build_preprocessor(
    df: pd.DataFrame,
    feature_columns: list[str],
    scale_numeric: bool,
) -> ColumnTransformer:
    numeric_features = [
        column for column in feature_columns 
        if pd.api.types.is_numeric_dtype(df[column]) and df[column].notna().any()
    ]
    categorical_features = [
        column for column in feature_columns if column not in numeric_features
    ]

    transformers: list[tuple[str, Pipeline, list[str]]] = []

    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))

    if numeric_features:
        transformers.append(("numeric", Pipeline(numeric_steps), numeric_features))

    if categorical_features:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                    ]
                ),
                categorical_features,
            )
        )

    return ColumnTransformer(transformers=transformers, remainder="drop", sparse_threshold=0)


def build_estimator(df: pd.DataFrame, feature_columns: list[str], spec: ModelSpec, target_config: dict | None = None) -> Any:
    if spec.name == "dummy_median":
        return clone(spec.estimator)

    use_log = spec.log_target
    if target_config and "log_target" in target_config:
        use_log = target_config.get("log_target", use_log)

    pipeline = Pipeline(
        [
            ("preprocess", build_preprocessor(df, feature_columns, spec.scale_numeric)),
            ("model", clone(spec.estimator)),
        ]
    )

    if not use_log:
        return pipeline

    return TransformedTargetRegressor(
        regressor=pipeline,
        func=np.log1p,
        inverse_func=np.expm1,
        check_inverse=False,
    )


def regression_metrics(y_true: pd.Series, predictions: np.ndarray) -> dict[str, float]:
    clipped_predictions = np.maximum(np.asarray(predictions, dtype=float), 0.0)
    return {
        "mae": float(mean_absolute_error(y_true, clipped_predictions)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, clipped_predictions))),
        "r2": float(r2_score(y_true, clipped_predictions)),
    }


def cross_validate_estimator(estimator: Any, x: pd.DataFrame, y: pd.Series) -> dict[str, float]:
    folds = min(5, len(y))
    cv = KFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    predictions = np.zeros(len(y), dtype=float)

    for train_index, valid_index in cv.split(x):
        fold_model = clone(estimator)
        fold_model.fit(x.iloc[train_index], y.iloc[train_index])
        predictions[valid_index] = fold_model.predict(x.iloc[valid_index])

    metrics = regression_metrics(y, predictions)
    return {f"cv_{name}": value for name, value in metrics.items()}


def holdout_evaluate_estimator(
    estimator: Any,
    x: pd.DataFrame,
    y: pd.Series,
) -> tuple[dict[str, float], pd.DataFrame]:
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        shuffle=True,
    )

    holdout_model = clone(estimator)
    holdout_model.fit(x_train, y_train)
    predictions = np.maximum(holdout_model.predict(x_test), 0.0)
    metrics = regression_metrics(y_test, predictions)

    prediction_frame = pd.DataFrame(
        {
            "row_index": x_test.index,
            "actual": y_test.to_numpy(),
            "predicted": predictions,
        }
    ).sort_values("row_index")

    return {f"test_{name}": value for name, value in metrics.items()}, prediction_frame


def temporal_evaluate_estimator(
    estimator: Any,
    x: pd.DataFrame,
    y: pd.Series,
    years: pd.Series,
) -> tuple[dict[str, float], pd.DataFrame | None]:
    """Strict temporal validation: train on earlier year(s), test on latest year.
    This gives a much more realistic estimate of forecasting reliability.
    """
    # Defensive: ensure we have a 1D Series (in case of accidental duplicate column selection upstream)
    if isinstance(years, pd.DataFrame):
        years = years.iloc[:, 0]
    years = pd.Series(years)
    # Ensure 'years' is always a proper 1-D Series (defensive against duplicate column selection)
    if isinstance(years, pd.DataFrame):
        years = years.iloc[:, 0] if years.shape[1] > 0 else pd.Series([np.nan] * len(years), index=years.index)
    years = pd.Series(years)

    unique_years = sorted(years.dropna().unique())
    if len(unique_years) < 2:
        return {}, None

    train_mask = years < unique_years[-1]
    test_mask = years == unique_years[-1]

    if train_mask.sum() < 5 or test_mask.sum() < 3:
        return {}, None

    x_train, y_train = x[train_mask], y[train_mask]
    x_test, y_test = x[test_mask], y[test_mask]

    temp_model = clone(estimator)
    temp_model.fit(x_train, y_train)
    predictions = np.maximum(temp_model.predict(x_test), 0.0)
    metrics = regression_metrics(y_test, predictions)

    prediction_frame = pd.DataFrame(
        {
            "year": years[test_mask].to_numpy(),
            "actual": y_test.to_numpy(),
            "predicted": predictions,
        }
    )

    return {f"temporal_{name}": value for name, value in metrics.items()}, prediction_frame


def filter_official_label_rows(
    df: pd.DataFrame,
    target: str,
    *,
    official_max_year: int = OFFICIAL_LABEL_MAX_YEAR,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Keep only official-era rows as supervised training examples.

    Prefer is_official_year==1 (SCRB/NCRB including pre-2022 and 2025–2026).
    Media-proxy rows stay in ml_ready for templates/news but never supervise y.
    """
    meta: dict[str, Any] = {
        "official_max_year": official_max_year,
        "used_official_filter": False,
        "rows_before": 0,
        "rows_after": 0,
        "years_used": [],
        "filter_mode": "none",
    }
    base = df.loc[df[target].notna()].copy()
    meta["rows_before"] = int(len(base))

    if base.empty:
        return base, meta

    if "is_official_year" in base.columns and base["is_official_year"].astype(bool).any():
        official = base.loc[base["is_official_year"].astype(bool)]
        meta["filter_mode"] = "is_official_year"
        meta["used_official_filter"] = True
    elif "data_source" in base.columns:
        src = base["data_source"].fillna("").astype(str).str.lower()
        official_tags = {"scrb", "ncrb", "scrb_ncrb", "official", "tn_police_table", "tn_scrb"}
        official = base.loc[src.isin(official_tags)]
        if official.empty and "year" in base.columns:
            years = pd.to_numeric(base["year"], errors="coerce")
            official = base.loc[years <= float(official_max_year)]
            meta["filter_mode"] = "legacy_year_cap"
        else:
            meta["filter_mode"] = "data_source"
        meta["used_official_filter"] = True
    elif "is_media_proxy_year" in base.columns:
        official = base.loc[~base["is_media_proxy_year"].astype(bool)]
        meta["filter_mode"] = "not_media_proxy"
        meta["used_official_filter"] = True
    elif "year" in base.columns:
        years = pd.to_numeric(base["year"], errors="coerce")
        official = base.loc[years <= float(official_max_year)]
        meta["filter_mode"] = "legacy_year_cap"
        meta["used_official_filter"] = True
    else:
        official = base

    meta["rows_after"] = int(len(official))
    if "year" in official.columns and not official.empty:
        meta["years_used"] = sorted(
            pd.to_numeric(official["year"], errors="coerce").dropna().astype(int).unique().tolist()
        )

    # Safety: if filter is too aggressive, fall back with a clear warning
    if len(official) < 10:
        print(
            f"[WARN] Official-year filter left {len(official)} rows for {target} "
            f"(need ≥10). Falling back to all non-null target rows. "
            f"Check dataset years ≤ {official_max_year}."
        )
        if "year" in base.columns:
            meta["years_used"] = sorted(
                pd.to_numeric(base["year"], errors="coerce").dropna().astype(int).unique().tolist()
            )
        meta["rows_after"] = int(len(base))
        meta["used_official_filter"] = False
        meta["fallback"] = True
        return base, meta

    meta["used_official_filter"] = True
    meta["fallback"] = False
    print(
        f"[INFO] {target}: training labels from official years only "
        f"{meta['years_used']} ({meta['rows_after']} rows; "
        f"excluded {meta['rows_before'] - meta['rows_after']} media-proxy rows)"
    )
    return official, meta


def fit_target_model(
    df: pd.DataFrame,
    target: str,
    model_dir: Path,
    *,
    official_max_year: int = OFFICIAL_LABEL_MAX_YEAR,
) -> tuple[list[dict[str, Any]], dict[str, Any], pd.DataFrame]:
    config = TARGET_CONFIGS[target]

    # Labels: official years only (≤ official_max_year by default)
    train_source, label_meta = filter_official_label_rows(
        df, target, official_max_year=official_max_year
    )

    feature_columns = select_feature_columns(train_source, target, config["exclude_prefixes"])
    # Drop label-meta columns if they slipped into features
    feature_columns = [
        c for c in feature_columns
        if c not in ("is_media_proxy_year", "is_official_year")
    ]

    # Prune on official training rows only
    feature_columns = prune_correlated_features(train_source, feature_columns)

    cols = feature_columns + [target]
    if "year" in train_source.columns and "year" not in cols:
        cols = cols + ["year"]
    # Keep identifiers for fitted_predictions export
    for id_col in ("district_city", "area_type"):
        if id_col in train_source.columns and id_col not in cols:
            cols = cols + [id_col]

    model_df = train_source.loc[:, [c for c in cols if c in train_source.columns]].copy()
    x = model_df[feature_columns]
    y = model_df[target].astype(float)
    years_series = model_df["year"] if "year" in model_df.columns else pd.Series([2022] * len(y))

    if len(y) < 10:
        raise ValueError(f"Need at least 10 rows to train target {target}; found {len(y)}")

    evaluated_rows: list[dict[str, Any]] = []

    for spec in candidate_models():
        estimator = build_estimator(model_df, feature_columns, spec, config)
        cv_metrics = cross_validate_estimator(estimator, x, y)
        test_metrics, _ = holdout_evaluate_estimator(estimator, x, y)
        temporal_metrics, _ = temporal_evaluate_estimator(estimator, x, y, years_series)

        row = {
            "target": target,
            "target_label": config["label"],
            "model_name": spec.name,
            "rows": len(model_df),
            "feature_count": len(feature_columns),
            "official_label_max_year": official_max_year,
            "training_years": ",".join(str(y) for y in label_meta.get("years_used", [])),
            "official_filter": label_meta.get("used_official_filter", False),
            **cv_metrics,
            **test_metrics,
            **temporal_metrics,
        }
        evaluated_rows.append(row)

    best_row = min(evaluated_rows, key=lambda row: row.get("temporal_mae", row["cv_mae"]))
    best_spec = next(spec for spec in candidate_models() if spec.name == best_row["model_name"])
    best_estimator = build_estimator(model_df, feature_columns, best_spec, config)
    best_estimator.fit(x, y)

    for stale_model in model_dir.glob(f"{slugify(target)}_*.joblib"):
        stale_model.unlink()

    model_path = model_dir / f"{slugify(target)}_{best_spec.name}.joblib"
    joblib.dump(
        {
            "model": best_estimator,
            "target": target,
            "target_label": config["label"],
            "feature_columns": feature_columns,
            "training_rows": len(model_df),
            "official_label_max_year": official_max_year,
            "training_years": label_meta.get("years_used", []),
            "metrics": best_row,
            "trained_at": datetime.now().isoformat(timespec="seconds"),
        },
        model_path,
    )

    best_row["is_best"] = True
    best_row["model_path"] = str(model_path)
    best_row["official_label_max_year"] = official_max_year
    best_row["training_years"] = label_meta.get("years_used", [])
    for row in evaluated_rows:
        row.setdefault("is_best", False)
        row.setdefault("model_path", "")

    fitted_predictions = pd.DataFrame(
        {
            "district_city": model_df["district_city"].to_numpy()
            if "district_city" in model_df.columns
            else np.array([""] * len(y)),
            "year": model_df["year"].to_numpy() if "year" in model_df.columns else np.array([np.nan] * len(y)),
            "area_type": model_df["area_type"].to_numpy()
            if "area_type" in model_df.columns
            else np.array([""] * len(y)),
            "target": target,
            "target_label": config["label"],
            "actual": y.to_numpy(),
            "predicted": np.maximum(best_estimator.predict(x), 0.0),
            "model_name": best_spec.name,
            "label_source": "official",
        }
    )

    return evaluated_rows, best_row, fitted_predictions


def write_training_report(
    metrics: pd.DataFrame,
    best_rows: list[dict[str, Any]],
    output_dir: Path,
    model_dir: Path,
    data_path: Path,
    dataset_rows: int,
    dataset_years: list[int],
) -> Path:
    report_file = output_dir / "training_report.md"
    lines = [
        "# Model Training Report",
        "",
        f"- Dataset: `{data_path}`",
        f"- Dataset rows: {dataset_rows}",
        f"- Dataset years (full table): {', '.join(str(year) for year in dataset_years)}",
        f"- **Training labels**: `is_official_year==1` (SCRB/NCRB any year, incl. pre-2022 & 2025–2026) "
        f"— media-proxy excluded; legacy cap if no flags: ≤ {OFFICIAL_LABEL_MAX_YEAR}",
        f"- Models directory: `{model_dir}`",
        f"- Trained targets: {len(best_rows)}",
        "",
        "RELIABILITY NOTE: Best model is chosen primarily by 'temporal_mae' (train on past year(s), test on most recent *official* year).",
        "This is a much stricter and more honest measure of how well the model would perform on future/unseen years.",
        "",
        "## Official vs media-proxy years",
        "",
        f"- **Official labels** (used for y): year ≤ {OFFICIAL_LABEL_MAX_YEAR} (real TN crime tables).",
        f"- **Media-proxy years** (2024+): may exist in `ml_ready` for maps/news features/templates, but are **not** used as training targets.",
        "- News/sentiment columns remain available as **features** when present on official-year rows.",
        "- Prediction still blends model output with district official history for rate ranking (see `predict.py`).",
        "",
        "## Notes",
        "",
        "- **Temporal evaluation** (train earlier year, test latest official year) is primary for realistic accuracy.",
        "- Each target excludes its own source family to reduce direct leakage.",
        "- `district_city` is excluded so the model does not simply memorize area names.",
        "- Highly correlated features are pruned (corr > 0.95) for more stable models.",
        "- `year` / `year_centered` / `is_latest_year`, population, and **sentiment features** are used when available.",
        "- More official years of data will still give the biggest gains.",
        "- Rate targets (e.g. murder_rate, rape_rate) + risk_index give the most reliable view.",
        "",
        "## Best Models",
        "",
        "| Target | Best model | Train years | Rows | CV MAE | Temporal MAE | Temporal R2 | Notes |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]

    for row in best_rows:
        temporal_mae = row.get("temporal_mae", float("nan"))
        temporal_r2 = row.get("temporal_r2", float("nan"))
        ty = row.get("training_years", [])
        if isinstance(ty, list):
            ty_s = ",".join(str(x) for x in ty)
        else:
            ty_s = str(ty)
        note = "official labels only"
        if not row.get("official_filter", True):
            note = "fallback: all years (too few official rows)"
        elif not np.isnan(temporal_mae):
            note = "official + temporal holdout"
        lines.append(
            "| "
            f"{row['target_label']} | "
            f"{row['model_name']} | "
            f"{ty_s} | "
            f"{row.get('rows', '')} | "
            f"{row['cv_mae']:.3f} | "
            f"{temporal_mae:.3f} | "
            f"{temporal_r2:.3f} | "
            f"{note} |"
        )

    lines.extend(
        [
            "",
            "## All Candidate Metrics",
            "",
            "Full metrics are saved in `training_metrics.csv`.",
        ]
    )

    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    metrics.to_csv(output_dir / "training_metrics.csv", index=False)
    return report_file


def train_models(
    data_path: Path = ML_READY_FILE,
    model_dir: Path = MODEL_DIR,
    output_dir: Path = OUTPUT_DIR,
    targets: list[str] | None = None,
    *,
    official_max_year: int = OFFICIAL_LABEL_MAX_YEAR,
) -> dict[str, Path]:
    model_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = ensure_training_data(data_path)
    selected_targets = targets or list(TARGET_CONFIGS)

    missing_targets = [target for target in selected_targets if target not in df.columns]
    if missing_targets:
        raise ValueError(f"Targets not found in dataset: {', '.join(missing_targets)}")

    print(
        f"[INFO] Training with official labels only (year ≤ {official_max_year}). "
        "Media-proxy years are excluded as supervision targets."
    )

    metrics_rows: list[dict[str, Any]] = []
    best_rows: list[dict[str, Any]] = []
    prediction_frames: list[pd.DataFrame] = []

    for target in selected_targets:
        target_rows, best_row, predictions = fit_target_model(
            df, target, model_dir, official_max_year=official_max_year
        )
        metrics_rows.extend(target_rows)
        best_rows.append(best_row)
        prediction_frames.append(predictions)

    metrics = pd.DataFrame(metrics_rows).sort_values(["target", "cv_mae"])
    predictions = pd.concat(prediction_frames, ignore_index=True)

    metrics_file = output_dir / "training_metrics.csv"
    predictions_file = output_dir / "fitted_predictions.csv"
    best_models_file = output_dir / "best_models.json"

    metrics.to_csv(metrics_file, index=False)
    predictions.to_csv(predictions_file, index=False)
    # JSON-serializable best rows
    best_for_json = []
    for row in best_rows:
        r = dict(row)
        # ensure lists are JSON-safe
        if isinstance(r.get("training_years"), np.ndarray):
            r["training_years"] = r["training_years"].tolist()
        best_for_json.append(r)
    best_models_file.write_text(json.dumps(best_for_json, indent=2, default=str), encoding="utf-8")
    dataset_years = sorted(df["year"].dropna().astype(int).unique().tolist())
    report_file = write_training_report(
        metrics,
        best_rows,
        output_dir,
        model_dir,
        data_path,
        dataset_rows=len(df),
        dataset_years=dataset_years,
    )

    return {
        "metrics": metrics_file,
        "predictions": predictions_file,
        "best_models": best_models_file,
        "report": report_file,
        "model_dir": model_dir,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train CRIMECAST prototype crime prediction models.")
    parser.add_argument("--data-path", type=Path, default=ML_READY_FILE)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--targets", nargs="+", choices=sorted(TARGET_CONFIGS), default=None)
    parser.add_argument(
        "--official-max-year",
        type=int,
        default=OFFICIAL_LABEL_MAX_YEAR,
        help=f"Only years ≤ this value are used as training labels (default {OFFICIAL_LABEL_MAX_YEAR}). "
        "Media-proxy years remain in the table for prediction templates.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = train_models(
        data_path=args.data_path,
        model_dir=args.model_dir,
        output_dir=args.output_dir,
        targets=args.targets,
        official_max_year=args.official_max_year,
    )
    print(f"Training metrics: {outputs['metrics']}")
    print(f"Fitted predictions: {outputs['predictions']}")
    print(f"Best model metadata: {outputs['best_models']}")
    print(f"Training report: {outputs['report']}")
    print(f"Saved models: {outputs['model_dir']}")


if __name__ == "__main__":
    main()
