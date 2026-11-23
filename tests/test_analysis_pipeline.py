"""Small synthetic checks of analytical invariants; these are not project results."""
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from analysis_pipeline import apriori_supports, forecast_daily_pm25, spatial_clustering


class AnalysisTests(unittest.TestCase):
    def test_apriori_joint_support_and_pruning(self):
        transactions = pd.DataFrame({"A": [1, 1, 0, 0], "B": [1, 0, 1, 0],
                                     "C": [0, 0, 0, 1]}, dtype=bool)
        supports = apriori_supports(transactions, min_support=0.25)
        self.assertEqual(supports[frozenset(["A", "B"])], 0.25)
        self.assertNotIn(frozenset(["A", "C"]), supports)
        self.assertNotIn(frozenset(["A", "B", "C"]), supports)

    def test_forecast_test_values_cannot_leak_into_training(self):
        days = pd.date_range("2020-01-01", periods=65, freq="D")
        baseline = np.arange(65, dtype=float) + 10
        baseline[5] = np.nan
        baseline[-3:] = [10000, 20000, 30000]
        daily = pd.DataFrame({"day": days, "station_name": "fixture", "PM25": baseline})
        fitted_inputs = []

        class FakeModel:
            def __init__(self, values, **kwargs):
                fitted_inputs.append(values.copy())
                self.values = values

            def fit(self, **kwargs):
                return self

            def forecast(self, horizon):
                index = pd.date_range(self.values.index[-1] + pd.Timedelta(days=1), periods=horizon)
                return pd.Series(np.repeat(self.values.iloc[-1], horizon), index=index)

        with patch("analysis_pipeline.ExponentialSmoothing", FakeModel):
            result = forecast_daily_pm25(daily, test_days=3, forecast_days=4)
        self.assertEqual(len(fitted_inputs), 2)
        self.assertEqual(len(fitted_inputs[0]), 62)
        self.assertLess(fitted_inputs[0].max(), 10000)
        self.assertEqual(fitted_inputs[0].iloc[5], fitted_inputs[0].iloc[4])
        self.assertEqual(fitted_inputs[1].max(), 30000)
        self.assertEqual(result["evaluation"][0]["Observed"], 10000)
        self.assertEqual(result["evaluation"][0]["Seasonal_naive"], baseline[55])
        self.assertEqual(len(result["future"]), 4)

    def test_dbscan_uses_kilometers_not_degrees(self):
        # Three stations within 0.2 km; a fourth roughly 11 km away.
        frame = pd.DataFrame({"station_name": ["a", "b", "c", "far"],
                              "Latitude": [38.0, 38.001, 38.002, 38.1],
                              "Longitude": [23.7] * 4})
        daily = pd.DataFrame({"station_name": frame["station_name"], "PM25": [1., 2., 3., 50.]})
        result = spatial_clustering(frame, daily, eps_km=2, min_samples=3)
        labels = {station["station_name"]: station["cluster"] for station in result["stations"]}
        self.assertEqual(labels["a"], labels["c"])
        self.assertNotEqual(labels["a"], -1)
        self.assertEqual(labels["far"], -1)
        self.assertEqual(result["noise_stations"], 1)
        self.assertEqual(result["summary"][0]["mean_PM25"], 2.)


if __name__ == "__main__":
    unittest.main()
