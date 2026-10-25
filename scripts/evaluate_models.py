#!/usr/bin/env python3
"""Model Candidate Evaluation Script for Wind Day-Ahead Estimator.
Evaluates four candidates:
1. v1_additive (p75)
2. v2_proportional (p75)
3. flat_15 (15% static)
4. expanding_ratio (completed days realization ratio)

Executes the selection protocol defined in docs/PROTOCOL.md:
- Selection half: Jan 1-15 decisions (targeting Jan 2-16)
- Holdout half: Jan 16-30 decisions (targeting Jan 17-31)
- Evaluates Volume Qualification Threshold (>= 90% of best avoided shortfall)
- Selects model with highest Efficiency (Avoided / (Avoided + Extra))
"""

import datetime
import os
import sys

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.services.prepare import DataManager
from app.services.models import v1_additive, v2_proportional, flat_15, expanding_ratio


def evaluate_window(start_day: int, end_day: int, dm: DataManager) -> dict:
    """Evaluate all 4 candidate models for decisions in range [start_day, end_day]."""
    results = {
        "raw_elexon": {"shortfall_mwh": 0.0, "surplus_mwh": 0.0, "forecast_mwh": 0.0, "actual_mwh": 0.0},
        "v1_additive": {"shortfall_mwh": 0.0, "surplus_mwh": 0.0, "avoided_mwh": 0.0, "extra_mwh": 0.0, "pos_days": 0},
        "v2_proportional": {"shortfall_mwh": 0.0, "surplus_mwh": 0.0, "avoided_mwh": 0.0, "extra_mwh": 0.0, "pos_days": 0},
        "flat_15": {"shortfall_mwh": 0.0, "surplus_mwh": 0.0, "avoided_mwh": 0.0, "extra_mwh": 0.0, "pos_days": 0},
        "expanding_ratio": {"shortfall_mwh": 0.0, "surplus_mwh": 0.0, "avoided_mwh": 0.0, "extra_mwh": 0.0, "pos_days": 0},
    }

    # Pre-gather all completed days actuals and day-ahead forecasts for expanding ratio
    completed_history_actuals = {}
    completed_history_forecasts = {}

    for d in range(1, 31):
        dec_d = datetime.date(2026, 1, d)
        tar_d = dec_d + datetime.timedelta(days=1)
        completed_history_forecasts[tar_d] = dm.select_target_forecast(dec_d, tar_d)
        completed_history_actuals[tar_d] = dm.get_target_actuals(tar_d)

    for d in range(start_day, end_day + 1):
        dec_d = datetime.date(2026, 1, d)
        tar_d = dec_d + datetime.timedelta(days=1)

        fcs = dm.select_target_forecast(dec_d, tar_d)
        cal = dm.get_calibration_observations(dec_d)
        acts = dm.get_target_actuals(tar_d)

        # Raw Elexon metrics
        e_sf = sum(max(0.0, f["generation_gw"] - a["generation_gw"]) * 500.0 for f, a in zip(fcs, acts))
        e_sp = sum(max(0.0, a["generation_gw"] - f["generation_gw"]) * 500.0 for f, a in zip(fcs, acts))
        results["raw_elexon"]["shortfall_mwh"] += e_sf
        results["raw_elexon"]["surplus_mwh"] += e_sp
        results["raw_elexon"]["forecast_mwh"] += sum(f["generation_gw"] * 500.0 for f in fcs)
        results["raw_elexon"]["actual_mwh"] += sum(a["generation_gw"] * 500.0 for a in acts)

        # 1. v1 additive
        v1_res = v1_additive(fcs, cal, percentile=75.0)
        v1_sf = sum(max(0.0, p - a["generation_gw"]) * 500.0 for p, a in zip(v1_res["plans"], acts))
        v1_sp = sum(max(0.0, a["generation_gw"] - p) * 500.0 for p, a in zip(v1_res["plans"], acts))
        v1_av = e_sf - v1_sf
        v1_ex = v1_sp - e_sp
        results["v1_additive"]["shortfall_mwh"] += v1_sf
        results["v1_additive"]["surplus_mwh"] += v1_sp
        results["v1_additive"]["avoided_mwh"] += v1_av
        results["v1_additive"]["extra_mwh"] += v1_ex
        if v1_av > v1_ex:
            results["v1_additive"]["pos_days"] += 1

        # 2. v2 proportional
        v2_res = v2_proportional(fcs, cal, percentile=75.0)
        v2_sf = sum(max(0.0, p - a["generation_gw"]) * 500.0 for p, a in zip(v2_res["plans"], acts))
        v2_sp = sum(max(0.0, a["generation_gw"] - p) * 500.0 for p, a in zip(v2_res["plans"], acts))
        v2_av = e_sf - v2_sf
        v2_ex = v2_sp - e_sp
        results["v2_proportional"]["shortfall_mwh"] += v2_sf
        results["v2_proportional"]["surplus_mwh"] += v2_sp
        results["v2_proportional"]["avoided_mwh"] += v2_av
        results["v2_proportional"]["extra_mwh"] += v2_ex
        if v2_av > v2_ex:
            results["v2_proportional"]["pos_days"] += 1

        # 3. flat 15%
        f15_res = flat_15(fcs, cal)
        f15_sf = sum(max(0.0, p - a["generation_gw"]) * 500.0 for p, a in zip(f15_res["plans"], acts))
        f15_sp = sum(max(0.0, a["generation_gw"] - p) * 500.0 for p, a in zip(f15_res["plans"], acts))
        f15_av = e_sf - f15_sf
        f15_ex = f15_sp - e_sp
        results["flat_15"]["shortfall_mwh"] += f15_sf
        results["flat_15"]["surplus_mwh"] += f15_sp
        results["flat_15"]["avoided_mwh"] += f15_av
        results["flat_15"]["extra_mwh"] += f15_ex
        if f15_av > f15_ex:
            results["flat_15"]["pos_days"] += 1

        # 4. expanding ratio
        # completed days up to D-1 delivery: target days Jan 2 through Jan (d-1)
        comp_acts = []
        comp_fcs = []
        for past_day in range(2, d):
            past_tar_d = datetime.date(2026, 1, past_day)
            comp_acts.extend(completed_history_actuals[past_tar_d])
            comp_fcs.extend(completed_history_forecasts[past_tar_d])

        er_res = expanding_ratio(fcs, completed_days_actuals=comp_acts, completed_days_forecasts=comp_fcs)
        er_sf = sum(max(0.0, p - a["generation_gw"]) * 500.0 for p, a in zip(er_res["plans"], acts))
        er_sp = sum(max(0.0, a["generation_gw"] - p) * 500.0 for p, a in zip(er_res["plans"], acts))
        er_av = e_sf - er_sf
        er_ex = er_sp - e_sp
        results["expanding_ratio"]["shortfall_mwh"] += er_sf
        results["expanding_ratio"]["surplus_mwh"] += er_sp
        results["expanding_ratio"]["avoided_mwh"] += er_av
        results["expanding_ratio"]["extra_mwh"] += er_ex
        if er_av > er_ex:
            results["expanding_ratio"]["pos_days"] += 1

    # Compute ratios
    for m in ["v1_additive", "v2_proportional", "flat_15", "expanding_ratio"]:
        av = results[m]["avoided_mwh"]
        ex = results[m]["extra_mwh"]
        results[m]["breakeven_ratio"] = round(ex / av, 3) if av > 0 else 999.0
        results[m]["efficiency"] = round(av / (av + ex), 4) if (av + ex) > 0 else 0.0

    return results


def main():
    dm = DataManager.get_instance()

    print("=" * 80)
    print("WIND DAY-AHEAD ESTIMATOR: MODEL PROTOCOL EVALUATION")
    print("=" * 80)

    # 1. Selection Half: Jan 1-15 decisions (targeting Jan 2-16)
    sel = evaluate_window(1, 15, dm)
    print("\n--- 1. SELECTION HALF (Jan 1-15 Decisions, 720 intervals) ---")
    print(f"Raw Elexon: Forecast = {sel['raw_elexon']['forecast_mwh']:,.1f} MWh, "
          f"Actual = {sel['raw_elexon']['actual_mwh']:,.1f} MWh, "
          f"Shortfall = {sel['raw_elexon']['shortfall_mwh']:,.1f} MWh")
    print(f"{'Model':<18} | {'Avoided (MWh)':<14} | {'Extra (MWh)':<12} | {'Break-even':<10} | {'Efficiency':<10} | {'Pos Days':<8}")
    print("-" * 84)

    for m in ["v1_additive", "v2_proportional", "flat_15", "expanding_ratio"]:
        r = sel[m]
        print(f"{m:<18} | {r['avoided_mwh']:>14,.1f} | {r['extra_mwh']:>12,.1f} | {r['breakeven_ratio']:>10.3f}x | {r['efficiency']*100:>9.1f}% | {r['pos_days']:>3}/15")

    # Evaluate decision rule on Selection Half
    max_avoided = max(sel[m]["avoided_mwh"] for m in ["v1_additive", "v2_proportional", "flat_15", "expanding_ratio"])
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
        print(f"  • {m:<18}: Avoided = {av:,.1f} MWh ({status}), Efficiency = {eff*100:.1f}%, BE = {be:.3f}x")
        if is_qual:
            qualified.append((m, eff, av))

    # Pick highest efficiency among qualified
    qualified.sort(key=lambda x: (x[1], x[2]), reverse=True)
    winner = qualified[0][0]
    print(f"\n>>> PROTOCOL WINNER: {winner} (Efficiency: {qualified[0][1]*100:.1f}%) <<<")

    # 2. Holdout Half: Jan 16-30 decisions (targeting Jan 17-31)
    hld = evaluate_window(16, 30, dm)
    print("\n--- 2. HOLDOUT HALF (Jan 16-30 Decisions, 720 intervals - EVALUATED ONCE) ---")
    print(f"Raw Elexon: Forecast = {hld['raw_elexon']['forecast_mwh']:,.1f} MWh, "
          f"Actual = {hld['raw_elexon']['actual_mwh']:,.1f} MWh, "
          f"Shortfall = {hld['raw_elexon']['shortfall_mwh']:,.1f} MWh")
    print(f"{'Model':<18} | {'Avoided (MWh)':<14} | {'Extra (MWh)':<12} | {'Break-even':<10} | {'Efficiency':<10} | {'Pos Days':<8}")
    print("-" * 84)

    for m in ["v1_additive", "v2_proportional", "flat_15", "expanding_ratio"]:
        r = hld[m]
        print(f"{m:<18} | {r['avoided_mwh']:>14,.1f} | {r['extra_mwh']:>12,.1f} | {r['breakeven_ratio']:>10.3f}x | {r['efficiency']*100:>9.1f}% | {r['pos_days']:>3}/15")

    # 3. Full Month: Jan 1-30 decisions (targeting Jan 2-31)
    tot = evaluate_window(1, 30, dm)
    print("\n--- 3. FULL MONTH (Jan 1-30 Decisions, 1,440 intervals) ---")
    print(f"Raw Elexon: Forecast = {tot['raw_elexon']['forecast_mwh']:,.1f} MWh, "
          f"Actual = {tot['raw_elexon']['actual_mwh']:,.1f} MWh, "
          f"Shortfall = {tot['raw_elexon']['shortfall_mwh']:,.1f} MWh")
    print(f"{'Model':<18} | {'Avoided (MWh)':<14} | {'Extra (MWh)':<12} | {'Break-even':<10} | {'Efficiency':<10} | {'Pos Days':<8}")
    print("-" * 84)

    for m in ["v1_additive", "v2_proportional", "flat_15", "expanding_ratio"]:
        r = tot[m]
        print(f"{m:<18} | {r['avoided_mwh']:>14,.1f} | {r['extra_mwh']:>12,.1f} | {r['breakeven_ratio']:>10.3f}x | {r['efficiency']*100:>9.1f}% | {r['pos_days']:>3}/30")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
