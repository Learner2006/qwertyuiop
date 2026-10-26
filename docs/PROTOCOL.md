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
  * If fewer than 2 completed delivery days exist ($< 96$ settlement intervals, i.e. $D \le 2$), falls back to the default 15% haircut ($\rho = 0.85$).
  * For $D \ge 3$, applies the expanding realized ratio directly, strictly clamped to $[0.0, 1.0]$:
    $$\text{Plan}_t = \max(0, \min(1.0, \rho) \times F_t)$$

> [!NOTE] Specification Correction (Finding F9)
> The initial implementation clamped the realization ratio to `min(1.2, rho)` instead of `min(1.0, rho)` and tested `len(intervals) >= 2` rather than completed delivery days ($\ge 96$ intervals). The corrected specification clamps strictly to $[0.0, 1.0]$ and enforces the $\ge 2$ completed delivery days threshold ($\ge 96$ intervals).
> Before/After Effect on January 2026 Full-Month Results:
> - Before correction: Avoided 880,900.8 MWh, Extra 313,618.8 MWh, Break-even 1.356×, Efficiency 73.8%.
> - After correction: Avoided 880,742.5 MWh, Extra 306,774.7 MWh, Break-even 1.348×, Efficiency 74.2%.

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

---

## 5. Candidate Evaluation Results & Model Selection Decision

Generated via `python3 scripts/evaluate_models.py` on 2026-10-25.

### 5.1 Selection Window Results (Jan 1–15 Decisions, 720 Settlement Intervals)
* Raw Elexon: Forecast = 4,489,423.0 MWh, Actual = 3,954,087.0 MWh, Shortfall = 618,188.5 MWh

| Candidate Model | Avoided Shortfall (MWh) | Incremental Extra (MWh) | Break-Even ($k^*$) | Efficiency (%) | Days where break-even < 2x | Qualification Status |
|---|---|---|---|---|---|---|
| `v1_additive` (p75) | 399,083.8 | 561,943.8 | 2.408× | 41.5% | 8 / 15 | Disqualified (< 90% threshold) |
| `v2_proportional` (p75) | 432,786.6 | 376,780.8 | 1.871× | 53.5% | 8 / 15 | Qualified ($\ge 401,062.7$ MWh) |
| **`flat_15` (15% Static)** | **445,625.2** | **227,788.3** | **1.511×** | **66.2%** | **9 / 15** | **Qualified & Winner (Highest Efficiency)** |
| `expanding_ratio` | 388,289.4 | 184,546.0 | 1.475× | 67.8% | 10 / 15 | Disqualified (< 90% threshold) |

**Decision Rule Application:**
* Maximum Avoided Shortfall: $445,625.2$ MWh (`flat_15`).
* 90% Qualification Threshold: $401,062.7$ MWh.
* Qualified Candidates: `flat_15` (445.6k MWh) and `v2_proportional` (432.8k MWh).
* Efficiency: `flat_15` achieves **66.2%** vs `v2_proportional` at **53.5%**.
* **Selected Headline Model:** **`flat_15`**.

---

### 5.2 Single-Pass Holdout Evaluation (Jan 16–30 Decisions, 720 Settlement Intervals)
* Evaluated strictly once following selection; zero hyperparameter tuning.
* Raw Elexon: Forecast = 5,034,554.0 MWh, Actual = 4,293,054.5 MWh, Shortfall = 767,740.5 MWh

| Candidate Model | Avoided Shortfall (MWh) | Incremental Extra (MWh) | Break-Even ($k^*$) | Efficiency (%) | Days where break-even < 2x |
|---|---|---|---|---|---|
| `v1_additive` (p75) | 569,819.7 | 423,584.2 | 1.743× | 57.4% | 9 / 15 |
| `v2_proportional` (p75) | 589,841.5 | 529,197.3 | 1.897× | 52.7% | 10 / 15 |
| **`flat_15` (Selected Headline)** | **571,037.0** | **184,146.1** | **1.322×** | **75.6%** | **13 / 15** |
| `expanding_ratio` | 492,453.1 | 122,228.8 | 1.248× | 80.1% | 13 / 15 |

---

### 5.3 Full Month Performance (Jan 1–30 Decisions, 1,440 Settlement Intervals)
* Raw Elexon: Forecast = 9,523,977.0 MWh, Actual = 8,247,141.5 MWh, Shortfall = 1,385,929.0 MWh

| Model | Total Avoided Shortfall (MWh) | Total Extra Supply (MWh) | Break-Even ($k^*$) | Efficiency (%) | Days where break-even < 2x |
|---|---|---|---|---|---|
| `v1_additive` (p75) | 968,903.4 | 985,528.0 | 2.017× | 49.6% | 17 / 30 |
| `v2_proportional` (p75) | 1,022,628.1 | 905,978.1 | 1.886× | 53.0% | 18 / 30 |
| **`flat_15` (Production Headline)** | **1,016,662.2** | **411,934.4** | **1.405×** | **71.2%** | **22 / 30** |
| `expanding_ratio` | 880,742.5 | 306,774.7 | 1.348× | 74.2% | 23 / 30 |

---

## 6. Frozen Parameter Confirmation
* **Headline Model:** `flat_15` (15% static uniform haircut).
* **Percentile Controls:** Maintained as an optional caution slider on Estimate and Check pages (allowing user risk preferences: p60, p75, p85, p90) but documented honestly as an empirical risk adjustment rather than the primary source of the base structural haircut.
* **Pre-selection Commit Hash:** `979d1ce`
* **Frozen Protocol Commit:** (recorded in git log)

