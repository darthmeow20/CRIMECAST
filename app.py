# -*- coding: utf-8 -*-
"""CRIMECAST console app."""
from __future__ import annotations

import argparse
import runpy
import subprocess
import sys
from pathlib import Path

from clean_data import run_cleaning
from predict import list_areas, parse_overrides, predict_many, resolve_target
from sentiment_analysis import analyze_sentiment
from sentiment_by_state import analyze_sentiment_by_state, get_state_comparison
from sentiment_visualize_states import generate_all_state_visualizations
from sentiment_tn_districts import analyze_tn_sentiment_by_district, get_tn_district_comparison
from sentiment_visualize_tn_districts import generate_all_tn_visualizations
from train_model import TARGET_CONFIGS, train_models
from visualize import create_visualizations

ROOT = Path(__file__).resolve().parent


def print_targets() -> None:
    for key, config in TARGET_CONFIGS.items():
        print(f"{key}: {config['label']}")


def print_areas() -> None:
    for area in list_areas():
        print(area)


def run_prediction(
    area: str,
    targets: list[str] | None = None,
    overrides: list[str] | None = None,
    year: int | None = None,
) -> None:
    try:
        parsed_overrides = parse_overrides(overrides) if overrides else None
        predictions = predict_many(
            area=area,
            targets=targets,
            year=year,
            overrides=parsed_overrides,
        )
        display_cols = ["area", "year", "target_label", "prediction"]
        if "risk_index" in predictions.columns:
            display_cols = [
                "area",
                "year",
                "target_label",
                "prediction",
                "risk_index",
                "risk_label",
            ]
        print("\nPredictions:")
        print(predictions[display_cols].to_string(index=False))
        print("\nSaved to: model_outputs/crime_predictions.csv")
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        print("Tip: Run option 1 first to ensure models and sentiment data exist.")


def run_news_signals(
    years: list[int] | None = None,
    *,
    demo: bool = False,
    fetch: str | None = None,
    lang: str = "ta",
) -> None:
    """
    Run acquire_news_signals.py — Tamil + English media harvest.
    Outlets: தினத்தந்தி, தினமலர், தினமணி, தமிழ் முரசு, புதிய தலைமுறை, விகடன், பிபிசி தமிழ்
    Keywords: கொலை, தாக்குதல், கடத்தல், லஞ்சம், திருட்டு, பாலியல் வன்கொடுமை, POCSO, …
    """
    script = ROOT / "acquire_news_signals.py"
    if not script.exists():
        print(f"[ERROR] Missing {script}")
        return

    cmd = [sys.executable, "-B", str(script)]
    if demo:
        cmd.append("--demo")
    elif fetch:
        cmd.extend(["--fetch", fetch, "--lang", lang, "--max-items", "25"])
    else:
        # Default: full media populate for 2024–2026
        if years:
            cmd.append("--populate-years")
            cmd.extend(str(y) for y in years)
        else:
            cmd.append("--populate-2024-2026")

    print("\n" + "=" * 60)
    print("NEWS SIGNALS — Tamil media harvest (acquire_news_signals.py)")
    print("=" * 60)
    print(f"Command: {' '.join(cmd)}")
    print("Outlets : தினத்தந்தி, தினமலர், தினமணி, தமிழ் முரசு,")
    print("          புதிய தலைமுறை, விகடன், பிபிசி தமிழ்")
    print("Keywords: கொலை, தாக்குதல், கடத்தல், லஞ்சம், திருட்டு,")
    print("          பாலியல் வன்கொடுமை, POCSO, போதைப்பொருள், கைது, FIR")
    print("=" * 60 + "\n")

    try:
        result = subprocess.run(cmd, cwd=str(ROOT), check=False)
        if result.returncode == 0:
            print("\n[OK] News signal harvest finished.")
            print("     Outputs: model_outputs/news_signals.csv")
            print("              model_outputs/media_harvest_*.csv")
            print("              dataset/tn_2024_*.csv … tn_2026_*.csv (if populate)")
        else:
            print(f"\n[WARN] acquire_news_signals exit code {result.returncode}")
            # In-process fallback
            try:
                from acquire_news_signals import populate_years_from_net, create_demo_data, save_signals

                if demo:
                    save_signals(create_demo_data(years or [2022, 2023, 2024, 2025, 2026]))
                else:
                    populate_years_from_net(years=years or [2024, 2025, 2026])
                print("[OK] Fallback in-process harvest completed.")
            except Exception as e2:
                print(f"[ERROR] News harvest failed: {e2}")
    except Exception as e:
        print(f"[ERROR] Could not run news harvest: {e}")


def run_full_pipeline() -> None:
    """
    Full pipeline uses EXISTING news + only NEW headlines (incremental).
    One-time bulk acquire is menu option n (mode 1), NOT repeated here.
    """
    print("[1/6] Pull NEW crime news only (incremental refresh)...")
    print("      (Bulk one-time acquire is option n — not re-run every pipeline)")
    try:
        script = ROOT / "acquire_news_signals.py"
        if script.exists():
            r = subprocess.run(
                [sys.executable, "-B", str(script), "--refresh-new", "--light-score"],
                cwd=str(ROOT),
                check=False,
            )
            if r.returncode != 0:
                # in-process fallback (lexicon only — no transformers)
                from acquire_news_signals import refresh_new_news

                refresh_new_news(light_score=True)
        else:
            print("[WARN] acquire_news_signals.py missing — using existing news_signals.csv only")
    except Exception as e:
        print(f"[WARN] New-news refresh skipped (will use existing signals): {e}")

    news_csv = ROOT / "model_outputs" / "news_signals.csv"
    if news_csv.exists():
        print(f"[OK] News signals available for clean fusion: {news_csv.name}")
    else:
        print("[WARN] No news_signals.csv yet. Run menu option n (mode 1) once for bulk acquire.")

    print("[2/6] Sentiment / NLP...")
    try:
        sentiment_outputs = analyze_sentiment()
    except Exception as e:
        sentiment_outputs = {"output_file": "N/A", "rows": 0, "message": str(e)}

    print("[3/6] Cleaning data (fuses existing + new news signals)...")
    cleaning_outputs = run_cleaning()

    print("[4/6] Training ML models...")
    training_outputs = train_models(data_path=cleaning_outputs["ml_ready"])

    print("[5/6] Charts...")
    visual_outputs = create_visualizations()

    print("[6/6] Done.")
    print(f"ML-ready: {cleaning_outputs['ml_ready']}")
    print(f"Sentiment rows: {sentiment_outputs.get('rows', 0)}")
    print(f"Training report: {training_outputs['report']}")
    print(f"Charts: {visual_outputs['figure_dir']}")


def run_2026_rape_prediction() -> None:
    """
    Option 7 — MUST use FIXED-NO-SKLEARN-v4 file only.
    Executes predict_2026_rape_all_districts.py as a fresh process so no
    stale in-memory sklearn code can run.
    """
    script = ROOT / "predict_2026_rape_all_districts.py"
    print("\n" + "=" * 70)
    print("OPTION 7 → subprocess (fresh interpreter, no stale imports)")
    print(f"Script: {script}")
    print(f"Python: {sys.executable}")
    print("=" * 70 + "\n")

    if not script.exists():
        print(f"[ERROR] Missing {script}")
        return

    # Preferred: brand-new process (cannot use old loaded modules)
    try:
        result = subprocess.run(
            [sys.executable, "-B", str(script)],
            cwd=str(ROOT),
            check=False,
        )
        if result.returncode == 0:
            print("\n[OK] Option 7 subprocess finished successfully.")
        else:
            print(f"\n[WARN] Subprocess exit code {result.returncode} — trying runpy fallback")
            runpy.run_path(str(script), run_name="__main__")
    except Exception as e:
        print(f"[WARN] Subprocess failed ({e}) — runpy fallback")
        try:
            runpy.run_path(str(script), run_name="__main__")
        except Exception as e2:
            print(f"[ERROR] {e2}")
            return

    # Optional charts from existing CSV
    try:
        from visualize_rape_2026 import main as viz_main

        print("\n[INFO] Charts from saved CSV...")
        viz_main()
    except Exception as viz_err:
        print(f"[WARN] Charts skipped: {viz_err}")

    out = ROOT / "model_outputs" / "rape_predictions_2026_all_districts.csv"
    if out.exists():
        print(f"\n[OK] Results: {out}")
    else:
        print("\n[ERROR] CSV missing. In this folder run:")
        print(f"  {sys.executable} predict_2026_rape_all_districts.py")


def interactive_menu() -> None:
    engine = ROOT / "predict_2026_rape_all_districts.py"
    print()
    print(f"[BOOT] app.py dir : {ROOT}")
    print(f"[BOOT] option-7   : {engine.name} exists={engine.exists()}")
    if engine.exists():
        head = engine.read_text(encoding="utf-8", errors="replace")[:200]
        if "FIXED-NO-SKLEARN-v4" in head or "FIXED-NO-SKLEARN-v4" in engine.read_text(
            encoding="utf-8", errors="replace"
        ):
            print("[BOOT] option-7 engine marker: FIXED-NO-SKLEARN-v4  OK")
        else:
            print("[BOOT] WARNING: option-7 file missing FIXED-NO-SKLEARN-v4 marker!")

    while True:
        print()
        print("=" * 40)
        print("        CRIMECAST PROJECT")
        print("=" * 40)
        print()
        print("ANALYSIS & PREDICTION")
        print("  1. Run full pipeline (NEW news only → sentiment → clean → train → charts)")
        print("  2. Predict for an area")
        print("  3. Create charts")
        print()
        print("NEWS & MEDIA (Tamil + English)")
        print("  n. News acquire / refresh  [acquire_news_signals.py]")
        print("     Mode 1 = ONE-TIME bulk (2024–2026 proxies) — run once")
        print("     Mode 2 = NEW headlines only (same as dashboard refresh)")
        print("     Mode 3 = Demo offline | Mode 4 = Live single query")
        print()
        print("OFFICIAL SCRB / NCRB")
        print("  s. SCRB/NCRB official ingest  [acquire_scrb_ncrb.py]")
        print("     Pre-2022 OpenCity tables + drop-ins for 2025/2026")
        print()
        print("SENTIMENT ANALYSIS")
        print("  4. Run sentiment scoring")
        print("  5. Sentiment by state/district")
        print("  6. Tamil Nadu district-wise sentiment")
        print()
        print("CRIME FORECASTING")
        print("  7. 2026 rape prediction ALL districts  [FIXED-NO-SKLEARN-v4]")
        print()
        print("UTILITIES")
        print("  8. List areas")
        print("  9. List targets")
        print("  t. Self-test option 7 fix")
        print("  c. Combined risk sample (Chennai)")
        print("  0. Exit")
        print()
        choice = input("Select option: ").strip().lower()

        if choice == "1":
            run_full_pipeline()
        elif choice == "2":
            area = input("Area [Chennai]: ").strip() or "Chennai"
            year_s = input("Year (blank=latest, or 2026): ").strip()
            year = int(year_s) if year_s else None
            t = input("Targets (blank=all, or rape murder ...): ").strip()
            targets = t.split() if t else None
            run_prediction(area=area, targets=targets, year=year)
        elif choice == "3":
            outputs = create_visualizations()
            print(f"[OK] Charts: {outputs['figure_dir']}")
        elif choice == "s":
            print("\nSCRB/NCRB mode:")
            print("  1 = Download OpenCity (2019–2021) + stage + apply + rebuild ML")
            print("  2 = Tag existing tn_2025/tn_2026 as SCRB official + rebuild")
            print("  3 = Stage only (no copy to dataset/)")
            sub = input("Mode [1]: ").strip() or "1"
            try:
                if sub == "2":
                    cmd = [
                        sys.executable, "-B", str(ROOT / "acquire_scrb_ncrb.py"),
                        "--tag-years", "2025", "2026", "--apply", "--rebuild-ml",
                    ]
                elif sub == "3":
                    cmd = [sys.executable, "-B", str(ROOT / "acquire_scrb_ncrb.py")]
                else:
                    cmd = [
                        sys.executable, "-B", str(ROOT / "acquire_scrb_ncrb.py"),
                        "--apply", "--rebuild-ml",
                    ]
                subprocess.run(cmd, cwd=str(ROOT), check=False)
            except Exception as e:
                print(f"[ERROR] {e}")
                print("Tip: python acquire_scrb_ncrb.py --apply --rebuild-ml")
        elif choice == "n":
            print("\nNews mode:")
            print("  1 = ONE-TIME bulk populate 2024+2025+2026 (full acquire)")
            print("  2 = NEW headlines only (incremental refresh)")
            print("  3 = Demo offline")
            print("  4 = Live single query")
            sub = input("Mode [2]: ").strip() or "2"
            if sub == "1":
                run_news_signals(years=[2024, 2025, 2026])
            elif sub == "3":
                run_news_signals(demo=True)
            elif sub == "4":
                q = input(
                    "Query [தமிழ்நாடு கொலை OR பாலியல்]: "
                ).strip() or "தமிழ்நாடு கொலை OR பாலியல் OR கைது"
                lang = input("Language en/ta [ta]: ").strip() or "ta"
                run_news_signals(fetch=q, lang=lang)
            else:
                # Incremental new-only
                print("[INFO] Refreshing NEW news only...")
                try:
                    r = subprocess.run(
                        [
                            sys.executable,
                            "-B",
                            str(ROOT / "acquire_news_signals.py"),
                            "--refresh-new",
                            "--light-score",
                        ],
                        cwd=str(ROOT),
                        check=False,
                    )
                    if r.returncode != 0:
                        from acquire_news_signals import refresh_new_news

                        refresh_new_news(light_score=True)
                except Exception as e:
                    print(f"[ERROR] {e}")
        elif choice == "4":
            result = analyze_sentiment()
            print(f"[OK] Rows: {result.get('rows')}")
        elif choice == "5":
            try:
                state_results = analyze_sentiment_by_state()
                print(f"[OK] {len(state_results)} states/districts")
                print(get_state_comparison().to_string(index=False))
                generate_all_state_visualizations()
            except Exception as e:
                print(f"[ERROR] {e}")
        elif choice == "6":
            try:
                tn_results = analyze_tn_sentiment_by_district()
                print(f"[OK] {len(tn_results)} TN districts")
                print(get_tn_district_comparison().to_string(index=False))
                generate_all_tn_visualizations()
            except Exception as e:
                print(f"[ERROR] {e}")
        elif choice == "7":
            run_2026_rape_prediction()
        elif choice == "8":
            print_areas()
        elif choice == "9":
            print_targets()
        elif choice == "t":
            test = ROOT / "tests" / "test_option7_fix.py"
            print(f"[INFO] Running {test.name} ...")
            try:
                r = subprocess.run(
                    [sys.executable, "-B", str(test)],
                    cwd=str(ROOT),
                    check=False,
                )
                print(f"[INFO] Self-test exit code: {r.returncode}")
            except Exception as e:
                print(f"[ERROR] {e}")
        elif choice == "c":
            try:
                preds = predict_many("Chennai", targets=None)
                cols = ["area", "target_label", "prediction"]
                if "risk_index" in preds.columns:
                    cols += ["risk_index", "risk_label"]
                print(preds[cols].head(6).to_string(index=False))
            except Exception as e:
                print(f"Run full pipeline first. Error: {e}")
        elif choice == "0":
            print("\n[OK] Goodbye!\n")
            return
        else:
            print("[ERROR] Invalid choice. Use 0-9, n, s, t, or c.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CRIMECAST project console app.")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--charts", action="store_true")
    parser.add_argument("--sentiment", action="store_true")
    parser.add_argument("--predict", action="store_true")
    parser.add_argument("--tn-district", action="store_true")
    parser.add_argument("--state", action="store_true")
    parser.add_argument("--rape-2026", action="store_true", help="Option 7 fixed engine")
    parser.add_argument(
        "--news",
        action="store_true",
        help="Harvest Tamil+English crime news (acquire_news_signals) for 2024–2026",
    )
    parser.add_argument(
        "--news-demo",
        action="store_true",
        help="Generate demo news signals only (offline)",
    )
    parser.add_argument(
        "--news-years",
        type=int,
        nargs="+",
        default=None,
        help="Years for --news (default 2024 2025 2026)",
    )
    parser.add_argument("--area", default="Chennai")
    parser.add_argument("--year", type=int, default=None)
    parser.add_argument("--target", nargs="+", default=None)
    parser.add_argument("--set", dest="overrides", action="append", default=None)
    parser.add_argument("--list-areas", action="store_true")
    parser.add_argument("--list-targets", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.full:
        run_full_pipeline()
    elif args.news or args.news_demo:
        run_news_signals(
            years=args.news_years or [2024, 2025, 2026],
            demo=bool(args.news_demo),
        )
    elif args.charts:
        outputs = create_visualizations()
        print(f"[OK] Charts: {outputs['figure_dir']}")
    elif args.sentiment:
        result = analyze_sentiment()
        print(f"[OK] Rows: {result.get('rows')}")
    elif args.predict:
        run_prediction(area=args.area, targets=args.target, overrides=args.overrides, year=args.year)
    elif args.tn_district:
        try:
            tn_results = analyze_tn_sentiment_by_district()
            print(f"[OK] {len(tn_results)} districts")
            print(get_tn_district_comparison().to_string(index=False))
        except Exception as e:
            print(f"[ERROR] {e}")
    elif args.state:
        try:
            state_results = analyze_sentiment_by_state()
            print(f"[OK] {len(state_results)}")
            print(get_state_comparison().to_string(index=False))
        except Exception as e:
            print(f"[ERROR] {e}")
    elif args.rape_2026:
        run_2026_rape_prediction()
    elif args.list_areas:
        print_areas()
    elif args.list_targets:
        print_targets()
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
