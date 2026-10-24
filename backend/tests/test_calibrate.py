"""Tests for backend/app/services/calibrate.py calibration methodology."""

import datetime
import pytest
import numpy as np
import pandas as pd

from app.services.calibrate import calibrate_daily_forecast, compute_confidence_and_weight


def make_dummy_forecast(n_intervals: int = 48, base_gw: float = 10.0):
    rows = []
    base_time = pd.Timestamp("2026-01-15T00:00:00Z")
    for i in range(n_intervals):
        rows.append({
            "interval_start": base_time + pd.Timedelta(minutes=30 * i),
            "settlement_period": i + 1,
            "generation_gw": base_gw + np.sin(i / 5.0),
        })
    return rows


def test_confidence_and_weight_rules():
    # Cold start: n = 0
    label, weight, method = compute_confidence_and_weight(0)
    assert label == "Low"
    assert weight == 0.0
    assert method == "cold_start"

    # Low boundary: n = 23
    label, weight, method = compute_confidence_and_weight(23)
    assert label == "Low"
    assert weight == pytest.approx(23 / 96.0)
    assert method == "blended"

    # Medium boundary: n = 24
    label, weight, method = compute_confidence_and_weight(24)
    assert label == "Medium"
    assert weight == pytest.approx(24 / 96.0)
    assert method == "blended"

    # Medium boundary: n = 95
    label, weight, method = compute_confidence_and_weight(95)
    assert label == "Medium"
    assert weight == pytest.approx(95 / 96.0)
    assert method == "blended"

    # High boundary: n = 96
    label, weight, method = compute_confidence_and_weight(96)
    assert label == "High"
    assert weight == 1.0
    assert method == "data_driven"


def test_cold_start_pure_haircut():
    fc = make_dummy_forecast(48, base_gw=10.0)
    res = calibrate_daily_forecast(fc, calibration_records=[], percentile=75.0)

    assert res["confidence_label"] == "Low"
    assert res["history_weight"] == 0.0
    assert res["methodology_type"] == "cold_start"
    assert res["historical_observations_count"] == 0

    # For each interval, safe estimate must be exactly raw * (1 - 0.15) = 0.85 * raw
    for raw_r, out_r in zip(fc, res["intervals"]):
        expected_safe = round(raw_r["generation_gw"] * 0.85, 4)
        assert out_r["safe_estimate_gw"] == pytest.approx(expected_safe, abs=1e-4)
        assert out_r["applied_margin_gw"] == pytest.approx(round(raw_r["generation_gw"] * 0.15, 4), abs=1e-4)


def test_pure_data_driven_96_obs():
    fc = make_dummy_forecast(48, base_gw=12.0)
    # Generate 96 errors with known distribution
    calib = [{"error_gw": 2.0} for _ in range(96)]
    res = calibrate_daily_forecast(fc, calib, percentile=75.0)

    assert res["confidence_label"] == "High"
    assert res["history_weight"] == 1.0
    assert res["methodology_type"] == "data_driven"

    # Margin should be exactly 2.0 GW
    for raw_r, out_r in zip(fc, res["intervals"]):
        expected_safe = round(raw_r["generation_gw"] - 2.0, 4)
        assert out_r["safe_estimate_gw"] == pytest.approx(expected_safe, abs=1e-4)
        assert out_r["applied_margin_gw"] == pytest.approx(2.0, abs=1e-4)


def test_negative_percentile_flooring():
    """If the empirical error percentile is negative (meaning forecast systematically underestimated),
    the applied margin must be floored at 0 so we never increase the forecast."""
    fc = make_dummy_forecast(48, base_gw=8.0)
    # Errors are negative: forecast was lower than actual
    calib = [{"error_gw": -1.5} for _ in range(96)]
    res = calibrate_daily_forecast(fc, calib, percentile=75.0)

    for raw_r, out_r in zip(fc, res["intervals"]):
        # Margin floored at 0
        assert out_r["applied_margin_gw"] == 0.0
        assert out_r["safe_estimate_gw"] == pytest.approx(round(raw_r["generation_gw"], 4), abs=1e-4)


def test_percentile_boundary_validation():
    fc = make_dummy_forecast(48, base_gw=10.0)
    # 59 is below minimum 60
    with pytest.raises(ValueError):
        calibrate_daily_forecast(fc, [], percentile=59.0)

    # 91 is above maximum 90
    with pytest.raises(ValueError):
        calibrate_daily_forecast(fc, [], percentile=91.0)

    # 60 and 90 must succeed
    res60 = calibrate_daily_forecast(fc, [], percentile=60.0)
    res90 = calibrate_daily_forecast(fc, [], percentile=90.0)
    assert res60["selected_percentile"] == 60.0
    assert res90["selected_percentile"] == 90.0


def test_safe_estimate_never_negative():
    # If raw forecast is small and margin is large, safe estimate must be clamped to 0
    small_fc = [{"interval_start": "2026-01-15T00:00:00Z", "settlement_period": 1, "generation_gw": 0.5}]
    calib = [{"error_gw": 2.0} for _ in range(96)]
    res = calibrate_daily_forecast(small_fc, calib, percentile=75.0)
    assert res["intervals"][0]["safe_estimate_gw"] == 0.0


def test_deterministic_behavior():
    fc = make_dummy_forecast(48, base_gw=10.0)
    calib = [{"error_gw": float(i % 5)} for i in range(96)]
    res1 = calibrate_daily_forecast(fc, calib, percentile=75.0)
    res2 = calibrate_daily_forecast(fc, calib, percentile=75.0)
    assert res1 == res2
