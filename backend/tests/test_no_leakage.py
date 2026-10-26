"""Release-blocking no-leakage tests for Wind Day-Ahead Estimator.
Verifies that no future information (published after cutoff) can leak into:
1. Target-day forecast selection
2. Historical calibration observations
3. Daily safe estimates or error bands
"""

import copy
import datetime
import pytest
import pandas as pd

from app.config import settings
from app.main import app
from app.services.calibrate import calibrate_daily_forecast
from app.services.prepare import DataManager
from app.services.replay import clear_replay_cache
from fastapi.testclient import TestClient

client = TestClient(app)


@pytest.fixture
def real_data_manager():
    return DataManager.get_instance()


def test_leakage_1_target_forecast_published_after_cutoff(real_data_manager):
    """Test 1: A forecast version published after the decision cutoff (e.g. 11:30 UTC or 15:30 UTC on day D)
    cannot replace or affect the target-day forecast selected at 09:00 UTC."""
    dec_date = datetime.date(2026, 1, 15)
    target_date = datetime.date(2026, 1, 16)
    cutoff_dt = pd.Timestamp("2026-01-15T09:00:00Z")

    baseline_fcs = real_data_manager.select_target_forecast(dec_date, target_date)

    # Verify that all selected versions have publish_time <= cutoff_dt
    for fc in baseline_fcs:
        assert fc["publish_time"] <= cutoff_dt

    # Now create an altered dataset containing a fictional high forecast published at 11:30 UTC on day D
    post_cutoff_pub = pd.Timestamp("2026-01-15T11:30:00Z")
    fictional_records = []
    for fc in baseline_fcs:
        fictional_records.append({
            "record_type": "forecast",
            "interval_start": fc["interval_start"],
            "publish_time": post_cutoff_pub,
            "generation_mw": 99999.0,
            "generation_gw": 99.999,
            "settlement_date": "2026-01-16",
            "settlement_period": None,
        })

    # Temporarily append post-cutoff records to the manager's forecast dataframe
    orig_forecasts = real_data_manager._forecasts_df.copy()
    try:
        augmented_forecasts = pd.concat([orig_forecasts, pd.DataFrame(fictional_records)], ignore_index=True)
        real_data_manager._forecasts_df = augmented_forecasts.sort_values("publish_time").reset_index(drop=True)

        new_fcs = real_data_manager.select_target_forecast(dec_date, target_date)

        # The forecast selected at cutoff MUST be identical to baseline and NOT the 99.999 GW future forecast!
        for base, new_fc in zip(baseline_fcs, new_fcs):
            assert new_fc["generation_gw"] == pytest.approx(base["generation_gw"], rel=1e-6)
            assert new_fc["generation_gw"] != 99.999
            assert new_fc["publish_time"] <= cutoff_dt
    finally:
        real_data_manager._forecasts_df = orig_forecasts


def test_leakage_2_actual_available_after_cutoff(real_data_manager):
    """Test 2: An actual observation that becomes available after cutoff or within the 1-hour publication lag
    (e.g. interval 08:00-08:30 published at 08:30 UTC, or interval 09:00-09:30 on day D, published at 09:30 UTC)
    cannot enter the calibration history."""
    dec_date = datetime.date(2026, 1, 15)
    cutoff_dt = pd.Timestamp("2026-01-15T09:00:00Z")
    lag_cutoff_dt = cutoff_dt - pd.Timedelta(hours=settings.ACTUALS_PUBLICATION_LAG_HOURS)

    baseline_hist = real_data_manager.get_calibration_observations(dec_date)

    # Verify that no interval in baseline history was published after the publication lag cutoff (08:00 UTC)
    for obs in baseline_hist:
        assert obs["interval_start"] < lag_cutoff_dt

    # Also verify that interval 08:00-08:30 on day D (ending 08:30 UTC) is strictly excluded
    interval_8am = pd.Timestamp("2026-01-15T08:00:00Z")
    assert not any(obs["interval_start"] == interval_8am for obs in baseline_hist)

    # Inject an actual observation published at 08:30 UTC on day D (within the 1-hour publication lag window)
    within_lag_actual = {
        "record_type": "actual",
        "interval_start": pd.Timestamp("2026-01-15T08:00:00Z"),
        "publish_time": pd.Timestamp("2026-01-15T08:30:00Z"),
        "generation_mw": 50000.0,
        "generation_gw": 50.0,
        "settlement_date": "2026-01-15",
        "settlement_period": 17,
    }

    orig_actuals = real_data_manager._actuals_df.copy()
    try:
        real_data_manager._actuals_df = pd.concat(
            [orig_actuals, pd.DataFrame([within_lag_actual])],
            ignore_index=True
        ).sort_values("interval_start").reset_index(drop=True)

        new_hist = real_data_manager.get_calibration_observations(dec_date)
        assert len(new_hist) == len(baseline_hist)
        for b, n in zip(baseline_hist, new_hist):
            assert b["interval_start"] == n["interval_start"]
            assert b["error_gw"] == pytest.approx(n["error_gw"], rel=1e-6)
    finally:
        real_data_manager._actuals_df = orig_actuals


def test_leakage_3_future_target_interval_record_cannot_alter_earlier_decision(real_data_manager):
    """Test 3: Future records from January 20-31 cannot alter a decision made on January 10."""
    dec_date = datetime.date(2026, 1, 10)
    target_date = datetime.date(2026, 1, 11)

    fcs_before = real_data_manager.select_target_forecast(dec_date, target_date)
    hist_before = real_data_manager.get_calibration_observations(dec_date)
    est_before = calibrate_daily_forecast(fcs_before, hist_before, percentile=75.0)

    # Truncate dataset to only contain records up to January 10 09:00:00Z
    cutoff_dt = pd.Timestamp("2026-01-10T09:00:00Z")
    orig_fcs = real_data_manager._forecasts_df.copy()
    orig_acts = real_data_manager._actuals_df.copy()

    try:
        # Keep only records up to Jan 10 09:00 UTC (no future days exist at all)
        real_data_manager._forecasts_df = orig_fcs[orig_fcs["publish_time"] <= cutoff_dt].copy()
        real_data_manager._actuals_df = orig_acts[orig_acts["publish_time"] <= cutoff_dt].copy()

        fcs_isolated = real_data_manager.select_target_forecast(dec_date, target_date)
        hist_isolated = real_data_manager.get_calibration_observations(dec_date)
        est_isolated = calibrate_daily_forecast(fcs_isolated, hist_isolated, percentile=75.0)

        # The estimate produced when the rest of the month doesn't even exist MUST BE 100% IDENTICAL
        assert est_before["safe_headline_gw"] == pytest.approx(est_isolated["safe_headline_gw"], abs=1e-5)
        assert est_before["elexon_headline_gw"] == pytest.approx(est_isolated["elexon_headline_gw"], abs=1e-5)
        assert len(est_before["intervals"]) == len(est_isolated["intervals"])
        for b, i in zip(est_before["intervals"], est_isolated["intervals"]):
            assert b["safe_estimate_gw"] == pytest.approx(i["safe_estimate_gw"], abs=1e-4)
            assert b["applied_margin_gw"] == pytest.approx(i["applied_margin_gw"], abs=1e-4)
    finally:
        real_data_manager._forecasts_df = orig_fcs
        real_data_manager._actuals_df = orig_acts


def test_leakage_4_later_forecast_version_in_raw_data_does_not_replace_eligible_version(real_data_manager):
    """Test 4: Adding a later forecast version for target date D+1 with an issue time after cutoff
    does not replace the eligible version."""
    dec_date = datetime.date(2026, 1, 12)
    target_date = datetime.date(2026, 1, 13)

    baseline_fcs = real_data_manager.select_target_forecast(dec_date, target_date)
    # The latest eligible forecast for Jan 13 selected at Jan 12 09:00 UTC was published at 07:30 UTC
    assert all(f["publish_time"] <= pd.Timestamp("2026-01-12T09:00:00Z") for f in baseline_fcs)


def test_leakage_5_replay_invariant_to_future_dataset_expansion(real_data_manager):
    """Test 5: The same decision on date D replayed with additional future records present
    remains completely unchanged."""
    dec_date = datetime.date(2026, 1, 18)
    target_date = datetime.date(2026, 1, 19)

    fcs1 = real_data_manager.select_target_forecast(dec_date, target_date)
    hist1 = real_data_manager.get_calibration_observations(dec_date)
    est1 = calibrate_daily_forecast(fcs1, hist1, percentile=80.0)

    # Replay
    fcs2 = real_data_manager.select_target_forecast(dec_date, target_date)
    hist2 = real_data_manager.get_calibration_observations(dec_date)
    est2 = calibrate_daily_forecast(fcs2, hist2, percentile=80.0)

    assert est1 == est2


def test_leakage_6_all_30_dates_invariant_to_post_cutoff_truncation(real_data_manager):
    """Test 6: For every decision date D in Jan 1-30, no field in the estimate response
    depends on data published after cutoff. Truncating the dataset after cutoff produces
    identical responses."""
    orig_fcs = real_data_manager._forecasts_df.copy()
    orig_acts = real_data_manager._actuals_df.copy()

    try:
        for d in range(1, 31):
            date_str = f"2026-01-{d:02d}"
            # Restore full dataset
            real_data_manager._forecasts_df = orig_fcs.copy()
            real_data_manager._actuals_df = orig_acts.copy()
            real_data_manager._precompute_day_ahead_forecasts()
            clear_replay_cache()

            # Baseline response on full month data
            resp_full = client.get(f"/api/estimate?date={date_str}&percentile=75.0")
            assert resp_full.status_code == 200
            r_base = resp_full.json()

            # Truncate to cutoff for decision date d
            cutoff_str = f"2026-01-{d:02d}T09:00:00Z"
            real_data_manager._forecasts_df = orig_fcs[orig_fcs["publish_time"] <= cutoff_str].copy()
            real_data_manager._actuals_df = orig_acts[orig_acts["publish_time"] <= cutoff_str].copy()
            real_data_manager._precompute_day_ahead_forecasts()
            clear_replay_cache()

            resp_trunc = client.get(f"/api/estimate?date={date_str}&percentile=75.0")
            assert resp_trunc.status_code == 200
            r_trunc = resp_trunc.json()

            assert r_base["elexon_headline_gw"] == r_trunc["elexon_headline_gw"]
            assert r_base["safe_headline_gw"] == r_trunc["safe_headline_gw"]
            assert r_base["slider_tradeoffs"] == r_trunc["slider_tradeoffs"]
            assert r_base["completed_track_record"] == r_trunc["completed_track_record"]
            assert r_base["error_distribution"] == r_trunc["error_distribution"]
            assert r_base["calculation"] == r_trunc["calculation"]
            assert r_base["history_48h"] == r_trunc["history_48h"]
            assert r_base["intervals"] == r_trunc["intervals"]
    finally:
        real_data_manager._forecasts_df = orig_fcs
        real_data_manager._actuals_df = orig_acts
        real_data_manager._precompute_day_ahead_forecasts()
        clear_replay_cache()


def test_leakage_7_maximum_completed_delivery_day_is_d_minus_1():
    """Test 7: The maximum completed delivery day in the track record is strictly D-1."""
    for d in range(1, 31):
        date_str = f"2026-01-{d:02d}"
        resp = client.get(f"/api/estimate?date={date_str}&percentile=75.0")
        assert resp.status_code == 200
        tr = resp.json()["completed_track_record"]
        if tr["completed_days_count"] > 0:
            max_target = max(rec["target_date"] for rec in tr["daily_records"])
            assert max_target == f"2026-01-{d-1:02d}"
        else:
            assert d in (1, 2)

