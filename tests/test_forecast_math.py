# -*- coding: utf-8 -*-
"""Focused math tests for forecast uncertainty band."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestForecastMath(unittest.TestCase):
    def test_non_negative_mid(self):
        from forecast_engine import _forecast_band

        low, mid, high = _forecast_band([2020, 2021, 2022], [100, 50, 10], 2026)
        self.assertGreaterEqual(mid, 0.0)
        self.assertGreaterEqual(low, 0.0)
        self.assertGreaterEqual(high, mid)

    def test_flat_series(self):
        from forecast_engine import _forecast_band

        low, mid, high = _forecast_band([2021, 2022, 2023], [5, 5, 5], 2026)
        self.assertAlmostEqual(mid, 5.0, places=5)
        self.assertTrue(math.isfinite(low) and math.isfinite(high))

    def test_increasing_trend_mid_above_last(self):
        from forecast_engine import _forecast_band

        # Strong upward trend → mid for 2024 should be above last (~12)
        _, mid, _ = _forecast_band([2021, 2022, 2023], [8, 10, 12], 2024)
        self.assertGreater(mid, 11.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
