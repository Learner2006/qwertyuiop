"""Reliability check router for Wind Day-Ahead Estimator.
Evaluates both Elexon forecast and safe estimate against actual wind generation outcomes.
Uses unified replay engine for canonical calculation of all metrics.
"""

import datetime
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas import BandCoverageInfo, CheckResponse
from app.services.calibrate import calibrate_daily_forecast
from app.services.metrics import compute_reliability_metrics
from app.services.prepare import DataManager
from app.services.replay import replay
from app.routers.estimate import _compute_trailing_band_coverage

router = APIRouter(tags=["Reliability Check"])


def parse_and_validate_date(date_str: str) -> datetime.date:
    try:
        dt = datetime.date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format '{date_str}'. Expected ISO format YYYY-MM-DD.",
        )

    min_d = datetime.date.fromisoformat(settings.MIN_DECISION_DATE)
    max_d = datetime.date.fromisoformat(settings.MAX_DECISION_DATE)
    if not (min_d <= dt <= max_d):
        raise HTTPException(
            status_code=400,
            detail=f"Decision date '{date_str}' is out of range. Allowed decision dates are {settings.MIN_DECISION_DATE} through {settings.MAX_DECISION_DATE}.",
        )
    return dt


@router.get("/check", response_model=CheckResponse)
def get_check(
    date: str = Query(
        ...,
        description="Decision date in YYYY-MM-DD format (Jan 1 to Jan 30, 2026)",
    ),
    percentile: float = Query(
        settings.DEFAULT_PERCENTILE,
        ge=settings.MIN_PERCENTILE,
        le=settings.MAX_PERCENTILE,
        description="Risk percentile between 60.0 and 90.0 (default 75.0)",
    ),
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
            percentile=percentile,
        )

        # 4. Target actuals for evaluation
        actual_records = dm.get_target_actuals(target_date)

        # 5. Compute evaluation metrics (for detailed half-hourly intervals and notes)
        metrics_res = compute_reliability_metrics(calib_res, actual_records)

        # 6. Replay models for this single decision date via unified replay engine
        r_v2 = replay(
            "v2_proportional", [dec_date], percentile=percentile, dm=dm
        )
        r_f15 = replay("flat_15", [dec_date], dm=dm)

        v2_raw = r_v2["per_day"][0]["raw_result"]
        f15_raw = r_f15["per_day"][0]["raw_result"]

        cutoff_utc_str = f"{dec_date.isoformat()}T{settings.DECISION_CUTOFF_HOUR_UTC:02d}:{settings.DECISION_CUTOFF_MINUTE_UTC:02d}:00Z"
        trailing_cov = _compute_trailing_band_coverage(dec_date, dm)
        band_cov_info = BandCoverageInfo(
            trailing_coverage_pct=trailing_cov,
            historical_full_month_coverage_pct=55.8,
            description="Empirical range (not a probability interval)"
        )

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
            v2_safe_headline_gw=v2_raw["headline_gw"],
            v2_safe_shortfall_mwh=r_v2["total_safe_shortfall_mwh"],
            v2_saved_shortfall_mwh=r_v2["total_avoided_shortfall_mwh"],
            v2_safe_surplus_mwh=r_v2["total_safe_surplus_mwh"],
            v2_incremental_surplus_mwh=r_v2["total_incremental_surplus_mwh"],
            v2_ratio=round(v2_raw["applied_ratio"], 4),
            flat15_safe_headline_gw=f15_raw["headline_gw"],
            flat15_safe_shortfall_mwh=r_f15["total_safe_shortfall_mwh"],
            flat15_saved_shortfall_mwh=r_f15["total_avoided_shortfall_mwh"],
            flat15_safe_surplus_mwh=r_f15["total_safe_surplus_mwh"],
            flat15_incremental_surplus_mwh=r_f15["total_incremental_surplus_mwh"],
            flat15_ratio=settings.COLD_START_HAIRCUT,
            elexon_mae_gw=metrics_res["elexon_mae_gw"],
            safe_mae_gw=metrics_res["safe_mae_gw"],
            indicative_range_coverage=metrics_res["indicative_range_coverage"],
            band_coverage=band_cov_info,
            band_realised_coverage_pct=55.8,
            trailing_band_coverage_pct=trailing_cov,
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
