# -*- coding: utf-8 -*-
"""
P3 — Data-quality asserts on ML-ready (and related outputs).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ML_READY = ROOT / "dataset" / "cleaned" / "crimecast_ml_ready.csv"
RAPE26 = ROOT / "model_outputs" / "rape_predictions_2026_all_districts.csv"
FITTED = ROOT / "model_outputs" / "fitted_predictions.csv"
METRICS = ROOT / "model_outputs" / "training_metrics.csv"


class TestMlReadyQualityP3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ML_READY.exists():
            raise unittest.SkipTest("crimecast_ml_ready.csv missing")
        cls.df = pd.read_csv(ML_READY)

    def test_not_empty(self):
        self.assertGreater(len(self.df), 10)

    def test_required_key_columns(self):
        for col in ("year", "district_city"):
            self.assertIn(col, self.df.columns)

    def test_years_in_sane_range(self):
        years = pd.to_numeric(self.df["year"], errors="coerce").dropna()
        self.assertTrue((years >= 2015).all())
        self.assertTrue((years <= 2030).all())

    def test_no_total_aggregate_rows(self):
        names = self.df["district_city"].astype(str).str.casefold()
        totals = names.str.contains(r"\btotal\b", regex=True, na=False)
        self.assertEqual(int(totals.sum()), 0, "ML-ready still has TOTAL aggregate rows")

    def test_crime_targets_present(self):
        wanted = [
            "murder_homicide_murder_rate",
            "murder_homicide_murder_incidence",
            "women_crimes_rape_sec_376_i",
            "complaints_total_complaints",
        ]
        present = [c for c in wanted if c in self.df.columns]
        self.assertGreaterEqual(len(present), 2, f"only found {present}")

    def test_targets_not_all_null(self):
        for col in (
            "murder_homicide_murder_rate",
            "women_crimes_rape_sec_376_i",
            "complaints_total_complaints",
        ):
            if col not in self.df.columns:
                continue
            s = pd.to_numeric(self.df[col], errors="coerce")
            self.assertGreater(int(s.notna().sum()), 0, f"{col} all null")

    def test_non_negative_counts_where_present(self):
        for col in (
            "murder_homicide_murder_incidence",
            "women_crimes_rape_sec_376_i",
            "complaints_total_complaints",
        ):
            if col not in self.df.columns:
                continue
            s = pd.to_numeric(self.df[col], errors="coerce").dropna()
            if s.empty:
                continue
            self.assertTrue((s >= 0).all(), f"negative values in {col}")

    def test_official_flag_if_present(self):
        if "is_official_year" not in self.df.columns:
            self.skipTest("no is_official_year column")
        flag = self.df["is_official_year"]
        # at least some official rows expected
        n_off = int(pd.to_numeric(flag, errors="coerce").fillna(0).astype(bool).sum())
        # also accept string true/false
        if n_off == 0:
            n_off = int(flag.astype(str).str.lower().isin(("1", "true", "yes")).sum())
        self.assertGreater(n_off, 0, "no official-year rows flagged")

    def test_district_name_nonempty(self):
        d = self.df["district_city"].astype(str).str.strip()
        self.assertFalse((d == "").any())
        self.assertFalse(d.str.lower().isin(("nan", "none")).any())

    def test_duplicate_year_district_documented(self):
        """Duplicates allowed for city vs district, but keys should not explode unbounded."""
        if "area_type" in self.df.columns:
            keys = ["year", "district_city", "area_type"]
        else:
            keys = ["year", "district_city"]
        n = len(self.df)
        n_unique = self.df.drop_duplicates(subset=keys).shape[0]
        # allow some dups but not majority
        self.assertGreaterEqual(n_unique / max(n, 1), 0.5)


class TestOutputQualityP3(unittest.TestCase):
    def test_training_metrics_best_models(self):
        if not METRICS.exists():
            self.skipTest("training_metrics.csv missing")
        m = pd.read_csv(METRICS)
        self.assertIn("target", m.columns)
        if "is_best" in m.columns:
            best = m[m["is_best"].astype(str).str.lower().isin(("true", "1", "yes"))]
            self.assertGreater(len(best), 0)

    def test_fitted_predictions_schema(self):
        if not FITTED.exists():
            self.skipTest("fitted_predictions.csv missing")
        f = pd.read_csv(FITTED, nrows=50)
        for col in ("district_city", "year", "target"):
            self.assertIn(col, f.columns)

    def test_rape_2026_non_negative(self):
        if not RAPE26.exists():
            self.skipTest("rape 2026 csv missing")
        r = pd.read_csv(RAPE26)
        vcol = (
            "predicted_2026_rape_incidents"
            if "predicted_2026_rape_incidents" in r.columns
            else "predicted_value"
        )
        if vcol not in r.columns:
            self.skipTest("no prediction column")
        s = pd.to_numeric(r[vcol], errors="coerce").dropna()
        self.assertTrue((s >= 0).all())

    def test_tn38_coverage_after_normalize(self):
        """After to_tn38 mapping, known junk should not dominate unique names."""
        if not ML_READY.exists():
            self.skipTest("ml ready missing")
        try:
            from district_entities import to_tn38, TN38
        except Exception:
            self.skipTest("district_entities unavailable")
        df = pd.read_csv(ML_READY)
        mapped = df["district_city"].astype(str).map(lambda x: to_tn38(x, default=None))
        known = mapped.dropna()
        if known.empty:
            self.skipTest("no mappable districts")
        # majority of mappable names should be in TN38
        in38 = known.isin(TN38).mean()
        self.assertGreaterEqual(in38, 0.7, f"only {in38:.0%} of mapped names in TN38")


if __name__ == "__main__":
    unittest.main(verbosity=2)
