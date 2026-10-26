"""Unified Replay Engine for Wind Day-Ahead Estimator.
Canonical and single source of truth for historical evaluation across all models.
Loops over intervals computing shortfall, surplus, cut, avoided shortfall,
and MAE metrics with no duplicated loops elsewhere.
"""

import datetime
from typing import Any, Dict, Iterable, List, Optional, Union
import numpy as np

from app.config import settings
from app.services.economics import break_even_price_ratio, cut_volume, net_saving
from app.services.models import get_model
from app.services.prepare import DataManager


_DAY_INPUTS_CACHE: Dict[datetime.date, Dict[str, Any]] = {}


def get_cached_day_inputs(dec_date: datetime.date, dm: Optional[DataManager] = None) -> Dict[str, Any]:
    """Retrieves and caches daily replay inputs (forecast, calibration obs, actuals)
    to prevent redundant DataFrame slicing across multiple model replays and sweeps.
    """
    if dec_date in _DAY_INPUTS_CACHE:
        return _DAY_INPUTS_CACHE[dec_date]

    mgr = dm or DataManager.get_instance()
    target_date = dec_date + datetime.timedelta(days=1)

    fc = mgr.select_target_forecast(dec_date, target_date)
    cal = mgr.get_calibration_observations(dec_date)
    acts = mgr.get_target_actuals(target_date)

    f_gw = np.array([float(x["generation_gw"]) for x in fc], dtype=float)
    a_gw = np.array([float(x["generation_gw"]) for x in acts], dtype=float)

    # Precalculate raw Elexon interval metrics
    e_sf = np.maximum(0.0, f_gw - a_gw) * settings.MWH_FACTOR
    e_sp = np.maximum(0.0, a_gw - f_gw) * settings.MWH_FACTOR

    cached = {
        "dec_date": dec_date,
        "target_date": target_date,
        "fc": fc,
        "cal": cal,
        "acts": acts,
        "f_gw": f_gw,
        "a_gw": a_gw,
        "e_sf": e_sf,
        "e_sp": e_sp,
    }
    _DAY_INPUTS_CACHE[dec_date] = cached
    return cached


def clear_replay_cache() -> None:
    """Clears the daily replay cache (used in testing or dataset reloads)."""
    _DAY_INPUTS_CACHE.clear()


def parse_day_to_date(day_val: Union[int, datetime.date, str]) -> datetime.date:
    """Normalizes day parameter to datetime.date object."""
    if isinstance(day_val, datetime.date):
        return day_val
    if isinstance(day_val, int):
        return datetime.date(2026, 1, day_val)
    if isinstance(day_val, str):
        return datetime.date.fromisoformat(day_val)
    raise ValueError(f"Unsupported decision day format: {day_val}")


def replay(
    model_name: str,
    decision_days: Iterable[Union[int, datetime.date, str]],
    percentile: float = settings.DEFAULT_PERCENTILE,
    s: float = 0.0,
    dm: Optional[DataManager] = None,
    **params: Any,
) -> Dict[str, Any]:
    """Replays a given model over a collection of decision dates.

    Args:
        model_name: Registered model identifier ('v1_additive', 'v2_proportional',
                    'flat_15', 'expanding_ratio', 'rolling_mean_bias', 'rolling_mean_ratio', 'flat_haircut')
        decision_days: Iterable of day numbers (1..30) or date objects
        percentile: Risk percentile for quantile-based models (default 75.0)
        s: Surplus recovery factor in [0, 1] (default 0.0)
        dm: Optional DataManager instance
        **params: Additional model hyperparameters (e.g. haircut for flat_haircut)

    Returns:
        Dictionary containing total and per-day metrics: avoided shortfall, extra supply,
        volume cut, shortfall, surplus, MAE, break-even ratio, and daily track record.
    """
    mgr = dm or DataManager.get_instance()
    model_fn = get_model(model_name)
    dates = [parse_day_to_date(d) for d in decision_days]

    # Pre-gather completed history if model is expanding_ratio
    needs_expanding_history = model_name == "expanding_ratio"
    completed_history_acts: Dict[datetime.date, List[dict]] = {}
    completed_history_fcs: Dict[datetime.date, List[dict]] = {}

    if needs_expanding_history:
        # Load all potential target days for January 2026
        for d_num in range(1, 31):
            d_date = datetime.date(2026, 1, d_num)
            inp = get_cached_day_inputs(d_date, mgr)
            completed_history_acts[inp["target_date"]] = inp["acts"]
            completed_history_fcs[inp["target_date"]] = inp["fc"]

    per_day: List[Dict[str, Any]] = []

    tot_fc_mwh = 0.0
    tot_act_mwh = 0.0
    tot_plan_mwh = 0.0
    tot_cut_mwh = 0.0

    tot_e_sf_mwh = 0.0
    tot_m_sf_mwh = 0.0
    tot_avoided_sf_mwh = 0.0

    tot_e_sp_mwh = 0.0
    tot_m_sp_mwh = 0.0
    tot_extra_sp_mwh = 0.0

    tot_e_abs_err = 0.0
    tot_m_abs_err = 0.0
    tot_slots = 0

    days_reduced = 0
    days_increased = 0
    days_be_under_2x = 0

    for dec_date in dates:
        day_inp = get_cached_day_inputs(dec_date, mgr)
        fc = day_inp["fc"]
        cal = day_inp["cal"]
        acts = day_inp["acts"]
        f_gw = day_inp["f_gw"]
        a_gw = day_inp["a_gw"]
        e_sf = day_inp["e_sf"]
        e_sp = day_inp["e_sp"]

        # Call model to produce plan
        model_kwargs = {
            "percentile": percentile,
            "calibration_records": cal,
            **params,
        }
        if needs_expanding_history:
            # Completed delivery days strictly before dec_date:
            # Target day D-1 delivered prior to dec_date 09:00 UTC.
            # Targets start at Jan 2. So past targets are Jan 2 through target of (dec_date - 1 day).
            comp_acts = []
            comp_fcs = []
            cur_target = dec_date  # target day that delivered up to 00:00 UTC on dec_date is dec_date
            start_target = datetime.date(2026, 1, 2)
            d_walk = start_target
            while d_walk < cur_target:
                if d_walk in completed_history_acts:
                    comp_acts.extend(completed_history_acts[d_walk])
                    comp_fcs.extend(completed_history_fcs[d_walk])
                d_walk += datetime.timedelta(days=1)
            model_kwargs["completed_days_actuals"] = comp_acts
            model_kwargs["completed_days_forecasts"] = comp_fcs

        res = model_fn(fc, **model_kwargs)
        plans = res["plans"]
        p_gw = np.array([float(x) for x in plans], dtype=float)

        # Vectorized interval calculations
        m_sf = np.maximum(0.0, p_gw - a_gw) * settings.MWH_FACTOR
        m_sp = np.maximum(0.0, a_gw - p_gw) * settings.MWH_FACTOR
        avoided_int = e_sf - m_sf
        extra_int = m_sp - e_sp
        cut_int = (f_gw - p_gw) * settings.MWH_FACTOR

        day_fc_mwh = float(f_gw.sum() * settings.MWH_FACTOR)
        day_act_mwh = float(a_gw.sum() * settings.MWH_FACTOR)
        day_plan_mwh = float(p_gw.sum() * settings.MWH_FACTOR)
        day_cut_mwh = float(cut_int.sum())

        day_e_sf = float(e_sf.sum())
        day_m_sf = float(m_sf.sum())
        day_avoided_sf = float(avoided_int.sum())

        day_e_sp = float(e_sp.sum())
        day_m_sp = float(m_sp.sum())
        day_extra_sp = float(extra_int.sum())

        day_e_mae = float(np.mean(np.abs(f_gw - a_gw)))
        day_m_mae = float(np.mean(np.abs(p_gw - a_gw)))

        is_red = day_avoided_sf > 0.05
        is_inc = day_avoided_sf < -0.05
        is_be_2x = day_avoided_sf > day_extra_sp

        if is_red:
            days_reduced += 1
        elif is_inc:
            days_increased += 1
        if is_be_2x:
            days_be_under_2x += 1

        tot_fc_mwh += day_fc_mwh
        tot_act_mwh += day_act_mwh
        tot_plan_mwh += day_plan_mwh
        tot_cut_mwh += day_cut_mwh

        tot_e_sf_mwh += day_e_sf
        tot_m_sf_mwh += day_m_sf
        tot_avoided_sf_mwh += day_avoided_sf

        tot_e_sp_mwh += day_e_sp
        tot_m_sp_mwh += day_m_sp
        tot_extra_sp_mwh += day_extra_sp

        tot_e_abs_err += float(np.abs(f_gw - a_gw).sum())
        tot_m_abs_err += float(np.abs(p_gw - a_gw).sum())
        tot_slots += len(f_gw)

        per_day.append({
            "decision_date": dec_date.isoformat(),
            "target_date": day_inp["target_date"].isoformat(),
            "target_date_label": day_inp["target_date"].strftime("%d %b"),
            "elexon_shortfall_mwh": round(day_e_sf, 1),
            "safe_shortfall_mwh": round(day_m_sf, 1),
            "avoided_shortfall_mwh": round(day_avoided_sf, 1),
            "elexon_surplus_mwh": round(day_e_sp, 1),
            "safe_surplus_mwh": round(day_m_sp, 1),
            "extra_supply_mwh": round(day_extra_sp, 1),
            "volume_cut_mwh": round(day_cut_mwh, 1),
            "elexon_mae_gw": round(day_e_mae, 4),
            "safe_mae_gw": round(day_m_mae, 4),
            "is_shortfall_reduced": is_red,
            "is_break_even_under_2x": is_be_2x,
            "plans": [round(x, 4) for x in plans],
            "raw_result": res,
        })

    eff_pct = (tot_avoided_sf_mwh / tot_cut_mwh * 100.0) if tot_cut_mwh > 0 else 0.0
    be_ratio = break_even_price_ratio(tot_avoided_sf_mwh, tot_extra_sp_mwh, s=s)

    elex_mae_gw = (tot_e_abs_err / tot_slots) if tot_slots > 0 else 0.0
    model_mae_gw = (tot_m_abs_err / tot_slots) if tot_slots > 0 else 0.0

    return {
        "model_name": model_name,
        "percentile": percentile,
        "s": s,
        "total_target_intervals": tot_slots,
        "total_actual_wind_mwh": round(tot_act_mwh, 1),
        "total_elexon_forecast_mwh": round(tot_fc_mwh, 1),
        "total_model_plan_mwh": round(tot_plan_mwh, 1),
        "total_volume_cut_mwh": round(tot_cut_mwh, 1),
        "total_elexon_shortfall_mwh": round(tot_e_sf_mwh, 1),
        "total_safe_shortfall_mwh": round(tot_m_sf_mwh, 1),
        "total_avoided_shortfall_mwh": round(tot_avoided_sf_mwh, 1),
        "total_elexon_surplus_mwh": round(tot_e_sp_mwh, 1),
        "total_safe_surplus_mwh": round(tot_m_sp_mwh, 1),
        "total_incremental_surplus_mwh": round(tot_extra_sp_mwh, 1),
        "efficiency_pct": round(eff_pct, 2),
        "breakeven_ratio": round(be_ratio, 3) if be_ratio is not None else None,
        "elexon_mae_gw": round(elex_mae_gw, 4),
        "safe_mae_gw": round(model_mae_gw, 4),
        "days_shortfall_reduced": days_reduced,
        "days_shortfall_increased": days_increased,
        "days_break_even_under_2x": days_be_under_2x,
        "completed_days_count": len(per_day),
        "per_day": per_day,
    }
