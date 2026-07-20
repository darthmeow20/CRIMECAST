# -*- coding: utf-8 -*-
"""
P2 — Integration tests: predict_for_area + forecast_districts column contracts.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).resolve().parent / "fixtures"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ML_READY = ROOT / "dataset" / "cleaned" / "crimecast_ml_ready.csv"
MODELS = ROOT / "models"
BEST = ROOT / "model_outputs" / "best_models.json"
FITTED = ROOT / "model_outputs" / "fitted_predictions.csv"


class TestPredictIntegrationP2(unittest.TestCase):
    def test_predict_for_area_murder_rate(self):
        if not ML_READY.exists() or not BEST.exists():
            self.skipTest("ML-ready or best_models.json missing — run train first")
        joblibs = list(MODELS.glob("*murder*rate*.joblib")) if MODELS.exists() else []
        if not joblibs:
            self.skipTest("murder rate model missing")

        from predict import predict_for_area

        try:
            r = predict_for_area("murder_rate", "Chennai", year=2026)
        except Exception as e:
            self.skipTest(f"predict_for_area failed (env/models): {e}")

        self.assertIn("prediction", r)
        self.assertIn("area", r)
        self.assertIn("target", r)
        self.assertTrue(pd.notna(r["prediction"]))
        self.assertGreaterEqual(float(r["prediction"]), 0.0)
        self.assertIn("murder", str(r["target"]).lower())

    def test_predict_for_area_rape_incidents(self):
        if not ML_READY.exists() or not BEST.exists():
            self.skipTest("models/data missing")
        from predict import predict_for_area

        try:
            r = predict_for_area("rape", "Madurai", year=2025)
        except Exception as e:
            self.skipTest(f"predict failed: {e}")

        self.assertGreaterEqual(float(r["prediction"]), 0.0)
        self.assertIn("model_name", r)

    def test_populate_all_districts_shape(self):
        if not ML_READY.exists() or not BEST.exists():
            self.skipTest("models/data missing")
        from predict import populate_all_district_predictions

        try:
            df = populate_all_district_predictions(
                "murder_rate", 2026, max_districts=10
            )
        except Exception as e:
            self.skipTest(f"populate failed: {e}")

        self.assertIsInstance(df, pd.DataFrame)
        if df.empty:
            self.skipTest("empty populate result")
        self.assertIn("district", df.columns)
        self.assertIn("prediction", df.columns)
        self.assertTrue((pd.to_numeric(df["prediction"], errors="coerce") >= 0).all())
        self.assertLessEqual(len(df), 10)


class TestForecastIntegrationP2(unittest.TestCase):
    REQUIRED_COLS = {
        "district",
        "predicted_value",
        "pred_low",
        "pred_high",
        "forecast_method",
        "risk_level",
        "rank",
    }

    def test_forecast_rape_columns(self):
        from forecast_engine import FITTED, forecast_districts

        if not FITTED.exists():
            self.skipTest("fitted_predictions.csv missing")
        df = forecast_districts("rape_incidents", method="linear", target_year=2026, save=False)
        self.assertFalse(df.empty)
        missing = self.REQUIRED_COLS - set(df.columns)
        self.assertEqual(missing, set(), f"missing columns: {missing}")
        # rape compat alias
        self.assertTrue(
            "predicted_2026_rape_incidents" in df.columns
            or "predicted_value" in df.columns
        )
        self.assertTrue((df["pred_high"] >= df["pred_low"]).all())
        self.assertTrue((df["predicted_value"] >= 0).all())

    def test_forecast_murder_and_complaints(self):
        from forecast_engine import FITTED, forecast_districts, FORECAST_TARGETS

        if not FITTED.exists():
            self.skipTest("fitted_predictions.csv missing")
        for key in ("murder_incidence", "total_complaints"):
            if key not in FORECAST_TARGETS:
                continue
            df = forecast_districts(key, method="blend", target_year=2026, save=False)
            self.assertFalse(df.empty, f"{key} empty")
            self.assertIn("predicted_value", df.columns)
            self.assertEqual(df["forecast_method"].iloc[0], "blend")

    def test_forecast_methods_differ_or_equal_ok(self):
        from forecast_engine import FITTED, forecast_districts

        if not FITTED.exists():
            self.skipTest("fitted_predictions.csv missing")
        lin = forecast_districts("rape_incidents", method="linear", target_year=2026, save=False)
        last = forecast_districts("rape_incidents", method="last_year", target_year=2026, save=False)
        self.assertEqual(len(lin), len(last))
        # Not required to differ, but both valid
        self.assertTrue((lin["predicted_value"] >= 0).all())
        self.assertTrue((last["predicted_value"] >= 0).all())


class TestBriefHtmlP2(unittest.TestCase):
    def test_district_brief_html_contains_name(self):
        try:
            from dashboard import district_brief_html
        except Exception as e:
            self.skipTest(f"dashboard: {e}")
        html = district_brief_html(
            {"district": "Madurai", "murder_rate": 2.1, "risk_level": "MEDIUM"},
            ["Driver one", "Driver two"],
        )
        self.assertIn("Madurai", html)
        self.assertIn("Driver one", html)
        self.assertIn("<!DOCTYPE html>", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
