"""Tests for Empirical [p10, p90] Band Coverage (Milestone R5 / Findings F5, F6).
Verifies that the nominal [p10, p90] error range does NOT achieve 80% coverage in GB wind outturn,
confirming an empirical mean realised coverage of ~55.8% in Jan 2026 and ~62.5% in Feb-Sep 2026,
with individual days reaching both 0.0% and 100.0%.
"""

import datetime
import os
import numpy as np
import pytest

from app.services.prepare import DataManager
from app.services.calibrate import calibrate_daily_forecast
from app.services.replay import clear_replay_cache

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "data"))
JAN_PARQUET = os.path.join(DATA_DIR, "jan2026.parquet")
VAL_PARQUET = os.path.join(DATA_DIR, "validation_2026-01-29_to_2026-09-30.parquet")


@pytest.fixture(autouse=True)
def reset_dm():
    yield
    DataManager._instance = None
    clear_replay_cache()
    DataManager.get_instance(data_path=JAN_PARQUET)


def test_january_2026_band_coverage_around_55_percent():
    dm = DataManager(data_path=JAN_PARQUET)
    daily_coverages = []

    for d in range(1, 31):
        dec_date = datetime.date(2026, 1, d)
        target_date = dec_date + datetime.timedelta(days=1)

        fc = dm.select_target_forecast(dec_date, target_date)
        cal = dm.get_calibration_observations(dec_date)
        acts = dm.get_target_actuals(target_date)

        res = calibrate_daily_forecast(fc, cal, percentile=75.0)

        inside_count = sum(
            1
            for inter, act in zip(res["intervals"], acts)
            if inter["indicative_lower_gw"] <= act["generation_gw"] <= inter["indicative_upper_gw"]
        )
        cov_pct = (inside_count / 48.0) * 100.0
        daily_coverages.append(cov_pct)

    assert len(daily_coverages) == 30

    mean_cov = float(np.mean(daily_coverages))
    min_cov = float(np.min(daily_coverages))
    max_cov = float(np.max(daily_coverages))

    # Realised coverage in Jan 2026 is exactly 55.76% (not 80%)
    assert 54.0 <= mean_cov <= 58.0, f"Expected ~55.8% mean coverage, got {mean_cov:.2f}%"
    assert abs(mean_cov - 55.76) < 0.2

    # Boundary coverage extremes: at least one day at 0% and at least one day at 100%
    assert min_cov == 0.0, f"Expected min coverage 0.0%, got {min_cov}%"
    assert max_cov == 100.0, f"Expected max coverage 100.0%, got {max_cov}%"


def test_validation_2026_band_coverage_under_80_percent():
    if not os.path.exists(VAL_PARQUET):
        pytest.skip("Validation dataset not found")

    dm = DataManager(data_path=VAL_PARQUET)
    daily_coverages = []

    cur_target = datetime.date(2026, 2, 1)
    end_target = datetime.date(2026, 9, 29)

    while cur_target <= end_target:
        dec_date = cur_target - datetime.timedelta(days=1)
        try:
            fc = dm.select_target_forecast(dec_date, cur_target)
            cal = dm.get_calibration_observations(dec_date)
            acts = dm.get_target_actuals(cur_target)
            res = calibrate_daily_forecast(fc, cal, percentile=75.0)

            inside_count = sum(
                1
                for inter, act in zip(res["intervals"], acts)
                if inter["indicative_lower_gw"] <= act["generation_gw"] <= inter["indicative_upper_gw"]
            )
            daily_coverages.append((inside_count / 48.0) * 100.0)
        except Exception:
            pass
        cur_target += datetime.timedelta(days=1)

    assert len(daily_coverages) >= 200

    mean_cov = float(np.mean(daily_coverages))
    min_cov = float(np.min(daily_coverages))
    max_cov = float(np.max(daily_coverages))

    # Realised coverage in Feb-Sep is ~62.5%, well below 80%
    assert 60.0 <= mean_cov <= 66.0, f"Expected ~62.5% mean coverage, got {mean_cov:.2f}%"
    assert min_cov == 0.0, f"Expected min coverage 0.0%, got {min_cov}%"
    assert max_cov == 100.0, f"Expected max coverage 100.0%, got {max_cov}%"
