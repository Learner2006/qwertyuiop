#!/usr/bin/env python3
"""Regenerate backend/tests/golden_numbers.json with mandatory reason logging and visual diff."""

import argparse
import difflib
import json
import os
import sys

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from app.main import app


GOLDEN_PATH = os.path.join(
    os.path.dirname(__file__), "..", "backend", "tests", "golden_numbers.json"
)


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate golden numbers with mandatory reason logging and diff."
    )
    parser.add_argument(
        "--reason",
        required=True,
        help="Mandatory reason explaining why golden numbers changed.",
    )
    args = parser.parse_args()

    client = TestClient(app)
    resp = client.get("/api/summary?percentile=75")
    if resp.status_code != 200:
        print(f"Error: /api/summary returned status {resp.status_code}: {resp.text}")
        sys.exit(1)

    data = resp.json()

    new_golden = {
        "full_month": {
            "total_slots": data["total_target_intervals"],
            "raw_elexon": {
                "forecast_mwh": data["total_elexon_forecast_mwh"],
                "actual_mwh": data["total_actual_wind_mwh"],
                "shortfall_mwh": data["total_elexon_shortfall_mwh"],
            },
            "v1_additive": {
                "avoided_shortfall_mwh": data["total_avoided_shortfall_mwh"],
                "extra_supply_mwh": data["total_incremental_surplus_mwh"],
                "breakeven_ratio": data["breakeven_ratio"],
            },
            "v2_proportional": {
                "avoided_shortfall_mwh": data["v2_proportional_benchmark"]["avoided_shortfall_mwh"],
                "extra_supply_mwh": data["v2_proportional_benchmark"]["extra_supply_mwh"],
                "breakeven_ratio": data["v2_proportional_benchmark"]["breakeven_ratio"],
            },
            "flat_15": {
                "avoided_shortfall_mwh": data["flat_15_benchmark"]["avoided_shortfall_mwh"],
                "extra_supply_mwh": data["flat_15_benchmark"]["extra_supply_mwh"],
                "breakeven_ratio": data["flat_15_benchmark"]["breakeven_ratio"],
            },
        },
        "first_half": {
            "total_slots": 720,
            "raw_elexon": {
                "forecast_mwh": 4489423.4,
                "actual_mwh": 3954087.0,
                "shortfall_mwh": 618188.0,
            },
            "v1_additive": {
                "avoided_shortfall_mwh": data["first_half_v1"]["avoided_shortfall_mwh"],
                "extra_supply_mwh": data["first_half_v1"]["extra_supply_mwh"],
                "breakeven_ratio": data["first_half_v1"]["breakeven_ratio"],
            },
            "v2_proportional": {
                "avoided_shortfall_mwh": data["first_half_v2"]["avoided_shortfall_mwh"],
                "extra_supply_mwh": data["first_half_v2"]["extra_supply_mwh"],
                "breakeven_ratio": data["first_half_v2"]["breakeven_ratio"],
            },
            "flat_15": {
                "avoided_shortfall_mwh": data["first_half_flat15"]["avoided_shortfall_mwh"],
                "extra_supply_mwh": data["first_half_flat15"]["extra_supply_mwh"],
                "breakeven_ratio": data["first_half_flat15"]["breakeven_ratio"],
            },
        },
    }

    old_content = ""
    if os.path.exists(GOLDEN_PATH):
        with open(GOLDEN_PATH, "r") as f:
            old_content = f.read()

    new_content = json.dumps(new_golden, indent=2) + "\n"

    diff = list(
        difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile="golden_numbers.json (old)",
            tofile="golden_numbers.json (new)",
        )
    )

    print("=" * 60)
    print(f"REASON: {args.reason}")
    print("=" * 60)
    if diff:
        print("DIFF:")
        for line in diff:
            sys.stdout.write(line)
        with open(GOLDEN_PATH, "w") as f:
            f.write(new_content)
        print(f"\nSuccessfully regenerated {GOLDEN_PATH}")
    else:
        print("No changes in golden numbers.")
    print("=" * 60)


if __name__ == "__main__":
    main()
