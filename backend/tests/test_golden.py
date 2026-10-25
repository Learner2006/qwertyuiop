"""Golden numbers regression test for Wind Day-Ahead Estimator.
Ensures baseline model numbers and baselines cannot drift or change silently.
"""

import json
import os
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "golden_numbers.json")


def test_golden_baseline_numbers():
    with open(GOLDEN_PATH, "r") as f:
        golden = json.load(f)

    resp = client.get("/api/summary?percentile=75")
    assert resp.status_code == 200
    data = resp.json()

    # Full month checks
    full = golden["full_month"]
    assert data["total_target_intervals"] == full["total_slots"]

    # Raw Elexon
    assert data["total_elexon_forecast_mwh"] == pytest.approx(full["raw_elexon"]["forecast_mwh"], abs=2.0)
    assert data["total_actual_wind_mwh"] == pytest.approx(full["raw_elexon"]["actual_mwh"], abs=2.0)
    assert data["total_elexon_shortfall_mwh"] == pytest.approx(full["raw_elexon"]["shortfall_mwh"], abs=2.0)

    # v1 Additive (p75)
    assert data["total_avoided_shortfall_mwh"] == pytest.approx(full["v1_additive"]["avoided_shortfall_mwh"], abs=2.0)
    assert data["total_incremental_surplus_mwh"] == pytest.approx(full["v1_additive"]["extra_supply_mwh"], abs=2.0)
    assert data["breakeven_ratio"] == pytest.approx(full["v1_additive"]["breakeven_ratio"], abs=0.01)

    # v2 Proportional (p75)
    v2_bench = data["v2_proportional_benchmark"]
    assert v2_bench["avoided_shortfall_mwh"] == pytest.approx(full["v2_proportional"]["avoided_shortfall_mwh"], abs=2.0)
    assert v2_bench["extra_supply_mwh"] == pytest.approx(full["v2_proportional"]["extra_supply_mwh"], abs=2.0)
    assert v2_bench["breakeven_ratio"] == pytest.approx(full["v2_proportional"]["breakeven_ratio"], abs=0.01)

    # Flat 15% Baseline
    f15_bench = data["flat_15_benchmark"]
    assert f15_bench["avoided_shortfall_mwh"] == pytest.approx(full["flat_15"]["avoided_shortfall_mwh"], abs=2.0)
    assert f15_bench["extra_supply_mwh"] == pytest.approx(full["flat_15"]["extra_supply_mwh"], abs=2.0)
    assert f15_bench["breakeven_ratio"] == pytest.approx(full["flat_15"]["breakeven_ratio"], abs=0.01)

    # First Half (Jan 1-15 decisions) checks
    first = golden["first_half"]
    
    # First half v1
    fh_v1 = data["first_half_v1"]
    assert fh_v1["avoided_shortfall_mwh"] == pytest.approx(first["v1_additive"]["avoided_shortfall_mwh"], abs=2.0)
    assert fh_v1["extra_supply_mwh"] == pytest.approx(first["v1_additive"]["extra_supply_mwh"], abs=2.0)
    assert fh_v1["breakeven_ratio"] == pytest.approx(first["v1_additive"]["breakeven_ratio"], abs=0.01)

    # First half v2
    fh_v2 = data["first_half_v2"]
    assert fh_v2["avoided_shortfall_mwh"] == pytest.approx(first["v2_proportional"]["avoided_shortfall_mwh"], abs=2.0)
    assert fh_v2["extra_supply_mwh"] == pytest.approx(first["v2_proportional"]["extra_supply_mwh"], abs=2.0)
    assert fh_v2["breakeven_ratio"] == pytest.approx(first["v2_proportional"]["breakeven_ratio"], abs=0.01)

    # First half Flat 15%
    fh_f15 = data["first_half_flat15"]
    assert fh_f15["avoided_shortfall_mwh"] == pytest.approx(first["flat_15"]["avoided_shortfall_mwh"], abs=2.0)
    assert fh_f15["extra_supply_mwh"] == pytest.approx(first["flat_15"]["extra_supply_mwh"], abs=2.0)
    assert fh_f15["breakeven_ratio"] == pytest.approx(first["flat_15"]["breakeven_ratio"], abs=0.01)


def test_summary_totals_equal_sum_of_per_day_checks():
    """Asserts that summary totals equal the sum of per-day check results for every model."""
    sum_resp = client.get("/api/summary?percentile=75")
    assert sum_resp.status_code == 200
    summary = sum_resp.json()

    tot_v1_avoided = 0.0
    tot_v1_extra = 0.0
    tot_v2_avoided = 0.0
    tot_v2_extra = 0.0

    for d in range(1, 31):
        c_resp = client.get(f"/api/check?date=2026-01-{d:02d}&percentile=75")
        assert c_resp.status_code == 200
        check = c_resp.json()
        tot_v1_avoided += check["saved_shortfall_mwh"]
        tot_v1_extra += check["incremental_surplus_mwh"]
        tot_v2_avoided += check["v2_saved_shortfall_mwh"]
        tot_v2_extra += check["v2_incremental_surplus_mwh"]

    # Verify v1
    assert summary["total_avoided_shortfall_mwh"] == pytest.approx(tot_v1_avoided, abs=1.0)
    assert summary["total_incremental_surplus_mwh"] == pytest.approx(tot_v1_extra, abs=1.0)

    # Verify v2
    v2_bench = summary["v2_proportional_benchmark"]
    assert v2_bench["avoided_shortfall_mwh"] == pytest.approx(tot_v2_avoided, abs=1.0)
    assert v2_bench["extra_supply_mwh"] == pytest.approx(tot_v2_extra, abs=1.0)

