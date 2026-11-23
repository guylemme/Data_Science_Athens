"""Reproduce the team's four Athens analyses from the original CSV.

Run: python analysis_pipeline.py data/athens_data.csv --output results/analysis.json
No synthetic observations or saved notebook outputs are substituted for the CSV.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from itertools import combinations
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def records(frame):
    """Input: DataFrame. Output: JSON-safe records (missing values become null)."""
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def load_data(file_path):
    """Input: CSV path. Output: cleaned DataFrame and original-data quality summary.

    Dates must be valid. Negative/infinite pollutant measurements become missing;
    tiny negative precipitation is clipped to zero, as in the team's notebook.
    No outlier concentration is removed merely because it is high.
    """
    frame = pd.read_csv(file_path)
    required = {"Date", "station_name", "PM2.5", "NO2", "Latitude", "Longitude",
                "Relative Humidity", "Temp", "Wind-Speed (U)", "Wind-Speed (V)"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")
    quality = {"rows": len(frame), "columns": len(frame.columns),
               "missing": {column: int(count) for column, count in frame.isna().sum().items()}}
    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise")
    if frame["Date"].isna().any() or frame["station_name"].isna().any():
        raise ValueError("Date and station_name must not contain missing values.")
    quality.update(date_min=frame["Date"].min().isoformat(),
                   date_max=frame["Date"].max().isoformat(),
                   stations=int(frame["station_name"].nunique()),
                   duplicate_station_timestamps=int(frame.duplicated(["station_name", "Date"]).sum()))
    for column in required - {"Date", "station_name"}:
        frame[column] = pd.to_numeric(frame[column], errors="raise").replace([np.inf, -np.inf], np.nan)
    quality["invalid_negative_pollutants"] = {}
    for column in ["PM2.5", "NO2"]:
        negative = frame[column] < 0
        quality["invalid_negative_pollutants"][column] = int(negative.sum())
        frame.loc[negative, column] = np.nan
    if "Total Percipitation" in frame:
        frame["Total Percipitation"] = frame["Total Percipitation"].clip(lower=0)
    if quality["duplicate_station_timestamps"]:
        raise ValueError("Duplicate station timestamps would inflate hourly counts; resolve them before analysis.")
    return frame, quality


def station_statistics(frame, threshold=25.0):
    """Input: hourly CSV DataFrame and exploratory PM2.5 threshold in µg/m³.

    Output: station averages, maxima, above-threshold observation counts and
    coordinates. The threshold is an analysis choice, not a regulatory claim.
    """
    result = frame.groupby("station_name").agg(
        pm25_mean=("PM2.5", "mean"), pm25_max=("PM2.5", "max"),
        no2_mean=("NO2", "mean"),
        pm25_exceedance_hours=("PM2.5", lambda values: (values > threshold).sum()),
        latitude=("Latitude", "first"), longitude=("Longitude", "first"),
    ).sort_values("pm25_mean", ascending=False).reset_index()
    return records(result)


def daily_environment(frame):
    """Input: hourly frame. Output: one daily mean per station and variable.

    Wind magnitude is computed hourly before averaging (not from mean vectors).
    """
    work = frame.assign(day=frame["Date"].dt.floor("D"),
                        Wind_Speed=np.hypot(frame["Wind-Speed (U)"], frame["Wind-Speed (V)"]))
    return work.groupby(["station_name", "day"]).agg(
        PM25=("PM2.5", "mean"), Humidity=("Relative Humidity", "mean"),
        Temperature=("Temp", "mean"), Wind_Speed=("Wind_Speed", "mean"),
    ).reset_index()


def apriori_supports(transactions, min_support=0.05, max_len=4):
    """Input: Boolean item columns, support and length bounds.

    Output: frequent itemsets mapped to their support. Implements Apriori's
    downward-closure pruning locally; no remote service or mlxtend is needed.
    """
    if transactions.empty:
        raise ValueError("No complete station-day transactions are available.")
    if not 0 < min_support <= 1 or max_len < 1:
        raise ValueError("Invalid support or maximum itemset length.")
    masks = {name: transactions[name].to_numpy(dtype=bool) for name in transactions}
    current = {frozenset([name]): float(mask.mean()) for name, mask in masks.items()
               if mask.mean() >= min_support}
    found = dict(current)
    for length in range(2, max_len + 1):
        previous = list(current)
        candidates = {left | right for left, right in combinations(previous, 2)
                      if len(left | right) == length}
        current = {}
        for candidate in candidates:
            if any(frozenset(subset) not in found for subset in combinations(candidate, length - 1)):
                continue
            support = float(np.logical_and.reduce([masks[item] for item in candidate]).mean())
            if support >= min_support:
                current[candidate] = support
        found.update(current)
        if not current:
            break
    return found


def frequent_patterns(daily, min_support=0.05, min_confidence=0.1):
    """Input: daily station means and mining bounds. Output: target rules, metadata.

    Low <= Q1; Medium is (Q1,Q3]; High > Q3. High is a relative dataset
    category, not a health threshold. Support=P(A and B), confidence=P(B|A),
    lift=P(B|A)/P(B). Associations do not establish causes.
    """
    columns = ["PM25", "Humidity", "Temperature", "Wind_Speed"]
    thresholds = daily[columns].quantile([0.25, 0.75])
    complete = daily.dropna(subset=columns).copy()
    category_columns = []
    for column in columns:
        q1, q3 = thresholds.loc[0.25, column], thresholds.loc[0.75, column]
        if not np.isfinite(q1) or not np.isfinite(q3) or q1 >= q3:
            raise ValueError(f"Cannot form three quartile categories for {column}.")
        name = column + "_Level"
        complete[name] = pd.cut(complete[column], [-np.inf, q1, q3, np.inf],
                                labels=["Low", "Medium", "High"])
        category_columns.append(name)
    transactions = pd.get_dummies(complete[category_columns], dtype=bool)
    supports = apriori_supports(transactions, min_support=min_support)
    rules = []
    rule_count = 0
    target = frozenset(["PM25_Level_High"])
    for itemset, support in supports.items():
        for length in range(1, len(itemset)):
            for subset in combinations(sorted(itemset), length):
                antecedent = frozenset(subset)
                consequent = itemset - antecedent
                confidence = support / supports[antecedent]
                if confidence >= min_confidence:
                    rule_count += 1
                    if consequent == target:
                        rules.append({"antecedents": sorted(antecedent),
                                      "consequent": "PM25_Level_High", "support": support,
                                      "confidence": confidence, "lift": confidence / supports[consequent]})
    rules.sort(key=lambda rule: (-rule["lift"], rule["antecedents"]))
    metadata = {"method": "Apriori", "transactions": len(complete),
                "removed_station_days": len(daily) - len(complete),
                "frequent_itemsets": len(supports), "total_rules": rule_count,
                "min_support": min_support, "min_confidence": min_confidence,
                "thresholds": {column: {"q1": float(thresholds.loc[0.25, column]),
                                         "q3": float(thresholds.loc[0.75, column])} for column in columns}}
    return rules, metadata


def forecast_daily_pm25(daily, test_days=30, forecast_days=30):
    """Input: daily station means and positive horizons. Output: history and forecasts.

    Network means weight each available station equally. Final test_days are
    excluded from fitting and training imputation. Holt-Winters uses additive
    damped trend and weekly additive seasonality. MAE/RMSE evaluate observed test
    days only. A final model is refitted on all history for future prediction.
    """
    series = daily.groupby("day")["PM25"].mean().sort_index().asfreq("D")
    if test_days < 1 or forecast_days < 1 or len(series) < test_days + 28:
        raise ValueError("Positive horizons and at least test_days + 28 history days are required.")
    train_raw, test = series.iloc[:-test_days], series.iloc[-test_days:]
    train = train_raw.ffill().bfill()
    if train.isna().any() or not test.notna().any():
        raise ValueError("Insufficient observed training or test values.")

    def fitted(values):
        """Input: regular daily series. Output: fitted weekly Holt-Winters model."""
        return ExponentialSmoothing(values, trend="add", damped_trend=True,
                                    seasonal="add", seasonal_periods=7,
                                    initialization_method="estimated").fit(optimized=True)

    prediction = fitted(train).forecast(test_days).clip(lower=0)
    evaluation = pd.DataFrame({"Date": test.index, "Observed": test.to_numpy(),
                               "Holt_Winters": prediction.to_numpy(),
                               "Seasonal_naive": np.resize(train.iloc[-7:].to_numpy(), test_days)})
    observed = evaluation.dropna(subset=["Observed"])
    metrics = [{"Model": name,
                "MAE": float(mean_absolute_error(observed["Observed"], observed[name])),
                "RMSE": float(np.sqrt(mean_squared_error(observed["Observed"], observed[name])))}
               for name in ["Holt_Winters", "Seasonal_naive"]]
    future = fitted(series.ffill().bfill()).forecast(forecast_days).clip(lower=0)
    return {"history": records(series.rename("Observed").rename_axis("Date").reset_index()),
            "evaluation": records(evaluation), "metrics": metrics,
            "future": records(future.rename("Predicted_PM25").rename_axis("Date").reset_index()),
            "training_end": train.index[-1].isoformat(), "test_start": test.index[0].isoformat(),
            "test_days": test_days, "forecast_days": forecast_days}


def spatial_clustering(frame, daily, eps_km=2.0, min_samples=3):
    """Input: hourly frame, daily means, DBSCAN radius in km and density bound.

    Output: station locations/labels and summaries excluding label -1 (noise).
    Clusters use geography only, not pollution similarity. Haversine inputs are
    radians and epsilon is divided by Earth's mean radius in kilometers.
    """
    if eps_km <= 0 or min_samples < 1:
        raise ValueError("DBSCAN radius and minimum samples must be positive.")
    valid = frame[frame["Latitude"].between(-90, 90) & frame["Longitude"].between(-180, 180)]
    if (valid.groupby("station_name")[["Latitude", "Longitude"]].nunique() > 1).any().any():
        raise ValueError("Some station names have multiple coordinates.")
    locations = valid[["station_name", "Latitude", "Longitude"]].drop_duplicates("station_name").rename(
        columns={"Latitude": "latitude", "Longitude": "longitude"})
    pollution = daily.groupby("station_name").agg(mean_PM25=("PM25", "mean"),
                                                  observed_days=("PM25", "count")).reset_index()
    stations = locations.merge(pollution, on="station_name", validate="one_to_one")
    if len(stations) < min_samples:
        raise ValueError("Not enough stations with valid coordinates for DBSCAN.")
    stations["cluster"] = DBSCAN(eps=eps_km / 6371.0088, min_samples=min_samples,
                                 metric="haversine", algorithm="ball_tree").fit_predict(
                                     np.radians(stations[["latitude", "longitude"]].to_numpy()))
    summary = stations[stations["cluster"] != -1].groupby("cluster").agg(
        number_of_stations=("station_name", "size"), mean_PM25=("mean_PM25", "mean"),
        min_station_PM25=("mean_PM25", "min"), max_station_PM25=("mean_PM25", "max"),
    ).sort_values("mean_PM25", ascending=False).reset_index()
    return {"stations": records(stations), "summary": records(summary),
            "noise_stations": int((stations["cluster"] == -1).sum()),
            "excluded_coordinate_stations": int(frame["station_name"].nunique() - len(stations)),
            "eps_km": eps_km, "min_samples": min_samples}


def main(file_path, output="results/analysis.json"):
    """Input: original CSV path and JSON destination. Output: complete result dict.

    All four analyses are run afresh; missing data files and computation errors
    propagate instead of falling back to demonstration or saved results.
    """
    source = Path(file_path)
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    frame, quality = load_data(source)
    daily = daily_environment(frame)
    rules, rules_metadata = frequent_patterns(daily)
    result = {"metadata": {"source": source.name, "source_sha256": digest.hexdigest(),
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                            "provenance": "Recomputed from original CSV",
                            "dataset": "Air Quality Monitoring in European Cities — Athens"},
              "quality": quality, "station_stats": station_statistics(frame),
              "rules": rules, "rules_metadata": rules_metadata,
              "temporal": forecast_daily_pm25(daily), "spatial": spatial_clustering(frame, daily)}
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Four analyses written to {destination} ({quality['rows']:,} original observations).")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Original athens_data.csv")
    parser.add_argument("--output", type=Path, default=Path("results/analysis.json"))
    args = parser.parse_args()
    main(args.csv, args.output)
