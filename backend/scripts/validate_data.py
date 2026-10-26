"""Validation script for cached January 2026 Elexon BMRS dataset.
Runs a strict audit of data integrity, unit conversions, timestamp semantics,
and historical replay feasibility.
"""

import datetime
import os
import sys
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "data", "jan2026.parquet")


def validate_dataset(path: str = DATA_PATH):
    print("=" * 60)
    print("ELEXON BMRS DATASET VALIDATION & AUDIT")
    print(f"Target file: {path}")
    print("=" * 60)

    if not os.path.exists(path):
        print(f"ERROR: Dataset file not found at {path}")
        sys.exit(1)

    file_size_kb = os.path.getsize(path) / 1024.0
    print(f"File exists: {path} ({file_size_kb:.2f} KB)")

    df = pd.read_parquet(path)
    print(f"Total records in parquet: {len(df):,}")

    # 1. Schema check
    expected_cols = {"record_type", "interval_start", "publish_time", "generation_mw", "generation_gw"}
    actual_cols = set(df.columns)
    missing_cols = expected_cols - actual_cols
    if missing_cols:
        print(f"ERROR: Missing expected columns: {missing_cols}")
        sys.exit(1)
    print("Schema check: PASS (All expected columns present)")

    # 2. Timezone checks
    if df["interval_start"].dt.tz is None:
        print("ERROR: interval_start is not timezone-aware UTC")
        sys.exit(1)
    if df["publish_time"].dt.tz is None:
        print("ERROR: publish_time is not timezone-aware UTC")
        sys.exit(1)
    print("Timezone check: PASS (All timestamps are UTC)")

    # 3. Unit conversion check
    diff = (df["generation_gw"] - (df["generation_mw"] / 1000.0)).abs().max()
    if diff > 1e-6:
        print(f"ERROR: GW conversion mismatch (max diff: {diff})")
        sys.exit(1)
    print("Unit conversion check: PASS (generation_gw == generation_mw / 1000.0)")

    # 4. Actuals check (FUELHH)
    actuals = df[df["record_type"] == "actual"].copy()
    print(f"\n--- ACTUALS (FUELHH WIND) ---")
    print(f"Total actual intervals: {len(actuals)}")
    if len(actuals) != 31 * 48:
        print(f"ERROR: Expected 1,488 actual intervals (31 days * 48 SP), found {len(actuals)}")
        sys.exit(1)

    # Check for negatives and NaNs
    if actuals["generation_mw"].isnull().any():
        print("ERROR: Null values found in actuals generation")
        sys.exit(1)
    if (actuals["generation_mw"] < 0).any():
        print("ERROR: Negative generation found in actuals")
        sys.exit(1)

    min_act = actuals["generation_gw"].min()
    max_act = actuals["generation_gw"].max()
    mean_act = actuals["generation_gw"].mean()
    print(f"Generation range: {min_act:.3f} GW to {max_act:.3f} GW (Mean: {mean_act:.3f} GW)")

    # Check each day has exactly 48 intervals
    day_counts = actuals.groupby(actuals["interval_start"].dt.date).size()
    if len(day_counts) != 31:
        print(f"ERROR: Expected 31 unique dates, got {len(day_counts)}")
        sys.exit(1)
    anomalous_days = day_counts[day_counts != 48]
    if len(anomalous_days) > 0:
        print(f"ERROR: Found days with != 48 intervals: {anomalous_days.to_dict()}")
        sys.exit(1)
    print("Actual daily coverage: PASS (All 31 days have exactly 48 half-hours)")

    # 5. Forecasts check (WINDFOR)
    forecasts = df[df["record_type"] == "forecast"].copy()
    print(f"\n--- FORECASTS (WINDFOR) ---")
    print(f"Total forecast vintage intervals: {len(forecasts):,}")
    unique_pub_times = forecasts["publish_time"].nunique()
    print(f"Unique forecast publication timestamps: {unique_pub_times}")

    # Check for negatives and NaNs
    if forecasts["generation_mw"].isnull().any():
        print("ERROR: Null values found in forecasts generation")
        sys.exit(1)
    if (forecasts["generation_mw"] < 0).any():
        print("ERROR: Negative generation found in forecasts")
        sys.exit(1)

    min_fc = forecasts["generation_gw"].min()
    max_fc = forecasts["generation_gw"].max()
    mean_fc = forecasts["generation_gw"].mean()
    print(f"Forecast range: {min_fc:.3f} GW to {max_fc:.3f} GW (Mean: {mean_fc:.3f} GW)")

    # 6. Historical Replay Coverage check for all 30 Decision Dates
    print(f"\n--- HISTORICAL REPLAY FEASIBILITY (Jan 1-30, Cutoff 09:00 UTC) ---")
    cutoff_time = datetime.time(9, 0, 0)
    all_decisions_valid = True

    for day_idx in range(1, 31):
        dec_date = datetime.date(2026, 1, day_idx)
        target_date = dec_date + datetime.timedelta(days=1)
        cutoff_dt = pd.Timestamp(datetime.datetime.combine(dec_date, cutoff_time), tz="UTC")

        # Eligible forecasts published at or before cutoff
        eligible_fc = forecasts[forecasts["publish_time"] <= cutoff_dt]

        # For target date D+1 (all 48 half-hours)
        target_start = pd.Timestamp(datetime.datetime.combine(target_date, datetime.time(0, 0, 0)), tz="UTC")
        target_end = pd.Timestamp(datetime.datetime.combine(target_date, datetime.time(23, 30, 0)), tz="UTC")

        target_intervals = pd.date_range(target_start, target_end, freq="30min")
        fc_target = eligible_fc[eligible_fc["interval_start"].isin(target_intervals)]

        # Latest version for each interval
        latest_fc = fc_target.sort_values("publish_time").groupby("interval_start").last()
        covered = len(latest_fc)
        if covered != 48:
            print(f"  Decision {dec_date} -> Target {target_date}: FAIL (only {covered}/48 intervals)")
            all_decisions_valid = False

    if all_decisions_valid:
        print("Historical replay coverage: PASS (All 30 decision dates have 100% 48/48 intervals)")
    else:
        print("ERROR: Some decision dates failed forecast coverage")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("ALL AUDIT CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    validate_dataset()
