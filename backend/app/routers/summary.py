"""Monthly summary endpoint for January 2026 performance replay."""

import datetime
from typing import Dict
from fastapi import APIRouter, Query

from app.config import settings
from app.schemas import MonthSummaryResponse
from app.services.calibrate import calibrate_daily_forecast
from app.services.metrics import compute_reliability_metrics
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
    total_elexon_sf = 0.0
    total_safe_sf = 0.0
    total_extra_adv = 0.0
    days_reduced = 0
    days_increased = 0

    for d in range(1, 31):
        dec_date = datetime.date(2026, 1, d)
        target_date = dec_date + datetime.timedelta(days=1)

        fc = dm.select_target_forecast(dec_date, target_date)
        calib_obs = dm.get_calibration_observations(dec_date)
        calib_res = calibrate_daily_forecast(fc, calib_obs, percentile=percentile)
        acts = dm.get_target_actuals(target_date)
        metrics = compute_reliability_metrics(calib_res, acts)

        total_elexon_sf += metrics["elexon_shortfall_mwh"]
        total_safe_sf += metrics["safe_shortfall_mwh"]
        total_extra_adv += metrics["extra_advance_planned_mwh"]
        if metrics["saved_shortfall_mwh"] > 0.05:
            days_reduced += 1
        elif metrics["saved_shortfall_mwh"] < -0.05:
            days_increased += 1

    total_avoided = total_elexon_sf - total_safe_sf
    sentence = (
        f"Across Jan 2026, planning with our estimate would have avoided "
        f"{round(total_avoided):,} MWh of shortfall (and arranged "
        f"{round(total_extra_adv):,} MWh extra in advance)."
    )

    res = MonthSummaryResponse(
        decision_dates_count=30,
        period_start="2026-01-01",
        period_end="2026-01-30",
        percentile=percentile,
        total_elexon_shortfall_mwh=round(total_elexon_sf, 1),
        total_safe_shortfall_mwh=round(total_safe_sf, 1),
        total_avoided_shortfall_mwh=round(total_avoided, 1),
        total_extra_advance_planned_mwh=round(total_extra_adv, 1),
        days_shortfall_reduced=days_reduced,
        days_shortfall_increased=days_increased,
        summary_sentence=sentence,
    )
    _summary_cache[percentile] = res
    return res
