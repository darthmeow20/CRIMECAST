# Thin wrapper — real engine is predict_2026_rape_all_districts.py (FIXED-NO-SKLEARN-v4)
from predict_2026_rape_all_districts import (  # noqa: F401
    SCRIPT_VERSION,
    generate_rape_report,
    main,
    predict_2026_rape_all_districts,
)

if __name__ == "__main__":
    main()
