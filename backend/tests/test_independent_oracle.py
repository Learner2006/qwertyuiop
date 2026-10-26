"""Independent oracle test (Milestone R7 / Finding F7).

Tests energy shortfall, surplus, avoided shortfall, incremental surplus,
total cut volume, and break-even economics against hand-calculated,
independently derived ground truth values completely outside application code.
No self-referential or circular assertions.
"""

import pytest
from app.services.economics import break_even_price_ratio, cut_volume, net_saving
from app.services.metrics import (
    calculate_daily_metrics,
    calculate_shortfall_mwh,
    calculate_surplus_mwh,
)


def test_independent_4_interval_hand_calculated_oracle():
    """Hand-calculated 4-interval oracle.
    Each interval is 30 minutes (0.5 h).
    Energy factor: 1 GW * 1,000 MW/GW * 0.5 h = 500 MWh per GW.

    Interval 1:
      Forecast: 10.0 GW (5,000 MWh)
      Actual:    8.0 GW (4,000 MWh)
      Haircut:  15% -> Safe Plan: 8.5 GW (4,250 MWh)
      Elexon Shortfall: max(0, 10.0 - 8.0) * 500 = 1,000.0 MWh
      Elexon Surplus:   max(0, 8.0 - 10.0) * 500 = 0.0 MWh
      Safe Shortfall:   max(0, 8.5 - 8.0) * 500  = 250.0 MWh
      Safe Surplus:     max(0, 8.0 - 8.5) * 500  = 0.0 MWh
      Avoided Shortfall:   1,000.0 - 250.0 = 750.0 MWh
      Incremental Surplus: 0.0 - 0.0       = 0.0 MWh
      Cut Volume:          (10.0 - 8.5) * 500 = 750.0 MWh

    Interval 2 (Wind over-performs forecast):
      Forecast: 12.0 GW (6,000 MWh)
      Actual:   14.0 GW (7,000 MWh)
      Haircut:  15% -> Safe Plan: 10.2 GW (5,100 MWh)
      Elexon Shortfall: 0.0 MWh
      Elexon Surplus:   (14.0 - 12.0) * 500 = 1,000.0 MWh
      Safe Shortfall:   0.0 MWh
      Safe Surplus:     (14.0 - 10.2) * 500 = 1,900.0 MWh
      Avoided Shortfall:   0.0 MWh
      Incremental Surplus: 1,900.0 - 1,000.0 = 900.0 MWh
      Cut Volume:          (12.0 - 10.2) * 500 = 900.0 MWh

    Interval 3 (Caution completely eliminates shortfall and creates mild surplus):
      Forecast: 6.0 GW (3,000 MWh)
      Actual:   5.5 GW (2,750 MWh)
      Haircut:  15% -> Safe Plan: 5.1 GW (2,550 MWh)
      Elexon Shortfall: (6.0 - 5.5) * 500 = 250.0 MWh
      Elexon Surplus:   0.0 MWh
      Safe Shortfall:   0.0 MWh (eliminated!)
      Safe Surplus:     (5.5 - 5.1) * 500 = 200.0 MWh
      Avoided Shortfall:   250.0 - 0.0 = 250.0 MWh
      Incremental Surplus: 200.0 - 0.0 = 200.0 MWh
      Cut Volume:          (6.0 - 5.1) * 500 = 450.0 MWh
      Notice: Avoided (250) + Incremental (200) = Cut (450)

    Interval 4 (Deep generation slump):
      Forecast: 4.0 GW (2,000 MWh)
      Actual:   2.0 GW (1,000 MWh)
      Haircut:  15% -> Safe Plan: 3.4 GW (1,700 MWh)
      Elexon Shortfall: (4.0 - 2.0) * 500 = 1,000.0 MWh
      Elexon Surplus:   0.0 MWh
      Safe Shortfall:   (3.4 - 2.0) * 500 = 700.0 MWh
      Safe Surplus:     0.0 MWh
      Avoided Shortfall:   1,000.0 - 700.0 = 300.0 MWh
      Incremental Surplus: 0.0 MWh
      Cut Volume:          (4.0 - 3.4) * 500 = 300.0 MWh
    """
    forecast_gw = [10.0, 12.0, 6.0, 4.0]
    actual_gw = [8.0, 14.0, 5.5, 2.0]
    plan_gw = [8.5, 10.2, 5.1, 3.4]

    # Hand-calculated oracle values
    oracle_elexon_shortfall_mwh = [1000.0, 0.0, 250.0, 1000.0]
    oracle_elexon_surplus_mwh = [0.0, 1000.0, 0.0, 0.0]
    oracle_safe_shortfall_mwh = [250.0, 0.0, 0.0, 700.0]
    oracle_safe_surplus_mwh = [0.0, 1900.0, 200.0, 0.0]

    oracle_avoided_shortfall_mwh = [750.0, 0.0, 250.0, 300.0]
    oracle_incremental_surplus_mwh = [0.0, 900.0, 200.0, 0.0]
    oracle_cut_volume_mwh = [750.0, 900.0, 450.0, 300.0]

    # Oracle aggregates
    expected_tot_elexon_shortfall = 2250.0
    expected_tot_safe_shortfall = 950.0
    expected_tot_avoided_shortfall = 1300.0

    expected_tot_elexon_surplus = 1000.0
    expected_tot_safe_surplus = 2100.0
    expected_tot_incremental_surplus = 1100.0

    expected_tot_cut_volume = 2400.0

    # 1. Interval-by-interval oracle verification
    for i in range(4):
        f = forecast_gw[i]
        a = actual_gw[i]
        p = plan_gw[i]

        e_sf = calculate_shortfall_mwh(f, a)
        e_sp = calculate_surplus_mwh(f, a)
        s_sf = calculate_shortfall_mwh(p, a)
        s_sp = calculate_surplus_mwh(p, a)

        assert e_sf == pytest.approx(oracle_elexon_shortfall_mwh[i], abs=1e-6)
        assert e_sp == pytest.approx(oracle_elexon_surplus_mwh[i], abs=1e-6)
        assert s_sf == pytest.approx(oracle_safe_shortfall_mwh[i], abs=1e-6)
        assert s_sp == pytest.approx(oracle_safe_surplus_mwh[i], abs=1e-6)

        avoided = e_sf - s_sf
        extra = s_sp - e_sp
        cut = (f - p) * 500.0

        assert avoided == pytest.approx(oracle_avoided_shortfall_mwh[i], abs=1e-6)
        assert extra == pytest.approx(oracle_incremental_surplus_mwh[i], abs=1e-6)
        assert cut == pytest.approx(oracle_cut_volume_mwh[i], abs=1e-6)

        # Physical conservation identity per interval: Cut = Avoided + Extra
        assert cut == pytest.approx(avoided + extra, abs=1e-6)

    # 2. Daily aggregate metrics verification
    daily_res = calculate_daily_metrics(plan_gw, forecast_gw, actual_gw)

    assert daily_res["elexon_shortfall_mwh"] == pytest.approx(expected_tot_elexon_shortfall, abs=1e-6)
    assert daily_res["safe_shortfall_mwh"] == pytest.approx(expected_tot_safe_shortfall, abs=1e-6)
    assert daily_res["avoided_shortfall_mwh"] == pytest.approx(expected_tot_avoided_shortfall, abs=1e-6)

    assert daily_res["elexon_surplus_mwh"] == pytest.approx(expected_tot_elexon_surplus, abs=1e-6)
    assert daily_res["safe_surplus_mwh"] == pytest.approx(expected_tot_safe_surplus, abs=1e-6)
    assert daily_res["incremental_surplus_mwh"] == pytest.approx(expected_tot_incremental_surplus, abs=1e-6)

    assert daily_res["total_cut_mwh"] == pytest.approx(expected_tot_cut_volume, abs=1e-6)
    assert cut_volume(expected_tot_avoided_shortfall, expected_tot_incremental_surplus) == pytest.approx(
        expected_tot_cut_volume, abs=1e-6
    )

    # 3. Independent economic oracle verification
    # Break-even ratio k* = 1 + extra / avoided = 1 + 1100 / 1300 = 1.8461538...
    expected_be_k = 1.0 + (1100.0 / 1300.0)
    computed_be_k = break_even_price_ratio(expected_tot_avoided_shortfall, expected_tot_incremental_surplus, s=0.0)
    assert computed_be_k == pytest.approx(expected_be_k, abs=1e-6)
    assert computed_be_k == pytest.approx(1.8461538, abs=1e-5)

    # Net saving at k = 1.0, s = 0.0, P_adv = 70.0:
    # (1300 * 0 - 1100 * 1) * 70 = -77,000.0 £
    net_k1 = net_saving(expected_tot_avoided_shortfall, expected_tot_incremental_surplus, k=1.0, s=0.0, p_adv=70.0)
    assert net_k1 == pytest.approx(-77000.0, abs=1e-6)

    # Net saving at k = 2.0, s = 0.0, P_adv = 70.0:
    # (1300 * 1 - 1100 * 1) * 70 = +200 * 70 = +14,000.0 £
    net_k2 = net_saving(expected_tot_avoided_shortfall, expected_tot_incremental_surplus, k=2.0, s=0.0, p_adv=70.0)
    assert net_k2 == pytest.approx(14000.0, abs=1e-6)

    # Net saving at exact break-even k*: must be exactly 0.0 £
    net_at_be = net_saving(
        expected_tot_avoided_shortfall,
        expected_tot_incremental_surplus,
        k=expected_be_k,
        s=0.0,
        p_adv=70.0,
    )
    assert net_at_be == pytest.approx(0.0, abs=1e-5)


def test_independent_oracle_zero_cut_identity():
    """Oracle test: when plan == forecast, all haircuts and impacts are zero."""
    forecast = [5.0, 7.5, 3.2]
    actual = [4.0, 8.0, 2.0]
    plan = list(forecast)

    res = calculate_daily_metrics(plan, forecast, actual)
    assert res["avoided_shortfall_mwh"] == 0.0
    assert res["incremental_surplus_mwh"] == 0.0
    assert res["total_cut_mwh"] == 0.0
    assert res["safe_shortfall_mwh"] == res["elexon_shortfall_mwh"]
    assert res["safe_surplus_mwh"] == res["elexon_surplus_mwh"]
