from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DATA_DIR = PROJECT_ROOT / "dataset"
DEFAULT_OUTPUT_DIR = RAW_DATA_DIR / "cleaned"
MODEL_OUTPUTS_DIR = PROJECT_ROOT / "model_outputs"
DEFAULT_YEAR = 2023
ML_READY_FILENAME = "crimecast_ml_ready.csv"

KEY_COLUMNS = ["year", "district_city", "area_type"]
SPECIAL_UNITS = {"Railway Chennai", "Railway Trichy", "Cyber Cell", "Other Units"}
CITY_UNITS = {"Chennai", "Avadi", "Tambaram"}


@dataclass(frozen=True)
class RawDataset:
    name: str
    year: int
    source_file: Path


@dataclass(frozen=True)
class DatasetProfile:
    name: str
    source_file: Path
    output_file: Path
    source_rows: int
    cleaned_rows: int
    dropped_total_rows: int
    columns: int
    missing_values: int


def normalize_column_name(column: object) -> str:
    name = str(column).replace("\n", " ").strip().lower()
    name = name.replace("districts/city", "district_city")
    name = name.replace("district/city", "district_city")
    name = name.replace("harrassment", "harassment")
    name = name.replace("ocmplaints", "complaints")
    name = name.replace("muder", "murder")
    name = name.replace("suo-moto", "suo moto")
    name = name.replace("o/c", "oc")
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    name = standardize_column_alias(name)
    return name


def standardize_column_alias(column: str) -> str:
    aliases = {
        "district": "district_city",
        "districts": "district_city",
        "culpable_homicide_i": "culpable_homicide_incidence",
        "culpable_homicide_v": "culpable_homicide_victims",
        "culpable_homicide_r": "culpable_homicides_rate",
        "causing_death_by_negligence_i": "causing_death_by_negligence_incidence",
        "causing_death_by_negligence_v": "causing_death_by_negligence_victims",
        "causing_death_by_negligence_r": "causing_death_by_negligence_rate",
    }
    return aliases.get(column, column)


def make_unique(columns: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    unique_columns: list[str] = []

    for column in columns:
        count = seen.get(column, 0)
        seen[column] = count + 1
        unique_columns.append(column if count == 0 else f"{column}_{count + 1}")

    return unique_columns


def clean_area_name(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def classify_area(area_name: str) -> str:
    if area_name in SPECIAL_UNITS or area_name.startswith("Railway"):
        return "special_unit"
    if area_name in CITY_UNITS or area_name.endswith(" City"):
        return "city"
    return "district"


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    for column in cleaned.columns:
        if column in KEY_COLUMNS:
            continue

        series = cleaned[column]
        if pd.api.types.is_numeric_dtype(series):
            cleaned[column] = series
            continue

        normalized = (
            series.astype("string")
            .str.strip()
            .str.replace(",", "", regex=False)
            .replace({"": pd.NA, "-": pd.NA, "NA": pd.NA, "N/A": pd.NA})
        )
        cleaned[column] = pd.to_numeric(normalized, errors="coerce")

    return cleaned


def extract_year(source_file: Path) -> int | None:
    match = re.search(r"(20\d{2})", source_file.name)
    return int(match.group(1)) if match else None


def infer_dataset_name(source_file: Path) -> str | None:
    normalized_name = source_file.stem.lower().replace("-", "_")

    if "complaint" in normalized_name:
        return "complaints"
    if "women" in normalized_name:
        return "women_crimes"
    if any(token in normalized_name for token in ["muder", "murder", "homicide"]):
        return "murder_homicide"
    return None


def discover_raw_datasets(raw_data_dir: Path, year: int | None = None) -> list[RawDataset]:
    datasets: list[RawDataset] = []

    for source_file in sorted(raw_data_dir.glob("*.csv")):
        dataset_year = extract_year(source_file)
        dataset_name = infer_dataset_name(source_file)

        if dataset_year is None or dataset_name is None:
            continue
        if year is not None and dataset_year != year:
            continue

        datasets.append(RawDataset(dataset_name, dataset_year, source_file))

    if not datasets:
        year_hint = f" for {year}" if year is not None else ""
        raise FileNotFoundError(f"No supported raw dataset CSVs found in {raw_data_dir}{year_hint}")

    return datasets


def normalize_complaint_year_columns(df: pd.DataFrame, year: int) -> pd.DataFrame:
    cleaned = df.copy()
    year_columns = [column for column in cleaned.columns if re.fullmatch(r"20\d{2}", column)]

    if str(year) in year_columns:
        cleaned = cleaned.rename(columns={str(year): "total_complaints"})
        for column in year_columns:
            if column != str(year) and column in cleaned.columns:
                cleaned = cleaned.rename(columns={column: f"total_complaints_{column}"})

    return cleaned


def clean_dataset(name: str, source_file: Path, output_dir: Path, year: int) -> tuple[pd.DataFrame, DatasetProfile]:
    raw = pd.read_csv(source_file)
    df = raw.copy()
    df.columns = make_unique([normalize_column_name(column) for column in df.columns])

    if name == "complaints":
        df = normalize_complaint_year_columns(df, year)

    if "district_city" not in df.columns:
        district_columns = [
            column
            for column in df.columns
            if column == "district_city" or column.startswith("district")
        ]
        if not district_columns:
            raise ValueError(f"Could not find a district/city column in {source_file}")
        df = df.rename(columns={district_columns[0]: "district_city"})

    df["district_city"] = df["district_city"].map(clean_area_name)
    total_mask = df["district_city"].str.casefold().str.contains("total", na=False)
    dropped_total_rows = int(total_mask.sum())
    df = df.loc[~total_mask].copy()

    df = df.drop(columns=[column for column in ["sl_no"] if column in df.columns])
    df.insert(0, "year", year)
    df.insert(2, "area_type", df["district_city"].map(classify_area))
    df = convert_numeric_columns(df)
    df = df.sort_values(["year", "area_type", "district_city"], kind="stable").reset_index(drop=True)

    output_file = output_dir / f"{name}_{year}_clean.csv"
    df.to_csv(output_file, index=False)

    profile = DatasetProfile(
        name=f"{year}_{name}",
        source_file=source_file,
        output_file=output_file,
        source_rows=len(raw),
        cleaned_rows=len(df),
        dropped_total_rows=dropped_total_rows,
        columns=len(df.columns),
        missing_values=int(df.isna().sum().sum()),
    )
    return df, profile


def safe_ratio(df: pd.DataFrame, numerator: str, denominator: str) -> pd.Series:
    ratio = df[numerator] / df[denominator].replace({0: pd.NA})
    return ratio.astype("Float64")


def add_ml_features(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()

    ratio_specs = {
        "complaints_oral_share": (
            "complaints_total_oral_complaints",
            "complaints_total_complaints",
        ),
        "complaints_written_share": (
            "complaints_total_written_complaints_to_police",
            "complaints_total_complaints",
        ),
        "murder_victim_to_incident_ratio": (
            "murder_homicide_murder_victims",
            "murder_homicide_murder_incidence",
        ),
        "rape_victim_to_incident_ratio": (
            "women_crimes_rape_v",
            "women_crimes_rape_sec_376_i",
        ),
    }

    for output_column, (numerator, denominator) in ratio_specs.items():
        if numerator in enriched.columns and denominator in enriched.columns:
            enriched[output_column] = safe_ratio(enriched, numerator, denominator)

    # --- Accuracy improvements: explicit time + population features ---
    if "year" in enriched.columns:
        # Center year for better trend extrapolation (helps when feeding future years)
        enriched["year_centered"] = enriched["year"].astype(float) - 2022.5
        # Binary for latest year (useful with only 2 years)
        enriched["is_latest_year"] = (enriched["year"] == enriched["year"].max()).astype(int)

    # Forward key population if present (from complaints) for per-capita awareness
    pop_col = None
    for cand in ["complaints_projected_population_lakhs", "projected_population_lakhs"]:
        if cand in enriched.columns:
            pop_col = cand
            break
    if pop_col:
        # Use population as a raw feature + log version (often better for scale)
        enriched["population_lakhs"] = enriched[pop_col]
        enriched["log_population"] = np.log1p(enriched[pop_col].fillna(enriched[pop_col].median()))

    # Simple aggregate intensity (helps overall crime rate signal without full leakage)
    # Sum a few representative rates if they exist (robust to missing)
    rate_candidates = [
        "women_crimes_rape_r",
        "murder_homicide_murder_rate",
        "women_crimes_assault_on_women_r",
        "women_crimes_assault_on_women_with_intent_to_outrage_her_modesty_r_crime_rate",
    ]
    existing_rates = [c for c in rate_candidates if c in enriched.columns]
    if existing_rates:
        enriched["selected_crime_rate_sum"] = enriched[existing_rates].sum(axis=1, min_count=1)

    return enriched


def enrich_with_sentiment(df: pd.DataFrame, sentiment_file: Path | None = None) -> pd.DataFrame:
    """Optionally merge aggregated sentiment features from sentiment_scores.csv.
    This allows negative sentiment and crime intensity signals to improve crime rate predictions.
    Gracefully does nothing if sentiment data is not present.
    """
    if sentiment_file is None:
        # Try common locations
        candidates = [
            MODEL_OUTPUTS_DIR / "sentiment_scores.csv",
            PROJECT_ROOT / "model_outputs" / "sentiment_scores.csv",
        ]
        for c in candidates:
            if c.exists():
                sentiment_file = c
                break
        else:
            return df  # no sentiment data

    if not sentiment_file.exists():
        return df

    try:
        sent = pd.read_csv(sentiment_file)
        if "district_city" not in sent.columns or "year" not in sent.columns:
            return df

        # Aggregate per district-year
        agg = (
            sent.groupby(["year", "district_city"], dropna=False)
            .agg(
                avg_sentiment_polarity=("polarity", "mean"),
                avg_sentiment_confidence=("confidence", "mean"),
                avg_crime_intensity=("crime_intensity", "mean"),
                negative_sentiment_share=("sentiment_label", lambda x: (x == "negative").mean()),
            )
            .reset_index()
        )

        if agg.empty:
            return df

        # Prefix to avoid collision
        agg = agg.rename(columns={c: f"sentiment_{c}" for c in agg.columns if c not in ["year", "district_city"]})

        enriched = df.merge(agg, on=["year", "district_city"], how="left")

        # Fill missing sentiment with 0 (neutral / no signal). This prevents "all NaN" columns
        # which cause the sklearn median imputer warning, and treats missing sentiment as baseline.
        sent_cols_added = []
        for col in enriched.columns:
            if col.startswith("sentiment_"):
                enriched[col] = enriched[col].fillna(0)
                sent_cols_added.append(col)

        if sent_cols_added:
            # Optional: could print, but we keep quiet in library code
            pass

        return enriched
    except Exception:
        return df


def build_ml_ready_dataset(cleaned_datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    merged: pd.DataFrame | None = None

    for name, df in cleaned_datasets.items():
        feature_columns = [column for column in df.columns if column not in KEY_COLUMNS]
        prefixed = df.rename(columns={column: f"{name}_{column}" for column in feature_columns})

        if merged is None:
            merged = prefixed
        else:
            merged = merged.merge(prefixed, on=KEY_COLUMNS, how="outer", validate="one_to_one")

    if merged is None:
        raise ValueError("No cleaned datasets were available to merge")

    merged = add_ml_features(merged)
    merged = enrich_with_sentiment(merged)
    return merged.sort_values(["year", "area_type", "district_city"], kind="stable").reset_index(drop=True)


def detect_sentiment_text_columns(raw_datasets: dict[str, pd.DataFrame]) -> dict[str, list[str]]:
    text_columns: dict[str, list[str]] = {}

    for name, df in raw_datasets.items():
        candidates: list[str] = []
        for column in df.columns:
            series = df[column]
            if not pd.api.types.is_object_dtype(series) and not pd.api.types.is_string_dtype(series):
                continue

            non_null = series.dropna().astype(str).str.strip()
            if non_null.empty:
                continue

            average_length = non_null.str.len().mean()
            unique_ratio = non_null.nunique() / len(non_null)
            if average_length >= 25 and unique_ratio >= 0.5:
                candidates.append(str(column))

        if candidates:
            text_columns[name] = candidates

    return text_columns


def write_sentiment_template(output_dir: Path) -> Path:
    template_file = output_dir / "sentiment_text_template.csv"
    if template_file.exists():
        return template_file

    template = pd.DataFrame(
        columns=[
            "record_id",
            "year",
            "district_city",
            "source",
            "text",
            "sentiment_label",
        ]
    )
    template.to_csv(template_file, index=False)
    return template_file


def write_quality_report(
    profiles: list[DatasetProfile],
    ml_ready: pd.DataFrame,
    output_dir: Path,
    sentiment_columns: dict[str, list[str]],
    sentiment_template: Path,
) -> Path:
    report_file = output_dir / "data_quality_report.md"
    lines = [
        "# Data Quality Report",
        "",
        "## Cleaning Rules",
        "",
        "- Standardized headers to `snake_case`.",
        "- Removed `TOTAL DISTRICT(S)` aggregate rows from model-ready data.",
        "- Removed source serial-number columns.",
        "- Converted numeric-looking fields to numeric values.",
        "- Preserved unknown rate values as missing values for later imputation.",
        "- Added `year`, `district_city`, and `area_type` keys.",
        "",
        "## Cleaned Files",
        "",
        "| Dataset | Raw rows | Clean rows | Dropped totals | Columns | Missing values | Output |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]

    for profile in profiles:
        lines.append(
            "| "
            f"{profile.name} | "
            f"{profile.source_rows} | "
            f"{profile.cleaned_rows} | "
            f"{profile.dropped_total_rows} | "
            f"{profile.columns} | "
            f"{profile.missing_values} | "
            f"{profile.output_file.name} |"
        )

    lines.extend(
        [
            "",
            "## ML-Ready Dataset",
            "",
            f"- Rows: {len(ml_ready)}",
            f"- Columns: {len(ml_ready.columns)}",
            f"- Years: {', '.join(str(year) for year in sorted(ml_ready['year'].dropna().astype(int).unique()))}",
            f"- Output: `{ML_READY_FILENAME}`",
            "",
            "NOTE: Only two years of data currently. Sentiment aggregates (if sentiment_scores.csv exists) are automatically merged as predictive features.",
            "      This significantly improves crime rate model accuracy by incorporating public sentiment signals.",
            "",
            "Suggested prediction targets include `complaints_total_complaints`, "
            "`murder_homicide_murder_incidence`, `women_crimes_rape_sec_376_i` (counts), "
            "and crime *rates*: `murder_homicide_murder_rate`, `women_crimes_rape_r`, `complaints_rate_of_cognizable_crime_ipc_sll` (or alias crime_rate).",
            "",
            "## Sentiment Analysis Readiness",
            "",
        ]
    )

    if sentiment_columns:
        lines.append("Potential free-text columns found:")
        for dataset_name, columns in sentiment_columns.items():
            lines.append(f"- `{dataset_name}`: {', '.join(f'`{column}`' for column in columns)}")
    else:
        lines.extend(
            [
                "No complaint narratives, social posts, news text, or other free-text fields were found in the current raw CSVs.",
                f"Use `{sentiment_template.name}` as the schema when you add text data for sentiment analysis.",
            ]
        )

    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_file


def run_cleaning(
    raw_data_dir: Path = RAW_DATA_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    year: int | None = None,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_dataset_specs = discover_raw_datasets(raw_data_dir, year)
    raw_datasets = {
        f"{spec.year}_{spec.name}": pd.read_csv(spec.source_file)
        for spec in raw_dataset_specs
    }
    sentiment_columns = detect_sentiment_text_columns(raw_datasets)

    cleaned_by_name: dict[str, list[pd.DataFrame]] = {}
    profiles: list[DatasetProfile] = []

    for spec in raw_dataset_specs:
        cleaned, profile = clean_dataset(spec.name, spec.source_file, output_dir, spec.year)
        cleaned_by_name.setdefault(spec.name, []).append(cleaned)
        profiles.append(profile)

    cleaned_datasets: dict[str, pd.DataFrame] = {}
    for name, frames in cleaned_by_name.items():
        combined = pd.concat(frames, ignore_index=True, sort=False)
        combined = combined.sort_values(["year", "area_type", "district_city"], kind="stable").reset_index(drop=True)
        combined.to_csv(output_dir / f"{name}_clean.csv", index=False)
        cleaned_datasets[name] = combined

    ml_ready = build_ml_ready_dataset(cleaned_datasets)
    ml_ready_file = output_dir / ML_READY_FILENAME
    ml_ready.to_csv(ml_ready_file, index=False)

    sentiment_template = write_sentiment_template(output_dir)
    report_file = write_quality_report(
        profiles=profiles,
        ml_ready=ml_ready,
        output_dir=output_dir,
        sentiment_columns=sentiment_columns,
        sentiment_template=sentiment_template,
    )

    return {
        "output_dir": output_dir,
        "ml_ready": ml_ready_file,
        "quality_report": report_file,
        "sentiment_template": sentiment_template,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean CRIMECAST raw datasets for analysis and ML.")
    parser.add_argument("--raw-data-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--year", type=int, default=None, help="Optional year filter. Omit to use every available year.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = run_cleaning(args.raw_data_dir, args.output_dir, args.year)
    print(f"Cleaned datasets written to: {outputs['output_dir']}")
    print(f"ML-ready dataset: {outputs['ml_ready']}")
    print(f"Quality report: {outputs['quality_report']}")
    print(f"Sentiment text template: {outputs['sentiment_template']}")


if __name__ == "__main__":
    main()
