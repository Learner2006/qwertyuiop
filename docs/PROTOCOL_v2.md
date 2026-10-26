# Out-of-Time Model Decision Protocol (v2)

**Status:** Frozen Protocol (Milestone R4)  
**Date:** October 2026  
**Evaluation Scope:** Out-of-Time Delivery Days: February 1, 2026 to September 30, 2026  
**Warm-Up Lookback:** Available data from January 29, 2026 00:00 UTC to provide rolling history for February 1 decisions.  
**Immutability:** This protocol is committed and tagged (`protocol-v2-frozen`) prior to downloading, inspecting, or processing any post-January 2026 data.

---

## 1. Motivation and Principles

In Round 1, candidate models were evaluated on January 2026 data. However, the holdout split within January occurred in the presence of prior exploration. To establish true out-of-time validity across multiple seasons (spring, summer, early autumn), this protocol pre-declares the evaluation criteria, models, metrics, sensitivity analyses, and model-selection decision rules for unseen data from February 1 to September 30, 2026.

---

## 2. Candidate Models

Four candidate models are evaluated under identical 09:00 UTC daily decision cutoff rules:

1. **`flat_15` (Static 15% Proportional Haircut):**
   $$\text{Plan}_t = 0.85 \times F_t$$
   Zero hyperparameter, zero lookback reliance.

2. **`expanding_ratio` (Cumulative Realization Ratio):**
   $$\rho = \frac{\sum_{i \in \text{past actuals}} A_i}{\sum_{i \in \text{past actuals}} F_i}$$
   Clamped strictly to $[0.0, 1.0]$. If fewer than 2 completed delivery days ($\ge 96$ settlement intervals) are available in the dataset history, falls back to static $\rho = 0.85$ (15% haircut). For $D \ge 3$, applies $\rho$ directly:
   $$\text{Plan}_t = \max(0, \rho \times F_t)$$

3. **`v1_additive` (48h Rolling Signed-Error Percentile, p75):**
   Computes signed errors ($F - A$) over up to 96 available intervals in the 48-hour lookback (accounting for 1-hour publication lag). Blends linearly with 15% haircut when $< 96$ intervals exist:
   $$\text{Plan}_t = \max(0, F_t - \text{Margin}_t)$$

4. **`v2_proportional` (48h Rolling Relative Error Percentile, p75):**
   Computes relative over-forecast error percentages ($(F - A)/F$) over the 48-hour lookback. Blends linearly with 15% haircut when $< 96$ intervals exist:
   $$\text{Plan}_t = \max(0, (1 - r_{\text{eff}}) \times F_t)$$

---

## 3. Metrics and Evaluation Standards

### 3.1 Primary Scalar Metric: Net MWh-equivalent ($k=2, s=0$)
The primary optimization and ranking metric across the validation window is the net energy-equivalent savings:
$$\text{Net MWh} = \text{Avoided Shortfall} - \text{Extra Advance} \times (1 - s) \times \frac{1}{k - 1}$$
Under the baseline operational assumptions ($k=2.0$ replacement power cost multiplier, $s=0.0$ unrecoverable surplus):
$$\text{Net MWh}_{k=2, s=0} = \text{Avoided Shortfall} - \text{Extra Advance}$$

### 3.2 Secondary Metrics
- **Avoided Shortfall (MWh):** $\sum \max(0, F_t - A_t) - \sum \max(0, \text{Plan}_t - A_t)$
- **Incremental Extra Advance Supply (MWh):** $\sum \max(0, A_t - \text{Plan}_t) - \sum \max(0, A_t - F_t)$
- **Break-Even Price Ratio ($k^*$):** $1 + \frac{\text{Extra Advance}}{\text{Avoided Shortfall}}$ (at $s=0.0$)
- **Days where break-even < 2x:** Number of delivery days where avoided shortfall exceeds extra advance supply.
- **Matched-Cut Comparison:** For each model $m$ with total cut volume $C_m = \sum (F_t - \text{Plan}_{m,t}) \times 0.5$, compute a static benchmark $\text{flat\_X}_m$ where $X_m = C_m / \sum (F_t \times 0.5)$. Evaluate whether model $m$ achieves higher Avoided Shortfall and higher Net MWh than a static haircut of the identical cut volume.

---

## 4. Sensitivity Grid Specification

To evaluate robustness against operational variations, the single-pass validation script will execute a 4-dimensional sensitivity sweep:
1. **Decision Cutoffs:** 07:00 UTC, 09:00 UTC, 11:00 UTC.
2. **Actuals Publication Lag:** 0 hours, 1 hour (baseline), 2 hours.
3. **Lookback Windows:** 24 hours (48 slots), 48 hours (96 slots, baseline), 72 hours (144 slots).
4. **Risk Percentiles:** p60, p75 (baseline), p85, p90.

---

## 5. Decision Rule for Headline Model Selection

The production headline model across the entire application will be determined as follows:
1. **Performance Rank:** Rank all four candidate models by cumulative Net MWh-equivalent at $k=2, s=0$ across the entire validation dataset (February 1 to September 30, 2026).
2. **Qualification:** A candidate must achieve positive cumulative Net MWh ($\text{Net} > 0$, i.e. break-even $k^* < 2.0$) over the validation dataset.
3. **Simplicity Tie-Breaker:** If the highest-performing dynamic model does not exceed `flat_15`'s Net MWh by at least **1.0%**, or if no dynamic model achieves $\text{Net} > 0$, `flat_15` is selected as the production headline model due to zero hyperparameter risk.
4. **Deployment:** If a dynamic candidate wins cleanly ($> 1.0\%$ net improvement over `flat_15`), it will be declared the production headline model in `config.py`, documentation, and summary metrics. Otherwise, `flat_15` remains the production headline model.
