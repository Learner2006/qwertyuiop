"""Reliability check router for Wind Day-Ahead Estimator.
Evaluates both Elexon forecast and safe estimate against actual wind generation outcomes.
"""

import datetime
import numpy as np
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas import CheckResponse
from app.services.calibrate import calibrate_daily_forecast
from app.services.metrics import compute_reliability_metrics
from app.services.models import v2_proportional, flat_15
from app.services.prepare import DataManager

router = APIRouter(tags=["Reliability Check"])


def parse_and_validate_date(date_str: str) -> datetime.date:
    try:
        dt = datetime.date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format '{date_str}'. Expected ISO format YYYY-MM-DD."
        )
    
    min_d = datetime.date.fromisoformat(settings.MIN_DECISION_DATE)
    max_d = datetime.date.fromisoformat(settings.MAX_DECISION_DATE)
    if not (min_d <= dt <= max_d):
        raise HTTPException(
            status_code=400,
            detail=f"Decision date '{date_str}' is out of range. Allowed decision dates are {settings.MIN_DECISION_DATE} through {settings.MAX_DECISION_DATE}."
        )
    return dt


@router.get("/check", response_model=CheckResponse)
def get_check(
    date: str = Query(..., description="Decision date in YYYY-MM-DD format (Jan 1 to Jan 30, 2026)"),
    percentile: float = Query(
        settings.DEFAULT_PERCENTILE,
        ge=settings.MIN_PERCENTILE,
        le=settings.MAX_PERCENTILE,
        description="Risk percentile between 60.0 and 90.0 (default 75.0)"
    )
):
    dec_date = parse_and_validate_date(date)
    target_date = dec_date + datetime.timedelta(days=1)
    
    try:
        dm = DataManager.get_instance()
        # 1. Select eligible forecast for target date (identical to estimate)
        raw_forecast_records = dm.select_target_forecast(dec_date, target_date)
        
        # 2. Assemble calibration history (identical to estimate)
        calibration_records = dm.get_calibration_observations(dec_date)
        
        # 3. Canonical calibration (shared function ensuring identical estimate)
        calib_res = calibrate_daily_forecast(
            raw_forecast_records=raw_forecast_records,
            calibration_records=calibration_records,
            percentile=percentile
        )
        
        # 4. Target actuals for evaluation
        actual_records = dm.get_target_actuals(target_date)
        
        # 5. Compute evaluation metrics
        metrics_res = compute_reliability_metrics(calib_res, actual_records)

        # 6. Compute v2 proportional metrics via model registry
        v2_res = v2_proportional(raw_forecast_records, calibration_records, percentile)
        v2_plans = v2_res["plans"]
        v2_headline_gw = v2_res["headline_gw"]
        v2_ratio = v2_res["applied_ratio"]
        v2_sf_mwh = sum(max(0.0, s - a["generation_gw"]) * 500.0 for s, a in zip(v2_plans, actual_records))
        v2_surplus_mwh = sum(max(0.0, a["generation_gw"] - s) * 500.0 for s, a in zip(v2_plans, actual_records))
        v2_saved_sf_mwh = metrics_res["elexon_shortfall_mwh"] - v2_sf_mwh
        v2_inc_surplus_mwh = v2_surplus_mwh - metrics_res["elexon_surplus_mwh"]

        # 7. Compute flat 15% baseline metrics via model registry
        f15_res = flat_15(raw_forecast_records, calibration_records)
        f15_plans = f15_res["plans"]
        f15_headline_gw = f15_res["headline_gw"]
        f15_sf_mwh = sum(max(0.0, s - a["generation_gw"]) * 500.0 for s, a in zip(f15_plans, actual_records))
        f15_surplus_mwh = sum(max(0.0, a["generation_gw"] - s) * 500.0 for s, a in zip(f15_plans, actual_records))
        f15_saved_sf_mwh = metrics_res["elexon_shortfall_mwh"] - f15_sf_mwh
        f15_inc_surplus_mwh = f15_surplus_mwh - metrics_res["elexon_surplus_mwh"]
        
        cutoff_utc_str = f"{dec_date.isoformat()}T{settings.DECISION_CUTOFF_HOUR_UTC:02d}:{settings.DECISION_CUTOFF_MINUTE_UTC:02d}:00Z"
        
        return CheckResponse(
            decision_date=dec_date.isoformat(),
            target_date=target_date.isoformat(),
            decision_cutoff_utc=cutoff_utc_str,
            selected_percentile=percentile,
            elexon_headline_gw=calib_res["elexon_headline_gw"],
            safe_headline_gw=calib_res["safe_headline_gw"],
            actual_headline_gw=metrics_res["actual_headline_gw"],
            indicative_lower_headline_gw=calib_res["indicative_lower_headline_gw"],
            indicative_upper_headline_gw=calib_res["indicative_upper_headline_gw"],
            elexon_shortfall_mwh=metrics_res["elexon_shortfall_mwh"],
            safe_shortfall_mwh=metrics_res["safe_shortfall_mwh"],
            saved_shortfall_mwh=metrics_res["saved_shortfall_mwh"],
            elexon_surplus_mwh=metrics_res["elexon_surplus_mwh"],
            safe_surplus_mwh=metrics_res["safe_surplus_mwh"],
            incremental_surplus_mwh=metrics_res["incremental_surplus_mwh"],
            v2_safe_headline_gw=v2_headline_gw,
            v2_safe_shortfall_mwh=round(v2_sf_mwh, 1),
            v2_saved_shortfall_mwh=round(v2_saved_sf_mwh, 1),
            v2_safe_surplus_mwh=round(v2_surplus_mwh, 1),
            v2_incremental_surplus_mwh=round(v2_inc_surplus_mwh, 1),
            v2_ratio=round(v2_ratio, 4),
            flat15_safe_headline_gw=f15_headline_gw,
            flat15_safe_shortfall_mwh=round(f15_sf_mwh, 1),
            flat15_saved_shortfall_mwh=round(f15_saved_sf_mwh, 1),
            flat15_safe_surplus_mwh=round(f15_surplus_mwh, 1),
            flat15_incremental_surplus_mwh=round(f15_inc_surplus_mwh, 1),
            flat15_ratio=0.15,
            elexon_mae_gw=metrics_res["elexon_mae_gw"],
            safe_mae_gw=metrics_res["safe_mae_gw"],
            indicative_range_coverage=metrics_res["indicative_range_coverage"],
            confidence_label=calib_res["confidence_label"],
            historical_observations_count=calib_res["historical_observations_count"],
            history_weight=calib_res["history_weight"],
            methodology_type=calib_res["methodology_type"],
            headline_result=metrics_res["headline_result"],
            valid_intervals_count=calib_res["valid_intervals_count"],
            methodology_notes=metrics_res["methodology_notes"],
            intervals=metrics_res["intervals"],
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
