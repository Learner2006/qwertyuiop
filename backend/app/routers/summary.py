"""Monthly summary endpoint for January 2026 performance replay.
Includes apples-to-apples shortfall and surplus comparisons, percentages of total wind generation,
flat-haircut baseline benchmarks (0-30%), efficiency comparisons, break-even ratio,
flat 15% pre-set benchmark, rolling mean-bias benchmark, percentile sensitivity sweep (p60-p90),
and cold-start (Jan 1-3) vs mature data-driven (Jan 4-30) split.
"""

import datetime
from typing import Dict, List
import numpy as np
from fastapi import APIRouter, Query

from app.config import settings
from app.schemas import (
    FlatHaircutBenchmark,
    ModelBenchmark,
    MonthSummaryResponse,
    PercentileSweepPoint,
)
from app.services.calibrate import calibrate_daily_forecast
from app.services.metrics import compute_reliability_metrics
from app.services.models import v2_proportional, flat_15, v1_additive
from app.services.prepare import DataManager

router = APIRouter(tags=["Summary"])

_summary_cache: Dict[float, MonthSummaryResponse] = {}


@router.get("/summary", response_model=MonthSummaryResponse)
def get_month_summary(
    percentile: float = Query(
        settings.DEFAULT_PERCENTILE,
        ge=settings.MIN_PERCENTILE,
        le=settings.MAX_PERCENTILE,
        description="Risk percentile between 60.0 and 90.0"
    )
):
    if percentile in _summary_cache:
        return _summary_cache[percentile]

    dm = DataManager.get_instance()
    
    # Store daily precomputed slices for fast aggregation
    days_data = []
    total_actual_mwh = 0.0
    total_fc_mwh = 0.0
    total_safe_plan_mwh = 0.0
    
    total_elexon_sf = 0.0
    total_safe_sf = 0.0
    total_elexon_surplus = 0.0
    total_safe_surplus = 0.0
    total_safe_margin_mwh = 0.0
    
    elex_abs_err = 0.0
    safe_abs_err = 0.0
    
    days_reduced = 0
    days_increased = 0
    days_breakeven_count = 0

    # Early cold-start (Jan 1-3) vs mature (Jan 4-30) accumulators
    cs_avoided_sf = 0.0
    cs_inc_surplus = 0.0
    cs_intervals = 0

    mature_avoided_sf = 0.0
    mature_inc_surplus = 0.0
    mature_intervals = 0

    for d in range(1, 31):
        dec_date = datetime.date(2026, 1, d)
        target_date = dec_date + datetime.timedelta(days=1)

        fc = dm.select_target_forecast(dec_date, target_date)
        calib_obs = dm.get_calibration_observations(dec_date)
        calib_res = calibrate_daily_forecast(fc, calib_obs, percentile=percentile)
        acts = dm.get_target_actuals(target_date)
        
        days_data.append({"fc": fc, "calib_obs": calib_obs, "acts": acts, "calib_res": calib_res})
        
        day_elex_sf = 0.0
        day_safe_sf = 0.0
        day_elex_surplus = 0.0
        day_safe_surplus = 0.0

        for f_item, safe_item, a_item in zip(fc, calib_res["intervals"], acts):
            f = f_item["generation_gw"]
            s = safe_item["safe_estimate_gw"]
            a = a_item["generation_gw"]
            
            total_actual_mwh += a * 500.0
            total_fc_mwh += f * 500.0
            total_safe_plan_mwh += s * 500.0
            total_safe_margin_mwh += (f - s) * 500.0
            
            e_sf = max(0.0, f - a) * 500.0
            s_sf = max(0.0, s - a) * 500.0
            e_surplus = max(0.0, a - f) * 500.0
            s_surplus = max(0.0, a - s) * 500.0
            
            day_elex_sf += e_sf
            day_safe_sf += s_sf
            day_elex_surplus += e_surplus
            day_safe_surplus += s_surplus

            total_elexon_sf += e_sf
            total_safe_sf += s_sf
            total_elexon_surplus += e_surplus
            total_safe_surplus += s_surplus
            
            elex_abs_err += abs(f - a)
            safe_abs_err += abs(s - a)

        day_avoided = day_elex_sf - day_safe_sf
        day_inc_surplus = day_safe_surplus - day_elex_surplus

        if d <= 3:
            cs_avoided_sf += day_avoided
            cs_inc_surplus += day_inc_surplus
            cs_intervals += len(fc)
        else:
            mature_avoided_sf += day_avoided
            mature_inc_surplus += day_inc_surplus
            mature_intervals += len(fc)
            
        day_saved = sum(
            (max(0.0, f["generation_gw"] - a["generation_gw"]) - max(0.0, s["safe_estimate_gw"] - a["generation_gw"])) * 500.0
            for f, s, a in zip(fc, calib_res["intervals"], acts)
        )
        if day_saved > 0.05:
            days_reduced += 1
        elif day_saved < -0.05:
            days_increased += 1

        if day_avoided > day_inc_surplus:
            days_breakeven_count += 1

    total_avoided_sf = total_elexon_sf - total_safe_sf
    total_incremental_surplus = total_safe_surplus - total_elexon_surplus
    
    elexon_mae = elex_abs_err / 1440.0
    safe_mae = safe_abs_err / 1440.0

    # Percentages of total wind generated (8,247,141.5 MWh)
    elex_sf_pct = (total_elexon_sf / total_actual_mwh) * 100.0
    safe_sf_pct = (total_safe_sf / total_actual_mwh) * 100.0
    avoided_sf_pct = (total_avoided_sf / total_actual_mwh) * 100.0
    
    elex_surplus_pct = (total_elexon_surplus / total_actual_mwh) * 100.0
    safe_surplus_pct = (total_safe_surplus / total_actual_mwh) * 100.0
    inc_surplus_pct = (total_incremental_surplus / total_actual_mwh) * 100.0

    # Level overforecast of raw Elexon forecast relative to outturn
    elexon_overforecast_pct = ((total_fc_mwh - total_actual_mwh) / total_actual_mwh) * 100.0

    # Matched haircut % (where flat haircut margin MWh matches our model's total margin MWh)
    matched_haircut_pct = (total_safe_margin_mwh / total_fc_mwh) * 100.0
    
    # Compute flat haircut benchmarks for [0, 5, 10, 15, 20, 25, 30]%
    flat_benchmarks: List[FlatHaircutBenchmark] = []
    for h in [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0]:
        h_ratio = h / 100.0
        h_sf = 0.0
        h_surplus = 0.0
        h_mae = 0.0
        for day in days_data:
            for f_item, a_item in zip(day["fc"], day["acts"]):
                f = f_item["generation_gw"]
                a = a_item["generation_gw"]
                p = max(0.0, f * (1.0 - h_ratio))
                h_sf += max(0.0, p - a) * 500.0
                h_surplus += max(0.0, a - p) * 500.0
                h_mae += abs(p - a)
        flat_benchmarks.append(FlatHaircutBenchmark(
            haircut_percent=h,
            shortfall_mwh=round(h_sf, 1),
            avoided_shortfall_mwh=round(total_elexon_sf - h_sf, 1),
            surplus_mwh=round(h_surplus, 1),
            incremental_surplus_mwh=round(h_surplus - total_elexon_surplus, 1),
            mae_gw=round(h_mae / 1440.0, 4),
        ))

    # Matched flat haircut calculation
    matched_sf = 0.0
    matched_surplus = 0.0
    m_ratio = matched_haircut_pct / 100.0
    for day in days_data:
        for f_item, a_item in zip(day["fc"], day["acts"]):
            f = f_item["generation_gw"]
            a = a_item["generation_gw"]
            p = max(0.0, f * (1.0 - m_ratio))
            matched_sf += max(0.0, p - a) * 500.0
            matched_surplus += max(0.0, a - p) * 500.0

    matched_avoided_sf = total_elexon_sf - matched_sf

    # Cut volume and efficiency calculations
    total_volume_cut = total_safe_margin_mwh
    safe_efficiency = (total_avoided_sf / total_volume_cut) * 100.0 if total_volume_cut > 0 else 0.0
    matched_flat_efficiency = (matched_avoided_sf / total_volume_cut) * 100.0 if total_volume_cut > 0 else 0.0
    breakeven_ratio = (total_incremental_surplus / total_avoided_sf) if total_avoided_sf > 0 else 1.0

    # 1. Flat 15% Benchmark (Fair pre-set rule)
    flat15_sf = 0.0
    flat15_surplus = 0.0
    flat15_mae = 0.0
    for day in days_data:
        for f_item, a_item in zip(day["fc"], day["acts"]):
            f = f_item["generation_gw"]
            a = a_item["generation_gw"]
            p = max(0.0, f * 0.85)
            flat15_sf += max(0.0, p - a) * 500.0
            flat15_surplus += max(0.0, a - p) * 500.0
            flat15_mae += abs(p - a)
    flat15_avoided = total_elexon_sf - flat15_sf
    flat15_extra = flat15_surplus - total_elexon_surplus
    flat15_cut = flat15_avoided + flat15_extra
    flat_15_benchmark = ModelBenchmark(
        name="Flat 15% Haircut",
        description="Fixed 15% reduction set in advance without hindsight.",
        cut_volume_mwh=round(flat15_cut, 1),
        cut_volume_pct=round((flat15_cut / total_fc_mwh) * 100.0, 1),
        avoided_shortfall_mwh=round(flat15_avoided, 1),
        extra_supply_mwh=round(flat15_extra, 1),
        efficiency_pct=round((flat15_avoided / flat15_cut) * 100.0, 1),
        breakeven_ratio=round(flat15_extra / flat15_avoided, 3),
        mae_gw=round(flat15_mae / 1440.0, 3),
    )

    # 2. Rolling Mean Bias Baseline (48h rolling average signed error floored at 0)
    mean_sf = 0.0
    mean_surplus = 0.0
    mean_mae = 0.0
    for day in days_data:
        errs = [obs["error_gw"] for obs in day["calib_obs"]]
        m_err = float(np.mean(errs)) if errs else 0.0
        margin = max(0.0, m_err)
        for f_item, a_item in zip(day["fc"], day["acts"]):
            f = f_item["generation_gw"]
            a = a_item["generation_gw"]
            p = max(0.0, f - margin)
            mean_sf += max(0.0, p - a) * 500.0
            mean_surplus += max(0.0, a - p) * 500.0
            mean_mae += abs(p - a)
    mean_avoided = total_elexon_sf - mean_sf
    mean_extra = mean_surplus - total_elexon_surplus
    mean_cut = mean_avoided + mean_extra
    rolling_mean_benchmark = ModelBenchmark(
        name="Rolling Mean Bias Correction",
        description="48-hour rolling mean forecast error subtracted from forecast.",
        cut_volume_mwh=round(mean_cut, 1),
        cut_volume_pct=round((mean_cut / total_fc_mwh) * 100.0, 1),
        avoided_shortfall_mwh=round(mean_avoided, 1),
        extra_supply_mwh=round(mean_extra, 1),
        efficiency_pct=round((mean_avoided / mean_cut) * 100.0, 1),
        breakeven_ratio=round(mean_extra / mean_avoided, 3),
        mae_gw=round(mean_mae / 1440.0, 3),
    )

    # 2b. Rolling Mean Ratio Baseline (48h rolling average percentage error)
    mean_ratio_sf = 0.0
    mean_ratio_surplus = 0.0
    mean_ratio_mae = 0.0
    for day in days_data:
        obs = day["calib_obs"]
        n = len(obs)
        w = min(1.0, n / 96.0)
        pct_errs = [(o["error_gw"] / o["forecast_gw"]) for o in obs] if obs else []
        raw_m = max(0.0, float(np.mean(pct_errs))) if pct_errs else 0.15
        ratio_m = (1.0 - w) * 0.15 + w * raw_m
        for f_item, a_item in zip(day["fc"], day["acts"]):
            f = f_item["generation_gw"]
            a = a_item["generation_gw"]
            p = max(0.0, f * (1.0 - ratio_m))
            mean_ratio_sf += max(0.0, p - a) * 500.0
            mean_ratio_surplus += max(0.0, a - p) * 500.0
            mean_ratio_mae += abs(p - a)
    mr_avoided = total_elexon_sf - mean_ratio_sf
    mr_extra = mean_ratio_surplus - total_elexon_surplus
    mr_cut = mr_avoided + mr_extra
    rolling_mean_ratio_benchmark = ModelBenchmark(
        name="Rolling Mean Ratio Baseline",
        description="48-hour rolling mean forecast error ratio (e/f) subtracted from forecast.",
        cut_volume_mwh=round(mr_cut, 1),
        cut_volume_pct=round((mr_cut / total_fc_mwh) * 100.0, 1),
        avoided_shortfall_mwh=round(mr_avoided, 1),
        extra_supply_mwh=round(mr_extra, 1),
        efficiency_pct=round((mr_avoided / mr_cut) * 100.0, 1) if mr_cut > 0 else 0.0,
        breakeven_ratio=round(mr_extra / mr_avoided, 3) if mr_avoided > 0 else 1.0,
        mae_gw=round(mean_ratio_mae / 1440.0, 3),
    )

    # Daily arrays for v1, v2, and Flat 15% across first-half (Jan 1-15) and second-half (Jan 16-30 out-of-sample)
    daily_v1 = []
    daily_v2 = []
    daily_f15 = []
    daily_elex = []
    
    for day in days_data:
        v2_res = v2_proportional(day["fc"], day["calib_obs"], 75.0)
        v2_plans = v2_res["plans"]
        
        d_v1_sf, d_v1_surplus, d_v1_mae = 0.0, 0.0, 0.0
        d_v2_sf, d_v2_surplus, d_v2_mae = 0.0, 0.0, 0.0
        d_f15_sf, d_f15_surplus, d_f15_mae = 0.0, 0.0, 0.0
        d_elex_sf, d_elex_surplus, d_fc = 0.0, 0.0, 0.0
        
        for f_item, s_item, a_item, s2 in zip(day["fc"], day["calib_res"]["intervals"], day["acts"], v2_plans):
            f = f_item["generation_gw"]
            a = a_item["generation_gw"]
            s1 = s_item["safe_estimate_gw"]
            sf15 = max(0.0, f * 0.85)
            
            d_fc += f * 500.0
            d_elex_sf += max(0.0, f - a) * 500.0
            d_elex_surplus += max(0.0, a - f) * 500.0
            
            d_v1_sf += max(0.0, s1 - a) * 500.0
            d_v1_surplus += max(0.0, a - s1) * 500.0
            d_v1_mae += abs(s1 - a)
            
            d_v2_sf += max(0.0, s2 - a) * 500.0
            d_v2_surplus += max(0.0, a - s2) * 500.0
            d_v2_mae += abs(s2 - a)
            
            d_f15_sf += max(0.0, sf15 - a) * 500.0
            d_f15_surplus += max(0.0, a - sf15) * 500.0
            d_f15_mae += abs(sf15 - a)
            
        daily_elex.append({"fc": d_fc, "sf": d_elex_sf, "surplus": d_elex_surplus})
        daily_v1.append({"sf": d_v1_sf, "surplus": d_v1_surplus, "mae": d_v1_mae})
        daily_v2.append({"sf": d_v2_sf, "surplus": d_v2_surplus, "mae": d_v2_mae})
        daily_f15.append({"sf": d_f15_sf, "surplus": d_f15_surplus, "mae": d_f15_mae})

    def calc_period_benchmark(name, desc, days_range, d_model):
        tot_fc_p = sum(daily_elex[i]["fc"] for i in days_range)
        tot_elex_sf_p = sum(daily_elex[i]["sf"] for i in days_range)
        tot_elex_sur_p = sum(daily_elex[i]["surplus"] for i in days_range)
        
        tot_sf = sum(d_model[i]["sf"] for i in days_range)
        tot_sur = sum(d_model[i]["surplus"] for i in days_range)
        tot_mae = sum(d_model[i]["mae"] for i in days_range)
        
        avoided = tot_elex_sf_p - tot_sf
        extra = tot_sur - tot_elex_sur_p
        cut = avoided + extra
        eff = (avoided / cut) * 100.0 if cut > 0 else 0.0
        be = (extra / avoided) if avoided > 0 else 999.0
        n_slots = len(days_range) * 48
        return ModelBenchmark(
            name=name,
            description=desc,
            cut_volume_mwh=round(cut, 1),
            cut_volume_pct=round((cut / tot_fc_p) * 100.0, 1),
            avoided_shortfall_mwh=round(avoided, 1),
            extra_supply_mwh=round(extra, 1),
            efficiency_pct=round(eff, 1),
            breakeven_ratio=round(be, 3),
            mae_gw=round(tot_mae / n_slots, 3),
        )

    first_half_days = range(0, 15)   # Jan 1-15 decisions
    second_half_days = range(15, 30) # Jan 16-30 decisions
    all_days = range(0, 30)

    first_half_v1 = calc_period_benchmark("v1 (Additive p75) - First Half", "First-half training window (Jan 1-15)", first_half_days, daily_v1)
    first_half_v2 = calc_period_benchmark("v2 (Proportional p75) - First Half", "First-half parameter selection (Jan 1-15)", first_half_days, daily_v2)
    first_half_flat15 = calc_period_benchmark("Flat 15% - First Half", "First-half pre-set baseline (Jan 1-15)", first_half_days, daily_f15)

    second_half_v1 = calc_period_benchmark("v1 (Additive p75) - Second Half", "Out-of-sample test window (Jan 16-30)", second_half_days, daily_v1)
    second_half_v2 = calc_period_benchmark("v2 (Proportional p75) - Second Half", "Out-of-sample test window (Jan 16-30)", second_half_days, daily_v2)
    second_half_flat15 = calc_period_benchmark("Flat 15% - Second Half", "Out-of-sample pre-set baseline (Jan 16-30)", second_half_days, daily_f15)

    v1_additive_benchmark = calc_period_benchmark("v1 (Additive p75)", "Original declared model (48h error quantile floored at 0).", all_days, daily_v1)
    v2_proportional_benchmark = calc_period_benchmark("v2 (Proportional p75)", "Proportional error quantile applied as fractional haircut.", all_days, daily_v2)

    # 3. Percentile Sensitivity Sweep (p60 to p90 in steps of 5)
    percentile_sweep: List[PercentileSweepPoint] = []
    for p_val in [60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0]:
        p_sf = 0.0
        p_surplus = 0.0
        p_mae = 0.0
        for day in days_data:
            calib = calibrate_daily_forecast(day["fc"], day["calib_obs"], percentile=p_val)
            for s_item, a_item in zip(calib["intervals"], day["acts"]):
                p = s_item["safe_estimate_gw"]
                a = a_item["generation_gw"]
                p_sf += max(0.0, p - a) * 500.0
                p_surplus += max(0.0, a - p) * 500.0
                p_mae += abs(p - a)
        p_avoided = total_elexon_sf - p_sf
        p_extra = p_surplus - total_elexon_surplus
        p_cut = p_avoided + p_extra
        percentile_sweep.append(PercentileSweepPoint(
            percentile=p_val,
            cut_volume_mwh=round(p_cut, 1),
            cut_volume_pct=round((p_cut / total_fc_mwh) * 100.0, 1),
            avoided_shortfall_mwh=round(p_avoided, 1),
            extra_supply_mwh=round(p_extra, 1),
            efficiency_pct=round((p_avoided / p_cut) * 100.0, 1) if p_cut > 0 else 0.0,
            breakeven_ratio=round(p_extra / p_avoided, 3) if p_avoided > 0 else 1.0,
            mae_gw=round(p_mae / 1440.0, 3),
        ))

    sentence = (
        f"Across Jan 2026, planning with our estimate would have avoided "
        f"{round(total_avoided_sf):,} MWh of shortfall ({avoided_sf_pct:.1f}% of total wind) "
        f"while arranging {round(total_incremental_surplus):,} MWh extra in advance ({inc_surplus_pct:.1f}% of total wind). "
        f"Break-even: the cautious plan pays off if replacement power costs at least {breakeven_ratio:.2f}x the cost of excess advance supply."
    )

    cold_start_ratio = (cs_avoided_sf / cs_inc_surplus) if cs_inc_surplus > 0 else 1.0
    mature_be_ratio = (mature_inc_surplus / mature_avoided_sf) if mature_avoided_sf > 0 else 1.0

    res = MonthSummaryResponse(
        decision_dates_count=30,
        total_target_intervals=1440,
        period_start="2026-01-01",
        period_end="2026-01-30",
        target_start="2026-01-02",
        target_end="2026-01-31",
        percentile=percentile,
        
        total_actual_wind_mwh=round(total_actual_mwh, 1),
        total_elexon_forecast_mwh=round(total_fc_mwh, 1),
        elexon_overforecast_pct=round(elexon_overforecast_pct, 2),
        
        total_elexon_shortfall_mwh=round(total_elexon_sf, 1),
        total_safe_shortfall_mwh=round(total_safe_sf, 1),
        total_avoided_shortfall_mwh=round(total_avoided_sf, 1),
        elexon_shortfall_pct_of_wind=round(elex_sf_pct, 1),
        safe_shortfall_pct_of_wind=round(safe_sf_pct, 1),
        avoided_shortfall_pct_of_wind=round(avoided_sf_pct, 1),
        
        total_elexon_surplus_mwh=round(total_elexon_surplus, 1),
        total_safe_surplus_mwh=round(total_safe_surplus, 1),
        total_incremental_surplus_mwh=round(total_incremental_surplus, 1),
        total_extra_advance_planned_mwh=round(total_incremental_surplus, 1),
        elexon_surplus_pct_of_wind=round(elex_surplus_pct, 1),
        safe_surplus_pct_of_wind=round(safe_surplus_pct, 1),
        incremental_surplus_pct_of_wind=round(inc_surplus_pct, 1),

        total_volume_cut_mwh=round(total_volume_cut, 1),
        safe_efficiency_pct=round(safe_efficiency, 2),
        matched_flat_efficiency_pct=round(matched_flat_efficiency, 2),
        breakeven_ratio=round(breakeven_ratio, 3),

        cold_start_days=3,
        cold_start_intervals=cs_intervals,
        cold_start_avoided_shortfall_mwh=round(cs_avoided_sf, 1),
        cold_start_incremental_surplus_mwh=round(cs_inc_surplus, 1),
        cold_start_ratio=round(cold_start_ratio, 3),

        mature_days=27,
        mature_intervals=mature_intervals,
        mature_avoided_shortfall_mwh=round(mature_avoided_sf, 1),
        mature_incremental_surplus_mwh=round(mature_inc_surplus, 1),
        mature_breakeven_ratio=round(mature_be_ratio, 3),

        flat_15_benchmark=flat_15_benchmark,
        rolling_mean_benchmark=rolling_mean_benchmark,
        rolling_mean_ratio_benchmark=rolling_mean_ratio_benchmark,
        v1_additive_benchmark=v1_additive_benchmark,
        v2_proportional_benchmark=v2_proportional_benchmark,
        first_half_v1=first_half_v1,
        first_half_v2=first_half_v2,
        first_half_flat15=first_half_flat15,
        second_half_v1=second_half_v1,
        second_half_v2=second_half_v2,
        second_half_flat15=second_half_flat15,
        percentile_sweep=percentile_sweep,

        elexon_mae_gw=round(elexon_mae, 4),
        safe_mae_gw=round(safe_mae, 4),
        
        matched_haircut_percent=round(matched_haircut_pct, 2),
        matched_haircut_shortfall_mwh=round(matched_sf, 1),
        matched_haircut_avoided_mwh=round(matched_avoided_sf, 1),
        matched_haircut_incremental_surplus_mwh=round(matched_surplus - total_elexon_surplus, 1),
        
        flat_benchmarks=flat_benchmarks,
        days_shortfall_reduced=days_reduced,
        days_shortfall_increased=days_increased,
        days_breakeven_count=days_breakeven_count,
        summary_sentence=sentence,
    )
    _summary_cache[percentile] = res
    return res
