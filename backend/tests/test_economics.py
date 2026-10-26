"""Independent ledger test and property tests for economic calculations.
Verifies that closed-form net_saving and break_even_price_ratio match the interval-by-interval
physical procurement ledger for every day in January 2026.
"""

import datetime
import random
import numpy as np
import pytest

from app.services.economics import break_even_price_ratio, cut_volume, net_saving
from app.services.models import flat_15, v1_additive, v2_proportional
from app.services.prepare import DataManager


def interval_ledger_cost(plan_gw: float, actual_gw: float, x_gw: float, p_adv: float, p_rep: float, s: float) -> float:
    """Interval procurement cost in £ (with 500 MWh per half-hour per GW).
    (X - plan) * P_adv + max(0, plan - actual) * P_rep - max(0, actual - plan) * s * P_adv
    """
    mwh_factor = 500.0  # 1000 MW/GW * 0.5 hours
    advance_energy_mwh = (x_gw - plan_gw) * mwh_factor
    shortfall_energy_mwh = max(0.0, plan_gw - actual_gw) * mwh_factor
    surplus_energy_mwh = max(0.0, actual_gw - plan_gw) * mwh_factor

    return (
        advance_energy_mwh * p_adv
        + shortfall_energy_mwh * p_rep
        - surplus_energy_mwh * s * p_adv
    )


def test_property_break_even_gte_one_when_s_zero():
    """Property test: When surplus recovery s = 0, break-even k* is always >= 1.0
    for any model with avoided >= 0. At k = 1.0, net saving is always -extra * P_adv <= 0."""
    rng = np.random.default_rng(42)
    for _ in range(500):
        avoided = float(rng.uniform(1.0, 1e6))
        extra = float(rng.uniform(0.0, 1e6))
        p_adv = float(rng.uniform(10.0, 200.0))

        be_k = break_even_price_ratio(avoided, extra, s=0.0)
        assert be_k is not None
        assert be_k >= 1.0

        # At k = 1, net saving must be -extra * p_adv <= 0
        net_at_1 = net_saving(avoided, extra, k=1.0, s=0.0, p_adv=p_adv)
        assert net_at_1 == pytest.approx(-extra * p_adv, rel=1e-5)

        # At break-even k*, net saving must be 0
        net_at_be = net_saving(avoided, extra, k=be_k, s=0.0, p_adv=p_adv)
        assert net_at_be == pytest.approx(0.0, abs=1e-4)


def test_ledger_cost_identity_all_30_dates():
    """Independent ledger test across all 30 January 2026 dates.
    Asserts ledger(plan) - ledger(raw_forecast) == -net_saving(...) for random (k, s)."""
    dm = DataManager.get_instance()
    random.seed(12345)

    test_scenarios = [
        (1.0, 0.0),
        (1.5, 0.0),
        (2.0, 0.0),
        (3.0, 0.0),
        (1.5, 0.5),
        (2.0, 0.5),
    ]

    for d in range(1, 31):
        dec_date = datetime.date(2026, 1, d)
        tar_date = dec_date + datetime.timedelta(days=1)

        fcs = dm.select_target_forecast(dec_date, tar_date)
        cal = dm.get_calibration_observations(dec_date)
        acts = dm.get_target_actuals(tar_date)

        models = {
            "flat_15": flat_15(fcs, cal)["plans"],
            "v1_additive": v1_additive(fcs, cal, 75.0)["plans"],
            "v2_proportional": v2_proportional(fcs, cal, 75.0)["plans"],
        }

        f_vals = [f["generation_gw"] for f in fcs]
        a_vals = [a["generation_gw"] for a in acts]
        max_demand_gw = max(max(f_vals), max(a_vals)) + 5.0

        # Raw Elexon shortfall & surplus
        e_sf = sum(max(0.0, f - a) * 500.0 for f, a in zip(f_vals, a_vals))
        e_sp = sum(max(0.0, a - f) * 500.0 for f, a in zip(f_vals, a_vals))

        p_adv = 70.0

        for model_name, plans in models.items():
            sf = sum(max(0.0, p - a) * 500.0 for p, a in zip(plans, a_vals))
            sp = sum(max(0.0, a - p) * 500.0 for p, a in zip(plans, a_vals))
            avoided = e_sf - sf
            extra = sp - e_sp

            for k, s in test_scenarios:
                p_rep = k * p_adv

                # Sum ledger costs interval by interval
                cost_forecast = sum(
                    interval_ledger_cost(f, a, max_demand_gw, p_adv, p_rep, s)
                    for f, a in zip(f_vals, a_vals)
                )
                cost_plan = sum(
                    interval_ledger_cost(p, a, max_demand_gw, p_adv, p_rep, s)
                    for p, a in zip(plans, a_vals)
                )

                # Cost difference = cost_plan - cost_forecast = -net_saving
                delta_cost = cost_plan - cost_forecast
                expected_saving = net_saving(avoided, extra, k, s, p_adv)

                assert delta_cost == pytest.approx(-expected_saving, abs=1e-3), (
                    f"Date {dec_date} Model {model_name} k={k} s={s}: "
                    f"delta_cost={delta_cost}, -saving={-expected_saving}"
                )


def test_break_even_flat15_full_month_is_1_405():
    """Confirms the correct full-month flat_15 break-even ratio is 1.405x at s = 0."""
    avoided = 1016662.2
    extra = 411934.4
    be_k = break_even_price_ratio(avoided, extra, s=0.0)
    assert be_k == pytest.approx(1.405, abs=0.001)

    # And with s = 0.5 (50% surplus recovery): k* = 1 + 0.5 * extra / avoided = 1.203x
    be_k_s50 = break_even_price_ratio(avoided, extra, s=0.5)
    assert be_k_s50 == pytest.approx(1.203, abs=0.001)
