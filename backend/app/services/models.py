"""Model registry and canonical implementation for all Wind Day-Ahead Estimators.
Single source of truth for:
- v1_additive (headline empirical quantile haircut with cold-start blend)
- v2_proportional (proportional error ratio quantile with cold-start blend)
- flat_15 (static pre-set 15.0% haircut baseline)
- expanding_ratio (empirical ratio of actual / forecast over all completed days to D-1)
"""

from typing import Any, Callable, Dict, List, Optional
import numpy as np

from app.config import settings
from app.services.calibrate import calibrate_daily_forecast, compute_confidence_and_weight


def v1_additive(
    raw_forecast_records: List[dict],
    calibration_records: Optional[List[dict]] = None,
    percentile: float = 75.0,
    **kwargs: Any,
) -> dict:
    """Canonical v1 additive model:
    Subtracts empirical signed-error quantile from forecast, blended with 15% cold start.
    Floors each half-hour plan at 0.0 GW.
    """
    calib_obs = calibration_records or []
    calib_res = calibrate_daily_forecast(raw_forecast_records, calib_obs, percentile)
    
    plans = [iv["safe_estimate_gw"] for iv in calib_res["intervals"]]
    headline_gw = calib_res["safe_headline_gw"]
    elexon_gw = calib_res["elexon_headline_gw"]
    margin_gw = round(elexon_gw - headline_gw, 4)

    return {
        "model_name": "v1_additive",
        "plans": plans,
        "intervals": calib_res["intervals"],
        "headline_gw": headline_gw,
        "elexon_headline_gw": elexon_gw,
        "margin_gw": margin_gw,
        "indicative_lower_headline_gw": calib_res["indicative_lower_headline_gw"],
        "indicative_upper_headline_gw": calib_res["indicative_upper_headline_gw"],
        "confidence_label": calib_res["confidence_label"],
        "historical_observations_count": calib_res["historical_observations_count"],
        "history_weight": calib_res["history_weight"],
        "methodology_type": calib_res["methodology_type"],
        "calculation": calib_res.get("calculation"),
    }


def v2_proportional(
    raw_forecast_records: List[dict],
    calibration_records: Optional[List[dict]] = None,
    percentile: float = 75.0,
    **kwargs: Any,
) -> dict:
    """Canonical v2 proportional model:
    Computes signed error ratios (error_gw / forecast_gw) from calibration window.
    Takes the specified percentile, blends with cold start 15% based on history weight,
    and applies fractional haircut: plan = max(0.0, forecast * (1.0 - applied_ratio)).
    """
    calib_obs = calibration_records or []
    n_obs = len(calib_obs)
    conf_label, history_weight, method_type = compute_confidence_and_weight(n_obs)

    pct_errs = [
        (obs["error_gw"] / obs["forecast_gw"])
        for obs in calib_obs
        if obs["forecast_gw"] > 0.01
    ]

    if pct_errs:
        q_pct = max(0.0, float(np.percentile(pct_errs, percentile, method="linear")))
    else:
        q_pct = settings.COLD_START_HAIRCUT

    applied_ratio = (1.0 - history_weight) * settings.COLD_START_HAIRCUT + history_weight * q_pct
    applied_ratio = max(0.0, min(1.0, applied_ratio))

    plans = []
    intervals = []
    for r in raw_forecast_records:
        f = float(r["generation_gw"])
        p = max(0.0, f * (1.0 - applied_ratio))
        plans.append(p)
        intervals.append({
            "interval_start": r["interval_start"],
            "settlement_period": r["settlement_period"],
            "forecast_gw": f,
            "plan_gw": round(p, 4),
            "margin_gw": round(f - p, 4),
        })

    elexon_gw = round(float(np.mean([float(r["generation_gw"]) for r in raw_forecast_records])), 4)
    headline_gw = round(float(np.mean(plans)), 4) if plans else 0.0
    margin_gw = round(elexon_gw - headline_gw, 4)

    return {
        "model_name": "v2_proportional",
        "plans": plans,
        "intervals": intervals,
        "headline_gw": headline_gw,
        "elexon_headline_gw": elexon_gw,
        "margin_gw": margin_gw,
        "applied_ratio": round(applied_ratio, 4),
        "confidence_label": conf_label,
        "historical_observations_count": n_obs,
        "history_weight": history_weight,
        "methodology_type": method_type,
    }


def flat_15(
    raw_forecast_records: List[dict],
    calibration_records: Optional[List[dict]] = None,
    percentile: Optional[float] = None,
    **kwargs: Any,
) -> dict:
    """Pre-set Flat 15.0% haircut baseline:
    plan = max(0.0, forecast * 0.85).
    """
    plans = []
    intervals = []
    haircut = settings.COLD_START_HAIRCUT # 0.15

    for r in raw_forecast_records:
        f = float(r["generation_gw"])
        p = max(0.0, f * (1.0 - haircut))
        plans.append(p)
        intervals.append({
            "interval_start": r["interval_start"],
            "settlement_period": r["settlement_period"],
            "forecast_gw": f,
            "plan_gw": round(p, 4),
            "margin_gw": round(f - p, 4),
        })

    elexon_gw = round(float(np.mean([float(r["generation_gw"]) for r in raw_forecast_records])), 4)
    headline_gw = round(float(np.mean(plans)), 4) if plans else 0.0
    margin_gw = round(elexon_gw - headline_gw, 4)

    return {
        "model_name": "flat_15",
        "plans": plans,
        "intervals": intervals,
        "headline_gw": headline_gw,
        "elexon_headline_gw": elexon_gw,
        "margin_gw": margin_gw,
        "applied_ratio": haircut,
    }


def expanding_ratio(
    raw_forecast_records: List[dict],
    completed_days_actuals: Optional[List[dict]] = None,
    completed_days_forecasts: Optional[List[dict]] = None,
    **kwargs: Any,
) -> dict:
    """Expanding-window ratio baseline:
    Empirical ratio of (total actual outturn MWh / total day-ahead forecast MWh)
    evaluated across all completed delivery days up to D-1.
    If fewer than 2 completed days exist, uses 15% haircut (ratio = 0.85).
    Plan = max(0.0, forecast * ratio).
    """
    acts = completed_days_actuals or []
    fcs = completed_days_forecasts or []

    if len(acts) >= 2 and len(fcs) >= 2:
        tot_act = sum(a["generation_gw"] for a in acts)
        tot_fc = sum(f["generation_gw"] for f in fcs)
        ratio = (tot_act / tot_fc) if tot_fc > 0 else 0.85
        ratio = max(0.0, min(1.2, ratio))
    else:
        ratio = 0.85

    plans = []
    intervals = []
    for r in raw_forecast_records:
        f = float(r["generation_gw"])
        p = max(0.0, f * ratio)
        plans.append(p)
        intervals.append({
            "interval_start": r["interval_start"],
            "settlement_period": r["settlement_period"],
            "forecast_gw": f,
            "plan_gw": round(p, 4),
            "margin_gw": round(f - p, 4),
        })

    elexon_gw = round(float(np.mean([float(r["generation_gw"]) for r in raw_forecast_records])), 4)
    headline_gw = round(float(np.mean(plans)), 4) if plans else 0.0
    margin_gw = round(elexon_gw - headline_gw, 4)

    return {
        "model_name": "expanding_ratio",
        "plans": plans,
        "intervals": intervals,
        "headline_gw": headline_gw,
        "elexon_headline_gw": elexon_gw,
        "margin_gw": margin_gw,
        "applied_ratio": round(1.0 - ratio, 4),
        "actual_to_forecast_ratio": round(ratio, 4),
    }


MODEL_REGISTRY: Dict[str, Callable[..., dict]] = {
    "v1_additive": v1_additive,
    "v2_proportional": v2_proportional,
    "flat_15": flat_15,
    "expanding_ratio": expanding_ratio,
}


def get_model(name: str) -> Callable[..., dict]:
    if name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model '{name}'. Available: {list(MODEL_REGISTRY.keys())}")
    return MODEL_REGISTRY[name]
