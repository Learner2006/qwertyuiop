#!/usr/bin/env python3
"""Model Candidate Evaluation Script for Wind Day-Ahead Estimator.
Evaluates four candidates:
1. v1_additive (p75)
2. v2_proportional (p75)
3. flat_15 (15% static)
4. expanding_ratio (completed days realization ratio)

Uses the canonical replay engine from app.services.replay.
Executes the selection protocol:
- Selection half: Jan 1-15 decisions (targeting Jan 2-16)
- Holdout half: Jan 16-30 decisions (targeting Jan 17-31)
- Evaluates Volume Qualification Threshold (>= 90% of best avoided shortfall)
- Selects model with highest Efficiency (Avoided / (Avoided + Extra))
"""

import os
import sys

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.services.prepare import DataManager
from app.services.replay import replay


def evaluate_window(start_day: int, end_day: int, dm: DataManager) -> dict:
    """Evaluate all 4 candidate models for decisions in range [start_day, end_day]."""
    days_range = range(start_day, end_day + 1)
    results = {}

    r_base = replay("v1_additive", days_range, dm=dm)
    results["raw_elexon"] = {
        "shortfall_mwh": r_base["total_elexon_shortfall_mwh"],
        "surplus_mwh": r_base["total_elexon_surplus_mwh"],
        "forecast_mwh": r_base["total_elexon_forecast_mwh"],
        "actual_mwh": r_base["total_actual_wind_mwh"],
    }

    for m in ["v1_additive", "v2_proportional", "flat_15", "expanding_ratio"]:
        r = replay(m, days_range, dm=dm)
        results[m] = {
            "shortfall_mwh": r["total_safe_shortfall_mwh"],
            "surplus_mwh": r["total_safe_surplus_mwh"],
            "avoided_mwh": r["total_avoided_shortfall_mwh"],
            "extra_mwh": r["total_incremental_surplus_mwh"],
            "pos_days": r["days_break_even_under_2x"],
            "breakeven_ratio": r["breakeven_ratio"] if r["breakeven_ratio"] is not None else 999.0,
            "efficiency": r["efficiency_pct"] / 100.0,
        }

    return results


def main():
    dm = DataManager.get_instance()

    print("=" * 80)
    print("WIND DAY-AHEAD ESTIMATOR: CANDIDATE MODEL EVALUATION & PROTOCOL REPLAY")
    print("=" * 80)

    # 1. Selection Half: Jan 1-15 decisions (targeting Jan 2-16)
    sel = evaluate_window(1, 15, dm)
    print("\n--- 1. SELECTION HALF (Jan 1-15 Decisions, 720 intervals) ---")
    print(
        f"Raw Elexon: Forecast = {sel['raw_elexon']['forecast_mwh']:,.1f} MWh, "
        f"Actual = {sel['raw_elexon']['actual_mwh']:,.1f} MWh, "
        f"Shortfall = {sel['raw_elexon']['shortfall_mwh']:,.1f} MWh"
    )
    print(
        f"{'Model':<18} | {'Avoided (MWh)':<14} | {'Extra (MWh)':<12} | {'Break-even':<10} | {'Efficiency':<10} | {'Pos Days':<8}"
    )
    print("-" * 84)

    for m in ["v1_additive", "v2_proportional", "flat_15", "expanding_ratio"]:
        r = sel[m]
        print(
            f"{m:<18} | {r['avoided_mwh']:>14,.1f} | {r['extra_mwh']:>12,.1f} | {r['breakeven_ratio']:>10.3f}x | {r['efficiency']*100:>9.1f}% | {r['pos_days']:>3}/15"
        )

    # Evaluate decision rule on Selection Half
    max_avoided = max(
        sel[m]["avoided_mwh"]
        for m in ["v1_additive", "v2_proportional", "flat_15", "expanding_ratio"]
    )
    threshold_avoided = 0.90 * max_avoided
    print(f"\nSelection Protocol Rule Check:")
    print(f"Max Avoided Shortfall on Selection Half: {max_avoided:,.1f} MWh")
    print(f"90% Qualification Threshold: {threshold_avoided:,.1f} MWh")

    qualified = []
    for m in ["v1_additive", "v2_proportional", "flat_15", "expanding_ratio"]:
        av = sel[m]["avoided_mwh"]
        eff = sel[m]["efficiency"]
        be = sel[m]["breakeven_ratio"]
        is_qual = av >= threshold_avoided
        status = "QUALIFIED" if is_qual else "DISQUALIFIED (< 90%)"
        print(
            f"  • {m:<18}: Avoided = {av:,.1f} MWh ({status}), Efficiency = {eff*100:.1f}%, BE = {be:.3f}x"
        )
        if is_qual:
            qualified.append((m, eff, av))

    # Pick highest efficiency among qualified
    winner = max(qualified, key=lambda x: x[1])
    print(
        f"\nWINNER of Protocol Selection Window: '{winner[0]}' with {winner[1]*100:.1f}% efficiency and {winner[2]:,.1f} MWh avoided shortfall."
    )

    # 2. Holdout Half: Jan 16-30 decisions (targeting Jan 17-31)
    hld = evaluate_window(16, 30, dm)
    print("\n--- 2. HOLDOUT HALF (Jan 16-30 Decisions, 720 intervals - EVALUATED ONCE) ---")
    print(
        f"Raw Elexon: Forecast = {hld['raw_elexon']['forecast_mwh']:,.1f} MWh, "
        f"Actual = {hld['raw_elexon']['actual_mwh']:,.1f} MWh, "
        f"Shortfall = {hld['raw_elexon']['shortfall_mwh']:,.1f} MWh"
    )
    print(
        f"{'Model':<18} | {'Avoided (MWh)':<14} | {'Extra (MWh)':<12} | {'Break-even':<10} | {'Efficiency':<10} | {'Pos Days':<8}"
    )
    print("-" * 84)

    for m in ["v1_additive", "v2_proportional", "flat_15", "expanding_ratio"]:
        r = hld[m]
        print(
            f"{m:<18} | {r['avoided_mwh']:>14,.1f} | {r['extra_mwh']:>12,.1f} | {r['breakeven_ratio']:>10.3f}x | {r['efficiency']*100:>9.1f}% | {r['pos_days']:>3}/15"
        )

    # 3. Full Month: Jan 1-30 decisions (targeting Jan 2-31)
    tot = evaluate_window(1, 30, dm)
    print("\n--- 3. FULL MONTH (Jan 1-30 Decisions, 1,440 intervals) ---")
    print(
        f"Raw Elexon: Forecast = {tot['raw_elexon']['forecast_mwh']:,.1f} MWh, "
        f"Actual = {tot['raw_elexon']['actual_mwh']:,.1f} MWh, "
        f"Shortfall = {tot['raw_elexon']['shortfall_mwh']:,.1f} MWh"
    )
    print(
        f"{'Model':<18} | {'Avoided (MWh)':<14} | {'Extra (MWh)':<12} | {'Break-even':<10} | {'Efficiency':<10} | {'Pos Days':<8}"
    )
    print("-" * 84)

    for m in ["v1_additive", "v2_proportional", "flat_15", "expanding_ratio"]:
        r = tot[m]
        print(
            f"{m:<18} | {r['avoided_mwh']:>14,.1f} | {r['extra_mwh']:>12,.1f} | {r['breakeven_ratio']:>10.3f}x | {r['efficiency']*100:>9.1f}% | {r['pos_days']:>3}/30"
        )

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
