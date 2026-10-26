"""Single-pass validation script for Out-of-Time Model Decision Protocol (v2).
Evaluates candidate models strictly under PROTOCOL_v2.md on post-January 2026 data.
Produces backend/app/data/validation_summary.json and prints markdown tables for docs/VALIDATION.md.
"""

import datetime
import hashlib
import json
import logging
import os
import sys
from typing import Any, Dict, List
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("validate_models")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.config import settings
from app.services.prepare import DataManager
from app.services.replay import replay, clear_replay_cache

DATA_DIR = os.path.join(BACKEND_DIR, "app", "data")
VALIDATION_PARQUET = os.path.join(DATA_DIR, "validation_2026-01-29_to_2026-09-30.parquet")
OUTPUT_JSON = os.path.join(DATA_DIR, "validation_summary.json")

CANDIDATE_MODELS = [
    ("flat_15", "flat_15", 75.0, {}),
    ("expanding_ratio", "expanding_ratio", 75.0, {}),
    ("v1_additive", "v1_additive", 75.0, {}),
    ("v2_proportional", "v2_proportional", 75.0, {}),
]


def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_validation():
    if not os.path.exists(VALIDATION_PARQUET):
        raise FileNotFoundError(f"Validation parquet not found at {VALIDATION_PARQUET}")

    val_hash = sha256_file(VALIDATION_PARQUET)
    val_size_kb = os.path.getsize(VALIDATION_PARQUET) / 1024.0
    logger.info("Validation dataset: %s (SHA-256: %s, Size: %.1f KB)", VALIDATION_PARQUET, val_hash, val_size_kb)

    # Initialize DataManager with validation parquet
    dm = DataManager(data_path=VALIDATION_PARQUET)
    clear_replay_cache()

    # Determine eligible decision dates:
    # Target delivery dates: 2026-02-01 through 2026-09-30.
    # Decision dates: 2026-01-31 through 2026-09-29.
    start_target = datetime.date(2026, 2, 1)
    end_target = datetime.date(2026, 9, 30)

    # Filter to target dates present with complete 48 intervals
    actuals_df = dm._actuals_df
    available_dates = set(actuals_df["interval_start"].dt.date.unique())

    eligible_decision_dates = []
    cur_target = start_target
    while cur_target <= end_target:
        dec_date = cur_target - datetime.timedelta(days=1)
        # Check that target actuals exist and decision cutoff has calibration data
        if cur_target in available_dates:
            try:
                # Test retrieving target actuals and forecast
                dm.get_target_actuals(cur_target)
                dm.select_target_forecast(dec_date, cur_target)
                eligible_decision_dates.append(dec_date)
            except Exception as e:
                logger.warning("Skipping target date %s (decision %s): %s", cur_target, dec_date, e)
        cur_target += datetime.timedelta(days=1)

    logger.info("Found %d eligible decision dates (%s to %s)",
                len(eligible_decision_dates),
                eligible_decision_dates[0],
                eligible_decision_dates[-1])

    # Group decision dates by target delivery month
    months: Dict[str, List[datetime.date]] = {}
    for d in eligible_decision_dates:
        target_month = (d + datetime.timedelta(days=1)).strftime("%Y-%m")
        months.setdefault(target_month, []).append(d)

    logger.info("Validation delivery months: %s", sorted(months.keys()))

    # 1. Evaluate candidate models month-by-month and overall
    monthly_results: Dict[str, Dict[str, Any]] = {}
    overall_results: Dict[str, Any] = {}

    for label, m_name, pct, extra_kwargs in CANDIDATE_MODELS:
        clear_replay_cache()
        # Full period replay
        full_res = replay(
            model_name=m_name,
            decision_days=eligible_decision_dates,
            percentile=pct,
            s=0.0,
            dm=dm,
            **extra_kwargs,
        )
        overall_results[label] = {
            "avoided_shortfall_mwh": full_res["total_avoided_shortfall_mwh"],
            "extra_advance_mwh": full_res["total_incremental_surplus_mwh"],
            "net_k2_s0_mwh": full_res["total_avoided_shortfall_mwh"] - full_res["total_incremental_surplus_mwh"],
            "break_even_price_ratio": full_res["breakeven_ratio"],
            "days_break_even_under_2x": full_res["days_break_even_under_2x"],
            "total_days": full_res["completed_days_count"],
            "total_cut_volume_mwh": full_res["total_volume_cut_mwh"],
            "total_forecast_mwh": full_res["total_elexon_forecast_mwh"],
            "cut_share_pct": round(full_res["total_volume_cut_mwh"] / full_res["total_elexon_forecast_mwh"] * 100, 2)
            if full_res["total_elexon_forecast_mwh"] > 0 else 0.0,
            "efficiency_pct": full_res["efficiency_pct"],
            "mae_gw": full_res["safe_mae_gw"],
            "elexon_mae_gw": full_res["elexon_mae_gw"],
        }

        # Month-by-month replay
        for m_str, m_dates in sorted(months.items()):
            monthly_results.setdefault(m_str, {})
            m_res = replay(
                model_name=m_name,
                decision_days=m_dates,
                percentile=pct,
                s=0.0,
                dm=dm,
                **extra_kwargs,
            )
            monthly_results[m_str][label] = {
                "avoided_shortfall_mwh": m_res["total_avoided_shortfall_mwh"],
                "extra_advance_mwh": m_res["total_incremental_surplus_mwh"],
                "net_k2_s0_mwh": m_res["total_avoided_shortfall_mwh"] - m_res["total_incremental_surplus_mwh"],
                "break_even_price_ratio": m_res["breakeven_ratio"],
                "days_break_even_under_2x": m_res["days_break_even_under_2x"],
                "total_days": m_res["completed_days_count"],
                "efficiency_pct": m_res["efficiency_pct"],
                "cut_volume_mwh": m_res["total_volume_cut_mwh"],
            }

    # 2. Matched-cut comparison test vs static haircut
    matched_cut_results: Dict[str, Any] = {}
    for label, m_name, pct, extra_kwargs in CANDIDATE_MODELS:
        m_tot = overall_results[label]
        cut_share = m_tot["cut_share_pct"] / 100.0  # fraction
        # Replay flat_haircut with exact cut_share
        clear_replay_cache()
        flat_matched_res = replay(
            model_name="flat_haircut",
            decision_days=eligible_decision_dates,
            s=0.0,
            dm=dm,
            haircut=cut_share,
        )
        flat_avoided = flat_matched_res["total_avoided_shortfall_mwh"]
        flat_extra = flat_matched_res["total_incremental_surplus_mwh"]
        flat_net = flat_avoided - flat_extra
        matched_cut_results[label] = {
            "model_avoided_mwh": m_tot["avoided_shortfall_mwh"],
            "model_extra_mwh": m_tot["extra_advance_mwh"],
            "model_net_k2_mwh": m_tot["net_k2_s0_mwh"],
            "matched_haircut_pct": round(cut_share * 100, 2),
            "matched_flat_avoided_mwh": flat_avoided,
            "matched_flat_extra_mwh": flat_extra,
            "matched_flat_net_k2_mwh": flat_net,
            "avoided_shortfall_advantage_mwh": m_tot["avoided_shortfall_mwh"] - flat_avoided,
            "net_k2_advantage_mwh": m_tot["net_k2_s0_mwh"] - flat_net,
            "beats_matched_flat": m_tot["net_k2_s0_mwh"] > flat_net,
        }

    # 3. Sensitivity grid sweep (on sample subset of dates or full validation window)
    sensitivity_results = {}
    
    # 3a. Cutoffs sweep: 07:00, 09:00, 11:00 UTC
    cutoff_sweep = {}
    for c_hour in [7, 9, 11]:
        dm.set_operational_parameters(cutoff_hour=c_hour)
        clear_replay_cache()
        c_models = {}
        for label, m_name, pct, extra_kwargs in CANDIDATE_MODELS:
            res = replay(
                model_name=m_name,
                decision_days=eligible_decision_dates,
                percentile=pct,
                s=0.0,
                dm=dm,
                **extra_kwargs,
            )
            c_models[label] = {
                "avoided_mwh": res["total_avoided_shortfall_mwh"],
                "extra_mwh": res["total_incremental_surplus_mwh"],
                "net_k2_mwh": res["total_avoided_shortfall_mwh"] - res["total_incremental_surplus_mwh"],
                "break_even": res["breakeven_ratio"],
            }
        cutoff_sweep[f"{c_hour:02d}:00 UTC"] = c_models
    sensitivity_results["cutoff_utc"] = cutoff_sweep
    dm.reset_operational_parameters()

    # 3b. Actuals publication lag sweep: 0h, 1h, 2h
    lag_sweep = {}
    for lag_h in [0, 1, 2]:
        dm.set_operational_parameters(lag_hours=lag_h)
        clear_replay_cache()
        l_models = {}
        for label, m_name, pct, extra_kwargs in CANDIDATE_MODELS:
            res = replay(
                model_name=m_name,
                decision_days=eligible_decision_dates,
                percentile=pct,
                s=0.0,
                dm=dm,
                **extra_kwargs,
            )
            l_models[label] = {
                "avoided_mwh": res["total_avoided_shortfall_mwh"],
                "extra_mwh": res["total_incremental_surplus_mwh"],
                "net_k2_mwh": res["total_avoided_shortfall_mwh"] - res["total_incremental_surplus_mwh"],
                "break_even": res["breakeven_ratio"],
            }
        lag_sweep[f"{lag_h}h"] = l_models
    sensitivity_results["actuals_lag_hours"] = lag_sweep
    dm.reset_operational_parameters()

    # 3c. Lookback sweep: 24h, 48h, 72h
    lookback_sweep = {}
    for lb_h in [24, 48, 72]:
        dm.set_operational_parameters(lookback_hours=lb_h)
        clear_replay_cache()
        lb_models = {}
        for label, m_name, pct, extra_kwargs in CANDIDATE_MODELS:
            res = replay(
                model_name=m_name,
                decision_days=eligible_decision_dates,
                percentile=pct,
                s=0.0,
                dm=dm,
                **extra_kwargs,
            )
            lb_models[label] = {
                "avoided_mwh": res["total_avoided_shortfall_mwh"],
                "extra_mwh": res["total_incremental_surplus_mwh"],
                "net_k2_mwh": res["total_avoided_shortfall_mwh"] - res["total_incremental_surplus_mwh"],
                "break_even": res["breakeven_ratio"],
            }
        lookback_sweep[f"{lb_h}h"] = lb_models
    sensitivity_results["lookback_hours"] = lookback_sweep
    dm.reset_operational_parameters()

    # 3d. Percentile sweep: p60, p75, p85, p90 (for dynamic models)
    pct_sweep = {}
    for p_val in [60.0, 75.0, 85.0, 90.0]:
        clear_replay_cache()
        p_models = {}
        for label, m_name, _, extra_kwargs in CANDIDATE_MODELS:
            res = replay(
                model_name=m_name,
                decision_days=eligible_decision_dates,
                percentile=p_val,
                s=0.0,
                dm=dm,
                **extra_kwargs,
            )
            p_models[label] = {
                "avoided_mwh": res["total_avoided_shortfall_mwh"],
                "extra_mwh": res["total_incremental_surplus_mwh"],
                "net_k2_mwh": res["total_avoided_shortfall_mwh"] - res["total_incremental_surplus_mwh"],
                "break_even": res["breakeven_ratio"],
            }
        pct_sweep[f"p{int(p_val)}"] = p_models
    sensitivity_results["percentile"] = pct_sweep

    # 4. Apply PROTOCOL_v2.md decision rule to determine winning model
    # Rule: Highest cumulative net MWh at k=2, s=0 across all validation months.
    # If top dynamic model does not beat flat_15 by > 1.0%, flat_15 wins.
    flat_net = overall_results["flat_15"]["net_k2_s0_mwh"]
    ranked_models = sorted(
        overall_results.items(),
        key=lambda item: item[1]["net_k2_s0_mwh"],
        reverse=True
    )
    winner = ranked_models[0][0]
    winner_net = ranked_models[0][1]["net_k2_s0_mwh"]
    win_reason = ""

    if winner == "flat_15":
        win_reason = "flat_15 achieved the highest cumulative Net MWh at k=2, s=0 across the validation dataset."
    else:
        # Check margin over flat_15
        if flat_net > 0:
            margin_pct = (winner_net - flat_net) / flat_net * 100.0
        else:
            margin_pct = 100.0
        if margin_pct < 1.0:
            winner = "flat_15"
            win_reason = f"{ranked_models[0][0]} beat flat_15 by only {margin_pct:.2f}% (< 1.0% threshold); flat_15 wins by simplicity tie-breaker."
        else:
            win_reason = f"{winner} achieved {winner_net:,.1f} Net MWh, beating flat_15 by {margin_pct:.2f}% (> 1.0% threshold)."

    summary = {
        "metadata": {
            "dataset_file": os.path.basename(VALIDATION_PARQUET),
            "sha256": val_hash,
            "size_kb": val_size_kb,
            "target_period_start": str(start_target),
            "target_period_end": str(end_target),
            "total_delivery_days": len(eligible_decision_dates),
            "total_settlement_intervals": len(eligible_decision_dates) * 48,
            "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        },
        "winner": {
            "model": winner,
            "reason": win_reason,
            "net_k2_s0_mwh": overall_results[winner]["net_k2_s0_mwh"],
            "break_even_price_ratio": overall_results[winner]["break_even_price_ratio"],
        },
        "overall_results": overall_results,
        "monthly_results": monthly_results,
        "matched_cut_results": matched_cut_results,
        "sensitivity": sensitivity_results,
    }

    with open(OUTPUT_JSON, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info("Validation summary successfully saved to %s", OUTPUT_JSON)

    # Print summary tables
    print("\n" + "=" * 80)
    print("OUT-OF-TIME VALIDATION RESULTS (Feb 1 to Sep 30, 2026)")
    print("=" * 80)
    print(f"Validation Dataset SHA-256: {val_hash}")
    print(f"Total delivery days: {len(eligible_decision_dates)} ({len(eligible_decision_dates)*48} intervals)")
    print(f"WINNING MODEL UNDER PROTOCOL_v2.md: {winner.upper()}")
    print(f"Decision Reason: {win_reason}\n")

    print("### Full Validation Period Aggregate Table (Feb–Sep 2026)")
    print("| Model | Avoided Shortfall (MWh) | Extra Advance (MWh) | Net at k=2 (MWh) | Break-Even (k*) | Days BE < 2x | Cut Share (%) |")
    print("|---|---|---|---|---|---|---|")
    for m, d in overall_results.items():
        print(f"| `{m}` | {d['avoided_shortfall_mwh']:,.1f} | {d['extra_advance_mwh']:,.1f} | {d['net_k2_s0_mwh']:,.1f} | {d['break_even_price_ratio']:.3f}× | {d['days_break_even_under_2x']}/{d['total_days']} | {d['cut_share_pct']}% |")

    print("\n### Month-by-Month Net at k=2 (MWh) Breakdown")
    m_keys = sorted(monthly_results.keys())
    header = "| Model | " + " | ".join(m_keys) + " | Total Net (MWh) |"
    print(header)
    print("|---" * (len(m_keys) + 2) + "|")
    for m in [c[0] for c in CANDIDATE_MODELS]:
        row = [f"`{m}`"]
        for mk in m_keys:
            val = monthly_results[mk][m]["net_k2_s0_mwh"]
            row.append(f"{val:,.0f}")
        row.append(f"{overall_results[m]['net_k2_s0_mwh']:,.0f}")
        print("| " + " | ".join(row) + " |")

    print("\n### Matched-Cut Comparison vs Equal-Volume Flat Haircut")
    print("| Model | Cut Share | Model Net k=2 | Matched Flat Net k=2 | Net Advantage | Beats Flat? |")
    print("|---|---|---|---|---|---|")
    for m, d in matched_cut_results.items():
        print(f"| `{m}` | {d['matched_haircut_pct']}% | {d['model_net_k2_mwh']:,.1f} | {d['matched_flat_net_k2_mwh']:,.1f} | {d['net_k2_advantage_mwh']:+,.1f} | {'YES' if d['beats_matched_flat'] else 'NO'} |")

    print("\n### Operational Sensitivity: Decision Cutoffs (Net MWh at k=2)")
    print("| Cutoff | " + " | ".join([f"`{c[0]}`" for c in CANDIDATE_MODELS]) + " |")
    print("|---" * (len(CANDIDATE_MODELS) + 1) + "|")
    for cut_label, cuts in sensitivity_results["cutoff_utc"].items():
        row = [cut_label] + [f"{cuts[c[0]]['net_k2_mwh']:,.0f}" for c in CANDIDATE_MODELS]
        print("| " + " | ".join(row) + " |")

    print("\n### Operational Sensitivity: Publication Lag (Net MWh at k=2)")
    print("| Lag | " + " | ".join([f"`{c[0]}`" for c in CANDIDATE_MODELS]) + " |")
    print("|---" * (len(CANDIDATE_MODELS) + 1) + "|")
    for lag_label, lags in sensitivity_results["actuals_lag_hours"].items():
        row = [lag_label] + [f"{lags[c[0]]['net_k2_mwh']:,.0f}" for c in CANDIDATE_MODELS]
        print("| " + " | ".join(row) + " |")

    print("\n### Operational Sensitivity: Lookback Window (Net MWh at k=2)")
    print("| Lookback | " + " | ".join([f"`{c[0]}`" for c in CANDIDATE_MODELS]) + " |")
    print("|---" * (len(CANDIDATE_MODELS) + 1) + "|")
    for lb_label, lbs in sensitivity_results["lookback_hours"].items():
        row = [lb_label] + [f"{lbs[c[0]]['net_k2_mwh']:,.0f}" for c in CANDIDATE_MODELS]
        print("| " + " | ".join(row) + " |")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    run_validation()
