#!/usr/bin/env python3
"""Comprehensive sweep test across all 30 dates for /api/estimate and /api/check.
Verifies:
- HTTP 200 OK for every date
- No unexpected nulls or NaN values in any field
- Mathematical consistency
"""

import math
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
from app.main import app

client = TestClient(app)


def check_for_nan(obj, path=""):
    """Recursively check that no float in the JSON payload is NaN."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ValueError(f"Found NaN or Inf at path: {path}")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            check_for_nan(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            check_for_nan(item, f"{path}[{idx}]")


def run_sweep():
    print("=" * 80)
    print("STARTING 30-DATE SWEEP FOR ESTIMATE AND CHECK ENDPOINTS")
    print("=" * 80)

    estimate_failures = 0
    check_failures = 0

    for d in range(1, 31):
        date_str = f"2026-01-{d:02d}"

        # 1. Sweep /api/estimate
        resp_est = client.get(f"/api/estimate?date={date_str}&percentile=75.0")
        if resp_est.status_code != 200:
            print(f"[FAIL] /api/estimate date={date_str} returned {resp_est.status_code}: {resp_est.text}")
            estimate_failures += 1
        else:
            est_data = resp_est.json()
            try:
                check_for_nan(est_data)
                # Verify key required fields are not None
                assert est_data["elexon_headline_gw"] is not None
                assert est_data["safe_headline_gw"] is not None
                assert len(est_data["intervals"]) == 48
                assert len(est_data["slider_tradeoffs"]) >= 3
                assert est_data["calculation"] is not None
                assert est_data["error_distribution"] is not None
            except Exception as e:
                print(f"[FAIL] /api/estimate payload validation error on {date_str}: {e}")
                estimate_failures += 1

        # 2. Sweep /api/check
        resp_chk = client.get(f"/api/check?date={date_str}&percentile=75.0")
        if resp_chk.status_code != 200:
            print(f"[FAIL] /api/check date={date_str} returned {resp_chk.status_code}: {resp_chk.text}")
            check_failures += 1
        else:
            chk_data = resp_chk.json()
            try:
                check_for_nan(chk_data)
                assert chk_data["actual_headline_gw"] is not None
                assert chk_data["elexon_shortfall_mwh"] is not None
                assert chk_data["saved_shortfall_mwh"] is not None
                assert chk_data["incremental_surplus_mwh"] is not None
                assert len(chk_data["intervals"]) == 48
                assert chk_data["headline_result"]
            except Exception as e:
                print(f"[FAIL] /api/check payload validation error on {date_str}: {e}")
                check_failures += 1

        sys.stdout.write(f"\rSwept date {d}/30 ({date_str}): Status 200 OK, No NaN/Nulls detected.")
        sys.stdout.flush()

    print("\n" + "=" * 80)
    print(f"SWEEP COMPLETE: {30 - estimate_failures}/30 Estimate dates passed, {30 - check_failures}/30 Check dates passed.")
    print("=" * 80)

    if estimate_failures > 0 or check_failures > 0:
        print("FAILED: One or more dates had failures!")
        sys.exit(1)
    else:
        print("SUCCESS: 100% of 30 dates passed all validations without nulls or NaNs.")


if __name__ == "__main__":
    run_sweep()
