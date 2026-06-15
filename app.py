from __future__ import annotations

import argparse

from clean_data import run_cleaning
from predict import list_areas, parse_overrides, predict_many, resolve_target
from sentiment_analysis import analyze_sentiment
from sentiment_by_state import analyze_sentiment_by_state, get_state_comparison
from sentiment_visualize_states import generate_all_state_visualizations
from sentiment_tn_districts import analyze_tn_sentiment_by_district, get_tn_district_comparison
from sentiment_visualize_tn_districts import generate_all_tn_visualizations
from train_model import TARGET_CONFIGS, train_models
from visualize import create_visualizations

try:
    from predict_2026_rape_all_districts import predict_2026_rape_all_districts, generate_rape_report
    from visualize_rape_2026 import main as visualize_rape_2026
    HAS_RAPE_2026 = True
except ImportError:
    HAS_RAPE_2026 = False


def print_targets() -> None:
    for key, config in TARGET_CONFIGS.items():
        print(f"{key}: {config['label']}")


def print_areas() -> None:
    for area in list_areas():
        print(area)


def run_full_pipeline() -> None:
    cleaning_outputs = run_cleaning()
    training_outputs = train_models(data_path=cleaning_outputs["ml_ready"])
    visual_outputs = create_visualizations()
    sentiment_outputs = analyze_sentiment()

    print("Pipeline completed.")
    print(f"Cleaned data: {cleaning_outputs['output_dir']}")
    print(f"ML-ready file: {cleaning_outputs['ml_ready']}")
    print(f"Training report: {training_outputs['report']}")
    print(f"Charts: {visual_outputs['figure_dir']}")
    print(f"Sentiment output: {sentiment_outputs['output_file']}")


def run_2026_rape_prediction() -> None:
    """Run 2026 rape crime prediction for all districts."""
    if not HAS_RAPE_2026:
        print("[ERROR] 2026 rape prediction modules not available")
        return
    
    print("\n[INFO] Generating 2026 rape crime predictions for all districts...\n")
    try:
        predictions = predict_2026_rape_all_districts()
        generate_rape_report(predictions)
        
        print("\n[INFO] Generating visualizations...")
        visualize_rape_2026()
        
        print("\n[OK] 2026 rape predictions completed!")
        print("[OK] Results saved to: model_outputs/")
        print(f"     - rape_predictions_2026_all_districts.csv")
        print(f"     - rape_predictions_2026_report.txt")
        print(f"     - figures/rape_2026_*.png (5 charts)")
    except Exception as e:
        print(f"[ERROR] {e}")



def interactive_menu() -> None:
    while True:
        print()
        print("=" * 40)
        print("        CRIMECAST PROJECT")
        print("=" * 40)
        print()
        print("ANALYSIS & PREDICTION")
        print("  1. Run full clean + train + chart pipeline")
        print("  2. Predict for an area")
        print("  3. Create charts")
        print()
        print("SENTIMENT ANALYSIS")
        print("  4. Run sentiment scoring")
        print("  5. Sentiment analysis by state/district")
        print("  6. Tamil Nadu district-wise sentiment [NEW]")
        print()
        print("CRIME FORECASTING")
        print("  7. 2026 rape crime prediction (all districts) [NEW]")
        print()
        print("DATA & INFO")
        print("  8. List areas")
        print("  9. List targets")
        print()
        print("  0. Exit")
        print()
        choice = input("Choose: ").strip()

        if choice == "1":
            run_full_pipeline()
        elif choice == "2":
            area = input("Area name, for example Chennai: ").strip() or "Chennai"
            target = input("Target, or leave blank for all: ").strip()
            targets = [target] if target else None
            year_value = input("Year, or leave blank for latest: ").strip()
            year = int(year_value) if year_value else None
            run_prediction(area=area, targets=targets, overrides=None, year=year)
        elif choice == "3":
            outputs = create_visualizations()
            print(f"[OK] Charts written to: {outputs['figure_dir']}")
        elif choice == "4":
            result = analyze_sentiment()
            print(f"[OK] Rows scored: {result['rows']}")
            print(f"[OK] Sentiment output: {result['output_file']}")
            if "message" in result:
                print(f"     {result['message']}")
        elif choice == "5":
            print("\n[INFO] Generating state-wise sentiment analysis...\n")
            try:
                state_results = analyze_sentiment_by_state()
                print(f"[OK] Analyzed {len(state_results)} states/districts\n")
                
                print("State Comparison:")
                comparison = get_state_comparison()
                print(comparison.to_string(index=False))
                
                print("\n[INFO] Generating visualizations...")
                figs = generate_all_state_visualizations()
                for name, path in figs.items():
                    print(f"  [OK] {name}")
                    
                print("\n[OK] Reports saved to: model_outputs/state_sentiment_reports/")
            except Exception as e:
                print(f"[ERROR] {e}")
        elif choice == "6":
            print("\n[INFO] Generating Tamil Nadu district-wise sentiment analysis...\n")
            try:
                tn_results = analyze_tn_sentiment_by_district()
                print(f"[OK] Analyzed {len(tn_results)} Tamil Nadu districts\n")
                
                print("Tamil Nadu District Comparison:")
                tn_comparison = get_tn_district_comparison()
                print(tn_comparison.to_string(index=False))
                
                print("\n[INFO] Generating visualizations...")
                tn_figs = generate_all_tn_visualizations()
                for name, path in tn_figs.items():
                    print(f"  [OK] {name}")
                    
                print("\n[OK] Reports saved to: model_outputs/tn_district_sentiment_reports/")
                print("[OK] Visualizations saved to: model_outputs/figures/")
            except Exception as e:
                print(f"[ERROR] {e}")
        elif choice == "7":
            run_2026_rape_prediction()
        elif choice == "8":
            print_areas()
        elif choice == "9":
            print_targets()
        elif choice == "0":
            print("\n[OK] Goodbye!\n")
            return
        else:
            print("[ERROR] Choose a number from the menu.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CRIMECAST project console app.")
    parser.add_argument("--full", action="store_true", help="Run clean, train, chart, and sentiment steps.")
    parser.add_argument("--charts", action="store_true", help="Create analysis charts.")
    parser.add_argument("--sentiment", action="store_true", help="Run sentiment scoring.")
    parser.add_argument("--predict", action="store_true", help="Predict crime target(s) for an area.")
    parser.add_argument("--tn-district", action="store_true", help="Run Tamil Nadu district-wise sentiment analysis.")
    parser.add_argument("--state", action="store_true", help="Run state-wise sentiment analysis.")
    parser.add_argument("--rape-2026", action="store_true", help="Generate 2026 rape crime predictions for all districts.")
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
    elif args.charts:
        outputs = create_visualizations()
        print(f"[OK] Charts written to: {outputs['figure_dir']}")
    elif args.sentiment:
        result = analyze_sentiment()
        print(f"[OK] Rows scored: {result['rows']}")
        print(f"[OK] Sentiment output: {result['output_file']}")
        if "message" in result:
            print(result["message"])
    elif args.predict:
        run_prediction(area=args.area, targets=args.target, overrides=args.overrides, year=args.year)
    elif args.tn_district:
        print("\n[INFO] Generating Tamil Nadu district-wise sentiment analysis...\n")
        try:
            tn_results = analyze_tn_sentiment_by_district()
            print(f"[OK] Analyzed {len(tn_results)} Tamil Nadu districts\n")
            
            print("Tamil Nadu District Comparison:")
            tn_comparison = get_tn_district_comparison()
            print(tn_comparison.to_string(index=False))
            
            print("\n[INFO] Generating visualizations...")
            tn_figs = generate_all_tn_visualizations()
            for name, path in tn_figs.items():
                print(f"  [OK] {name}")
                
            print("\n[OK] Reports saved to: model_outputs/tn_district_sentiment_reports/")
        except Exception as e:
            print(f"[ERROR] {e}")
    elif args.state:
        print("\n[INFO] Generating state-wise sentiment analysis...\n")
        try:
            state_results = analyze_sentiment_by_state()
            print(f"[OK] Analyzed {len(state_results)} states/districts\n")
            
            print("State Comparison:")
            comparison = get_state_comparison()
            print(comparison.to_string(index=False))
            
            print("\n[INFO] Generating visualizations...")
            figs = generate_all_state_visualizations()
            for name, path in figs.items():
                print(f"  [OK] {name}")
                
            print("\n[OK] Reports saved to: model_outputs/state_sentiment_reports/")
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
