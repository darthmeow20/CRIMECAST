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


def compute_risk_index(prediction_row: dict, sentiment_polarity: float | None = None, crime_intensity: float | None = None) -> dict:
    """Compute a blended risk index from predicted crime value + negative sentiment.
    Higher = worse (more crime + more negative public feeling).
    """
    pred = max(prediction_row.get("prediction", 0), 0)
    target = prediction_row.get("target", "")

    # Normalize roughly by rough scale (crude but useful for ranking)
    if "rape" in target or "women" in target:
        norm_pred = min(pred / 30.0, 1.0)   # rough max seen
    elif "murder" in target:
        norm_pred = min(pred / 100.0, 1.0)
    else:
        norm_pred = min(pred / 100000.0, 1.0)

    sent_component = 0.0
    if sentiment_polarity is not None:
        sent_component = max(0.0, -sentiment_polarity) * 0.5   # negative polarity increases risk
    if crime_intensity is not None:
        sent_component = max(sent_component, min(crime_intensity / 10.0, 1.0) * 0.4)

    risk = min(1.0, 0.6 * norm_pred + 0.4 * sent_component)
    risk_label = "HIGH" if risk > 0.7 else ("MEDIUM" if risk > 0.4 else "LOW")

    return {
        **prediction_row,
        "risk_index": round(risk, 3),
        "risk_label": risk_label,
        "sentiment_polarity_used": sentiment_polarity,
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

    # Try to enrich with risk using latest sentiment if available
    try:
        sent_path = Path("model_outputs/sentiment_scores.csv")
        if sent_path.exists():
            sent_df = pd.read_csv(sent_path)
            sent_latest = (
                sent_df.sort_values("year")
                .groupby("district_city")
                .tail(1)[["district_city", "polarity", "crime_intensity"]]
                .rename(columns={"polarity": "sentiment_polarity", "crime_intensity": "crime_intensity"})
            )
            predictions = predictions.merge(sent_latest, left_on="area", right_on="district_city", how="left")
            risk_rows = []
            for _, r in predictions.iterrows():
                risk_rows.append(compute_risk_index(r.to_dict(), r.get("sentiment_polarity"), r.get("crime_intensity")))
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
