#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "WIND DAY-AHEAD ESTIMATOR: COMPLETE VERIFICATION SUITE"
echo "=========================================================="

# 1. Dataset validation
echo ""
echo "--> STEP 1: Validating Cached Elexon BMRS Parquet Dataset..."
python3 backend/scripts/validate_data.py

# 2. Audit Checks Baseline
echo ""
echo "--> STEP 2: Running Audit Checks (F1-F12 Verification)..."
python3 scripts/audit_checks.py

# 3. 30-Date Endpoint Sweep
echo ""
echo "--> STEP 3: Running 30-Date Endpoint Sweep (/api/estimate & /api/check)..."
python3 scripts/sweep_test.py

# 4. Backend Automated Tests (59 tests including oracles, properties, bootstrap, lint)
echo ""
echo "--> STEP 4: Running Backend Test Suite (pytest)..."
python3 -m pytest backend/tests -v

# 5. Frontend TypeScript Typecheck
echo ""
echo "--> STEP 5: Running Frontend TypeScript Check (tsc)..."
(cd frontend && npx tsc --noEmit)

# 6. Frontend Production Build
echo ""
echo "--> STEP 6: Running Frontend Production Build (vite build)..."
(cd frontend && npm run build)

echo ""
echo "=========================================================="
echo "ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!"
echo "=========================================================="
