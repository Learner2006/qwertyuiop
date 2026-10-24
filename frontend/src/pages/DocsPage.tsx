import React from "react";
import { BookOpen } from "lucide-react";

export const DocsPage: React.FC = () => {
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
          Technical specification, mathematical definitions, historical replay rules, and limitations. Designed so that an engineer or analyst can reproduce all calculations independently.
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
          Conversely, if wind exceeds the planned quantity, the buyer has arranged more advance supply than required. The <strong>Wind Day-Ahead Estimator</strong> applies a deliberately cautious adjustment to Elexon's published wind forecast, evaluating whether shifting planned generation downward reduces shortfall energy across a full historical month.
        </p>
      </section>

      {/* 2. Data Source */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-sky-100 text-sky-700 text-xs flex items-center justify-center font-bold">2</span>
          <span>Data Sources & Semantics</span>
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
              • Units: Raw values in MW. Converted explicitly in backend to <strong>GW</strong> for power (<code className="bg-white px-1 py-0.5 rounded">MW / 1000</code>) and <strong>MWh</strong> for energy.
            </div>
          </div>
        </div>
      </section>

      {/* 3. Historical Replay & No-Leakage Rules */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-sky-100 text-sky-700 text-xs flex items-center justify-center font-bold">3</span>
          <span>Historical Replay & No-Leakage Rules</span>
        </h2>
        <div className="p-4 rounded-xl bg-sky-50/70 border border-sky-200 text-xs text-sky-950 space-y-2">
          <p className="font-semibold text-sm">
            Core Replay Rule: At decision date D cutoff 09:00 UTC, use only information available by 09:00 UTC on day D.
          </p>
          <ul className="list-disc list-inside space-y-1 text-sky-900">
            <li><strong>Target Forecast:</strong> For target day D+1, select the latest forecast vintage published at or before D at 09:00 UTC. Never use intraday updates or forecasts published after the cutoff.</li>
            <li><strong>Historical Calibration:</strong> Calibration history uses prior half-hourly slots where both the day-ahead forecast and actual generation were published at or before D at 09:00 UTC.</li>
            <li><strong>Zero Future Leakage:</strong> No target-day actual observations or outcome statistics are ever passed to the estimate pipeline. Verified by automated release-blocking unit tests.</li>
          </ul>
        </div>
      </section>

      {/* 4. Error Calibration Equations */}
      <section className="space-y-4">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-sky-100 text-sky-700 text-xs flex items-center justify-center font-bold">4</span>
          <span>Estimation Methodology</span>
        </h2>

        <div className="space-y-3 text-sm text-slate-600">
          <h3 className="font-semibold text-slate-900 text-sm">4.1 Signed Error Definition</h3>
          <p>For each eligible historical half-hourly observation in the lookback window:</p>
          <div className="bg-slate-900 text-white p-3 rounded-lg font-mono text-xs">
            error_GW = eligible_forecast_GW − actual_GW
          </div>
          <p className="text-xs text-slate-500">
            A positive error means the forecast overestimated wind generation (downside shortfall risk). A negative error means wind generation exceeded forecast.
          </p>

          <h3 className="font-semibold text-slate-900 text-sm mt-4">4.2 Data-Driven Margin & Zero Flooring</h3>
          <p>Let <code className="font-mono text-slate-800">p</code> be the selected risk percentile (60 to 90, default 75):</p>
          <div className="bg-slate-900 text-white p-3 rounded-lg font-mono text-xs">
            data_margin = max(0, percentile(historical_errors, p, method='linear'))
          </div>
          <p className="text-xs text-slate-500">
            Because a negative margin would increase the forecast instead of making it cautious, the applied margin is floored at zero.
          </p>

          <h3 className="font-semibold text-slate-900 text-sm mt-4">4.3 Cold Start & Linear History Blending</h3>
          <p>When fewer than 96 historical observations exist, the model blends the empirical data margin with a fixed 15% cold-start haircut:</p>
          <div className="bg-slate-900 text-white p-3 rounded-lg font-mono text-xs space-y-1">
            <div>cold_margin = max(0, raw_forecast_GW) × 0.15</div>
            <div>history_weight = min(1.0, n_observations / 96)</div>
            <div>applied_margin = (1 − history_weight) × cold_margin + history_weight × data_margin</div>
            <div>safe_estimate_GW = max(0, raw_forecast_GW − applied_margin)</div>
          </div>
        </div>
      </section>

      {/* 5. Confidence Labels */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-sky-100 text-sky-700 text-xs flex items-center justify-center font-bold">5</span>
          <span>Confidence Labels</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-amber-50 border border-amber-200">
            <span className="font-bold text-amber-900 text-xs uppercase block">Low Confidence</span>
            <span className="font-mono text-xs text-amber-700 block mt-1">n &lt; 24 observations</span>
            <p className="text-xs text-amber-800 mt-2">
              Occurs during cold start (Jan 1–2). Heavily relies on 15% fixed haircut.
            </p>
          </div>
          <div className="p-4 rounded-lg bg-sky-50 border border-sky-200">
            <span className="font-bold text-sky-900 text-xs uppercase block">Medium Confidence</span>
            <span className="font-mono text-xs text-sky-700 block mt-1">24 ≤ n ≤ 95 observations</span>
            <p className="text-xs text-sky-800 mt-2">
              Occurs during history accumulation (Jan 3). Blends empirical and cold start.
            </p>
          </div>
          <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200">
            <span className="font-bold text-emerald-900 text-xs uppercase block">High Confidence</span>
            <span className="font-mono text-xs text-emerald-700 block mt-1">n = 96 observations</span>
            <p className="text-xs text-emerald-800 mt-2">
              Full 48-hour calibration lookback (Jan 4–30). 100% data-driven margin.
            </p>
          </div>
        </div>
        <p className="text-xs text-slate-500 italic">
          * Note: Confidence labels measure historical calibration sample size, not a mathematical probability that the estimate will match reality.
        </p>
      </section>

      {/* 6. Reliability Metrics */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-sky-100 text-sky-700 text-xs flex items-center justify-center font-bold">6</span>
          <span>Reliability & Evaluation Metrics</span>
        </h2>
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 space-y-4 text-xs font-mono">
          <div>
            <span className="font-bold text-slate-900 block">Shortfall Energy (MWh):</span>
            <div className="text-slate-600 mt-1">
              shortfall_MWh = sum( max(0, Planned_GW − Actual_GW) × 1000 MW/GW × 0.5 hours )
            </div>
          </div>
          <div>
            <span className="font-bold text-slate-900 block">Saved Shortfall Energy (MWh):</span>
            <div className="text-slate-600 mt-1">
              saved_MWh = elexon_shortfall_MWh − safe_shortfall_MWh
            </div>
            <div className="text-slate-400 mt-0.5 italic">
              * Negative values are preserved honestly if our estimate underperformed.
            </div>
          </div>
          <div>
            <span className="font-bold text-slate-900 block">Additional Advance-Planned Wind (MWh):</span>
            <div className="text-slate-600 mt-1">
              extra_advance_MWh = sum( max(0, Actual_GW − Safe_Estimate_GW) × 1000 × 0.5 )
            </div>
            <div className="text-slate-400 mt-0.5">
              Measures realized wind generation above our cautious plan (cost-side trade-off).
            </div>
          </div>
          <div>
            <span className="font-bold text-slate-900 block">Mean Absolute Error (MAE in GW):</span>
            <div className="text-slate-600 mt-1">
              MAE_GW = mean( abs(Predicted_GW − Actual_GW) )
            </div>
          </div>
        </div>
      </section>

      {/* 7. Assumptions & Limitations */}
      <section className="space-y-3">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-amber-100 text-amber-700 text-xs flex items-center justify-center font-bold">7</span>
          <span>Declared Assumptions & Known Limitations</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-600">
          <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-2">
            <h4 className="font-bold text-slate-900 uppercase">Assumptions</h4>
            <p>• 09:00 UTC day-ahead cutoff is standard operating market cutoff assumption.</p>
            <p>• January 2026 experiment uses historical data only.</p>
            <p>• Fixed 15% cold-start haircut assumption.</p>
            <p>• Hourly WINDFOR forecast applies uniformly to both constituent 30-min settlement periods.</p>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-4 space-y-2">
            <h4 className="font-bold text-slate-900 uppercase">Limitations</h4>
            <p>• No price-aware procurement model; avoided shortfall is not cash savings.</p>
            <p>• Not a live trading or operational bidding system.</p>
            <p>• Indicative range band is based on empirical error quantiles, not a guaranteed prediction interval.</p>
            <p>• Simple scalar margin applied uniformly across all 48 target half-hours.</p>
          </div>
        </div>
      </section>

      {/* 8. Future Improvements */}
      <section className="space-y-3 pb-8">
        <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
          <span className="w-6 h-6 rounded-md bg-slate-100 text-slate-700 text-xs flex items-center justify-center font-bold">8</span>
          <span>Future Scope (Unimplemented by Design)</span>
        </h2>
        <ul className="list-disc list-inside text-sm text-slate-600 space-y-1.5">
          <li>Multi-year historical calendar with seasonal calibration windows.</li>
          <li>Price-aware cost optimization balancing imbalance prices with day-ahead forward procurement.</li>
          <li>Per-hour settlement period calibration accounting for diurnal wind cycles.</li>
          <li>Live operational API ingestion with automated morning cutoff processing.</li>
        </ul>
      </section>
    </div>
  );
};
