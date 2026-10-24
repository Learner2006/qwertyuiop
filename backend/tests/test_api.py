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
    payload_str = resp.text.lower()
    
    # Must not contain actual generation keys
    assert "actual_generation" not in payload_str
    assert "actual_headline" not in payload_str
    assert "shortfall_mwh" not in payload_str
    assert "extra_advance" not in payload_str
    assert "mae_gw" not in payload_str
    assert "range_coverage" not in payload_str


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
