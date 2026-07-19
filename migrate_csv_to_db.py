# -*- coding: utf-8 -*-
"""
CRIMECAST — move main CSVs into SQLite (data/crimecast.db)

Does NOT delete CSVs (they remain as backup / export).
Dashboard loaders prefer DB, then fall back to CSV.

Usage:
  python migrate_csv_to_db.py
  python migrate_csv_to_db.py --list
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate CRIMECAST CSVs → SQLite")
    parser.add_argument("--list", action="store_true", help="List datasets already in DB")
    parser.add_argument("--no-structured", action="store_true", help="Skip news/alert structured sync")
    args = parser.parse_args()

    from db import (
        get_sqlite_path,
        list_datasets,
        migrate_csvs_to_db,
        init_db,
    )

    init_db()
    print("=" * 60)
    print("CRIMECAST CSV → SQLite")
    print("=" * 60)
    print(f"DB: {get_sqlite_path()}")

    if args.list:
        reg = list_datasets()
        if reg.empty:
            print("No datasets in registry yet. Run without --list first.")
        else:
            print(reg.to_string(index=False))
        return 0

    stats = migrate_csvs_to_db(also_structured=not args.no_structured)
    print()
    for name, info in stats.get("datasets", {}).items():
        st = info.get("status")
        if st == "ok":
            print(f"  [OK]   {name:22} {info.get('rows'):>6} rows · {info.get('cols')} cols")
        elif st == "skip":
            print(f"  [SKIP] {name:22} {info.get('reason')}")
        else:
            print(f"  [ERR]  {name:22} {info.get('error')}")

    if stats.get("structured"):
        print()
        print("Structured tables:", stats["structured"])
    if stats.get("errors"):
        print()
        print("Errors:")
        for e in stats["errors"]:
            print(" ", e)

    out = ROOT / "model_outputs" / "csv_migrate_report.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(stats, indent=2, default=str), encoding="utf-8")
        print()
        print(f"Report → {out}")
    except Exception:
        pass

    print()
    print("Done. CSVs kept on disk. Dashboard reads DB first.")
    print("Re-run this script after refreshing news or re-training.")
    print("=" * 60)
    return 1 if stats.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
