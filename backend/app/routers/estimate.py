"""Estimate router for Wind Day-Ahead Estimator.
Returns safe wind estimate and indicative range for target day (decision date + 1).
Excludes all target-day actual outcomes to prevent leakage.
"""

import datetime
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas import EstimateResponse
from app.services.calibrate import calibrate_daily_forecast
from app.services.prepare import DataManager

router = APIRouter(tags=["Estimate"])


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


@router.get("/estimate", response_model=EstimateResponse)
def get_estimate(
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
        # 1. Select eligible forecast for target date (published <= cutoff)
        raw_forecast_records = dm.select_target_forecast(dec_date, target_date)
        
        # 2. Assemble calibration history (observations available <= cutoff)
        calibration_records = dm.get_calibration_observations(dec_date)
        
        # 3. Deterministic calibration
        calibration_result = calibrate_daily_forecast(
            raw_forecast_records=raw_forecast_records,
            calibration_records=calibration_records,
            percentile=percentile
        )
        
        cutoff_utc_str = f"{dec_date.isoformat()}T{settings.DECISION_CUTOFF_HOUR_UTC:02d}:{settings.DECISION_CUTOFF_MINUTE_UTC:02d}:00Z"
        
        return EstimateResponse(
            decision_date=dec_date.isoformat(),
            target_date=target_date.isoformat(),
            decision_cutoff_utc=cutoff_utc_str,
            selected_percentile=percentile,
            elexon_headline_gw=calibration_result["elexon_headline_gw"],
            safe_headline_gw=calibration_result["safe_headline_gw"],
            indicative_lower_headline_gw=calibration_result["indicative_lower_headline_gw"],
            indicative_upper_headline_gw=calibration_result["indicative_upper_headline_gw"],
            confidence_label=calibration_result["confidence_label"],
            historical_observations_count=calibration_result["historical_observations_count"],
            history_weight=calibration_result["history_weight"],
            methodology_type=calibration_result["methodology_type"],
            valid_intervals_count=calibration_result["valid_intervals_count"],
            intervals=calibration_result["intervals"],
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
