"""Property-based invariant tests (Milestone R7 / Finding F7).

Verifies fundamental physical and mathematical invariants across 1,000 randomised
forecast, actual, and plan sequences:
1. Monotonicity: larger haircut never increases shortfall or decreases cut volume.
2. Conservation: avoided shortfall + incremental surplus == total cut volume.
3. Non-negativity: shortfall, surplus, cut, and avoided shortfall are non-negative for non-negative inputs.
4. Identity: when forecast == actual, shortfall == 0 and avoided shortfall == 0.
5. Linearity: net saving scales linearly with advance price and monotonically with replacement ratio k.
"""

import numpy as np
import pytest

from app.services.economics import break_even_price_ratio, cut_volume, net_saving
from app.services.metrics import (
    calculate_daily_metrics,
    calculate_shortfall_mwh,
    calculate_surplus_mwh,
)


def test_property_monotonicity_of_haircut():
    """Property 1: Monotonicity.
    For any forecast and actual sequence, increasing the haircut fraction:
    - Never increases safe generation plan (p2 <= p1).
    - Never decreases total cut volume (cut2 >= cut1).
    - Never increases shortfall (shortfall2 <= shortfall1).
    - Never decreases avoided shortfall (avoided2 >= avoided1).
    - Never decreases extra supply arranged (extra2 >= extra1).
    """
    rng = np.random.default_rng(2026)

    for _ in range(500):
        n_intervals = 48
        forecast = rng.uniform(1.0, 20.0, size=n_intervals)
        actual = rng.uniform(0.5, 22.0, size=n_intervals)

        h1, h2 = sorted(rng.uniform(0.01, 0.50, size=2))  # h1 < h2
        plan1 = forecast * (1.0 - h1)
        plan2 = forecast * (1.0 - h2)

        res1 = calculate_daily_metrics(plan1.tolist(), forecast.tolist(), actual.tolist())
        res2 = calculate_daily_metrics(plan2.tolist(), forecast.tolist(), actual.tolist())

        # Invariants:
        assert np.all(plan2 <= plan1 + 1e-9), "Plan 2 should be <= Plan 1"
        assert res2["total_cut_mwh"] >= res1["total_cut_mwh"] - 1e-6, "Cut volume should increase with haircut"
        assert res2["safe_shortfall_mwh"] <= res1["safe_shortfall_mwh"] + 1e-6, "Safe shortfall should decrease or stay equal"
        assert res2["avoided_shortfall_mwh"] >= res1["avoided_shortfall_mwh"] - 1e-6, "Avoided shortfall should increase or stay equal"
        assert res2["incremental_surplus_mwh"] >= res1["incremental_surplus_mwh"] - 1e-6, "Incremental surplus should increase or stay equal"


def test_property_conservation_of_cut_volume():
    """Property 2: Physical Conservation.
    For ANY non-negative forecast, actual, and plan (where plan <= forecast):
    avoided_shortfall_mwh + incremental_surplus_mwh == total_cut_mwh
    Both at the half-hourly interval level and at the aggregated daily level.
    """
    rng = np.random.default_rng(101)

    for _ in range(500):
        n_intervals = 48
        forecast = rng.uniform(0.1, 25.0, size=n_intervals)
        actual = rng.uniform(0.0, 25.0, size=n_intervals)
        # Any plan between 0 and forecast
        cut_fraction = rng.uniform(0.0, 1.0, size=n_intervals)
        plan = forecast * (1.0 - cut_fraction)

        # Interval-by-interval conservation
        for f, a, p in zip(forecast, actual, plan):
            e_sf = calculate_shortfall_mwh(f, a)
            e_sp = calculate_surplus_mwh(f, a)
            s_sf = calculate_shortfall_mwh(p, a)
            s_sp = calculate_surplus_mwh(p, a)

            avoided = e_sf - s_sf
            extra = s_sp - e_sp
            cut = (f - p) * 500.0

            assert cut == pytest.approx(avoided + extra, abs=1e-5), f"Conservation failed: cut={cut}, avoided={avoided}, extra={extra}"

        # Aggregated daily conservation
        res = calculate_daily_metrics(plan.tolist(), forecast.tolist(), actual.tolist())
        assert res["total_cut_mwh"] == pytest.approx(
            res["avoided_shortfall_mwh"] + res["incremental_surplus_mwh"],
            abs=1e-5,
        )


def test_property_non_negativity():
    """Property 3: Non-negativity.
    For non-negative forecast, actual, and plan <= forecast:
    shortfall >= 0, surplus >= 0, avoided_shortfall >= 0, incremental_surplus >= 0.
    """
    rng = np.random.default_rng(777)

    for _ in range(500):
        n_intervals = 48
        forecast = rng.uniform(0.0, 20.0, size=n_intervals)
        actual = rng.uniform(0.0, 20.0, size=n_intervals)
        plan = forecast * rng.uniform(0.5, 1.0, size=n_intervals)

        res = calculate_daily_metrics(plan.tolist(), forecast.tolist(), actual.tolist())
        assert res["elexon_shortfall_mwh"] >= -1e-9
        assert res["safe_shortfall_mwh"] >= -1e-9
        assert res["avoided_shortfall_mwh"] >= -1e-9
        assert res["elexon_surplus_mwh"] >= -1e-9
        assert res["safe_surplus_mwh"] >= -1e-9
        assert res["incremental_surplus_mwh"] >= -1e-9
        assert res["total_cut_mwh"] >= -1e-9


def test_property_identity_perfect_forecast():
    """Property 4: Identity under perfect forecast.
    When forecast == actual across all intervals:
    - Elexon shortfall = 0
    - Elexon surplus = 0
    - Any haircut > 0 yields safe shortfall = 0, avoided shortfall = 0
    - Extra supply arranged == total cut volume
    - break_even_price_ratio is None because avoided shortfall is 0.
    """
    rng = np.random.default_rng(888)

    for _ in range(100):
        n_intervals = 48
        forecast = rng.uniform(1.0, 15.0, size=n_intervals)
        actual = forecast.copy()  # Perfect forecast

        haircut = float(rng.uniform(0.05, 0.30))
        plan = forecast * (1.0 - haircut)

        res = calculate_daily_metrics(plan.tolist(), forecast.tolist(), actual.tolist())

        assert res["elexon_shortfall_mwh"] == 0.0
        assert res["safe_shortfall_mwh"] == 0.0
        assert res["avoided_shortfall_mwh"] == 0.0
        assert res["incremental_surplus_mwh"] == pytest.approx(res["total_cut_mwh"], abs=1e-5)

        be_k = break_even_price_ratio(res["avoided_shortfall_mwh"], res["incremental_surplus_mwh"], s=0.0)
        assert be_k is None, "Break-even ratio must be None when avoided shortfall is 0"


def test_property_economic_linearity():
    """Property 5: Economic linearity and scaling.
    - net_saving is strictly linear in P_adv.
    - net_saving is strictly monotonically increasing in k (when avoided > 0).
    - net_saving is strictly monotonically increasing in s (when extra > 0).
    """
    rng = np.random.default_rng(999)

    for _ in range(200):
        avoided = float(rng.uniform(100.0, 10000.0))
        extra = float(rng.uniform(50.0, 8000.0))

        # Linearity in P_adv
        p1 = float(rng.uniform(20.0, 50.0))
        p2 = float(rng.uniform(60.0, 120.0))
        ratio = p2 / p1

        net1 = net_saving(avoided, extra, k=2.0, s=0.0, p_adv=p1)
        net2 = net_saving(avoided, extra, k=2.0, s=0.0, p_adv=p2)
        assert net2 == pytest.approx(net1 * ratio, rel=1e-5)

        # Monotonicity in k
        k1, k2 = sorted(rng.uniform(1.0, 5.0, size=2))
        if k2 > k1:
            assert net_saving(avoided, extra, k=k2, s=0.0, p_adv=p1) > net_saving(avoided, extra, k=k1, s=0.0, p_adv=p1)

        # Monotonicity in s
        s1, s2 = sorted(rng.uniform(0.0, 1.0, size=2))
        if s2 > s1:
            assert net_saving(avoided, extra, k=2.0, s=s2, p_adv=p1) > net_saving(avoided, extra, k=2.0, s=s1, p_adv=p1)
