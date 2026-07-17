"""
Acquire & normalize SCRB / NCRB-class official crime tables for CRIMECAST.

- Pre-2022: downloads public OpenCity Tamil Nadu tables (2019–2021 IPC, murder, women, complaints).
- 2025 / 2026: prefer SCRB/NCRB drop-ins over media-proxy fills.
- Writes project-shaped CSVs under dataset/ and tags data_source=scrb_ncrb.

Usage:
  python acquire_scrb_ncrb.py              # download + convert + stage
  python acquire_scrb_ncrb.py --apply      # also copy into dataset/ for clean_data
  python acquire_scrb_ncrb.py --apply --rebuild-ml   # clean_data after apply

Drop-in (your SCRB/NCRB extracts for any year including 2025–2026):
  dataset/scrb_ncrb/dropin/tn_2025_complaints.csv
  dataset/scrb_ncrb/dropin/tn_2025_muder_homicide.csv
  dataset/scrb_ncrb/dropin/tn_2025_crimes_against_women.csv
  (same pattern for 2026, 2018, …)

Sources (public):
  https://data.opencity.in/dataset/tamil-nadu-crime-data
  NCRB Crime in India (manual drop-in when published)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import urllib.request
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
DATASET = PROJECT_ROOT / "dataset"
SCRB_ROOT = DATASET / "scrb_ncrb"
RAW_DIR = SCRB_ROOT / "raw"
STAGED_DIR = SCRB_ROOT / "staged"
DROPIN_DIR = SCRB_ROOT / "dropin"
POLICY_PATH = PROJECT_ROOT / "config" / "official_data_policy.json"

# OpenCity / Greater Chennai Police published TN district tables (SCRB-class)
OPENCITY_URLS = {
    "ipc_2019_2021.csv": (
        "https://data.opencity.in/dataset/1ae54d8f-6cbd-4cda-9021-d46314f2b17c/"
        "resource/2a6b9737-9ddb-4393-a3f5-db9a770014ff/download/"
        "8e47b896-53f4-4e9e-bda7-f23b7dbe23f2.csv"
    ),
    "deaths_crime_negligence.csv": (
        "https://data.opencity.in/dataset/1ae54d8f-6cbd-4cda-9021-d46314f2b17c/"
        "resource/4e55bc7c-7d4c-4241-a854-8df6458beda0/download/"
        "9e487b59-d50e-462f-b0c9-bfe7fde85ff3.csv"
    ),
    "complaints_2021.csv": (
        "https://data.opencity.in/dataset/1ae54d8f-6cbd-4cda-9021-d46314f2b17c/"
        "resource/742ba1d4-7e33-48f6-b417-f8bbc24ea33f/download/"
        "7c1dfb74-70a9-45a3-939b-1f5bf949c10a.csv"
    ),
    "women_crimes_2021.csv": (
        "https://data.opencity.in/dataset/1ae54d8f-6cbd-4cda-9021-d46314f2b17c/"
        "resource/d33de71f-2a48-4a39-8de1-d54717515737/download/"
        "f3a241ff-63be-41e7-9110-7d4475214bb1.csv"
    ),
}

SOURCE_TAG = "scrb_ncrb"


def load_policy() -> dict[str, Any]:
    if POLICY_PATH.exists():
        return json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    return {
        "sources_official": ["scrb", "ncrb", "scrb_ncrb", "official"],
        "prefer_scrb_dropin_over_media": True,
    }


def download_raw(force: bool = False) -> list[Path]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    got: list[Path] = []
    for name, url in OPENCITY_URLS.items():
        dest = RAW_DIR / name
        if dest.exists() and dest.stat().st_size > 100 and not force:
            print(f"[OK] cached {dest.name}")
            got.append(dest)
            continue
        print(f"[GET] {name} …")
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "CRIMECAST-scrb/1.0 (research)"}
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                dest.write_bytes(resp.read())
            print(f"  → {dest} ({dest.stat().st_size} bytes)")
            got.append(dest)
        except Exception as e:
            print(f"  [WARN] download failed: {e}")
            if dest.exists():
                got.append(dest)
    return got


def _clean_district(s: object) -> str:
    t = re.sub(r"\s+", " ", str(s or "").strip())
    t = t.replace("Coimbatore  City", "Coimbatore City")
    t = t.replace("CyberCell", "Cyber Cell")
    return t


def _drop_totals(df: pd.DataFrame, district_col: str) -> pd.DataFrame:
    d = df.copy()
    d[district_col] = d[district_col].map(_clean_district)
    mask = ~d[district_col].astype(str).str.upper().isin(
        {"TOTAL", "TOTAL DISTRICT(S)", "TOTAL DISTRICTS", "NAN", ""}
    )
    return d.loc[mask].reset_index(drop=True)


def _to_num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str).str.replace(",", "").str.replace("—", "").str.replace("-", "nan"),
        errors="coerce",
    )


def convert_ipc_years(path: Path) -> dict[int, pd.DataFrame]:
    """IPC cognizable counts 2019–2021 → complaints-shaped frames per year."""
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    dcol = "District" if "District" in df.columns else df.columns[1]
    df = _drop_totals(df, dcol)
    out: dict[int, pd.DataFrame] = {}
    for year in (2019, 2020, 2021):
        ycol = str(year)
        if ycol not in df.columns:
            continue
        rows = pd.DataFrame({
            "Sl No": range(1, len(df) + 1),
            "District/City": df[dcol].map(_clean_district),
            "Total Complaints": _to_num(df[ycol]),
            str(year): _to_num(df[ycol]),
        })
        if "Rate of cognizable crime IPC (2021)" in df.columns and year == 2021:
            rows["Rate of Cognizable Crime IPC+SLL"] = _to_num(
                df["Rate of cognizable crime IPC (2021)"]
            )
        if "Mid-year projected population (2021) (lakhs)" in df.columns and year == 2021:
            rows["Projected Population (lakhs)"] = _to_num(
                df["Mid-year projected population (2021) (lakhs)"]
            )
        rows["data_source"] = SOURCE_TAG
        out[year] = rows
    return out


def convert_complaints_2021(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    dcol = "District" if "District" in df.columns else df.columns[1]
    df = _drop_totals(df, dcol)
    # Map toward project tn_2023_complaints style
    rename = {
        dcol: "District/City",
        "Total Oral Complaints": "Total Oral Complaints",
        "Narrated to (O/C)/SHO": "Oral - Narrated to O/C /SHO",
        "Dial 100 - Distress Call": "Oral -Distress Call over phone/dial 100",
        "Total Written Complaints to Police": "Total written complaints to police",
        "To O/C /SHO": "Written - To O/C /SHO",
        "To SP/Senior Officers": "Written - To SP/Senior officers",
        "Electronic Form": "Written - Electronic form",
        "Written Complaints to Courts": "Written Complaint to courts",
        "Written - NHRC/SHRC": "Written - NHRC and SHRC",
        "Written - SCs Commission": "Written - SCs commissions",
        "Written - STs Commissions": "Written - STs commissions",
        "Written - National / State Commission of Women": "Written - NCW/SCW",
        "Written - Children Welfare Boards/Commissions": "Written - Child welfare boards/commissions",
        "Suo-Moto from Police": "Suo-moto police ocmplaints",
        "Other Written Complaints": "Other Written Complaints",
        "Total Complaints": "Total Complaints",
    }
    out = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    out["District/City"] = out["District/City"].map(_clean_district)
    out.insert(0, "Sl No", range(1, len(out) + 1))
    out["data_source"] = SOURCE_TAG
    return out


def convert_murder(path: Path, year: int = 2021) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    dcol = "District" if "District" in df.columns else df.columns[1]
    df = _drop_totals(df, dcol)
    explicit = {
        "District": "Districts/City",
        "Murder - Incidence (I)": "Murder - Incidence",
        "Murder -Victims (V)": "Murder - Victims",
        "Murder - Rate ( R )": "Murder - Rate",
        "Culpable Homicide Not Murder - I": "Culpable homicide - Incidence",
        "Culpable Homicide Not Murder - V": "Culpable Homicide - Victims",
        "Culpable Homicide Not Murder - R": "Culpable Homicides - Rate",
        "Causing Death by Negligence - I": "Causing Death by Negligence - Incidence",
        "Causing Death by Negligence - V": "Causing Death by Negligence - Victims",
        "Causing Death by Negligence - R": "Causing Death by Negligence - Rate",
    }
    out = df.rename(columns={k: v for k, v in explicit.items() if k in df.columns})
    if "Districts/City" not in out.columns:
        out = out.rename(columns={dcol: "Districts/City"})
    out["Districts/City"] = out["Districts/City"].map(_clean_district)
    for c in out.columns:
        if c not in ("Districts/City", "Sl No", "data_source"):
            out[c] = _to_num(out[c])
    out.insert(0, "Sl No", range(1, len(out) + 1))
    out["data_source"] = SOURCE_TAG
    out.attrs["year"] = year
    return out


def convert_women(path: Path) -> pd.DataFrame:
    """Women crimes / sexual harassment OpenCity table → near project women layout."""
    # Multiline headers: read carefully
    df = pd.read_csv(path)
    # Flatten columns
    df.columns = [
        re.sub(r"\s+", " ", str(c).replace("\n", " ")).strip() for c in df.columns
    ]
    dcol = next((c for c in df.columns if "district" in c.lower()), df.columns[1])
    df = _drop_totals(df, dcol)
    # Build map to project-like names used in tn-2022-crimes-against-women
    out = pd.DataFrame()
    out["Sl No"] = range(1, len(df) + 1)
    out["Districts/City"] = df[dcol].map(_clean_district)

    def pick(*needles: str) -> pd.Series | None:
        for c in df.columns:
            cl = c.lower()
            if all(n in cl for n in needles):
                return _to_num(df[c])
        return None

    mapping = {
        "Assault on Women with Intent to Outrage her Modesty - Incidents (I)": (
            "assault", "outrage", "incidents"
        ),
        "Rape (Sec 376) - I": ("rape", "376", "- i"),
    }
    # Direct common OpenCity names
    direct = {
        "Assault on Women with Intent to Outrage her Modesty - Incidents (I)":
            "Assault on Women with Intent to Outrage her Modesty - Incidents (I)",
        "Assault on Women with Intent to Outrage her Modesty - Victims (V)":
            "Assault on Women with Intent to Outrage her Modesty - Victims (V)",
        "Assault on Women with Intent to Outrage her Modesty - R (Crime Rate)":
            "Assault on Women with Intent to Outrage her Modesty - R (Crime Rate)",
        "Rape (Sec 376) - I": "Rape (Sec 376) - I",
        "Rape - V": "Rape - V",
        "Rape - R": "Rape - R",
        "Attempt to Commit Rape (Sec.376/511) - I": "Attempt to Commit Rape (Sec.376/511) - I",
        "Attempt to Commit Rape - V": "Attempt to Commit Rape - V",
        "Attempt to Commit Rape - R": "Attempt to Commit Rape - R",
        "Stalking - I": "Stalking - I",
        "Stalking - V": "Stalking - V",
        "Stalking - R": "Stalking - R",
        "Voyeurism - I": "Voyeurism - I",
        "Voyeurism - V": "Voyeurism - V",
        "Voyeurism - R": "Voyeurism - R",
        "Sexual Harrassment Total - I": "Sexual Harrassment Total - I",
        "Sexual Harrassment Total - V": "Sexual Harrassment Total - V",
        "Sexual Harrassment Total - R": "Sexual Harrassment Total - R",
    }
    for src, dst in direct.items():
        if src in df.columns:
            out[dst] = _to_num(df[src])
        else:
            # fuzzy
            s = pick(*[p for p in src.lower().replace("(", " ").split() if len(p) > 2][:3])
            if s is not None:
                out[dst] = s

    out["data_source"] = SOURCE_TAG
    return out


def stage_all() -> dict[str, Path]:
    STAGED_DIR.mkdir(parents=True, exist_ok=True)
    DROPIN_DIR.mkdir(parents=True, exist_ok=True)
    download_raw()
    written: dict[str, Path] = {}

    ipc_path = RAW_DIR / "ipc_2019_2021.csv"
    if ipc_path.exists():
        for year, frame in convert_ipc_years(ipc_path).items():
            # Prefer detailed complaints for 2021 if available
            p = STAGED_DIR / f"tn_{year}_complaints.csv"
            if year == 2021 and (RAW_DIR / "complaints_2021.csv").exists():
                continue
            frame.to_csv(p, index=False)
            written[f"complaints_{year}"] = p
            print(f"[STAGE] {p.name} rows={len(frame)}")

    c2021 = RAW_DIR / "complaints_2021.csv"
    if c2021.exists():
        f = convert_complaints_2021(c2021)
        p = STAGED_DIR / "tn_2021_complaints.csv"
        f.to_csv(p, index=False)
        written["complaints_2021"] = p
        print(f"[STAGE] {p.name} rows={len(f)}")

    mur = RAW_DIR / "deaths_crime_negligence.csv"
    if mur.exists():
        f = convert_murder(mur, year=2021)
        p = STAGED_DIR / "tn_2021_muder_homicide.csv"
        f.to_csv(p, index=False)
        written["homicide_2021"] = p
        print(f"[STAGE] {p.name} rows={len(f)}")

    wom = RAW_DIR / "women_crimes_2021.csv"
    if wom.exists():
        f = convert_women(wom)
        p = STAGED_DIR / "tn_2021_crimes_against_women.csv"
        f.to_csv(p, index=False)
        written["women_2021"] = p
        print(f"[STAGE] {p.name} rows={len(f)}")

    # Drop-ins win (SCRB/NCRB files you provide for 2018…2026)
    for f in DROPIN_DIR.glob("tn_*.csv"):
        dest = STAGED_DIR / f.name
        try:
            df = pd.read_csv(f)
            if "data_source" not in df.columns:
                df["data_source"] = SOURCE_TAG
            else:
                df["data_source"] = df["data_source"].fillna(SOURCE_TAG)
                df.loc[
                    df["data_source"].astype(str).str.lower().isin(["", "nan", "media_proxy"]),
                    "data_source",
                ] = SOURCE_TAG
            df.to_csv(dest, index=False)
            written[f"dropin_{f.name}"] = dest
            print(f"[STAGE] drop-in {f.name} → official SCRB/NCRB")
        except Exception as e:
            print(f"[WARN] drop-in {f.name}: {e}")

    # Manifest
    manifest = {
        "source": SOURCE_TAG,
        "staged": {k: str(v) for k, v in written.items()},
        "policy": load_policy(),
        "note": "2019–2021 from OpenCity TN crime tables; drop-ins for 2025/2026 SCRB/NCRB",
    }
    (SCRB_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return written


def apply_to_dataset(prefer_over_media: bool = True) -> list[str]:
    """Copy staged SCRB files into dataset/ for clean_data discovery."""
    STAGED_DIR.mkdir(parents=True, exist_ok=True)
    applied: list[str] = []
    if not any(STAGED_DIR.glob("tn_*.csv")):
        stage_all()

    for src in STAGED_DIR.glob("tn_*.csv"):
        dest = DATASET / src.name
        if dest.exists() and not prefer_over_media:
            # only overwrite media proxy years or missing
            pass
        # Always prefer SCRB staged for years it covers
        year_m = re.search(r"tn_(\d{4})_", src.name)
        year = int(year_m.group(1)) if year_m else None
        if dest.exists() and year and year >= 2024:
            # Check if existing is media proxy — overwrite with SCRB when drop-in/staged present
            try:
                old = pd.read_csv(dest, nrows=3)
                # media fills often lack data_source or have different shape; still overwrite if staged
            except Exception:
                pass
        shutil.copy2(src, dest)
        applied.append(src.name)
        print(f"[APPLY] {src.name} → dataset/")

    # Also write year-level source registry
    registry = {
        "official_years": {},
        "note": "Years listed here are SCRB/NCRB-class for training labels",
    }
    for src in STAGED_DIR.glob("tn_*.csv"):
        ym = re.search(r"tn_(\d{4})_", src.name)
        if ym:
            y = ym.group(1)
            registry["official_years"].setdefault(y, []).append(src.name)
    (SCRB_ROOT / "official_years_registry.json").write_text(
        json.dumps(registry, indent=2), encoding="utf-8"
    )
    print(f"[OK] Applied {len(applied)} SCRB/NCRB files")
    return applied


def tag_existing_project_years_as_scrb(years: list[int]) -> None:
    """
    When user asserts 2025/2026 (or other) project CSVs are SCRB/NCRB official tables,
    stamp data_source=scrb_ncrb on those raw files so clean_data marks is_official_year=1.
    """
    patterns = [
        "tn_{y}_complaints.csv",
        "tn_{y}_muder_homicide.csv",
        "tn_{y}_crimes_against_women.csv",
        "tn-{y}-crimes-against-women.csv",
    ]
    for y in years:
        for pat in patterns:
            p = DATASET / pat.format(y=y)
            if not p.exists():
                continue
            try:
                df = pd.read_csv(p)
                df["data_source"] = SOURCE_TAG
                df.to_csv(p, index=False)
                print(f"[TAG] {p.name} → data_source={SOURCE_TAG}")
            except Exception as e:
                print(f"[WARN] tag {p.name}: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="SCRB/NCRB official data for CRIMECAST")
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Copy staged files into dataset/")
    parser.add_argument(
        "--tag-years",
        type=int,
        nargs="*",
        default=None,
        help="Stamp existing dataset/tn_YEAR_*.csv as SCRB/NCRB official (e.g. 2025 2026)",
    )
    parser.add_argument(
        "--rebuild-ml",
        action="store_true",
        help="Run clean_data after apply to rebuild crimecast_ml_ready.csv",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("CRIMECAST · SCRB / NCRB official ingest")
    print("=" * 60)
    download_raw(force=args.force_download)
    stage_all()

    if args.tag_years:
        tag_existing_project_years_as_scrb(args.tag_years)

    if args.apply:
        apply_to_dataset(prefer_over_media=True)

    if args.rebuild_ml:
        print("[RUN] clean_data.main …")
        from clean_data import main as clean_main

        clean_main()

    print()
    print("Next:")
    print("  1) Drop SCRB/NCRB CSVs for 2025/2026 into dataset/scrb_ncrb/dropin/")
    print("  2) python acquire_scrb_ncrb.py --apply --rebuild-ml")
    print("  3) Or tag existing files: python acquire_scrb_ncrb.py --tag-years 2025 2026 --apply --rebuild-ml")
    print("  4) Retrain: python train_model.py")


if __name__ == "__main__":
    main()
