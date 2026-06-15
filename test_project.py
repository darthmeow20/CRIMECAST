#!/usr/bin/env python3
"""
Comprehensive project health check script for CRIMECAST
Tests all major components and verifies functionality
"""

import sys
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\n" + "=" * 60)
    print("CHECKING DEPENDENCIES")
    print("=" * 60)
    
    dependencies = {
        "pandas": "Data processing",
        "numpy": "Numerical computing",
        "sklearn": "Machine learning",
        "matplotlib": "Visualization",
        "seaborn": "Advanced plotting",
        "textblob": "TextBlob sentiment (fallback)",
        "transformers": "DistilBERT sentiment (primary)",
        "torch": "PyTorch (for DistilBERT)",
    }
    
    all_ok = True
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"[OK] {package:20} - {description}")
        except ImportError:
            print(f"[FAIL] {package:20} - {description} - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def check_files():
    """Check if all required files exist."""
    print("\n" + "=" * 60)
    print("CHECKING PROJECT FILES")
    print("=" * 60)
    
    base_path = Path(__file__).parent
    required_files = {
        "app.py": "Main application",
        "sentiment_analysis.py": "Sentiment analysis module",
        "clean_data.py": "Data cleaning",
        "train_model.py": "Model training",
        "predict.py": "Prediction module",
        "visualize.py": "Visualization",
        "sentiment_tn_districts.py": "TN district analysis",
        "sentiment_visualize_tn_districts.py": "TN visualizations",
        "requirements.txt": "Dependencies",
    }
    
    all_exist = True
    for filename, description in required_files.items():
        filepath = base_path / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"[OK] {filename:40} - {description:30} ({size:,} bytes)")
        else:
            print(f"[FAIL] {filename:40} - {description:30} - MISSING")
            all_exist = False
    
    return all_exist

def check_imports():
    """Test if all modules can be imported."""
    print("\n" + "=" * 60)
    print("CHECKING MODULE IMPORTS")
    print("=" * 60)
    
    modules = [
        ("clean_data", "Data cleaning"),
        ("train_model", "Model training"),
        ("predict", "Predictions"),
        ("visualize", "Visualizations"),
        ("sentiment_analysis", "Sentiment analysis"),
        ("sentiment_by_state", "State sentiment analysis"),
        ("sentiment_tn_districts", "TN district analysis"),
    ]
    
    all_ok = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"[OK] {module_name:30} - {description}")
        except Exception as e:
            print(f"[FAIL] {module_name:30} - {description}")
            print(f"       Error: {str(e)[:60]}")
            all_ok = False
    
    return all_ok

def check_sentiment_scoring():
    """Test sentiment analysis with sample text."""
    print("\n" + "=" * 60)
    print("TESTING SENTIMENT ANALYSIS")
    print("=" * 60)
    
    try:
        from sentiment_analysis import score_text, HAS_DISTILBERT, HAS_TEXTBLOB
        
        # Check available method
        method = "DistilBERT" if HAS_DISTILBERT else ("TextBlob" if HAS_TEXTBLOB else "Lexicon-based")
        print(f"[INFO] Using sentiment method: {method}")
        
        test_texts = [
            "Crime rate increased, people are afraid and unsafe",
            "Police arrested the suspects quickly, justice served",
            "Mixed feelings about the incident and response",
        ]
        
        for i, text in enumerate(test_texts, 1):
            try:
                result = score_text(text)
                print(f"\n[OK] Test {i}: '{text[:50]}...'")
                print(f"     Label: {result['sentiment_label']}, "
                      f"Polarity: {result['polarity']}, "
                      f"Confidence: {result['confidence']}")
                print(f"     Crime Intensity: {result['crime_intensity']}")
            except Exception as e:
                print(f"[FAIL] Test {i}: {str(e)}")
                return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Sentiment analysis test failed: {e}")
        return False

def check_output_dirs():
    """Check if output directories exist or can be created."""
    print("\n" + "=" * 60)
    print("CHECKING OUTPUT DIRECTORIES")
    print("=" * 60)
    
    try:
        from train_model import OUTPUT_DIR
        from clean_data import DEFAULT_OUTPUT_DIR
        
        dirs = {
            "Model outputs": OUTPUT_DIR,
            "Data outputs": DEFAULT_OUTPUT_DIR,
            "Figures": OUTPUT_DIR / "figures",
            "Reports": OUTPUT_DIR / "sentiment_reports",
        }
        
        all_ok = True
        for name, path in dirs.items():
            if path.exists():
                print(f"[OK] {name:25} exists at {path}")
            else:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    print(f"[OK] {name:25} created at {path}")
                except Exception as e:
                    print(f"[FAIL] {name:25} cannot create: {e}")
                    all_ok = False
        
        return all_ok
    except Exception as e:
        print(f"[FAIL] Output directory check failed: {e}")
        return False

def check_data_files():
    """Check if necessary data files exist."""
    print("\n" + "=" * 60)
    print("CHECKING DATA FILES")
    print("=" * 60)
    
    try:
        from clean_data import DEFAULT_OUTPUT_DIR
        
        # Check for sentiment template
        template_file = DEFAULT_OUTPUT_DIR / "sentiment_text_template.csv"
        if template_file.exists():
            size = template_file.stat().st_size
            print(f"[OK] Sentiment template found: {size:,} bytes")
            # Count rows
            import pandas as pd
            df = pd.read_csv(template_file)
            print(f"     Rows: {len(df)}, Columns: {len(df.columns)}")
            return True
        else:
            print(f"[WARN] Sentiment template not found at {template_file}")
            return True  # Not a fatal error
    except Exception as e:
        print(f"[WARN] Data file check error: {e}")
        return True

def run_full_check():
    """Run all checks and summarize results."""
    print("\n\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "CRIMECAST PROJECT HEALTH CHECK" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Project Files", check_files),
        ("Module Imports", check_imports),
        ("Output Directories", check_output_dirs),
        ("Data Files", check_data_files),
        ("Sentiment Scoring", check_sentiment_scoring),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"\n[ERROR] {check_name} check failed: {e}")
            results[check_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for check_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {check_name}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print("\n" + "=" * 60)
    print(f"OVERALL: {passed}/{total} checks passed")
    print("=" * 60)
    
    if passed == total:
        print("\n[SUCCESS] Project is healthy and ready to use!")
        print("\nQuick start commands:")
        print("  python app.py              - Interactive menu")
        print("  python app.py --tn-district - Tamil Nadu analysis")
        print("  python sentiment_analysis.py - Run sentiment analysis")
        return 0
    else:
        print("\n[WARNING] Some checks failed. Review above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(run_full_check())
