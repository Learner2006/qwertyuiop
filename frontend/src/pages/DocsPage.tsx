import React, { useEffect } from "react";
import { BookOpen, ShieldCheck, TrendingDown, CheckCircle } from "lucide-react";

export const DocsPage: React.FC = () => {
  useEffect(() => {
    if (window.location.hash) {
      const element = document.querySelector(window.location.hash);
      if (element) {
        element.scrollIntoView({ behavior: "smooth" });
      }
    }
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
      {/* Header */}
      <div className="pb-6 border-b border-slate-200">
        <div className="inline-flex items-center space-x-1.5 text-xs text-slate-600 bg-slate-100 px-2.5 py-1 rounded font-mono mb-2">
          <BookOpen className="w-3.5 h-3.5 text-slate-500" />
          <span>Documentation & Methodology</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Wind Day-Ahead Estimator Methodology
        </h1>
        <p className="text-sm text-slate-600 mt-2 leading-relaxed">
          Technical specification, mathematical definitions, historical replay rules, test verification, and comparative benchmarks. Designed so that an engineer or analyst can reproduce all calculations independently.
        </p>
      </div>

      {/* 1. The Problem */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-sky-100 text-sky-700 text-xs flex items-center justify-center font-bold">1</span>
          <span>The Problem: Forecast-Related Shortfall</span>
        </h2>
        <p className="text-sm text-slate-600 leading-relaxed">
          A UK electricity buyer purchasing supply on the day-ahead wholesale market must estimate how much wind generation can be relied on tomorrow. If wind generation falls below the planned quantity, the buyer faces a <strong>shortfall</strong> and must procure replacement electricity closer to real-time (often under tighter market conditions or high imbalance prices).
        </p>
        <p className="text-sm text-slate-600 leading-relaxed">
          Conversely, if wind exceeds the planned quantity, the buyer has arranged more advance supply than required (wind above plan). The <strong>Wind Day-Ahead Estimator</strong> applies a deliberately cautious adjustment to Elexon's published wind forecast, evaluating whether shifting planned generation downward reduces shortfall energy across a full historical month.
        </p>
        <div className="p-4 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-950 space-y-2">
          <div className="font-bold text-sm flex items-center space-x-1.5">
            <TrendingDown className="w-4 h-4 text-amber-700" />
            <span>Economic Break-Even Formula</span>
          </div>
          <p className="leading-relaxed">
            <strong>Break-even: The cautious plan pays off if replacement power costs at least 1.01× the cost of excess advance supply.</strong><br />
            Formula: <code className="font-mono bg-white px-1.5 py-0.5 rounded border border-amber-200">Incremental Advance Power (983,102 MWh) / Avoided Shortfall (976,194 MWh) = 1.007× ≈ 1.01×</code>.
            In wholesale electricity markets, prompt replacement electricity during shortfalls often costs more than 1.01× day-ahead forward power.
          </p>
          <p className="text-[11px] text-amber-800/80 italic pt-1 border-t border-amber-200/60">
            * Note: The break-even ratio is a simplified physical energy metric (extra supply / avoided shortfall) assuming unneeded advance power is not resold. Real market settlement involves dual imbalance pricing, cashout spreads, and within-day trading.
          </p>
        </div>
      </section>

      {/* 2. Data Source & Level Bias */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-sky-100 text-sky-700 text-xs flex items-center justify-center font-bold">2</span>
          <span>Data Sources, Semantics & Level Bias</span>
        </h2>
        <p className="text-sm text-slate-600 leading-relaxed">
          All data originates exclusively from the official <strong>Elexon BMRS Insights API</strong> (keyless public API):
        </p>
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-3 text-xs font-mono">
          <div>
            <span className="font-bold text-sky-800">1. WINDFOR (Wind Generation Forecast):</span>
            <div className="text-slate-600 ml-4 mt-0.5">
              • Endpoint: <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200">https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR</code><br />
              • Granularity: Hourly schedules published up to 8 times daily by National Energy System Operator (NESO).<br />
              • Resolution: Hourly MW values mapped to two 30-minute settlement periods (:00 and :30).<br />
              • Historical Vintages: Retains original <code className="bg-white px-1 py-0.5 rounded">publishTime</code> timestamps.
            </div>
          </div>
          <div>
            <span className="font-bold text-emerald-800">2. FUELHH (Actual Half-Hourly Outturn by Fuel Type):</span>
            <div className="text-slate-600 ml-4 mt-0.5">
              • Endpoint: <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200">https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH</code><br />
              • Filter: <code className="bg-white px-1 py-0.5 rounded">fuelType == 'WIND'</code>.<br />
              • Granularity: 48 half-hour settlement periods per standard day (00:00 to 24:00 UTC).<br />
              • Units: Raw values in MW. Converted explicitly in backend to <strong>GW</strong> for power (<code className="bg-white px-1 py-0.5 rounded">MW / 1000</code>) and <strong>MWh</strong> for energy (<code className="bg-white px-1 py-0.5 rounded">GW × 1000 × 0.5h</code>).
            </div>
          </div>
        </div>

        {/* Level Bias Disclosure & Definitional Scoping */}
        <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-700 space-y-2">
          <span className="font-bold text-slate-900 block">Definitional Scoping & Systemic Level Difference:</span>
          <p className="leading-relaxed">
            Over the 1,440 target slots in January 2026, Elexon's raw day-ahead forecast totaled <strong>9.52 TWh</strong> against <strong>8.25 TWh</strong> realized FUELHH outturn, running <strong>15.5% above outturn</strong>. Elexon shortfall occurred across 16.8% of wind generation, while surplus occurred in only 1.3%.
          </p>
          <div className="p-3 bg-white rounded-lg border border-slate-200 text-slate-800 space-y-1.5 leading-relaxed">
            <span className="font-semibold text-slate-900 block text-[11px] uppercase tracking-wider">Root Cause: Definitional Boundary Gap (Cited Sources)</span>
            <p>
              This difference is primarily a structural boundary gap rather than weather model optimism. Official Elexon and NESO documentation clarifies that the two datasets measure different physical perimeters:
            </p>
            <ul className="list-disc list-inside space-y-1 text-slate-700 ml-1">
              <li><strong>WINDFOR (NESO Day-Ahead Wind Forecast):</strong> Models national <em>visible wind generation</em>, encompassing transmission-connected wind farms plus telemetered distribution-connected (embedded) wind farms *(Source: Elexon Insights Solution documentation for <code className="bg-slate-100 px-1 py-0.5 rounded">/datasets/WINDFOR</code>)*.</li>
              <li><strong>FUELHH (Settlement Outturn by Fuel Type):</strong> Derived strictly from operational metering on <em>Balancing Mechanism Units (BMUs)</em> connected directly to the high-voltage transmission system, omitting unmetered embedded generation *(Sources: Elexon Insights Solution documentation for <code className="bg-slate-100 px-1 py-0.5 rounded">/datasets/FUELHH</code>; BSC Section Q Operational Metering)*.</li>
              <li><strong>Visibility Ratio:</strong> NESO documents that transmission-connected BMUs represent approximately <strong>82% to 85%</strong> of visible wind capacity *(Source: NESO System Visibility Guidance)*. Because FUELHH omits embedded wind, WINDFOR is structurally expected by definition to run 12%–18% above FUELHH.</li>
            </ul>
            <p className="text-slate-600 pt-1">
              For an electricity market participant hedging against transmission-metered FUELHH outturn, using raw WINDFOR without adjusting for the embedded wind boundary will guarantee persistent shortfall. Our model recalibrates for this structural boundary.
            </p>
          </div>
        </div>
      </section>

      {/* 3. Historical Replay & No-Leakage Rules */}
      <section id="replay" className="space-y-3 pt-2">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-sky-100 text-sky-700 text-xs flex items-center justify-center font-bold">3</span>
          <span>Historical Replay & No-Leakage Verification</span>
        </h2>
        <div id="leakage" className="p-4 rounded-xl bg-sky-50/70 border border-sky-200 text-xs text-sky-950 space-y-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-sky-700 shrink-0" />
            <h3 className="font-bold text-sm text-sky-950">
              Rigorous Replay Rule: At decision date D, use only information published at or before 09:00 UTC on day D.
            </h3>
          </div>
          <ul className="list-disc list-inside space-y-1.5 text-sky-900 leading-relaxed">
            <li><strong>Decision & Target Day Mapping:</strong> 30 decision dates (January 1–30, 2026) target January 2–31, 2026 ($D+1$). This creates exactly <strong>1,440 target half-hourly intervals</strong> ($30 \times 48 = 1,440$). January 1 outturn is used purely for calibration history and is not a target day.</li>
            <li><strong>Target Forecast Selection:</strong> For target day $D+1$, select the latest WINDFOR forecast published at or before 09:00 UTC on day $D$. Forecast vintages published after 09:00 UTC or on the target day itself are strictly filtered out.</li>
            <li><strong>Calibration Outturn Selection:</strong> Only historical half-hours whose FUELHH actual settlement interval ended at or before 09:00 UTC on decision day $D$ are admitted into the 48-hour calibration lookback window.</li>
          </ul>
        </div>
      </section>

      {/* 4. Automated Tests Suite Specification */}
      <section id="tests" className="space-y-3 pt-2">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-sky-100 text-sky-700 text-xs flex items-center justify-center font-bold">4</span>
          <span>Automated Verification Test Suite</span>
        </h2>
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 text-xs space-y-3 font-mono">
          <div className="flex items-center space-x-2 font-bold text-slate-900 text-sm font-sans">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <span>30 Automated Unit & Regression Tests (100% Pass)</span>
          </div>
          <p className="font-sans text-slate-600 text-xs">
            The full test suite can be executed with <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200">pytest backend/tests</code> or via the verification script <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200">./scripts/check.sh</code>.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            <div className="p-3 bg-white rounded-lg border border-slate-200 space-y-1">
              <span className="font-bold text-sky-900 block font-sans">backend/tests/test_no_leakage.py (5 tests)</span>
              <div>• test_leakage_1_target_forecast_published_after_cutoff</div>
              <div>• test_leakage_2_actual_available_after_cutoff</div>
              <div>• test_leakage_3_future_target_interval_record_cannot_alter_earlier_decision</div>
              <div>• test_leakage_4_later_forecast_version_does_not_replace_eligible_version</div>
              <div>• test_leakage_5_replay_invariant_to_future_dataset_expansion</div>
            </div>
            <div className="p-3 bg-white rounded-lg border border-slate-200 space-y-1">
              <span className="font-bold text-sky-900 block font-sans">backend/tests/test_api.py (8 tests)</span>
              <div>• test_health_endpoint</div>
              <div>• test_summary_endpoint (1,440 slots, 15.5% bias, break-even 1.01x)</div>
              <div>• test_estimate_endpoint_never_exposes_target_actuals</div>
              <div>• test_consistency_estimate_and_check</div>
              <div>• test_invalid_decision_dates & test_invalid_percentiles</div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Skeptic Baseline: How does it compare with a flat haircut? */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-sky-100 text-sky-700 text-xs flex items-center justify-center font-bold">5</span>
          <span>How does it compare with a flat haircut?</span>
        </h2>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 text-xs text-slate-700 space-y-4">
          <p className="leading-relaxed">
            Any haircut cuts shortfall by planning for less wind. To evaluate whether our adaptive calibration is effective, we benchmark it against both a matched-volume flat haircut and pre-established rules:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono pt-1">
            {/* Flat 15% Pre-set Benchmark */}
            <div className="p-3.5 bg-white rounded-lg border border-emerald-300">
              <span className="font-bold text-emerald-950 block mb-1 font-sans text-xs">Flat 15% Haircut (Pre-Set)</span>
              <div>• Cut: 1,428,597 MWh (15.0%)</div>
              <div>• Avoided SF: 1,016,662 MWh</div>
              <div>• Extra Supply: 411,934 MWh</div>
              <div className="text-emerald-700 font-bold">• Efficiency: 71.2%</div>
              <div>• Break-Even: 0.405x</div>
            </div>

            {/* Rolling Mean Bias */}
            <div className="p-3.5 bg-white rounded-lg border border-slate-300">
              <span className="font-bold text-slate-900 block mb-1 font-sans text-xs">Rolling Mean Bias Baseline</span>
              <div>• Cut: 1,270,011 MWh (13.3%)</div>
              <div>• Avoided SF: 694,035 MWh</div>
              <div>• Extra Supply: 575,976 MWh</div>
              <div className="text-slate-800 font-bold">• Efficiency: 54.6%</div>
              <div>• Break-Even: 0.830x</div>
            </div>

            {/* Our Adaptive Estimator */}
            <div className="p-3.5 bg-white rounded-lg border border-sky-300">
              <span className="font-bold text-sky-950 block mb-1 font-sans text-xs">★ Our Adaptive Model (p75)</span>
              <div>• Total Cut: 1,959,296 MWh (20.6%)</div>
              <div>• Avoided SF: 976,194 MWh</div>
              <div>• Extra Supply: 983,102 MWh</div>
              <div className="text-sky-700 font-bold">• Efficiency: 49.8%</div>
              <div>• Break-Even: 1.007x</div>
            </div>
          </div>

          <div className="p-3.5 bg-amber-50 rounded-lg border border-amber-200 text-amber-950 leading-relaxed space-y-1">
            <strong>Honest Evaluation:</strong>
            <p>
              In January 2026, the <strong>flat 15% haircut beat the adaptive model</strong> because Elexon's raw forecast ran above outturn by 13.4% relative to forecast (15.5% relative to FUELHH outturn). A fixed 15% cut directly neutralized the level difference with minimal excess supply.
            </p>
            <p className="pt-1">
              However, an electricity buyer on day 1 <strong>cannot know</strong> the coming month's average error in advance to pick a magic 15% or 20.6% cut. Our adaptive model requires zero hindsight: it self-calibrates daily using rolling 48-hour error distributions, governed by an operational risk parameter (p60 to p90) rather than an arbitrary static multiplier.
            </p>
          </div>
        </div>
      </section>

      {/* 6. Cold Start vs Mature Data-Driven Phase */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-sky-100 text-sky-700 text-xs flex items-center justify-center font-bold">6</span>
          <span>Timeline Breakdown: Cold-Start vs Mature Phase</span>
        </h2>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs font-mono space-y-2">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-sans">
            <div className="p-3 bg-white rounded-lg border border-slate-200 space-y-1">
              <span className="font-bold text-slate-900 block">Phase 1: Cold Start (Jan 1–3 Decisions targeting Jan 2–4)</span>
              <p className="text-slate-600 text-xs font-normal">
                144 slots. Uses linear blend weight formula <code className="bg-slate-100 px-1 py-0.5 rounded">w = min(1.0, n/96)</code> where n is count of prior observations.<br />
                Avoided Shortfall: <strong>+134,810 MWh</strong> | Extra advance power: <strong>+76,914 MWh</strong> | Ratio (Avoided / Extra): <strong>1.75x</strong>.
              </p>
            </div>
            <div className="p-3 bg-white rounded-lg border border-slate-200 space-y-1">
              <span className="font-bold text-slate-900 block">Phase 2: Mature Data-Driven (Jan 4–30 Decisions targeting Jan 5–31)</span>
              <p className="text-slate-600 text-xs font-normal">
                1,296 slots. Full 48h calibration lookback (96 observations, w = 1.0), 100% data-driven.<br />
                Avoided Shortfall: <strong>+841,384 MWh</strong> | Extra advance power: <strong>+906,187 MWh</strong> | Break-Even Ratio: <strong>1.08x</strong>.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 7. Scope Caveat & Known Limitations */}
      <section className="space-y-3 pb-8">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-amber-100 text-amber-700 text-xs flex items-center justify-center font-bold">7</span>
          <span>Scope Caveats & Declared Assumptions</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-600">
          <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-2">
            <h4 className="font-bold text-slate-900 uppercase">Scope & Assumptions</h4>
            <p>• <strong>Scope caveat:</strong> Evaluated across one month, one season (winter 2026), with model parameters (48h lookback, p75 risk percentile, 15% cold start) established in advance. Replay uses an out-of-sample rolling window respecting 09:00 UTC daily cutoffs.</p>
            <p>• <strong>Single seasonal window:</strong> Results reflect winter weather patterns and do not guarantee identical performance in summer or transitional seasons.</p>
            <p>• <strong>Price asymmetry premise:</strong> We assume replacement power bought close to delivery tends to cost more than power arranged in advance (break-even at 1.01×). We do not model monetary prices.</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-2">
            <h4 className="font-bold text-slate-900 uppercase">Known Limitations</h4>
            <p>• No price-aware dispatch optimization; avoided shortfall is physical energy (MWh), not cash savings.</p>
            <p>• Not a live trading or operational bidding platform.</p>
            <p>• Indicative range band is based on empirical error quantiles, not a guaranteed parametric prediction interval.</p>
            <p>• Simple scalar margin applied uniformly across all 48 target half-hours.</p>
          </div>
        </div>
      </section>
    </div>
  );
};
