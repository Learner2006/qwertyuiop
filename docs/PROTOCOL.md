# Model Decision Protocol & Selection Specification

**Status:** Pre-registered Protocol  
**Date:** January 2026 (Documented for Audit)  
**Evaluation Cutoff:** January 1–15, 2026 Decisions  
**Holdout Range:** January 16–30, 2026 Decisions  

---

## 1. Objective and Principles

The objective of this protocol is to establish a rigorous, objective, and auditable methodology for selecting the headline production model for the Wind Day-Ahead Estimator. To prevent p-hacking, overfitting, and post-hoc rationalization, model selection is governed by a pre-registered rule evaluated strictly on the **Selection Window (January 1–15 decisions)** before examining or tuning against the **Holdout Window (January 16–30 decisions)**.

---

## 2. Model Candidates

Four model candidates are evaluated under this protocol:

### Candidate 1: `v1_additive` (Rolling Signed-Error Percentile)
* **Status:** Pre-declared *a priori* baseline.
* **Mechanism:** Computes half-hourly signed forecast errors ($F - A$) over a 48-hour rolling lookback (up to 96 observations). Extracts the $p$-th percentile (default $p=75$). If fewer than 96 observations are available, linearly blends the empirical error margin with a 15% cold-start proportional haircut:
  $$\text{Margin} = w \cdot \text{Percentile}(F - A, p) + (1 - w) \cdot (0.15 \times \bar{F})$$
  $$\text{Plan}_t = \max(0, F_t - \text{Margin})$$

### Candidate 2: `v2_proportional` (Rolling Relative Error Percentile)
* **Status:** Exploratory / Post-hoc candidate, proposed after observing high-wind regime volatility on January 13–14.
* **Mechanism:** Computes relative over-forecast error percentages ($(F - A) / F$) over the 48-hour lookback. Extracts the $p$-th percentile ($r_p$, default $p=75$), floored at 0 and capped at 100%. Blends linearly with 15% cold-start:
  $$r_{\text{eff}} = w \cdot r_p + (1 - w) \cdot 0.15$$
  $$\text{Plan}_t = \max(0, (1 - r_{\text{eff}}) \times F_t)$$

### Candidate 3: `flat_15` (Static 15% Proportional Haircut)
* **Status:** Pre-declared *a priori* baseline (identical to the cold-start fallback).
* **Mechanism:** Static, zero-parameter proportional reduction of 15% applied uniformly to all half-hourly day-ahead forecasts:
  $$\text{Plan}_t = 0.85 \times F_t$$

### Candidate 4: `expanding_ratio` (Expanding Window Empirical Realization Ratio)
* **Status:** Exploratory candidate, designed after observing full-month outturn persistence.
* **Mechanism:** Tracks the cumulative empirical realization ratio $\rho = \frac{\sum A}{\sum F}$ over all completed delivery days up to $D-1$.
  * If fewer than 2 completed delivery days exist ($D \le 2$), falls back to the default 15% haircut ($\rho = 0.85$).
  * For $D \ge 3$, applies the expanding realized ratio directly:
    $$\text{Plan}_t = \max(0, \min(1.0, \rho) \times F_t)$$

---

## 3. Selection Methodology

### 3.1 Evaluation Window
* **Selection Dataset:** Decisions made between January 1, 2026 09:00 UTC and January 15, 2026 09:00 UTC inclusive (15 decision days, 720 target half-hourly settlement periods targeting January 2 to January 16 delivery).

### 3.2 Metrics & Definitions
For each candidate model $m$:
1. **Avoided Shortfall (MWh):**
   $$\Delta \text{Shortfall}_m = \text{Shortfall}_{\text{Elexon}} - \text{Shortfall}_m$$
   where $\text{Shortfall} = \sum \max(0, \text{Plan}_t - \text{Actual}_t) \times 0.5 \text{ h} \times 1000 \text{ MWh/GWh}$.
2. **Incremental Extra Supply (MWh):**
   $$\Delta \text{Surplus}_m = \text{Surplus}_m - \text{Surplus}_{\text{Elexon}}$$
   where $\text{Surplus} = \sum \max(0, \text{Actual}_t - \text{Plan}_t) \times 0.5 \text{ h} \times 1000 \text{ MWh/GWh}$.
3. **Efficiency (Share of Total Cut Avoiding Shortfall):**
   $$\text{Efficiency}_m = \frac{\Delta \text{Shortfall}_m}{\Delta \text{Shortfall}_m + \Delta \text{Surplus}_m}$$
   *(Note: The break-even price ratio $k^* = \frac{\Delta \text{Surplus}}{\Delta \text{Shortfall}} = \frac{1}{\text{Efficiency}} - 1$)*.

### 3.3 Written Decision Rule
The headline model will be selected strictly according to the following 3-stage decision rule:

1. **Volume Qualification Threshold:**
   Calculate the maximum Avoided Shortfall across all candidates on the selection window:
   $$S_{\max} = \max_{m} \Delta \text{Shortfall}_m$$
   A candidate is qualified if and only if it captures at least 90% of the maximum avoided shortfall:
   $$\Delta \text{Shortfall}_m \ge 0.90 \times S_{\max}$$

2. **Efficiency Maximization:**
   Among all qualified candidates, select the candidate with the highest **Efficiency** (equivalently, the lowest break-even ratio $k^*$).

3. **Simplicity Tie-Breaker:**
   If two or more candidates have Efficiency within 1.0 percentage point ($\le 0.01$), select the simpler model (fewer parameters, no rolling window hyperparameter risk).

---

## 4. Single-Pass Holdout Evaluation

Once the headline model is determined by the decision rule on the selection half:
1. The parameters and model choice are **frozen**.
2. The candidates are evaluated **exactly once** on the Holdout Window: January 16, 2026 09:00 UTC through January 30, 2026 09:00 UTC (15 decision days, 720 target half-hourly settlement periods targeting January 17 to January 31 delivery).
3. The results on both the selection half and the holdout half are reported transparently in the final results table.
4. No further tuning, adjustments, or model switches are permitted.
