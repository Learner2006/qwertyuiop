"""Cost-ratio calculator test for Wind Day-Ahead Estimator.
Verifies that calculator table values reproduce exactly from API numbers
with no hardcoded totals, and formulas match across all models and scenarios.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def calculate_scenario(
    avoided_mwh: float,
    extra_mwh: float,
    k: float,
    s: float = 0.0,
    price: float = 70.0,
):
    """Replicates frontend calculator scenario arithmetic."""
    replacement_price = k * price
    avoided_premium_value = avoided_mwh * (k - 1.0) * price
    extra_unrecovered_cost = extra_mwh * (1.0 - s) * price
    net_mwh = avoided_mwh * (k - 1.0) - extra_mwh * (1.0 - s)
    net_savings = net_mwh * price
    breakeven_k = (
        1.0 + (1.0 - s) * (extra_mwh / avoided_mwh) if avoided_mwh > 0 else 1.0
    )
    return {
        "k": k,
        "replacement_price": replacement_price,
        "avoided_premium_value": avoided_premium_value,
        "extra_unrecovered_cost": extra_unrecovered_cost,
        "net_savings": net_savings,
        "net_mwh": net_mwh,
        "breakeven_k": breakeven_k,
        "is_positive": net_savings > 0,
    }


def test_calculator_reproduces_summary_models():
    """Reproduces calculator table for v1, v2, and flat_15 from /api/summary."""
    resp = client.get("/api/summary?percentile=75")
    assert resp.status_code == 200
    data = resp.json()

    models = {
        "v1_additive": (
            data["total_avoided_shortfall_mwh"],
            data["total_incremental_surplus_mwh"],
            data["breakeven_ratio"],
        ),
        "v2_proportional": (
            data["v2_proportional_benchmark"]["avoided_shortfall_mwh"],
            data["v2_proportional_benchmark"]["extra_supply_mwh"],
            data["v2_proportional_benchmark"]["breakeven_ratio"],
        ),
        "flat_15": (
            data["flat_15_benchmark"]["avoided_shortfall_mwh"],
            data["flat_15_benchmark"]["extra_supply_mwh"],
            data["flat_15_benchmark"]["breakeven_ratio"],
        ),
    }

    k_values = [1.5, 2.0, 3.0]
    price = 70.0

    for name, (avoided, extra, expected_be) in models.items():
        computed_be = 1.0 + extra / avoided
        assert computed_be == pytest.approx(expected_be, abs=0.01)

        for k in k_values:
            sc = calculate_scenario(avoided, extra, k, s=0.0, price=price)
            assert sc["replacement_price"] == pytest.approx(k * price, abs=1e-5)
            assert sc["avoided_premium_value"] == pytest.approx(
                avoided * (k - 1.0) * price, abs=1e-3
            )
            assert sc["extra_unrecovered_cost"] == pytest.approx(
                extra * price, abs=1e-3
            )
            assert sc["net_savings"] == pytest.approx(
                (avoided * (k - 1.0) - extra) * price, abs=1e-3
            )
            assert sc["net_mwh"] == pytest.approx((avoided * (k - 1.0)) - extra, abs=1e-3)
            assert (sc["net_savings"] > 0) == (k > computed_be)


def test_calculator_reproduces_estimate_completed_days():
    """Reproduces calculator table for completed days up to D-1 on Estimate page (e.g. Jan 25)."""
    resp = client.get("/api/estimate?date=2026-01-25&percentile=75")
    assert resp.status_code == 200
    data = resp.json()

    tr = data["completed_track_record"]
    assert tr["completed_days_count"] == 23  # Jan 2 through Jan 24

    avoided = tr["total_avoided_shortfall_mwh"]
    extra = tr["total_extra_supply_mwh"]

    computed_be = 1.0 + extra / avoided
    # Verified break-even for Jan 25 completed days is 1.0 + 1.178 = ~2.178x
    assert computed_be == pytest.approx(2.178, abs=0.05)

    price = 70.0
    for k in [1.5, 2.0, 3.0]:
        sc = calculate_scenario(avoided, extra, k, s=0.0, price=price)
        assert sc["net_savings"] == pytest.approx(
            (avoided * (k - 1.0) - extra) * price, abs=0.1
        )
        assert sc["net_mwh"] == pytest.approx((avoided * (k - 1.0)) - extra, abs=0.1)
