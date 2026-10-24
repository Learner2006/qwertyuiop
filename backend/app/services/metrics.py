"""Reliability metrics engine for the Wind Day-Ahead Estimator.
Calculates half-hourly and aggregated daily energy shortfall (MWh),
saved shortfall energy, additional advance-planned energy, MAE (GW),
and empirical range coverage.
"""

from typing import Dict, List
import numpy as np

from app.config import settings


def compute_reliability_metrics(
    calibration_result: dict,
    actual_records: List[dict]
) -> dict:
    """Compute reliability check metrics comparing Elexon forecast and Safe estimate against actuals.
    
    Args:
        calibration_result: Output dict from calibrate_daily_forecast
        actual_records: List of 48 target actual records with keys:
            interval_start, settlement_period, generation_gw
    """
    intervals = calibration_result["intervals"]
    if len(intervals) != len(actual_records):
        raise ValueError(f"Interval count mismatch: {len(intervals)} forecast vs {len(actual_records)} actuals")

    check_intervals = []
    total_elexon_sf = 0.0
    total_safe_sf = 0.0
    total_extra_adv = 0.0
    elexon_abs_errors = []
    safe_abs_errors = []
    in_range_count = 0
    actual_values = []

    dt = settings.DT_HOURS
    mw_factor = settings.MW_PER_GW * dt  # 1000 * 0.5 = 500

    for fc_int, act_rec in zip(intervals, actual_records):
        f_gw = float(fc_int["elexon_forecast_gw"])
        s_gw = float(fc_int["safe_estimate_gw"])
        a_gw = float(act_rec["generation_gw"])
        actual_values.append(a_gw)
        
        low_gw = float(fc_int["indicative_lower_gw"])
        high_gw = float(fc_int["indicative_upper_gw"])

        # Shortfall: max(0, Planned - Actual) * 1000 * 0.5
        elex_sf = max(0.0, f_gw - a_gw) * mw_factor
        safe_sf = max(0.0, s_gw - a_gw) * mw_factor
        diff_sf = elex_sf - safe_sf
        
        # Extra advance planned: actual wind above safe estimate
        extra_adv = max(0.0, a_gw - s_gw) * mw_factor

        total_elexon_sf += elex_sf
        total_safe_sf += safe_sf
        total_extra_adv += extra_adv

        elexon_abs_errors.append(abs(f_gw - a_gw))
        safe_abs_errors.append(abs(s_gw - a_gw))

        # Check indicative range coverage
        if low_gw <= a_gw <= high_gw:
            in_range_count += 1

        check_intervals.append({
            "interval_start": fc_int["interval_start"],
            "settlement_period": fc_int["settlement_period"],
            "elexon_forecast_gw": f_gw,
            "safe_estimate_gw": s_gw,
            "actual_generation_gw": round(a_gw, 4),
            "indicative_lower_gw": low_gw,
            "indicative_upper_gw": high_gw,
            "elexon_shortfall_mwh": round(elex_sf, 2),
            "safe_shortfall_mwh": round(safe_sf, 2),
            "saved_mwh": round(diff_sf, 2),
            "is_elexon_shortfall": elex_sf > 1e-4,
            "is_safe_shortfall": safe_sf > 1e-4,
        })

    saved_total_sf = total_elexon_sf - total_safe_sf
    elex_mae = float(np.mean(elexon_abs_errors))
    safe_mae = float(np.mean(safe_abs_errors))
    actual_headline = float(np.mean(actual_values))
    coverage = float(in_range_count / len(intervals)) if intervals else 0.0

    # Dynamic headline statement
    if saved_total_sf > 0.05:
        headline_result = f"Using our estimate would have reduced forecast-related shortfall by {saved_total_sf:,.1f} MWh on this target day."
    elif saved_total_sf < -0.05:
        headline_result = f"Our estimate produced {abs(saved_total_sf):,.1f} MWh more shortfall than Elexon's forecast on this target day."
    else:
        headline_result = "Both methods produced the same shortfall energy on this target day."

    methodology_notes = [
        "Historical replay using Elexon BMRS WINDFOR and FUELHH data for January 2026 (UTC).",
        "Shortfall energy is calculated as max(0, planned - actual) * 1000 * 0.5 hours.",
        "Saved shortfall MWh is an avoided shortfall volume, not verified financial cash savings.",
        "Additional advance-planned MWh measures actual wind above our safe estimate.",
        "Indicative error band is derived from historical errors and does not guarantee future generation."
    ]

    return {
        "actual_headline_gw": round(actual_headline, 4),
        "elexon_shortfall_mwh": round(total_elexon_sf, 1),
        "safe_shortfall_mwh": round(total_safe_sf, 1),
        "saved_shortfall_mwh": round(saved_total_sf, 1),
        "extra_advance_planned_mwh": round(total_extra_adv, 1),
        "elexon_mae_gw": round(elex_mae, 4),
        "safe_mae_gw": round(safe_mae, 4),
        "indicative_range_coverage": round(coverage, 4),
        "headline_result": headline_result,
        "methodology_notes": methodology_notes,
        "intervals": check_intervals,
    }
