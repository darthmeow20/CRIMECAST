# -*- coding: utf-8 -*-
"""
CRIMECAST test runner (Python — no .bat needed).

Usage (from project root):
  python run_tests.py
  python run_tests.py -v
  python run_tests.py tests.test_p1_unit_clean_blend_alerts
  python run_tests.py --list

Exit code 0 = success (skips allowed).
"""
from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CRIMECAST unit / integration tests")
    parser.add_argument(
        "modules",
        nargs="*",
        help="Optional test module(s), e.g. tests.test_p1_unit_clean_blend_alerts",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=True,
        help="Verbose output (default on)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Less output",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List discovered tests and exit",
    )
    parser.add_argument(
        "-k",
        "--pattern",
        default="test_*.py",
        help="Test file pattern under tests/ (default: test_*.py)",
    )
    args = parser.parse_args(argv)

    verbosity = 1 if args.quiet else 2
    tests_dir = ROOT / "tests"

    print("=" * 60)
    print("CRIMECAST tests  P0–P4")
    print("=" * 60)
    print(f"Root:  {ROOT}")
    print(f"Tests: {tests_dir}")
    print()

    if args.modules:
        suite = unittest.defaultTestLoader.loadTestsFromNames(args.modules)
    else:
        suite = unittest.defaultTestLoader.discover(
            start_dir=str(tests_dir),
            pattern=args.pattern,
            top_level_dir=str(ROOT),
        )

    if args.list:
        count = suite.countTestCases()
        print(f"Discovered {count} test case(s):\n")
        _print_suite(suite)
        return 0

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    print()
    print("-" * 60)
    print(
        f"Ran {result.testsRun} test(s)  |  "
        f"failures={len(result.failures)}  "
        f"errors={len(result.errors)}  "
        f"skipped={len(result.skipped)}"
    )
    if result.wasSuccessful():
        print("RESULT: OK")
    else:
        print("RESULT: FAILED")
    print("-" * 60)
    print("Manual UI checklist: docs/MANUAL_UI_CHECKLIST.md")
    print("=" * 60)

    return 0 if result.wasSuccessful() else 1


def _print_suite(suite: unittest.TestSuite, indent: int = 0) -> None:
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            _print_suite(test, indent)
        else:
            print("  " * indent + str(test))


if __name__ == "__main__":
    raise SystemExit(main())
