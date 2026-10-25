# AGENT_PLAN.md: Wind Day-Ahead Estimator

Goals and milestones for the coding agent. This plan is based on a read of the repository (`fuelhh.zip`) and an independent re-run of the backend. Where a number is quoted below, it was reproduced from the code, unless marked **(reviewer analysis)**, which means it came from a separate script and is not yet in the repo.

## 0. Ground rules (read first)

1. **Evidence before "done".** A milestone is done only when its acceptance checks have been run and their output is pasted into the milestone's log. Phrases like "verified", "validated" and "all tests pass" are not evidence by themselves.
2. **No parameter tuning after Milestone 3.** Percentile defaults, window length, haircut and model choice are frozen once M3 is signed off. Do not adjust them to improve a chart.
3. **Every number shown to a user comes from the backend API.** No numeric literals or `||` fallback values in the frontend or docs. If the API fails, show an error state, not a stale number.
4. **Report bad results as they are.** If a result is weak, the page says so. Do not reword to look better.
5. **Decision-time pages show only decision-time information.** Anything that uses outcomes after the decision cutoff belongs on the Reliability Check or Methodology pages and must be labelled as a backtest.
6. **Stop and ask** if a requirement conflicts with another, or if a check fails twice for the same reason.

## 1. Current state (verified)

**What works**
- Backend tests: 31 of 31 pass (`python3 -m pytest backend/tests`).
- The summary endpoint reproduces these figures at p75 over 30 decision days (1,440 slots):

| Model | Avoided shortfall (MWh) | Extra supply (MWh) | Break-even ratio |
|---|---|---|---|
| v1 additive | 968,903 | 985,528 | 1.017 |
| v2 proportional | 1,022,628 | 905,978 | 0.886 |
| Flat 15% (pre-set) | 1,016,662 | 411,934 | 0.405 |

- Raw Elexon: 9,523,977 MWh forecast vs 8,247,142 MWh actual (15.5% above). Raw shortfall 1,385,929 MWh.
- On the pre-declared "selection half" (Jan 1–15 decisions) flat 15% also beats v2:

| Model, Jan 1–15 | Avoided | Extra | Break-even |
|---|---|---|---|
| v1 | 399,084 | 561,944 | 1.408 |
| v2 | 432,787 | 376,781 | 0.871 |
| Flat 15% | 445,625 | 227,788 | 0.511 |

So the choice of v2 over flat 15% is not supported by the half it was chosen on.

**Problems found in the code**
- **P1. Hardcoded numbers.**
  - `ComparativeAnalysisSection.tsx` has literal table values (about lines 150–230).
  - Fallbacks such as `|| 1022627.7`, `|| 627721.3` and `|| 739465.9` appear in `ComparativeAnalysisSection.tsx` and `EstimateDeepDive.tsx`.
  - `CostRatioCalculator.tsx` has default props with literals.
  - `totalGenerationMwh={8247000}` and `6263226.5` are literals.
- **P2. Stale text.**
  - `DocsPage.tsx` still shows 976,194 / 983,102 (about lines 49 and 203–204).
  - `README.md` (about line 149) says 976,194 avoided and "1,092,195 extra", but 1,092,195 is the *total* safe surplus, not the incremental extra (985,528).
- **P3. Duplicated model logic.** v2 is computed separately in `routers/check.py` and `routers/summary.py`, while v1 lives in `services/calibrate.py`. The models can drift apart.
- **P4. A trivially true metric.** The summary returns `days_shortfall_reduced: 30`. Any haircut reduces shortfall, so this must not be used as evidence. The meaningful metric is days where avoided shortfall exceeded extra supply.
- **P5. Test gaps.** There is no test that summary totals equal the sum of the daily check results, none that the Estimate page's track record, slider table and calculator never include data after D, and none covering v2 or the baselines.
- **P6. Claims that no longer hold.** "Parameters established in advance, not re-tuned after seeing outturn" and similar text on Landing, Docs and Estimate pages (v2 was introduced after v1's results were seen).
- **P7. Unverified citations.** The definitional paragraph (WINDFOR vs FUELHH, "82–85%", BSC Section Q, NESO/DUKES) has no primary-source quote.

**Data facts to respect**
- Actuals' `publish_time` equals interval end; the 1-hour lag is an assumption and must stay labelled as one.
- The dataset has no Dec 31 actuals, so the first usable calibration pair is Jan 2 (explains the 66-slot history on Jan 3).
- Daily actual/forecast ratio across January: mean 0.875, standard deviation 0.11, min 0.52, max 1.13 **(reviewer analysis)**. The gap is not a stable constant.

## 2. Milestones

### M0. Freeze a baseline (small)
**Goal:** be able to prove later that nothing changed by accident.
- Tag the current commit.
- Add `backend/tests/golden_numbers.json` containing the values in the table above (v1, v2, flat 15%, raw Elexon totals, first-half values).
- Add a test that recomputes them and fails on any difference.

**Done when:** the golden test passes and is part of `scripts/check.sh`.

### M1. Single source of truth for numbers and models
**Goal:** one place computes every plan and metric; everything else reads it.
- Create `backend/app/services/models.py` with a registry: `v1_additive`, `v2_proportional`, `flat_15`, plus any model added in M3. Each model takes `(forecast, calibration_records, percentile)` and returns a plan. Move the v2 code out of the routers.
- `estimate`, `check` and `summary` all call the registry.
- Remove every item in P1 from the frontend. Components receive values only through the API types in `types/index.ts`. Missing data renders an error/empty state.
- Fix P2: regenerate `DocsPage.tsx` text from API values (or link to them), and rewrite the README results line from a script, with the correct incremental-extra wording.
- Drop `days_shortfall_reduced` from user-facing copy (P4). Replace it with "days where avoided shortfall exceeded extra supply (equal cost)".

**Done when:**
- `grep -rnE "[0-9]{3},[0-9]{3}|\|\| *[0-9]" frontend/src` returns no numeric literals except in fixtures/tests.
- A new test asserts that summary totals equal the sum of per-day check results for every model.
- The golden test (M0) still passes.

### M2. Decision-time purity
**Goal:** the Estimate page for decision date D contains only information available at D 09:00 UTC.
- Estimate-page track record, slider table and calculator use delivery days up to the one completed before D only (Jan 2 … D−1 delivery days; e.g. D = Jan 25 → Jan 2–24).
- Move the full-month and Jan 16–30 holdout results to the Reliability Check page and Methodology only. Label them "backtest".
- Add tests: (a) for every D in Jan 1–30, no field in the estimate response depends on data after the cutoff (truncate the dataset after cutoff and compare responses); (b) the maximum completed delivery day is D−1.

**Done when:** both tests pass for all 30 dates and the Estimate page source contains no reference to the summary endpoint.

### M3. Model decision protocol (decide once, then freeze)
**Goal:** pick the headline model by a written rule, not by looking at charts.

Protocol (write it into `docs/PROTOCOL.md` *before* running anything new):
1. **Candidates:** v1, v2, flat 15%, and one new candidate: an **expanding-window ratio** (actual ÷ forecast over all completed delivery days up to D−1, with the 15% haircut until two days exist). Mark it *exploratory, designed after seeing results*.
2. **Selection data:** Jan 1–15 decisions only.
3. **Rule:** choose the candidate with the highest share of cut that avoids shortfall (efficiency), provided its avoided shortfall is at least 90% of the best candidate's. Ties go to the simpler model.
4. **Holdout:** Jan 16–30 decisions, evaluated once, all candidates reported.
5. **Disclosure:** the page states which models were declared before results (flat 15% cold-start rule, v1), which were added after (v2, expanding ratio), and that one month is a small sample.

For orientation **(reviewer analysis, not in the repo)**: flat 15% was net-positive at equal cost on 22 of 30 days; an expanding ratio gave 880,901 avoided / 313,619 extra with 22 of 30 positive days. Flat 15% on Jan 1–15 beats v2 on both avoided and extra. Expect the rule to pick a simple model. The percentile slider can remain as an optional "extra caution" control on top of whichever model is chosen, but it must not be described as the source of the benefit.

**Done when:** `docs/PROTOCOL.md` exists and is committed *before* the results table; the table is generated by a script; the headline model is whatever the rule selects; parameters are frozen (record the commit hash).

### M4. Cost-ratio calculator
**Goal:** answer "where does this pay off?" without implying savings.
- Use the same model and the same days as the surrounding page (Estimate: completed days to D−1; Check: full backtest).
- Default view is **per 100 MWh of the buyer's own volume** (and a custom volume input). No GB-wide £ headline.
- Show break-even: `k* = extra ÷ avoided`, and net MWh-equivalents at k = 1, 1.5, 2, 3.
- Price input is an editable example, not a claim. Remove "Typical UK day-ahead £60–£90" unless a source is added.
- Note on the page: this treats extra advance power as unrecoverable, which overstates the cost when surplus can be resold.

**Done when:** a test reproduces the table for each model from the API values, and the page has no hardcoded £ totals.

### M5. Claims audit
**Goal:** every sentence on every page is supported or softened.
- Replace "parameters fixed in advance, not re-tuned" with an accurate timeline (see M3 item 5).
- Replace "verified", "official audit trail", "guarantees persistent shortfall", "structurally expected by definition" with calibrated wording.
- **Definitional paragraph:** open the Elexon Insights pages for WINDFOR and FUELHH, copy the exact sentence describing each dataset's coverage into the Methodology page with the URL and access date. Remove the 82–85% figure and the BSC/NESO/DUKES references unless you can quote them from a source you opened. If you cannot confirm the coverage difference, say the gap is unexplained.
- Use one denominator for bias percentages (state "% of forecast" or "% of outturn" every time). The month is 15.5% of outturn, which is about 13.3% of forecast.
- Keep the no-leakage statement once near the top and once in the provenance box.
- Keep `"1-hour publication lag"` labelled as an assumption.

**Done when:** a checklist in `docs/CLAIMS_AUDIT.md` lists each changed string with its source or its softened form.

### M6. Reliability Check page
**Goal:** the page that answers "did it work?" visually.
- Range bars on one axis: Elexon plan, our plan, and the actual as a vertical line.
- Half-hourly chart with the shortfall zone shaded (both Elexon and ours).
- Paired bars: shortfall Elexon vs ours, and extra supply Elexon-surplus vs ours.
- One headline sentence, with both sides stated (avoided shortfall and extra supply).
- Backtest section (full month, first half vs holdout) and the calculator from M4, clearly labelled as backtest.
- Model selector uses the registry from M1, defaults to the M3 headline model.

**Done when:** the page renders for Jan 1, Jan 3, Jan 25 and Jan 30 without errors, and the numbers match `/api/check` for those dates.

### M7. Estimate, Landing, Docs, README, deploy
- Estimate page: apply the M2 changes; the confidence label reflects data volume only (the code already returns Low/Medium/High at n<24, n<96, n=96; show the label as "Full / Partial / No history").
- Landing page: results block reads the summary endpoint, leads with the problem, then the correction, then results; one primary call to action.
- Docs page: method, protocol (link `docs/PROTOCOL.md`), assumptions, limitations, the break-even statement.
- README regenerated from the API; setup, Docker, tests, known limitations.
- Verify `frontend/vercel.json` rewrites so `/jan25` and `/jan25/check` work on direct visit; confirm the Docker image builds and starts.
- Remove `"*"` from CORS origins in production config.

**Done when:** fresh clone → `docker compose up` (or the documented commands) works; direct visits to every route return the app.

### M8. Final verification
- `scripts/check.sh` passes; paste its output.
- Run a sweep script that loads Estimate and Check for all 30 dates, records HTTP status, and fails on any `null`/`NaN`.
- Screenshot Estimate and Check for Jan 1, 3, 25, 30 (desktop and mobile width).
- Re-run the grep from M1.
- Confirm the golden numbers changed only where M3 changed the headline, and list every difference.

**Done when:** all items above are attached to the final report.

## 3. Open decisions (owner: project lead, before M3)
1. Decision cutoff: 09:00 UTC is an assumption; check the exchange rules and cite them, or keep it labelled as assumed.
2. Whether a Dec 2025 warm-up is allowed by the brief. Default stays off; implement as a config flag only if approved.
3. Whether the percentile slider stays as an optional caution control after M3.

## 4. Reporting format for each milestone
```
Milestone: Mx
Changes: files and one line each
Commands run: exact commands
Output: pasted results
Acceptance checks: pass/fail each, with evidence
Deviations: anything not done as written, and why
```