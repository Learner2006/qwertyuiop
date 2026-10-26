"""Tests for unified replay engine and model registry (Milestone R2).
Verifies:
1. /api/summary totals equal the sum of per-day /api/check results and equal replay()
   for every registry model.
2. expanding_ratio adheres to F9 resolved specification (clamped to [0.0, 1.0], fallback to 15%
   until >= 2 completed delivery days, i.e. 96 intervals).
"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.models import expanding_ratio, get_model
from app.services.replay import replay

client = TestClient(app)


def test_summary_totals_equal_sum_of_checks_and_equal_replay():
    """Asserts /api/summary totals equal the sum of per-day /api/check results
    and equal replay() for every registry model.
    """
    sum_resp = client.get("/api/summary?percentile=75")
    assert sum_resp.status_code == 200
    summary = sum_resp.json()

    # Direct replay() calls
    all_days = range(1, 31)
    r_v1 = replay("v1_additive", all_days, percentile=75.0)
    r_v2 = replay("v2_proportional", all_days, percentile=75.0)
    r_f15 = replay("flat_15", all_days)

    # Check that summary totals match replay() directly
    assert summary["total_avoided_shortfall_mwh"] == pytest.approx(
        r_v1["total_avoided_shortfall_mwh"], abs=0.1
    )
    assert summary["total_incremental_surplus_mwh"] == pytest.approx(
        r_v1["total_incremental_surplus_mwh"], abs=0.1
    )
    assert summary["breakeven_ratio"] == pytest.approx(
        r_v1["breakeven_ratio"], abs=0.005
    )

    v2_bench = summary["v2_proportional_benchmark"]
    assert v2_bench["avoided_shortfall_mwh"] == pytest.approx(
        r_v2["total_avoided_shortfall_mwh"], abs=0.1
    )
    assert v2_bench["extra_supply_mwh"] == pytest.approx(
        r_v2["total_incremental_surplus_mwh"], abs=0.1
    )
    assert v2_bench["breakeven_ratio"] == pytest.approx(
        r_v2["breakeven_ratio"], abs=0.005
    )

    f15_bench = summary["flat_15_benchmark"]
    assert f15_bench["avoided_shortfall_mwh"] == pytest.approx(
        r_f15["total_avoided_shortfall_mwh"], abs=0.1
    )
    assert f15_bench["extra_supply_mwh"] == pytest.approx(
        r_f15["total_incremental_surplus_mwh"], abs=0.1
    )
    assert f15_bench["breakeven_ratio"] == pytest.approx(
        r_f15["breakeven_ratio"], abs=0.005
    )

    # Sum of per-day /api/check calls
    tot_chk_v1_avoided = 0.0
    tot_chk_v1_extra = 0.0
    tot_chk_v2_avoided = 0.0
    tot_chk_v2_extra = 0.0
    tot_chk_f15_avoided = 0.0
    tot_chk_f15_extra = 0.0

    for d in range(1, 31):
        c_resp = client.get(f"/api/check?date=2026-01-{d:02d}&percentile=75")
        assert c_resp.status_code == 200
        chk = c_resp.json()

        tot_chk_v1_avoided += chk["saved_shortfall_mwh"]
        tot_chk_v1_extra += chk["incremental_surplus_mwh"]

        tot_chk_v2_avoided += chk["v2_saved_shortfall_mwh"]
        tot_chk_v2_extra += chk["v2_incremental_surplus_mwh"]

        tot_chk_f15_avoided += chk["flat15_saved_shortfall_mwh"]
        tot_chk_f15_extra += chk["flat15_incremental_surplus_mwh"]

    # Verify summary matches sum of checks (within 2.0 MWh rounding accumulation)
    assert summary["total_avoided_shortfall_mwh"] == pytest.approx(
        tot_chk_v1_avoided, abs=2.0
    )
    assert summary["total_incremental_surplus_mwh"] == pytest.approx(
        tot_chk_v1_extra, abs=2.0
    )

    assert v2_bench["avoided_shortfall_mwh"] == pytest.approx(
        tot_chk_v2_avoided, abs=2.0
    )
    assert v2_bench["extra_supply_mwh"] == pytest.approx(
        tot_chk_v2_extra, abs=2.0
    )

    assert f15_bench["avoided_shortfall_mwh"] == pytest.approx(
        tot_chk_f15_avoided, abs=2.0
    )
    assert f15_bench["extra_supply_mwh"] == pytest.approx(
        tot_chk_f15_extra, abs=2.0
    )


def test_expanding_ratio_f9_spec_and_clamping():
    """Verifies F9 resolution:
    1. Fallback to 15% haircut when completed observations < 96 intervals (2 days).
    2. Correct ratio when >= 96 intervals.
    3. Strictly clamped to [0.0, 1.0] (no ratio > 1.0 planning above forecast).
    4. Full month totals match audited F9 reference values.
    """
    dummy_fc = [
        {"interval_start": "2026-01-03T00:00:00Z", "settlement_period": 1, "generation_gw": 10.0}
    ]

    # Less than 96 intervals: must fallback to 15% haircut (applied_ratio = 0.15, plan = 8.5)
    acts_48 = [{"generation_gw": 5.0} for _ in range(48)]
    fcs_48 = [{"generation_gw": 10.0} for _ in range(48)]
    res_fallback = expanding_ratio(dummy_fc, acts_48, fcs_48)
    assert res_fallback["applied_ratio"] == settings.COLD_START_HAIRCUT
    assert res_fallback["plans"][0] == pytest.approx(8.5, abs=1e-4)

    # 96 intervals: 2 completed days (outturn 4.0 GW vs forecast 10.0 GW -> ratio = 0.40)
    acts_96 = [{"generation_gw": 4.0} for _ in range(96)]
    fcs_96 = [{"generation_gw": 10.0} for _ in range(96)]
    res_96 = expanding_ratio(dummy_fc, acts_96, fcs_96)
    assert res_96["actual_to_forecast_ratio"] == pytest.approx(0.40, abs=1e-4)
    assert res_96["plans"][0] == pytest.approx(4.0, abs=1e-4)

    # Outturn higher than forecast (e.g. outturn 12.0 GW vs forecast 10.0 GW -> ratio 1.2)
    # Must be clamped strictly to 1.0 (plan = 10.0, never exceeds forecast)
    acts_high = [{"generation_gw": 12.0} for _ in range(96)]
    res_high = expanding_ratio(dummy_fc, acts_high, fcs_96)
    assert res_high["actual_to_forecast_ratio"] == pytest.approx(1.0, abs=1e-4)
    assert res_high["plans"][0] == pytest.approx(10.0, abs=1e-4)

    # Full month replay matches audited values
    r_er = replay("expanding_ratio", range(1, 31))
    assert r_er["total_avoided_shortfall_mwh"] == pytest.approx(880742.5, abs=2.0)
    assert r_er["total_incremental_surplus_mwh"] == pytest.approx(306774.7, abs=2.0)
    assert r_er["breakeven_ratio"] == pytest.approx(1.348, abs=0.01)
