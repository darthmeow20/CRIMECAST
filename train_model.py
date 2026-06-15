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

IDENTIFIER_COLUMNS = {"district_city"}
TARGET_CONFIGS = {
    "complaints_total_complaints": {
        "label": "Total complaints",
        "exclude_prefixes": ("complaints_",),
    },
    "murder_homicide_murder_incidence": {
        "label": "Murder incidence",
        "exclude_prefixes": ("murder_homicide_", "murder_"),
    },
    "women_crimes_rape_sec_376_i": {
        "label": "Rape incidents",
        "exclude_prefixes": ("women_crimes_", "rape_"),
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
        ModelSpec("ridge_log", Ridge(alpha=10.0), scale_numeric=True, log_target=True),
        ModelSpec(
            "random_forest_log",
            RandomForestRegressor(
                n_estimators=400,
                min_samples_leaf=2,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
            log_target=True,
        ),
        ModelSpec(
            "gradient_boosting_log",
            GradientBoostingRegressor(
                n_estimators=120,
                learning_rate=0.05,
                max_depth=2,
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

    return features


def build_preprocessor(
    df: pd.DataFrame,
    feature_columns: list[str],
    scale_numeric: bool,
) -> ColumnTransformer:
    numeric_features = [
        column for column in feature_columns if pd.api.types.is_numeric_dtype(df[column])
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


def build_estimator(df: pd.DataFrame, feature_columns: list[str], spec: ModelSpec) -> Any:
    if spec.name == "dummy_median":
        return clone(spec.estimator)

    pipeline = Pipeline(
        [
            ("preprocess", build_preprocessor(df, feature_columns, spec.scale_numeric)),
            ("model", clone(spec.estimator)),
        ]
    )

    if not spec.log_target:
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


def fit_target_model(
    df: pd.DataFrame,
    target: str,
    model_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], pd.DataFrame]:
    config = TARGET_CONFIGS[target]
    feature_columns = select_feature_columns(df, target, config["exclude_prefixes"])
    model_df = df.loc[df[target].notna(), feature_columns + [target]].copy()
    x = model_df[feature_columns]
    y = model_df[target].astype(float)

    if len(y) < 10:
        raise ValueError(f"Need at least 10 rows to train target {target}; found {len(y)}")

    evaluated_rows: list[dict[str, Any]] = []
    holdout_predictions: dict[str, pd.DataFrame] = {}

    for spec in candidate_models():
        estimator = build_estimator(model_df, feature_columns, spec)
        cv_metrics = cross_validate_estimator(estimator, x, y)
        test_metrics, predictions = holdout_evaluate_estimator(estimator, x, y)
        row = {
            "target": target,
            "target_label": config["label"],
            "model_name": spec.name,
            "rows": len(model_df),
            "feature_count": len(feature_columns),
            **cv_metrics,
            **test_metrics,
        }
        evaluated_rows.append(row)
        holdout_predictions[spec.name] = predictions

    best_row = min(evaluated_rows, key=lambda row: row["cv_mae"])
    best_spec = next(spec for spec in candidate_models() if spec.name == best_row["model_name"])
    best_estimator = build_estimator(model_df, feature_columns, best_spec)
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
            "metrics": best_row,
            "trained_at": datetime.now().isoformat(timespec="seconds"),
        },
        model_path,
    )

    best_row["is_best"] = True
    best_row["model_path"] = str(model_path)
    for row in evaluated_rows:
        row.setdefault("is_best", False)
        row.setdefault("model_path", "")

    fitted_predictions = pd.DataFrame(
        {
            "district_city": df.loc[model_df.index, "district_city"].to_numpy(),
            "year": df.loc[model_df.index, "year"].to_numpy(),
            "area_type": df.loc[model_df.index, "area_type"].to_numpy(),
            "target": target,
            "target_label": config["label"],
            "actual": y.to_numpy(),
            "predicted": np.maximum(best_estimator.predict(x), 0.0),
            "model_name": best_spec.name,
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
        f"- Dataset years: {', '.join(str(year) for year in dataset_years)}",
        f"- Models directory: `{model_dir}`",
        f"- Trained targets: {len(best_rows)}",
        "",
        "## Notes",
        "",
        "- Each target excludes its own source family to reduce direct leakage.",
        "- `district_city` is excluded so the model does not simply memorize area names.",
        "- More years make the model more useful, but this is still a prototype until the dataset covers several years consistently.",
        "- Sentiment features were not used because the available CSVs do not contain free-text records yet.",
        "",
        "## Best Models",
        "",
        "| Target | Best model | CV MAE | CV RMSE | CV R2 | Test MAE | Test RMSE | Test R2 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for row in best_rows:
        lines.append(
            "| "
            f"{row['target_label']} | "
            f"{row['model_name']} | "
            f"{row['cv_mae']:.3f} | "
            f"{row['cv_rmse']:.3f} | "
            f"{row['cv_r2']:.3f} | "
            f"{row['test_mae']:.3f} | "
            f"{row['test_rmse']:.3f} | "
            f"{row['test_r2']:.3f} |"
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
) -> dict[str, Path]:
    model_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = ensure_training_data(data_path)
    selected_targets = targets or list(TARGET_CONFIGS)

    missing_targets = [target for target in selected_targets if target not in df.columns]
    if missing_targets:
        raise ValueError(f"Targets not found in dataset: {', '.join(missing_targets)}")

    metrics_rows: list[dict[str, Any]] = []
    best_rows: list[dict[str, Any]] = []
    prediction_frames: list[pd.DataFrame] = []

    for target in selected_targets:
        target_rows, best_row, predictions = fit_target_model(df, target, model_dir)
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
    best_models_file.write_text(json.dumps(best_rows, indent=2), encoding="utf-8")
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = train_models(
        data_path=args.data_path,
        model_dir=args.model_dir,
        output_dir=args.output_dir,
        targets=args.targets,
    )
    print(f"Training metrics: {outputs['metrics']}")
    print(f"Fitted predictions: {outputs['predictions']}")
    print(f"Best model metadata: {outputs['best_models']}")
    print(f"Training report: {outputs['report']}")
    print(f"Saved models: {outputs['model_dir']}")


if __name__ == "__main__":
    main()
