"""Estimate router for Wind Day-Ahead Estimator.
Returns safe wind estimate and indicative range for target day (decision date + 1).
Excludes all target-day actual outcomes to prevent leakage.
Includes hand-checkable calculation steps, 48h history, error histogram,
slider trade-offs across completed days, completed track record, and provenance.
"""

import datetime
from typing import Dict, List
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.schemas import (
    CalculationStep,
    CompletedTrackRecord,
    CompletedTrackRecordDay,
    ErrorDistribution,
    EstimateResponse,
    HistogramBin,
    History48hObservation,
    ProvenanceMetadata,
    SliderTradeoffPoint,
)
from app.services.calibrate import calibrate_daily_forecast
from app.services.models import v2_proportional
from app.services.prepare import DataManager

router = APIRouter(tags=["Estimate"])

# Cache for historical daily replay inputs to guarantee sub-millisecond execution
_daily_inputs_cache: Dict[int, dict] = {}


def _get_day_inputs(d: int, dm: DataManager) -> dict:
    if d not in _daily_inputs_cache:
        d_date = datetime.date(2026, 1, d)
        t_date = d_date + datetime.timedelta(days=1)
        fc = dm.select_target_forecast(d_date, t_date)
        cal = dm.get_calibration_observations(d_date)
        acts = dm.get_target_actuals(t_date)
        _daily_inputs_cache[d] = {
            "dec_date": d_date,
            "target_date": t_date,
            "fc": fc,
            "cal": cal,
            "acts": acts,
        }
    return _daily_inputs_cache[d]


def _compute_completed_track_record(
    dec_date: datetime.date,
    percentile: float,
    dm: DataManager
) -> CompletedTrackRecord:
    d = dec_date.day
    daily_records: List[CompletedTrackRecordDay] = []
    tot_avoided = 0.0
    tot_extra = 0.0
    reduced_count = 0
    increased_count = 0
    breakeven_count = 0

    # Only completed target days before cutoff of dec_date:
    # On dec_date at 09:00 UTC, target day d-1 is fully delivered and actuals available.
    # Target day d-1 was decided on day d-2.
    # So decisions k in [1, d-2] are the completed decisions.
    for k in range(1, d - 1):
        day_inp = _get_day_inputs(k, dm)
        res = calibrate_daily_forecast(day_inp["fc"], day_inp["cal"], percentile)
        acts = day_inp["acts"]
        fc = day_inp["fc"]

        # 500 MWh per half hour per GW
        e_sf = sum(max(0.0, f["generation_gw"] - a["generation_gw"]) * 500.0 for f, a in zip(fc, acts))
        s_sf = sum(max(0.0, s["safe_estimate_gw"] - a["generation_gw"]) * 500.0 for s, a in zip(res["intervals"], acts))
        avoided = e_sf - s_sf

        e_sp = sum(max(0.0, a["generation_gw"] - f["generation_gw"]) * 500.0 for f, a in zip(fc, acts))
        s_sp = sum(max(0.0, a["generation_gw"] - s["safe_estimate_gw"]) * 500.0 for s, a in zip(res["intervals"], acts))
        extra = s_sp - e_sp

        tot_avoided += avoided
        tot_extra += extra
        if avoided > 0.01:
            reduced_count += 1
        else:
            increased_count += 1

        is_be = (avoided > extra)
        if is_be:
            breakeven_count += 1

        daily_records.append(CompletedTrackRecordDay(
            decision_date=day_inp["dec_date"].isoformat(),
            target_date=day_inp["target_date"].isoformat(),
            target_date_label=day_inp["target_date"].strftime("%d %b"),
            elexon_shortfall_mwh=round(e_sf, 1),
            safe_shortfall_mwh=round(s_sf, 1),
            avoided_shortfall_mwh=round(avoided, 1),
            extra_supply_mwh=round(extra, 1),
            is_shortfall_reduced=avoided > 0.01,
            is_breakeven=is_be,
        ))

    return CompletedTrackRecord(
        completed_days_count=len(daily_records),
        total_avoided_shortfall_mwh=round(tot_avoided, 1),
        total_extra_supply_mwh=round(tot_extra, 1),
        days_reduced_count=reduced_count,
        days_increased_count=increased_count,
        days_breakeven_count=breakeven_count,
        daily_records=daily_records,
    )


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
        
        # 4. Hand-checkable calculation step
        elexon_avg = round(calibration_result["elexon_headline_gw"], 4)
        safe_avg = round(calibration_result["safe_headline_gw"], 4)
        margin_avg = round(elexon_avg - safe_avg, 4)
        n_obs = calibration_result["historical_observations_count"]
        weight = calibration_result["history_weight"]

        cold_margin = round(elexon_avg * settings.COLD_START_HAIRCUT, 4)
        if len(calibration_records) > 0:
            errors = np.array([r["error_gw"] for r in calibration_records], dtype=float)
            data_margin = round(float(max(0.0, np.percentile(errors, percentile, method="linear"))), 4)
        else:
            data_margin = 0.0

        is_blended = (n_obs < settings.BLEND_THRESHOLD_OBSERVATIONS)
        if is_blended and n_obs > 0:
            blend_formula_text = (
                f"Margin = ({weight:.2f} × {data_margin:.1f} GW) + "
                f"({1.0 - weight:.2f} × (15% × {elexon_avg:.1f} GW = {cold_margin:.1f} GW)) = {margin_avg:.1f} GW"
            )
        elif n_obs == 0:
            blend_formula_text = f"Margin = 15% × {elexon_avg:.1f} GW = {cold_margin:.1f} GW (Cold Start)"
        else:
            blend_formula_text = None

        calculation = CalculationStep(
            elexon_day_ahead_avg_gw=elexon_avg,
            historical_observations_count=n_obs,
            percentile=percentile,
            error_margin_gw=margin_avg,
            safe_plan_gw=safe_avg,
            formula_text=f"{elexon_avg:.1f} GW − {margin_avg:.1f} GW = {safe_avg:.1f} GW",
            history_weight=round(weight, 4),
            data_margin_gw=data_margin,
            cold_margin_gw=cold_margin,
            is_blended=is_blended,
            blend_formula_text=blend_formula_text,
        )
        
        # 5. History 48h observations (strictly <= cutoff)
        history_48h = [
            History48hObservation(
                interval_start=r["interval_start"].isoformat() if hasattr(r["interval_start"], "isoformat") else str(r["interval_start"]),
                forecast_gw=round(float(r["forecast_gw"]), 4),
                actual_gw=round(float(r["actual_gw"]), 4),
                error_gw=round(float(r["error_gw"]), 4),
            )
            for r in calibration_records
        ]
        
        # 6. Error distribution & histogram
        if len(calibration_records) > 0:
            errors = np.array([r["error_gw"] for r in calibration_records], dtype=float)
            min_err = float(np.min(errors))
            max_err = float(np.max(errors))
            mean_err = float(np.mean(errors))
            p10_err = float(np.percentile(errors, 10, method="linear"))
            p50_err = float(np.percentile(errors, 50, method="linear"))
            p60_err = float(np.percentile(errors, 60, method="linear"))
            p75_err = float(np.percentile(errors, 75, method="linear"))
            p90_err = float(np.percentile(errors, 90, method="linear"))
            over_cnt = int(np.sum(errors > 0.0))
            tot_cnt = len(errors)
            over_pct = round((over_cnt / tot_cnt) * 100.0, 1)

            mean_fc = float(np.mean([r["forecast_gw"] for r in calibration_records]))
            bias_pct = round((mean_err / mean_fc) * 100.0, 1) if mean_fc > 0 else 0.0

            counts, bin_edges = np.histogram(errors, bins=min(10, max(4, tot_cnt // 4)))
            hist_bins = [
                HistogramBin(
                    bin_start=round(float(bin_edges[i]), 2),
                    bin_end=round(float(bin_edges[i+1]), 2),
                    count=int(counts[i]),
                    bin_label=f"{bin_edges[i]:.1f}–{bin_edges[i+1]:.1f} GW"
                )
                for i in range(len(counts))
            ]
        else:
            min_err = max_err = mean_err = p10_err = p50_err = p60_err = p75_err = p90_err = 0.0
            over_cnt = tot_cnt = 0
            over_pct = 0.0
            mean_fc = 0.0
            bias_pct = 0.0
            hist_bins = []

        error_distribution = ErrorDistribution(
            min_error_gw=round(min_err, 4),
            max_error_gw=round(max_err, 4),
            mean_error_gw=round(mean_err, 4),
            p10_error_gw=round(p10_err, 4),
            p50_error_gw=round(p50_err, 4),
            p60_error_gw=round(p60_err, 4),
            p75_error_gw=round(p75_err, 4),
            p90_error_gw=round(p90_err, 4),
            overforecast_count=over_cnt,
            total_count=tot_cnt,
            overforecast_pct=over_pct,
            histogram_bins=hist_bins,
            mean_forecast_gw=round(mean_fc, 4),
            bias_pct=bias_pct,
        )

        # 7. Completed track record up to decision day
        completed_track_record = _compute_completed_track_record(dec_date, percentile, dm)

        # 8. Slider trade-off table (p60, p75, p90 steps)
        standard_pts = [60.0, 75.0, 90.0]
        if any(abs(percentile - sp) < 2.0 for sp in standard_pts):
            pts = standard_pts
        else:
            pts = sorted(standard_pts + [percentile])

        slider_tradeoffs = []
        for p in pts:
            p_calib = calibrate_daily_forecast(raw_forecast_records, calibration_records, p)
            p_tr = _compute_completed_track_record(dec_date, p, dm)
            p_margin = round(p_calib["elexon_headline_gw"] - p_calib["safe_headline_gw"], 4)
            label = f"p{int(p)}" if p.is_integer() else f"p{p:.1f}"
            is_sel = abs(p - percentile) < 1e-4 or (
                any(abs(percentile - sp) < 2.0 for sp in standard_pts) and
                abs(percentile - p) == min(abs(percentile - sp) for sp in standard_pts)
            )
            slider_tradeoffs.append(SliderTradeoffPoint(
                percentile=p,
                label=label,
                plan_gw=round(p_calib["safe_headline_gw"], 4),
                margin_gw=p_margin,
                completed_avoided_shortfall_mwh=p_tr.total_avoided_shortfall_mwh,
                completed_extra_supply_mwh=p_tr.total_extra_supply_mwh,
                is_selected=is_sel
            ))

        # 9. Data Provenance
        latest_publish_dt = max(r["publish_time"] for r in raw_forecast_records)
        latest_pub_str = latest_publish_dt.isoformat() if hasattr(latest_publish_dt, "isoformat") else str(latest_publish_dt)

        cutoff_dt = pd.Timestamp(
            datetime.datetime.combine(
                dec_date,
                datetime.time(settings.DECISION_CUTOFF_HOUR_UTC, settings.DECISION_CUTOFF_MINUTE_UTC)
            ),
            tz="UTC"
        )
        target_intervals = dm.get_target_intervals(target_date)
        eligible = dm._forecasts_df[dm._forecasts_df["publish_time"] <= cutoff_dt]
        target_fc = eligible[eligible["interval_start"].isin(target_intervals)]
        revisions_count = int(target_fc["publish_time"].nunique()) if not target_fc.empty else 1
        rows_count = len(target_fc)

        # 10. v2 Proportional Margin Calculation via model registry
        v2_res = v2_proportional(raw_forecast_records, calibration_records, percentile)
        v2_safe_headline = v2_res["headline_gw"]
        v2_ratio = v2_res["applied_ratio"]

        provenance = ProvenanceMetadata(
            forecast_latest_publish_utc=latest_pub_str,
            forecast_revisions_count=revisions_count,
            target_forecast_rows_count=rows_count,
            freeze_cutoff_utc=cutoff_utc_str,
        )

        return EstimateResponse(
            decision_date=dec_date.isoformat(),
            target_date=target_date.isoformat(),
            decision_cutoff_utc=cutoff_utc_str,
            selected_percentile=percentile,
            elexon_headline_gw=calibration_result["elexon_headline_gw"],
            safe_headline_gw=calibration_result["safe_headline_gw"],
            v2_safe_headline_gw=v2_safe_headline,
            v2_ratio=round(v2_ratio, 4),
            indicative_lower_headline_gw=calibration_result["indicative_lower_headline_gw"],
            indicative_upper_headline_gw=calibration_result["indicative_upper_headline_gw"],
            confidence_label=calibration_result["confidence_label"],
            historical_observations_count=calibration_result["historical_observations_count"],
            history_weight=calibration_result["history_weight"],
            methodology_type=calibration_result["methodology_type"],
            valid_intervals_count=calibration_result["valid_intervals_count"],
            intervals=calibration_result["intervals"],
            calculation=calculation,
            history_48h=history_48h,
            error_distribution=error_distribution,
            slider_tradeoffs=slider_tradeoffs,
            completed_track_record=completed_track_record,
            provenance=provenance,
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))
