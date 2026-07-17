"""
CRIMECAST system health check — usable / reliable ops.

Run:  python health_check.py
Exit code 0 = OK enough to demo; 1 = blocking issues.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT = PROJECT_ROOT / "model_outputs"
MODELS = PROJECT_ROOT / "models"
DATASET = PROJECT_ROOT / "dataset" / "cleaned"
DATA_DB = PROJECT_ROOT / "data" / "crimecast.db"
ASSETS = PROJECT_ROOT / "assets"


def _age_days(path: Path) -> float | None:
    if not path.exists():
        return None
    return (datetime.now().timestamp() - path.stat().st_mtime) / 86400.0


def _ok(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def run_health_check() -> dict:
    checks: list[dict] = []

    def add(name: str, status: str, detail: str, blocking: bool = False) -> None:
        checks.append({
            "name": name,
            "status": status,  # ok | warn | fail
            "detail": detail,
            "blocking": blocking,
        })

    # SCRB / NCRB staging
    scrb = PROJECT_ROOT / "dataset" / "scrb_ncrb"
    staged = list((scrb / "staged").glob("tn_*.csv")) if (scrb / "staged").exists() else []
    dropin = list((scrb / "dropin").glob("tn_*.csv")) if (scrb / "dropin").exists() else []
    if staged or dropin:
        add(
            "SCRB/NCRB files",
            "ok",
            f"staged={len(staged)} drop-in={len(dropin)} · run acquire_scrb_ncrb.py --apply --rebuild-ml",
        )
    else:
        add(
            "SCRB/NCRB files",
            "warn",
            "No staged SCRB yet — python acquire_scrb_ncrb.py --apply (pre-2022 + drop-ins for 2025/2026)",
        )

    # Core data
    ml = DATASET / "crimecast_ml_ready.csv"
    if _ok(ml):
        try:
            import pandas as pd

            peek = pd.read_csv(ml, nrows=3)
            years = ""
            if "year" in peek.columns:
                full = pd.read_csv(ml, usecols=["year"])
                ys = sorted(pd.to_numeric(full["year"], errors="coerce").dropna().unique().tolist())
                years = f" years={ys}"
            add("ML-ready data", "ok", f"{ml.name} · {ml.stat().st_size // 1024} KB{years}")
        except Exception as e:
            add("ML-ready data", "warn", f"Readable but parse issue: {e}")
    else:
        add("ML-ready data", "fail", f"Missing {ml} — run clean_data / app option 1", True)

    # Models
    joblibs = list(MODELS.glob("*.joblib")) if MODELS.exists() else []
    crime_models = [p for p in joblibs if "sentiment" not in p.name]
    if len(crime_models) >= 3:
        add("Trained models", "ok", f"{len(crime_models)} crime models in models/")
    elif crime_models:
        add("Trained models", "warn", f"Only {len(crime_models)} models — retrain recommended")
    else:
        add("Trained models", "fail", "No .joblib models — run train_model / option 1", True)

    # News
    harvest = OUTPUT / "media_harvest_tn_crime_latest.csv"
    news = OUTPUT / "news_signals.csv"
    if _ok(harvest) or _ok(news):
        age = _age_days(harvest if _ok(harvest) else news)
        path = harvest if _ok(harvest) else news
        st = "ok" if age is not None and age <= 7 else "warn"
        add(
            "News / media",
            st,
            f"{path.name} · age {age:.1f}d" if age is not None else path.name
            + (" · refresh if >7 days old" if st == "warn" else ""),
        )
    else:
        add("News / media", "warn", "No harvest yet — dashboard 🔄 or acquire_news_signals.py --refresh-new")

    # 2026
    rape = OUTPUT / "rape_predictions_2026_all_districts.csv"
    if _ok(rape):
        add("2026 forecasts", "ok", f"{rape.name} present")
    else:
        add("2026 forecasts", "warn", "Missing — run option 7 / predict_2026_rape_all_districts.py")

    # Map
    geo = ASSETS / "tamil_nadu_districts.geojson"
    if _ok(geo):
        add("TN map GeoJSON", "ok", "Cached under assets/")
    else:
        add("TN map GeoJSON", "warn", "Not cached — first map load needs network once")

    # SQLite
    if DATA_DB.exists():
        add("SQLite DB", "ok", f"data/crimecast.db · {DATA_DB.stat().st_size // 1024} KB")
    else:
        add("SQLite DB", "warn", "Not created yet — opens on first dashboard/db sync")

    # Best models registry
    best = OUTPUT / "best_models.json"
    if _ok(best):
        add("Model registry", "ok", "best_models.json present")
    else:
        add("Model registry", "warn", "best_models.json missing — predict may fail")

    blocking = sum(1 for c in checks if c["status"] == "fail")
    warns = sum(1 for c in checks if c["status"] == "warn")
    overall = "ready" if blocking == 0 else "blocked"
    if blocking == 0 and warns:
        overall = "ready_with_warnings"

    return {
        "overall": overall,
        "blocking": blocking,
        "warnings": warns,
        "checks": checks,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(PROJECT_ROOT),
    }


def print_report(report: dict) -> None:
    print("=" * 60)
    print("CRIMECAST HEALTH CHECK")
    print("=" * 60)
    print(f"Overall: {report['overall']}  |  blocking={report['blocking']}  warnings={report['warnings']}")
    print(f"Root: {report['project_root']}")
    print("-" * 60)
    for c in report["checks"]:
        mark = {"ok": "[OK]  ", "warn": "[WARN]", "fail": "[FAIL]"}[c["status"]]
        print(f"  {mark} {c['name']}: {c['detail']}")
    print("-" * 60)
    if report["overall"] == "ready":
        print("Demo-ready. Launch: streamlit run dashboard.py")
    elif report["overall"] == "ready_with_warnings":
        print("Usable with gaps. Prefer refresh news + option 7 before demos.")
    else:
        print("Fix FAIL items first (usually option 1 full pipeline).")
    print("=" * 60)


def main() -> int:
    report = run_health_check()
    print_report(report)
    out = OUTPUT / "health_check.json"
    try:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote {out}")
    except Exception:
        pass
    return 1 if report["blocking"] else 0


if __name__ == "__main__":
    sys.exit(main())
