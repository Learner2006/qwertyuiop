"""Tests for backend/app/services/prepare.py data preparation and loading logic."""

import datetime
import pytest
import pandas as pd
from app.services.prepare import DataManager
from app.config import settings


@pytest.fixture
def data_manager():
    return DataManager.get_instance()


def test_dataset_metadata(data_manager):
    meta = data_manager.get_dataset_metadata()
    assert meta["available"] is True
    assert meta["count"] > 35000
    assert meta["start"] == "2026-01-01"
    assert meta["end"] == "2026-01-31"


def test_target_intervals_utc_alignment(data_manager):
    target_date = datetime.date(2026, 1, 15)
    intervals = data_manager.get_target_intervals(target_date)
    assert len(intervals) == 48
    assert intervals[0] == pd.Timestamp("2026-01-15T00:00:00Z")
    assert intervals[-1] == pd.Timestamp("2026-01-15T23:30:00Z")
    # All intervals spaced by exactly 30 minutes
    for i in range(len(intervals) - 1):
        diff = intervals[i + 1] - intervals[i]
        assert diff == pd.Timedelta(minutes=30)


def test_select_target_forecast_coverage(data_manager):
    dec_date = datetime.date(2026, 1, 10)
    target_date = datetime.date(2026, 1, 11)
    fcs = data_manager.select_target_forecast(dec_date, target_date)
    assert len(fcs) == 48
    for idx, r in enumerate(fcs):
        assert r["settlement_period"] == idx + 1
        assert r["generation_gw"] > 0
        assert r["generation_mw"] == pytest.approx(r["generation_gw"] * 1000.0, rel=1e-5)
        # Verify forecast was published strictly at or before cutoff (09:00 UTC)
        cutoff_dt = pd.Timestamp("2026-01-10T09:00:00Z")
        assert r["publish_time"] <= cutoff_dt


def test_calibration_observations_history(data_manager):
    # Jan 1: no previous days in Jan 2026, so n = 0
    hist_jan1 = data_manager.get_calibration_observations(datetime.date(2026, 1, 1))
    assert len(hist_jan1) == 0

    # Jan 2: intervals from Jan 2 morning (00:00 to 08:30) = 18 intervals
    hist_jan2 = data_manager.get_calibration_observations(datetime.date(2026, 1, 2))
    assert len(hist_jan2) == 18

    # Jan 3: Jan 2 (48) + Jan 3 morning (18) = 66 intervals
    hist_jan3 = data_manager.get_calibration_observations(datetime.date(2026, 1, 3))
    assert len(hist_jan3) == 66

    # Jan 4 onwards: capped at 96 intervals
    hist_jan4 = data_manager.get_calibration_observations(datetime.date(2026, 1, 4))
    assert len(hist_jan4) == 96

    # Verify each observation has signed error
    for obs in hist_jan4:
        assert "error_gw" in obs
        assert obs["error_gw"] == pytest.approx(obs["forecast_gw"] - obs["actual_gw"], rel=1e-5)


def test_target_actuals(data_manager):
    target_date = datetime.date(2026, 1, 20)
    actuals = data_manager.get_target_actuals(target_date)
    assert len(actuals) == 48
    for idx, act in enumerate(actuals):
        assert act["settlement_period"] == idx + 1
        assert act["generation_gw"] > 0
        assert act["generation_mw"] == pytest.approx(act["generation_gw"] * 1000.0, rel=1e-5)
