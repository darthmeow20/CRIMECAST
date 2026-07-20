# -*- coding: utf-8 -*-
"""
P1 — Unit tests: fixtures, clean_data, blend_with_history, alert rules.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).resolve().parent / "fixtures"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestCleanDataP1(unittest.TestCase):
    def test_normalize_column_name_typos(self):
        from clean_data import normalize_column_name

        self.assertEqual(normalize_column_name("District/City"), "district_city")
        self.assertEqual(normalize_column_name("Muder Incidence"), "murder_incidence")
        self.assertIn("harassment", normalize_column_name("Harrassment Total"))

    def test_make_unique_columns(self):
        from clean_data import make_unique

        self.assertEqual(make_unique(["a", "a", "b"]), ["a", "a_2", "b"])

    def test_classify_area(self):
        from clean_data import classify_area

        self.assertEqual(classify_area("Railway Chennai"), "special_unit")
        self.assertEqual(classify_area("Madurai City"), "city")
        self.assertEqual(classify_area("Chennai"), "city")  # in CITY_UNITS
        self.assertEqual(classify_area("Dindigul"), "district")

    def test_extract_year_and_infer_name(self):
        from clean_data import extract_year, infer_dataset_name

        p = Path("tn_2023_total_complaints.csv")
        self.assertEqual(extract_year(p), 2023)
        self.assertEqual(infer_dataset_name(p), "complaints")
        self.assertEqual(infer_dataset_name(Path("tn_2022_muder_homicide.csv")), "murder_homicide")
        self.assertEqual(infer_dataset_name(Path("tn_2023_crimes_against_women.csv")), "women_crimes")

    def test_convert_numeric_columns(self):
        from clean_data import convert_numeric_columns

        df = pd.DataFrame(
            {
                "year": [2023, 2023],
                "district_city": ["A", "B"],
                "count": ["1,200", "-"],
            }
        )
        out = convert_numeric_columns(df)
        self.assertEqual(float(out.loc[0, "count"]), 1200.0)
        self.assertTrue(pd.isna(out.loc[1, "count"]))

    def test_clean_dataset_drops_total_rows(self):
        from clean_data import clean_dataset

        src = FIX / "mini_complaints_2023.csv"
        if not src.exists():
            self.skipTest("fixture missing")
        with tempfile.TemporaryDirectory() as tmp:
            df, profile = clean_dataset("complaints", src, Path(tmp), 2023)
            names = df["district_city"].astype(str).str.casefold().tolist()
            self.assertFalse(any("total" in n for n in names))
            self.assertGreaterEqual(profile.dropped_total_rows, 1)
            self.assertIn("year", df.columns)
            self.assertIn("area_type", df.columns)
            self.assertEqual(int(df["year"].iloc[0]), 2023)


class TestBlendHistoryP1(unittest.TestCase):
    def test_blend_none_history(self):
        from predict import _blend_with_history

        self.assertEqual(_blend_with_history(10.0, None, "murder_homicide_murder_rate"), 10.0)
        self.assertEqual(_blend_with_history(-5.0, None, "x"), 0.0)

    def test_blend_rate_weights_history_more(self):
        from predict import _blend_with_history

        # rate: w_hist=0.62, w_model=0.38 → closer to history
        model, hist = 10.0, 2.0
        blended = _blend_with_history(model, hist, "murder_homicide_murder_rate")
        expected = 0.38 * 10.0 + 0.62 * 2.0
        self.assertAlmostEqual(blended, expected, places=5)
        # closer to history than to model
        self.assertLess(abs(blended - hist), abs(blended - model))

    def test_blend_count_weights_model_more(self):
        from predict import _blend_with_history

        model, hist = 10.0, 2.0
        blended = _blend_with_history(model, hist, "murder_homicide_murder_incidence")
        expected = 0.65 * 10.0 + 0.35 * 2.0
        self.assertAlmostEqual(blended, expected, places=5)
        self.assertLess(abs(blended - model), abs(blended - hist))

    def test_blend_rape_r_is_rate(self):
        from predict import _blend_with_history

        # women_crimes_rape_r ends with _r → rate weights
        b = _blend_with_history(10.0, 0.0, "women_crimes_rape_r")
        self.assertAlmostEqual(b, 0.38 * 10.0, places=5)

    def test_blend_non_negative(self):
        from predict import _blend_with_history

        self.assertGreaterEqual(_blend_with_history(-100.0, -50.0, "rate"), 0.0)


class TestAlertRulesP1(unittest.TestCase):
    def test_thoothukudi_vs_madurai_high(self):
        # Avoid full dashboard import cost if streamlit missing
        try:
            from dashboard import compute_alert_rules
        except Exception as e:
            self.skipTest(f"dashboard import failed: {e}")

        ml = pd.DataFrame(
            {
                "district_city": ["Thoothukudi", "Madurai", "Chennai"],
                "year": [2023, 2023, 2023],
                "murder_homicide_murder_rate": [4.5, 2.0, 1.0],
            }
        )
        rape = pd.DataFrame(
            {
                "district": ["Salem", "Chennai"],
                "risk_level": ["HIGH", "LOW"],
                "rape_risk_index": [0.8, 0.1],
            }
        )
        # Empty news → skip spike rule (get_current_affairs_heat may still run)
        alerts = compute_alert_rules(ml, pd.DataFrame(), pd.DataFrame(), rape)
        levels = [a["level"] for a in alerts]
        titles = " ".join(a["title"] for a in alerts)
        self.assertIn("HIGH", levels)
        self.assertTrue(
            "Thoothukudi" in titles or "rape-risk" in titles.lower() or "HIGH" in titles
        )

    def test_no_alert_when_madurai_higher(self):
        try:
            from dashboard import compute_alert_rules
        except Exception as e:
            self.skipTest(f"dashboard import failed: {e}")

        ml = pd.DataFrame(
            {
                "district_city": ["Thoothukudi", "Madurai"],
                "year": [2023, 2023],
                "murder_homicide_murder_rate": [1.0, 3.0],
            }
        )
        rape = pd.DataFrame({"district": ["X"], "risk_level": ["LOW"], "rape_risk_index": [0.1]})
        alerts = compute_alert_rules(ml, pd.DataFrame(), pd.DataFrame(), rape)
        murder_alerts = [a for a in alerts if "Thoothukudi > Madurai" in a.get("title", "")]
        self.assertEqual(len(murder_alerts), 0)

    def test_high_rape_2026_alert(self):
        try:
            from dashboard import compute_alert_rules
        except Exception as e:
            self.skipTest(f"dashboard import failed: {e}")

        ml = pd.DataFrame(
            {
                "district_city": ["Chennai"],
                "year": [2023],
                "murder_homicide_murder_rate": [1.0],
            }
        )
        rape = pd.read_csv(FIX / "mini_rape_2026.csv") if (FIX / "mini_rape_2026.csv").exists() else pd.DataFrame(
            {"district": ["Salem"], "risk_level": ["HIGH"], "rape_risk_index": [0.9]}
        )
        alerts = compute_alert_rules(ml, pd.DataFrame(), pd.DataFrame(), rape)
        high_titles = [a["title"] for a in alerts if a["level"] == "HIGH"]
        self.assertTrue(any("2026" in t and "HIGH" in t for t in high_titles))


class TestTnMapNormalizeP1(unittest.TestCase):
    def test_aliases(self):
        from tn_map import _normalize_name

        self.assertEqual(_normalize_name("Madurai City"), "madurai")
        self.assertEqual(_normalize_name("Thoothukudi"), "thoothukkudi")
        self.assertEqual(_normalize_name("Trichy"), "tiruchirappalli")
        self.assertEqual(_normalize_name("Avadi"), "chennai")


if __name__ == "__main__":
    unittest.main(verbosity=2)
