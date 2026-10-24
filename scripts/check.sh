#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "WIND DAY-AHEAD ESTIMATOR: COMPLETE VERIFICATION SUITE"
echo "=========================================================="

# 1. Dataset validation
echo ""
echo "--> STEP 1: Validating Cached Elexon BMRS Parquet Dataset..."
python3 backend/scripts/validate_data.py

# 2. Backend Automated Tests (including no-leakage, calibration, metrics, api)
echo ""
echo "--> STEP 2: Running Backend Automated Tests (pytest)..."
python3 -m pytest backend/tests -v

# 3. Frontend TypeScript Typecheck
echo ""
echo "--> STEP 3: Running Frontend TypeScript Check (tsc)..."
cd frontend && npx tsc --noEmit && cd ..

# 4. Frontend Production Build
echo ""
echo "--> STEP 4: Running Frontend Production Build (vite build)..."
cd frontend && npm run build && cd ..

echo ""
echo "=========================================================="
echo "ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!"
echo "=========================================================="
