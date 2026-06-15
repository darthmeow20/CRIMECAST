from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from train_model import ML_READY_FILE, MODEL_DIR, OUTPUT_DIR, TARGET_CONFIGS, train_models


BEST_MODELS_FILE = OUTPUT_DIR / "best_models.json"
PREDICTION_OUTPUT_FILE = OUTPUT_DIR / "crime_predictions.csv"

TARGET_ALIASES = {
    "complaints": "complaints_total_complaints",
    "total_complaints": "complaints_total_complaints",
    "murder": "murder_homicide_murder_incidence",
    "murder_incidence": "murder_homicide_murder_incidence",
    "rape": "women_crimes_rape_sec_376_i",
    "rape_incidents": "women_crimes_rape_sec_376_i",
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
            raise ValueError(f"Area '{area}' was found, but not for year {year}")
    else:
        matches = matches[matches["year"] == matches["year"].max()]

    return matches.sort_values("year").iloc[-1].copy()


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
    feature_columns = artifact["feature_columns"]
    prediction_row = apply_overrides(source_row, overrides or {}, feature_columns)
    x = pd.DataFrame([prediction_row[feature_columns]], columns=feature_columns)
    prediction = max(float(artifact["model"].predict(x)[0]), 0.0)

    actual = source_row.get(resolved_target, pd.NA)
    return {
        "area": source_row["district_city"],
        "year": int(source_row["year"]),
        "area_type": source_row["area_type"],
        "target": resolved_target,
        "target_label": artifact.get("target_label", TARGET_CONFIGS[resolved_target]["label"]),
        "model_name": artifact["metrics"]["model_name"],
        "prediction": prediction,
        "actual": None if pd.isna(actual) else float(actual),
        "overrides": overrides or {},
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
        help="Target(s) to predict. Use complaints, murder, rape, or exact target column names.",
    )
    parser.add_argument("--data-path", type=Path, default=ML_READY_FILE)
    parser.add_argument("--output-file", type=Path, default=PREDICTION_OUTPUT_FILE)
    parser.add_argument("--year", type=int, default=None, help="Prediction template year. Defaults to latest available.")
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

    print(predictions[["area", "year", "target_label", "model_name", "prediction", "actual"]].to_string(index=False))
    print(f"Saved predictions: {args.output_file}")


if __name__ == "__main__":
    main()
