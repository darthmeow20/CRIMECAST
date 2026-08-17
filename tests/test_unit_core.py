# -*- coding: utf-8 -*-
"""
CRIMECAST unit tests — core logic (no Streamlit UI, no network).

Run:
  py -3 -m unittest discover -s tests -p "test_*.py" -v
  or:  RUN_TESTS.bat
"""
from __future__ import annotations

import math
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestDistrictEntities(unittest.TestCase):
    def test_tn38_count(self):
        from district_entities import TN38

        self.assertEqual(len(TN38), 38)
        self.assertIn("Chennai", TN38)
        self.assertIn("Madurai", TN38)

    def test_city_to_parent(self):
        from district_entities import to_tn38, parent_district

        self.assertEqual(to_tn38("Madurai City"), "Madurai")
        self.assertEqual(to_tn38("Avadi"), "Chennai")
        self.assertEqual(to_tn38("Tambaram"), "Chennai")
        self.assertEqual(to_tn38("Salem City"), "Salem")
        self.assertEqual(parent_district("Trichy City"), "Tiruchirappalli")

    def test_aliases(self):
        from district_entities import to_tn38

        self.assertEqual(to_tn38("Kanyakumari"), "Kanniyakumari")
        self.assertEqual(to_tn38("Thoothukudi"), "Thoothukkudi")
        self.assertEqual(to_tn38("Villupuram"), "Viluppuram")
        self.assertEqual(to_tn38("Nilgiris"), "The Nilgiris")

    def test_junk_returns_none(self):
        from district_entities import to_tn38

        self.assertIsNone(to_tn38("Cyber Cell", default=None))
        self.assertIsNone(to_tn38("Other Units", default=None))
        self.assertIsNone(to_tn38("Railway Chennai", default=None))

    def test_population_estimate(self):
        from district_entities import estimate_population_lakhs

        ch = estimate_population_lakhs("Chennai")
        self.assertIsNotNone(ch)
        self.assertGreater(float(ch), 10.0)


class TestForecastEngine(unittest.TestCase):
    def test_forecast_band_single_point(self):
        from forecast_engine import _forecast_band

        low, mid, high = _forecast_band([2023], [10.0], 2026)
        self.assertEqual(mid, 10.0)
        self.assertLessEqual(low, mid)
        self.assertGreaterEqual(high, mid)

    def test_forecast_band_linear(self):
        from forecast_engine import _forecast_band

        years = [2022, 2023]
        vals = [10.0, 12.0]
        low, mid, high = _forecast_band(years, vals, 2024)
        self.assertTrue(math.isfinite(mid))
        self.assertGreaterEqual(mid, 0.0)
        self.assertLessEqual(low, mid)
        self.assertGreaterEqual(high, mid)

    def test_forecast_band_empty(self):
        from forecast_engine import _forecast_band

        low, mid, high = _forecast_band([], [], 2026)
        self.assertEqual((low, mid, high), (0.0, 0.0, 0.0))

    def test_methods_constant(self):
        from forecast_engine import METHODS, FORECAST_TARGETS

        self.assertIn("linear", METHODS)
        self.assertIn("last_year", METHODS)
        self.assertIn("blend", METHODS)
        self.assertIn("rape_incidents", FORECAST_TARGETS)
        self.assertIn("murder_incidence", FORECAST_TARGETS)

    def test_forecast_districts_runs(self):
        """Integration-lite: runs if fitted_predictions exists."""
        from forecast_engine import FITTED, forecast_districts

        if not FITTED.exists():
            self.skipTest("fitted_predictions.csv missing")
        df = forecast_districts("rape_incidents", method="linear", target_year=2026, save=False)
        self.assertFalse(df.empty)
        self.assertIn("district", df.columns)
        self.assertIn("predicted_value", df.columns)
        # TN38-ish count
        self.assertGreaterEqual(len(df), 30)
        self.assertLessEqual(len(df), 45)
        self.assertTrue((df["predicted_value"] >= 0).all())

    def test_last_year_vs_linear_columns(self):
        from forecast_engine import FITTED, forecast_districts

        if not FITTED.exists():
            self.skipTest("fitted_predictions.csv missing")
        a = forecast_districts("rape_incidents", method="last_year", target_year=2026, save=False)
        b = forecast_districts("rape_incidents", method="linear", target_year=2026, save=False)
        self.assertEqual(set(a.columns), set(b.columns))
        self.assertIn("forecast_method", a.columns)

    def test_backtest_shape(self):
        from forecast_engine import FITTED, backtest_year

        if not FITTED.exists():
            self.skipTest("fitted_predictions.csv missing")
        df = backtest_year("women_crimes_rape_sec_376_i", holdout_year=2024, max_districts=20)
        # may be empty if no holdout actuals — still must be DataFrame
        self.assertIsNotNone(df)
        if not df.empty:
            self.assertIn("district", df.columns)
            self.assertIn("predicted", df.columns)


class TestSentimentWordclouds(unittest.TestCase):
    def test_tokenize_filters_stopwords(self):
        from sentiment_wordclouds import tokenize

        toks = tokenize("The police arrested a thief in the city today")
        self.assertNotIn("the", toks)
        self.assertNotIn("in", toks)
        self.assertTrue(any(t in toks for t in ("police", "arrested", "thief", "city")))

    def test_tokenize_keeps_tamil(self):
        from sentiment_wordclouds import tokenize, has_tamil

        text = "சென்னையில் போலீஸ் கைது — police arrest case"
        toks = tokenize(text)
        self.assertTrue(any(has_tamil(t) for t in toks), f"expected Tamil tokens, got {toks}")
        self.assertIn("police", toks)
        self.assertIn("arrest", toks)
        self.assertNotIn("ஒரு", toks)  # stopword if present alone only

    def test_balance_lang_keeps_english_and_tamil(self):
        from collections import Counter
        from sentiment_wordclouds import balance_lang_frequencies, lang_counts

        # Many Tamil tokens would dominate plain most_common(10)
        raw = Counter()
        for i in range(20):
            raw[f"தமிழ்சொல்{i}"] = 10
        raw.update({"police": 3, "arrest": 3, "murder": 2, "court": 2, "crime": 1})
        bal = balance_lang_frequencies(raw, top_n=12, lang_mode="both")
        lc = lang_counts(bal)
        self.assertGreaterEqual(lc["english"], 3, msg=f"EN under-represented: {bal}")
        self.assertGreaterEqual(lc["tamil"], 3, msg=f"TA under-represented: {bal}")

    def test_word_freq(self):
        from sentiment_wordclouds import word_freq_for_district, collect_district_texts
        import pandas as pd

        raw = pd.DataFrame(
            {
                "district": ["Chennai", "Chennai", "Madurai"],
                "headline": [
                    "Murder case police arrest Chennai",
                    "Police patrol improved safety Chennai",
                    "Madurai court hearing crime",
                ],
            }
        )
        texts = collect_district_texts(raw, None, None)
        ctr = word_freq_for_district(texts, "Chennai", top_n=20)
        self.assertGreater(sum(ctr.values()), 0)

    def test_freq_dataframe(self):
        from collections import Counter
        from sentiment_wordclouds import freq_dataframe

        fdf = freq_dataframe(Counter({"crime": 3, "police": 2}), top_n=5)
        self.assertIn("word", fdf.columns)
        self.assertIn("count", fdf.columns)
        self.assertEqual(len(fdf), 2)

    def test_make_wordcloud_image_returns_or_errors_cleanly(self):
        from collections import Counter
        from sentiment_wordclouds import make_wordcloud_image, ensure_tamil_font

        font = ensure_tamil_font(force_download=False)
        img, err = make_wordcloud_image(
            Counter({"police": 5, "arrest": 3, "கைது": 4}),
            return_error=True,
        )
        # On Windows, Nirmala should produce an image; elsewhere download/system may apply
        if font:
            self.assertIsNotNone(img, msg=f"expected image with font={font}, err={err}")
            self.assertTrue(hasattr(img, "size"))
            self.assertGreater(img.size[0], 10)
        elif img is None:
            self.assertTrue(err and len(str(err)) > 3)


class TestRiskExplain(unittest.TestCase):
    def test_composite_risk_factors(self):
        from risk_explain import composite_risk_factors

        card = {
            "district": "Test",
            "murder_rate": 5.0,
            "rape_rate": 2.0,
            "news_90d": 20.0,
            "forecast_2026_rape": 15.0,
            "rape_risk_index": 0.5,
            "sentiment_polarity": -0.4,
        }
        meds = {
            "murder_rate": 2.0,
            "rape_rate": 1.0,
            "news_90d": 10.0,
            "forecast_2026_rape": 8.0,
        }
        df = composite_risk_factors("Test", card, state_medians=meds)
        self.assertFalse(df.empty)
        self.assertIn("risk_push", df.columns)
        self.assertIn("factor", df.columns)

    def test_composite_empty_card(self):
        from risk_explain import composite_risk_factors

        df = composite_risk_factors("X", {})
        # may still have risk index missing — empty ok
        self.assertIsNotNone(df)


class TestDbDatasetStore(unittest.TestCase):
    def test_save_load_dataset_table(self):
        import pandas as pd
        from db import save_dataset_table, load_dataset_table, init_db, get_sqlite_path

        init_db()
        # use unique name so we don't wipe prod tables badly
        name = "_unit_test_tiny"
        df = pd.DataFrame({"district": ["A", "B"], "value": [1.0, 2.0]})
        n = save_dataset_table(name, df)
        self.assertEqual(n, 2)
        loaded = load_dataset_table(name)
        self.assertEqual(len(loaded), 2)
        self.assertIn("district", loaded.columns)
        self.assertTrue(get_sqlite_path().exists())


class TestNormalize2026(unittest.TestCase):
    def test_normalize_rolls_cities(self):
        import pandas as pd

        # Import normalize from dashboard may pull streamlit — use forecast path instead
        try:
            from predict_2026_rape_all_districts import _normalize_to_tn38_df
        except Exception:
            self.skipTest("predict_2026 normalize helper unavailable")

        raw = pd.DataFrame(
            {
                "district": ["Madurai City", "Madurai", "Salem City", "Cyber Cell"],
                "predicted_2026_rape_incidents": [10.0, 5.0, 8.0, 99.0],
                "pred_low": [8.0, 4.0, 6.0, 1.0],
                "pred_high": [12.0, 6.0, 10.0, 2.0],
            }
        )
        out = _normalize_to_tn38_df(raw)
        self.assertFalse(out.empty)
        self.assertIn("district", out.columns)
        # Madurai should be rolled (city+district)
        m = out[out["district"] == "Madurai"]
        if not m.empty and "predicted_2026_rape_incidents" in m.columns:
            self.assertGreaterEqual(float(m.iloc[0]["predicted_2026_rape_incidents"]), 10.0)
        # junk dropped from TN38 list
        self.assertNotIn("Cyber Cell", out["district"].astype(str).tolist())


class TestPredictHelpers(unittest.TestCase):
    def test_resolve_target_aliases(self):
        from predict import resolve_target

        self.assertEqual(resolve_target("murder"), "murder_homicide_murder_incidence")
        self.assertEqual(resolve_target("rape"), "women_crimes_rape_sec_376_i")
        self.assertEqual(resolve_target("murder_rate"), "murder_homicide_murder_rate")

    def test_resolve_target_invalid(self):
        from predict import resolve_target

        with self.assertRaises(ValueError):
            resolve_target("not_a_real_target_xyz")

    def test_series_to_feature_frame(self):
        import pandas as pd
        from predict import series_to_feature_frame

        row = pd.Series({"a": 1.0, "b": "x", "c": None})
        frame = series_to_feature_frame(row, ["a", "b", "c", "missing"])
        self.assertEqual(len(frame), 1)
        self.assertEqual(list(frame.columns), ["a", "b", "c", "missing"])
        self.assertEqual(float(frame.iloc[0]["a"]), 1.0)
        self.assertEqual(float(frame.iloc[0]["missing"]), 0.0)


class TestHealthCheck(unittest.TestCase):
    def test_run_health_check_structure(self):
        from health_check import run_health_check

        report = run_health_check()
        self.assertIn("overall", report)
        self.assertIn("checks", report)
        self.assertIsInstance(report["checks"], list)
        self.assertGreater(len(report["checks"]), 0)
        for c in report["checks"]:
            self.assertIn(c["status"], ("ok", "warn", "fail"))


class TestProjectLayout(unittest.TestCase):
    def test_critical_files_exist(self):
        needed = [
            "dashboard.py",
            "predict.py",
            "train_model.py",
            "clean_data.py",
            "district_entities.py",
            "forecast_engine.py",
            "db.py",
            "risk_explain.py",
            "sentiment_wordclouds.py",
            "predict_2026_rape_all_districts.py",
            "requirements.txt",
        ]
        for name in needed:
            self.assertTrue((ROOT / name).exists(), f"missing {name}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
