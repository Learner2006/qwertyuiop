"""API integration tests for Wind Day-Ahead Estimator."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["dataset_available"] is True
    assert data["dataset_records_count"] > 35000
    assert data["date_coverage_start"] == "2026-01-01"
    assert data["date_coverage_end"] == "2026-01-31"


def test_summary_endpoint():
    resp = client.get("/api/summary?percentile=75")
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision_dates_count"] == 30
    assert data["total_target_intervals"] == 1440
    assert data["total_elexon_shortfall_mwh"] > 1000000
    assert data["total_avoided_shortfall_mwh"] > 0
    assert data["total_incremental_surplus_mwh"] > 0
    assert data["total_extra_advance_planned_mwh"] > 0
    assert data["total_actual_wind_mwh"] > 8000000
    assert data["elexon_overforecast_pct"] == pytest.approx(15.48, abs=0.1)
    assert data["safe_efficiency_pct"] == pytest.approx(49.57, abs=0.2)
    assert data["matched_flat_efficiency_pct"] == pytest.approx(60.56, abs=0.2)
    assert data["breakeven_ratio"] == pytest.approx(1.02, abs=0.02)
    assert data["cold_start_intervals"] == 144
    assert data["mature_intervals"] == 1296
    assert data["cold_start_avoided_shortfall_mwh"] > 100000
    assert data["mature_avoided_shortfall_mwh"] > 800000
    assert data["flat_15_benchmark"]["name"] == "Flat 15% Haircut"
    assert data["flat_15_benchmark"]["avoided_shortfall_mwh"] > 1000000
    assert data["rolling_mean_benchmark"]["name"] == "Rolling Mean Bias Correction"
    assert len(data["percentile_sweep"]) == 7
    assert len(data["flat_benchmarks"]) == 7
    assert "Break-even: the cautious plan pays off if replacement power costs at least" in data["summary_sentence"]


def test_estimate_endpoint_valid():
    resp = client.get("/api/estimate?date=2026-01-25&percentile=75")
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision_date"] == "2026-01-25"
    assert data["target_date"] == "2026-01-26"
    assert data["selected_percentile"] == 75.0
    assert data["valid_intervals_count"] == 48
    assert len(data["intervals"]) == 48
    assert data["elexon_headline_gw"] > 0
    assert data["safe_headline_gw"] > 0
    assert data["confidence_label"] == "High"
    assert data["historical_observations_count"] == 96
    assert data["history_weight"] == 1.0


def test_estimate_endpoint_never_exposes_target_actuals():
    """Verify that estimate endpoint never discloses target-day actual outcomes."""
    resp = client.get("/api/estimate?date=2026-01-25&percentile=75")
    assert resp.status_code == 200
    data = resp.json()
    
    # Must not contain target-day actual generation keys or target evaluation outcomes
    assert "actual_headline_gw" not in data
    assert "range_coverage" not in data
    for interval in data["intervals"]:
        assert "actual_generation_gw" not in interval
        assert "shortfall_mwh" not in interval
        assert "saved_mwh" not in interval


def test_check_endpoint_valid():
    resp = client.get("/api/check?date=2026-01-25&percentile=75")
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision_date"] == "2026-01-25"
    assert data["target_date"] == "2026-01-26"
    assert data["selected_percentile"] == 75.0
    assert data["valid_intervals_count"] == 48
    assert len(data["intervals"]) == 48
    assert data["actual_headline_gw"] > 0
    assert "elexon_shortfall_mwh" in data
    assert "safe_shortfall_mwh" in data
    assert "saved_shortfall_mwh" in data
    assert "extra_advance_planned_mwh" in data
    assert "headline_result" in data


def test_consistency_estimate_and_check():
    """For identical date and percentile, the safe estimate and Elexon headline in /api/estimate
    must match the estimate components in /api/check."""
    resp_est = client.get("/api/estimate?date=2026-01-15&percentile=70")
    resp_chk = client.get("/api/check?date=2026-01-15&percentile=70")

    assert resp_est.status_code == 200
    assert resp_chk.status_code == 200

    est = resp_est.json()
    chk = resp_chk.json()

    assert est["elexon_headline_gw"] == pytest.approx(chk["elexon_headline_gw"], abs=1e-4)
    assert est["safe_headline_gw"] == pytest.approx(chk["safe_headline_gw"], abs=1e-4)
    assert est["indicative_lower_headline_gw"] == pytest.approx(chk["indicative_lower_headline_gw"], abs=1e-4)
    assert est["indicative_upper_headline_gw"] == pytest.approx(chk["indicative_upper_headline_gw"], abs=1e-4)

    for i_est, i_chk in zip(est["intervals"], chk["intervals"]):
        assert i_est["interval_start"] == i_chk["interval_start"]
        assert i_est["settlement_period"] == i_chk["settlement_period"]
        assert i_est["elexon_forecast_gw"] == pytest.approx(i_chk["elexon_forecast_gw"], abs=1e-4)
        assert i_est["safe_estimate_gw"] == pytest.approx(i_chk["safe_estimate_gw"], abs=1e-4)


def test_invalid_decision_dates():
    # Jan 31 is not a valid decision date (target would be Feb 1, out of Jan 2026)
    resp = client.get("/api/estimate?date=2026-01-31")
    assert resp.status_code == 400

    # Dec 31, 2025 is outside allowed range
    resp = client.get("/api/estimate?date=2025-12-31")
    assert resp.status_code == 400

    # Malformed date string
    resp = client.get("/api/estimate?date=not-a-date")
    assert resp.status_code == 400


def test_invalid_percentiles():
    # Below min (60)
    resp = client.get("/api/estimate?date=2026-01-20&percentile=55")
    assert resp.status_code == 422 or resp.status_code == 400

    # Above max (90)
    resp = client.get("/api/estimate?date=2026-01-20&percentile=95")
    assert resp.status_code == 422 or resp.status_code == 400


def test_estimate_deep_dive_fields():
    resp = client.get("/api/estimate?date=2026-01-25&percentile=75")
    assert resp.status_code == 200
    data = resp.json()

    # Calculation step
    assert "calculation" in data
    calc = data["calculation"]
    assert calc["elexon_day_ahead_avg_gw"] == pytest.approx(12.4, abs=0.1)
    assert calc["historical_observations_count"] == 96
    assert calc["error_margin_gw"] == pytest.approx(2.5, abs=0.1)
    assert calc["safe_plan_gw"] == pytest.approx(9.9, abs=0.1)

    # 48h history
    assert "history_48h" in data
    assert len(data["history_48h"]) == 96

    # Error distribution
    assert "error_distribution" in data
    ed = data["error_distribution"]
    assert ed["overforecast_count"] == 96
    assert ed["overforecast_pct"] == 100.0
    assert len(ed["histogram_bins"]) > 0

    # Trade-offs
    assert "slider_tradeoffs" in data
    assert len(data["slider_tradeoffs"]) >= 3

    # Completed track record (Jan 2 to Jan 24 = 23 days)
    assert "completed_track_record" in data
    ctr = data["completed_track_record"]
    assert ctr["completed_days_count"] == 23
    assert ctr["total_avoided_shortfall_mwh"] > 0
    assert ctr["days_reduced_count"] == 23

    # Provenance
    assert "provenance" in data
    prov = data["provenance"]
    assert prov["freeze_cutoff_utc"] == "2026-01-25T09:00:00Z"
    assert prov["forecast_revisions_count"] >= 1
