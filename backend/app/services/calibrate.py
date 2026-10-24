"""Calibration engine for the Wind Day-Ahead Estimator.
Implements deterministic percentile calibration, cold-start haircut (15%),
linear history blending, and indicative error band calculation.
Shared by both estimate and check pipelines.
"""

from typing import Dict, List, Tuple
import numpy as np

from app.config import settings


def compute_confidence_and_weight(n_obs: int) -> Tuple[str, float, str]:
    """Calculate confidence label, history weight, and methodology type.
    Low: n < 24
    Medium: 24 <= n <= 95
    High: n == 96
    """
    if n_obs < 24:
        label = "Low"
    elif n_obs < 96:
        label = "Medium"
    else:
        label = "High"

    weight = min(1.0, max(0.0, n_obs / float(settings.BLEND_THRESHOLD_OBSERVATIONS)))

    if n_obs == 0:
        method = "cold_start"
    elif n_obs < settings.BLEND_THRESHOLD_OBSERVATIONS:
        method = "blended"
    else:
        method = "data_driven"

    return label, weight, method


def calibrate_daily_forecast(
    raw_forecast_records: List[dict],
    calibration_records: List[dict],
    percentile: float
) -> dict:
    """Run canonical estimation for all intervals of the target day.
    
    Args:
        raw_forecast_records: List of 48 interval dicts with keys:
            interval_start, settlement_period, generation_gw
        calibration_records: Historical calibration observation dicts with key 'error_gw'
        percentile: Risk percentile between 60.0 and 90.0
    
    Returns:
        dict containing headline metrics and half-hourly intervals.
    """
    if not (settings.MIN_PERCENTILE <= percentile <= settings.MAX_PERCENTILE):
        raise ValueError(
            f"Percentile {percentile} is outside valid range [{settings.MIN_PERCENTILE}, {settings.MAX_PERCENTILE}]"
        )

    n_obs = len(calibration_records)
    conf_label, history_weight, method_type = compute_confidence_and_weight(n_obs)

    # 1. Calculate empirical data margin
    if n_obs > 0:
        errors = np.array([r["error_gw"] for r in calibration_records], dtype=float)
        p_error = float(np.percentile(errors, percentile, method="linear"))
        # Floor margin at 0.0 so we never adjust upward
        data_margin = max(0.0, p_error)
        q90_error = float(np.percentile(errors, settings.ERROR_BAND_UPPER_QUANTILE, method="linear"))
        q10_error = float(np.percentile(errors, settings.ERROR_BAND_LOWER_QUANTILE, method="linear"))
    else:
        errors = np.array([], dtype=float)
        data_margin = 0.0
        q90_error = 0.0
        q10_error = 0.0

    interval_results = []
    
    for r in raw_forecast_records:
        istart = r["interval_start"]
        sp = r["settlement_period"]
        f_raw = float(r["generation_gw"])
        
        # Cold start haircut margin: 15% of raw forecast
        cold_margin = max(0.0, f_raw) * settings.COLD_START_HAIRCUT
        
        # Linear blend between cold start margin and data-driven margin
        applied_margin = (1.0 - history_weight) * cold_margin + history_weight * data_margin
        
        # Safe estimate floored at 0
        safe_est = max(0.0, f_raw - applied_margin)
        
        # Indicative error band bounds
        if n_obs == 0:
            lower_bound = max(0.0, f_raw * (1.0 - settings.COLD_START_HAIRCUT))
            upper_bound = f_raw * (1.0 + settings.COLD_START_HAIRCUT)
        else:
            cold_q90 = f_raw * settings.COLD_START_HAIRCUT
            cold_q10 = -f_raw * settings.COLD_START_HAIRCUT
            
            applied_q90 = (1.0 - history_weight) * cold_q90 + history_weight * q90_error
            applied_q10 = (1.0 - history_weight) * cold_q10 + history_weight * q10_error
            
            lower_bound = max(0.0, f_raw - applied_q90)
            upper_bound = max(lower_bound, f_raw - applied_q10)
        
        interval_results.append({
            "interval_start": istart.isoformat() if hasattr(istart, "isoformat") else str(istart),
            "settlement_period": sp,
            "elexon_forecast_gw": round(f_raw, 4),
            "safe_estimate_gw": round(safe_est, 4),
            "indicative_lower_gw": round(lower_bound, 4),
            "indicative_upper_gw": round(upper_bound, 4),
            "applied_margin_gw": round(applied_margin, 4),
        })

    # Headlines: arithmetic mean over valid intervals
    elexon_headline = float(np.mean([i["elexon_forecast_gw"] for i in interval_results]))
    safe_headline = float(np.mean([i["safe_estimate_gw"] for i in interval_results]))
    lower_headline = float(np.mean([i["indicative_lower_gw"] for i in interval_results]))
    upper_headline = float(np.mean([i["indicative_upper_gw"] for i in interval_results]))

    return {
        "confidence_label": conf_label,
        "historical_observations_count": n_obs,
        "history_weight": round(history_weight, 4),
        "methodology_type": method_type,
        "selected_percentile": float(percentile),
        "elexon_headline_gw": round(elexon_headline, 4),
        "safe_headline_gw": round(safe_headline, 4),
        "indicative_lower_headline_gw": round(lower_headline, 4),
        "indicative_upper_headline_gw": round(upper_headline, 4),
        "valid_intervals_count": len(interval_results),
        "intervals": interval_results,
    }
