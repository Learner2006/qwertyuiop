"""Tests for backend/app/services/metrics.py reliability metrics calculations."""

import pytest
from app.services.metrics import compute_reliability_metrics


def make_dummy_calibration_result(n_intervals=48, forecast_gw=10.0, safe_gw=8.5, low_gw=7.0, high_gw=11.0):
    intervals = []
    for i in range(n_intervals):
        intervals.append({
            "interval_start": f"2026-01-15T{i//2:02d}:{(i%2)*30:02d}:00Z",
            "settlement_period": i + 1,
            "elexon_forecast_gw": forecast_gw,
            "safe_estimate_gw": safe_gw,
            "indicative_lower_gw": low_gw,
            "indicative_upper_gw": high_gw,
            "applied_margin_gw": forecast_gw - safe_gw,
        })
    return {
        "intervals": intervals,
        "elexon_headline_gw": forecast_gw,
        "safe_headline_gw": safe_gw,
        "indicative_lower_headline_gw": low_gw,
        "indicative_upper_headline_gw": high_gw,
        "confidence_label": "High",
        "historical_observations_count": 96,
        "history_weight": 1.0,
        "methodology_type": "data_driven",
    }


def make_dummy_actuals(n_intervals=48, actual_gw=9.0):
    return [
        {
            "interval_start": f"2026-01-15T{i//2:02d}:{(i%2)*30:02d}:00Z",
            "settlement_period": i + 1,
            "generation_gw": actual_gw,
        }
        for i in range(n_intervals)
    ]


def test_positive_saved_shortfall():
    """Forecast = 10 GW, Safe = 8 GW, Actual = 7 GW.
    Elexon shortfall per interval: (10 - 7) * 500 = 1500 MWh. Total: 48 * 1500 = 72000 MWh.
    Our shortfall per interval: (8 - 7) * 500 = 500 MWh. Total: 48 * 500 = 24000 MWh.
    Saved: 72000 - 24000 = 48000 MWh.
    Extra advance: actual (7) < safe (8) -> 0 MWh.
    """
    calib = make_dummy_calibration_result(48, forecast_gw=10.0, safe_gw=8.0, low_gw=6.0, high_gw=12.0)
    actuals = make_dummy_actuals(48, actual_gw=7.0)
    res = compute_reliability_metrics(calib, actuals)

    assert res["elexon_shortfall_mwh"] == 72000.0
    assert res["safe_shortfall_mwh"] == 24000.0
    assert res["saved_shortfall_mwh"] == 48000.0
    assert res["safe_surplus_mwh"] == 0.0
    assert "reduced forecast-related shortfall" in res["headline_result"]


def test_zero_shortfall_and_extra_advance_planned():
    """Forecast = 10 GW, Safe = 8 GW, Actual = 12 GW.
    Actual exceeds both plans -> 0 shortfall for both!
    Saved: 0 MWh.
    Extra advance: (12 - 8) * 500 = 2000 MWh per interval. Total: 48 * 2000 = 96000 MWh.
    """
    calib = make_dummy_calibration_result(48, forecast_gw=10.0, safe_gw=8.0, low_gw=7.0, high_gw=11.0)
    actuals = make_dummy_actuals(48, actual_gw=12.0)
    res = compute_reliability_metrics(calib, actuals)

    assert res["elexon_shortfall_mwh"] == 0.0
    assert res["safe_shortfall_mwh"] == 0.0
    assert res["saved_shortfall_mwh"] == 0.0
    assert res["safe_surplus_mwh"] == 96000.0
    assert "same shortfall energy" in res["headline_result"]


def test_negative_saved_shortfall_honesty():
    """Suppose safe estimate was somehow higher than elexon (e.g. hypothetical stress test).
    Or verify that negative saved shortfall is preserved honestly and not clamped to zero."""
    calib = make_dummy_calibration_result(48, forecast_gw=8.0, safe_gw=10.0, low_gw=6.0, high_gw=12.0)
    actuals = make_dummy_actuals(48, actual_gw=7.0)
    res = compute_reliability_metrics(calib, actuals)

    # Elexon sf: (8-7)*500*48 = 24000
    # Safe sf: (10-7)*500*48 = 72000
    # Saved: 24000 - 72000 = -48000
    assert res["saved_shortfall_mwh"] == -48000.0
    assert "more shortfall than Elexon's forecast" in res["headline_result"]


def test_mae_and_range_coverage():
    # 48 intervals, actual = 9 GW.
    # Elexon fc = 10 GW -> abs error = 1 GW -> MAE = 1.0 GW
    # Safe est = 8 GW -> abs error = 1 GW -> MAE = 1.0 GW
    # Range is [7, 11] -> 9 is inside range for all 48 intervals -> coverage = 1.0
    calib = make_dummy_calibration_result(48, forecast_gw=10.0, safe_gw=8.0, low_gw=7.0, high_gw=11.0)
    actuals = make_dummy_actuals(48, actual_gw=9.0)
    res = compute_reliability_metrics(calib, actuals)

    assert res["elexon_mae_gw"] == pytest.approx(1.0)
    assert res["safe_mae_gw"] == pytest.approx(1.0)
    assert res["indicative_range_coverage"] == 1.0


def test_half_interval_coverage():
    # First 24 intervals inside range [7, 11], next 24 intervals at 12 GW (outside range)
    calib = make_dummy_calibration_result(48, forecast_gw=10.0, safe_gw=8.0, low_gw=7.0, high_gw=11.0)
    actuals = [
        {"interval_start": f"2026-01-15T{i//2:02d}:{(i%2)*30:02d}:00Z", "settlement_period": i + 1, "generation_gw": 9.0 if i < 24 else 12.0}
        for i in range(48)
    ]
    res = compute_reliability_metrics(calib, actuals)
    assert res["indicative_range_coverage"] == pytest.approx(0.5)
