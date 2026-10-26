"""Summary router for Wind Day-Ahead Estimator.
Full-month January 2026 replay summary across 30 decision dates (1,440 half-hours).
Evaluates candidate models, first-half/second-half splits,
flat-haircut baseline sweeps, efficiency comparisons, break-even ratio,
and cold start vs mature data phases.
Uses unified replay engine as the single source of truth.
"""

from typing import Dict, List
from fastapi import APIRouter, Query

from app.config import settings
from app.schemas import (
    FlatHaircutBenchmark,
    ModelBenchmark,
    MonthSummaryResponse,
    PercentileSweepPoint,
)
from app.services.replay import replay

router = APIRouter(tags=["Summary"])

_summary_cache: Dict[float, MonthSummaryResponse] = {}


def _make_benchmark(
    name: str, desc: str, r: dict, total_fc_mwh: float
) -> ModelBenchmark:
    cut = r["total_volume_cut_mwh"]
    cut_pct = (
        round((cut / total_fc_mwh) * 100.0, 1) if total_fc_mwh > 0 else 0.0
    )
    return ModelBenchmark(
        name=name,
        description=desc,
        cut_volume_mwh=cut,
        cut_volume_pct=cut_pct,
        avoided_shortfall_mwh=r["total_avoided_shortfall_mwh"],
        extra_supply_mwh=r["total_incremental_surplus_mwh"],
        efficiency_pct=r["efficiency_pct"],
        breakeven_ratio=r["breakeven_ratio"] if r["breakeven_ratio"] is not None else 1.0,
        mae_gw=r["safe_mae_gw"],
    )


@router.get("/summary", response_model=MonthSummaryResponse)
def get_month_summary(
    percentile: float = Query(
        settings.DEFAULT_PERCENTILE,
        ge=settings.MIN_PERCENTILE,
        le=settings.MAX_PERCENTILE,
        description="Risk percentile between 60.0 and 90.0 (default 75.0)",
    )
):
    if percentile in _summary_cache:
        return _summary_cache[percentile]

    all_days = range(1, 31)
    first_half_days = range(1, 16)
    second_half_days = range(16, 31)
    cold_start_days = range(1, 4)
    mature_days = range(4, 31)

    # 1. Main headline replay (v1_additive)
    r_v1 = replay("v1_additive", all_days, percentile=percentile)
    tot_fc_mwh = r_v1["total_elexon_forecast_mwh"]
    tot_act_mwh = r_v1["total_actual_wind_mwh"]

    # 2. Benchmark models
    r_f15 = replay("flat_15", all_days)
    r_rmb = replay("rolling_mean_bias", all_days)
    r_rmr = replay("rolling_mean_ratio", all_days)
    r_v2 = replay("v2_proportional", all_days, percentile=percentile)

    # 3. Phase 1 (Jan 1-3) vs Phase 2 (Jan 4-30)
    r_cs = replay("v1_additive", cold_start_days, percentile=percentile)
    r_mat = replay("v1_additive", mature_days, percentile=percentile)

    cs_avoided = r_cs["total_avoided_shortfall_mwh"]
    cs_extra = r_cs["total_incremental_surplus_mwh"]
    cs_ratio = (cs_avoided / cs_extra) if cs_extra > 0 else 1.0

    # 4. Period benchmarks (First Half vs Second Half)
    r_v1_h1 = replay("v1_additive", first_half_days, percentile=percentile)
    r_v2_h1 = replay("v2_proportional", first_half_days, percentile=percentile)
    r_f15_h1 = replay("flat_15", first_half_days)

    r_v1_h2 = replay("v1_additive", second_half_days, percentile=percentile)
    r_v2_h2 = replay("v2_proportional", second_half_days, percentile=percentile)
    r_f15_h2 = replay("flat_15", second_half_days)

    first_half_v1 = _make_benchmark(
        "v1 (Additive p75) - First Half",
        "First-half training window (Jan 1-15)",
        r_v1_h1,
        r_v1_h1["total_elexon_forecast_mwh"],
    )
    first_half_v2 = _make_benchmark(
        "v2 (Proportional p75) - First Half",
        "First-half parameter selection (Jan 1-15)",
        r_v2_h1,
        r_v2_h1["total_elexon_forecast_mwh"],
    )
    first_half_flat15 = _make_benchmark(
        "Flat 15% - First Half",
        "First-half pre-set baseline (Jan 1-15)",
        r_f15_h1,
        r_f15_h1["total_elexon_forecast_mwh"],
    )

    second_half_v1 = _make_benchmark(
        "v1 (Additive p75) - Second Half",
        "Second-half evaluation window (Jan 16-30)",
        r_v1_h2,
        r_v1_h2["total_elexon_forecast_mwh"],
    )
    second_half_v2 = _make_benchmark(
        "v2 (Proportional p75) - Second Half",
        "Second-half evaluation window (Jan 16-30)",
        r_v2_h2,
        r_v2_h2["total_elexon_forecast_mwh"],
    )
    second_half_flat15 = _make_benchmark(
        "Flat 15% - Second Half",
        "Second-half pre-set baseline (Jan 16-30)",
        r_f15_h2,
        r_f15_h2["total_elexon_forecast_mwh"],
    )

    flat_15_benchmark = _make_benchmark(
        "Flat 15% Haircut",
        "Fixed 15% reduction set in advance.",
        r_f15,
        tot_fc_mwh,
    )
    rolling_mean_benchmark = _make_benchmark(
        "Rolling Mean Bias Correction",
        "48-hour rolling mean forecast error subtracted from forecast.",
        r_rmb,
        tot_fc_mwh,
    )
    rolling_mean_ratio_benchmark = _make_benchmark(
        "Rolling Mean Ratio Baseline",
        "48-hour rolling mean forecast error ratio (e/f) subtracted from forecast.",
        r_rmr,
        tot_fc_mwh,
    )
    v1_additive_benchmark = _make_benchmark(
        "v1 (Additive p75)",
        "Original declared model (48h error quantile floored at 0).",
        r_v1,
        tot_fc_mwh,
    )
    v2_proportional_benchmark = _make_benchmark(
        "v2 (Proportional p75)",
        "Proportional error quantile applied as fractional haircut.",
        r_v2,
        tot_fc_mwh,
    )

    # 5. Flat Haircut Trade-off Curve (0% to 30% in steps of 5%)
    flat_benchmarks: List[FlatHaircutBenchmark] = []
    for h in [0, 5, 10, 15, 20, 25, 30]:
        h_ratio = h / 100.0
        r_h = replay("flat_haircut", all_days, haircut=h_ratio)
        flat_benchmarks.append(
            FlatHaircutBenchmark(
                haircut_percent=h,
                shortfall_mwh=r_h["total_safe_shortfall_mwh"],
                avoided_shortfall_mwh=r_h["total_avoided_shortfall_mwh"],
                surplus_mwh=r_h["total_safe_surplus_mwh"],
                incremental_surplus_mwh=r_h["total_incremental_surplus_mwh"],
                mae_gw=r_h["safe_mae_gw"],
            )
        )

    # 6. Matched Haircut Baseline (match total volume cut of r_v1)
    target_cut = r_v1["total_volume_cut_mwh"]
    lo_h, hi_h = 0.0, 0.60
    for _ in range(40):
        mid_h = (lo_h + hi_h) / 2.0
        c = (1.0 - (1.0 - mid_h)) * tot_fc_mwh
        if c < target_cut:
            lo_h = mid_h
        else:
            hi_h = mid_h
    matched_h = (lo_h + hi_h) / 2.0
    r_matched = replay("flat_haircut", all_days, haircut=matched_h)

    # 7. Percentile Sensitivity Sweep (p60 to p90 in steps of 5)
    percentile_sweep: List[PercentileSweepPoint] = []
    for p_val in [60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0]:
        r_p = replay("v1_additive", all_days, percentile=p_val)
        p_cut = r_p["total_volume_cut_mwh"]
        p_avoided = r_p["total_avoided_shortfall_mwh"]
        percentile_sweep.append(
            PercentileSweepPoint(
                percentile=p_val,
                cut_volume_mwh=p_cut,
                cut_volume_pct=round((p_cut / tot_fc_mwh) * 100.0, 1),
                avoided_shortfall_mwh=p_avoided,
                extra_supply_mwh=r_p["total_incremental_surplus_mwh"],
                efficiency_pct=r_p["efficiency_pct"],
                breakeven_ratio=r_p["breakeven_ratio"] if r_p["breakeven_ratio"] is not None else 1.0,
                mae_gw=r_p["safe_mae_gw"],
            )
        )

    elex_overforecast_pct = (
        ((tot_fc_mwh - tot_act_mwh) / tot_act_mwh) * 100.0
        if tot_act_mwh > 0
        else 0.0
    )
    elex_sf_pct = (r_v1["total_elexon_shortfall_mwh"] / tot_act_mwh) * 100.0
    safe_sf_pct = (r_v1["total_safe_shortfall_mwh"] / tot_act_mwh) * 100.0
    avoided_sf_pct = (r_v1["total_avoided_shortfall_mwh"] / tot_act_mwh) * 100.0

    elex_sur_pct = (r_v1["total_elexon_surplus_mwh"] / tot_act_mwh) * 100.0
    safe_sur_pct = (r_v1["total_safe_surplus_mwh"] / tot_act_mwh) * 100.0
    inc_sur_pct = (r_v1["total_incremental_surplus_mwh"] / tot_act_mwh) * 100.0

    sentence = (
        f"Across Jan 2026, planning with our estimate would have avoided "
        f"{round(r_v1['total_avoided_shortfall_mwh']):,} MWh of shortfall ({avoided_sf_pct:.1f}% of total wind) "
        f"while arranging {round(r_v1['total_incremental_surplus_mwh']):,} MWh extra in advance ({inc_sur_pct:.1f}% of total wind). "
        f"Break-even: the cautious plan pays off if replacement power costs at least {r_v1['breakeven_ratio']:.2f}x advance power (at s=0 surplus recovery)."
    )

    res = MonthSummaryResponse(
        decision_dates_count=len(all_days),
        total_target_intervals=settings.FULL_MONTH_SLOTS,
        period_start="2026-01-01",
        period_end="2026-01-30",
        target_start="2026-01-02",
        target_end="2026-01-31",
        percentile=percentile,
        total_actual_wind_mwh=tot_act_mwh,
        total_elexon_forecast_mwh=tot_fc_mwh,
        elexon_overforecast_pct=round(elex_overforecast_pct, 2),
        total_elexon_shortfall_mwh=r_v1["total_elexon_shortfall_mwh"],
        total_safe_shortfall_mwh=r_v1["total_safe_shortfall_mwh"],
        total_avoided_shortfall_mwh=r_v1["total_avoided_shortfall_mwh"],
        elexon_shortfall_pct_of_wind=round(elex_sf_pct, 1),
        safe_shortfall_pct_of_wind=round(safe_sf_pct, 1),
        avoided_shortfall_pct_of_wind=round(avoided_sf_pct, 1),
        total_elexon_surplus_mwh=r_v1["total_elexon_surplus_mwh"],
        total_safe_surplus_mwh=r_v1["total_safe_surplus_mwh"],
        total_incremental_surplus_mwh=r_v1["total_incremental_surplus_mwh"],
        elexon_surplus_pct_of_wind=round(elex_sur_pct, 1),
        safe_surplus_pct_of_wind=round(safe_sur_pct, 1),
        incremental_surplus_pct_of_wind=round(inc_sur_pct, 1),
        total_volume_cut_mwh=r_v1["total_volume_cut_mwh"],
        safe_efficiency_pct=r_v1["efficiency_pct"],
        matched_flat_efficiency_pct=r_matched["efficiency_pct"],
        breakeven_ratio=r_v1["breakeven_ratio"],
        cold_start_days=len(cold_start_days),
        cold_start_intervals=r_cs["total_target_intervals"],
        cold_start_avoided_shortfall_mwh=r_cs["total_avoided_shortfall_mwh"],
        cold_start_incremental_surplus_mwh=r_cs["total_incremental_surplus_mwh"],
        cold_start_ratio=round(cs_ratio, 3),
        mature_days=len(mature_days),
        mature_intervals=r_mat["total_target_intervals"],
        mature_avoided_shortfall_mwh=r_mat["total_avoided_shortfall_mwh"],
        mature_incremental_surplus_mwh=r_mat["total_incremental_surplus_mwh"],
        mature_breakeven_ratio=r_mat["breakeven_ratio"],
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
        elexon_mae_gw=r_v1["elexon_mae_gw"],
        safe_mae_gw=r_v1["safe_mae_gw"],
        matched_haircut_percent=round(matched_h * 100.0, 2),
        matched_haircut_shortfall_mwh=r_matched["total_safe_shortfall_mwh"],
        matched_haircut_avoided_mwh=r_matched["total_avoided_shortfall_mwh"],
        matched_haircut_incremental_surplus_mwh=r_matched["total_incremental_surplus_mwh"],
        flat_benchmarks=flat_benchmarks,
        days_shortfall_reduced=r_v1["days_shortfall_reduced"],
        days_shortfall_increased=r_v1["days_shortfall_increased"],
        days_break_even_under_2x=r_v1["days_break_even_under_2x"],
        summary_sentence=sentence,
    )
    _summary_cache[percentile] = res
    return res
