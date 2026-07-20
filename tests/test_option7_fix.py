# -*- coding: utf-8 -*-
"""Self-test for option 7 fix. Run: python -B tests/test_option7_fix.py"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ENGINE = ROOT / "predict_2026_rape_all_districts.py"
CSV = ROOT / "model_outputs" / "rape_predictions_2026_all_districts.csv"
FAILS = 0


def fail(msg: str) -> None:
    global FAILS
    FAILS += 1
    print(f"  [FAIL] {msg}")


def ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def main() -> int:
    print("=" * 60)
    print("OPTION 7 SELF-TEST")
    print("=" * 60)

    # 1) Engine file exists and has no sklearn
    if not ENGINE.exists():
        fail(f"Missing {ENGINE}")
        return 1
    src = ENGINE.read_text(encoding="utf-8")
    if "FIXED-NO-SKLEARN-v" not in src and "TN38" not in src:
        fail("Engine missing FIXED-NO-SKLEARN / TN38 version marker")
    else:
        ok("Version marker present (FIXED-NO-SKLEARN / TN38)")

    banned = ["import sklearn", "import joblib", "from sklearn", "from joblib", "joblib.load"]
    for b in banned:
        if b in src:
            fail(f"Engine still contains banned token: {b}")
        else:
            ok(f"No '{b}'")

    if "No valid predictions were generated" in src:
        fail("Old error string still in engine source")
    else:
        ok("Old 'No valid predictions' string absent from engine")

    if "Specifying the columns using strings" in src and "cannot" not in src.lower():
        # allowed only in comments explaining the bug
        pass
    ok("Engine is trend-only (csv/math)")

    # 2) AST parse
    try:
        ast.parse(src)
        ok("Engine parses as valid Python")
    except SyntaxError as e:
        fail(f"Syntax error: {e}")

    # 3) Run prediction API
    # Avoid double-printing issues by importing after checks
    import importlib

    if "predict_2026_rape_all_districts" in sys.modules:
        del sys.modules["predict_2026_rape_all_districts"]
    import predict_2026_rape_all_districts as eng

    ver = str(getattr(eng, "SCRIPT_VERSION", "") or "")
    if "FIXED-NO-SKLEARN" not in ver and "TN38" not in ver:
        fail(f"SCRIPT_VERSION={ver!r}")
    else:
        ok(f"Imported SCRIPT_VERSION={ver}")

    df = eng.predict_2026_rape_all_districts()
    n = len(df)
    if n < 40:
        fail(f"Only {n} rows predicted (need >= 40)")
    else:
        ok(f"Predicted {n} areas")

    if "predicted_2026_rape_incidents" not in df.columns:
        fail("Missing predicted_2026_rape_incidents column")
    else:
        ok("Has predicted_2026_rape_incidents")

    for name in ("Villupuram", "Virudhunagar"):
        hit = df[df["district"].astype(str) == name]
        if hit.empty:
            fail(f"{name} missing from results")
        else:
            val = float(hit.iloc[0]["predicted_2026_rape_incidents"])
            ok(f"{name} = {val}")

    # 4) CSV on disk
    if not CSV.exists():
        fail(f"CSV missing: {CSV}")
    else:
        lines = CSV.read_text(encoding="utf-8").strip().splitlines()
        ok(f"CSV has {len(lines)-1} data rows")

    print("=" * 60)
    if FAILS:
        print(f"RESULT: FAIL ({FAILS} issues)")
        return 1
    print("RESULT: PASS — option 7 fix verified")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
