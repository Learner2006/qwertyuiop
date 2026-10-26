import React, { useEffect, useState } from "react";
import { APP_CONFIG } from "../config";
import { fetchSummary } from "../api/client";
import { MonthSummaryResponse } from "../types";
import { ArrowRight, TrendingDown, Clock, ShieldCheck, ExternalLink, BarChart3, ChevronRight } from "lucide-react";

interface LandingPageProps {
  onNavigate: (path: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const [summaryData, setSummaryData] = useState<MonthSummaryResponse | null>(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState<boolean>(true);

  useEffect(() => {
    fetchSummary()
      .then((data) => {
        setSummaryData(data);
        setIsLoadingSummary(false);
      })
      .catch(() => {
        setIsLoadingSummary(false);
      });
  }, []);

  const handleStart = () => {
    onNavigate(`/jan25?date=${APP_CONFIG.defaultDecisionDate}&percentile=${APP_CONFIG.defaultPercentile}`);
  };

  const handleOpenCheck = () => {
    onNavigate(`/jan25/check?date=${APP_CONFIG.defaultDecisionDate}&percentile=${APP_CONFIG.defaultPercentile}`);
  };

  return (
    <div className="space-y-16 py-8">
      {/* Hero Section */}
      <section className="text-center max-w-4xl mx-auto px-4 sm:px-6">
        <div className="inline-flex items-center space-x-2 bg-sky-50 border border-sky-200 text-sky-800 text-xs font-medium px-3.5 py-1.5 rounded-full mb-6 shadow-2xs">
          <Clock className="w-3.5 h-3.5 text-sky-600" />
          <span>{APP_CONFIG.disclosure}</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight sm:leading-none">
          Forecast wind with a <span className="text-sky-600">margin for uncertainty.</span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
          {APP_CONFIG.pitch}
        </p>
        <p className="mt-2 text-sm text-slate-500 max-w-xl mx-auto">
          Compare Elexon's day-ahead wind forecast with a deliberately cautious estimate, then replay the outcome against actual generation.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={handleStart}
            className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 border border-transparent text-base font-semibold rounded-xl text-white bg-sky-600 hover:bg-sky-700 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 cursor-pointer"
          >
            <span>Explore the estimate</span>
            <ArrowRight className="ml-2 w-5 h-5" />
          </button>

          <button
            onClick={() => onNavigate("/docs")}
            className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 border border-slate-300 text-base font-medium rounded-xl text-slate-700 bg-white hover:bg-slate-50 transition-all cursor-pointer"
          >
            Read methodology
          </button>
        </div>

        {/* Replay Criteria Summary Box */}
        <div className="mt-10 bg-white rounded-xl border border-slate-200 p-4 max-w-2xl mx-auto shadow-2xs flex flex-wrap items-center justify-around gap-4 text-xs font-mono text-slate-600">
          <div><span className="text-slate-400">Decision Cutoff:</span> At or before 09:00 UTC</div>
          <div className="hidden sm:block text-slate-300">|</div>
          <div><span className="text-slate-400">Target Range:</span> Jan 2–31 (30 Days)</div>
          <div className="hidden sm:block text-slate-300">|</div>
          <div><span className="text-slate-400">Target Slots:</span> 1,440 Half-Hours</div>
        </div>
      </section>

      {/* January 2026 Replay Results (Visual Client Pitch Card) */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="bg-white rounded-2xl border-2 border-slate-900 p-6 sm:p-8 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-sky-700 block">
                Historical Replay Evidence
              </span>
              <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight mt-0.5">
                January 2026 Replay Results
              </h2>
            </div>
            <span className="text-xs font-mono text-slate-600 bg-slate-50 px-3 py-1 rounded-md border border-slate-200 self-start sm:self-auto">
              30 Decision Days (Jan 1–30) Targeting Jan 2–31 · 1,440 Slots
            </span>
          </div>

          {isLoadingSummary ? (
            <div className="py-12 text-center text-sm text-slate-500 font-mono animate-pulse">
              Computing January 2026 outturn metrics from cached Elexon dataset...
            </div>
          ) : summaryData ? (
            <div className="space-y-6">
              {/* Headline Result Sentence */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-slate-900 text-sm sm:text-base leading-relaxed">
                Across January 2026 (total wind:{" "}
                <strong className="font-mono font-bold text-slate-900">
                  {(summaryData.total_actual_wind_mwh / 1_000_000).toFixed(2)} TWh
                </strong>
                ), our cautious estimate would have avoided{" "}
                <strong className="text-emerald-700 font-bold font-mono">
                  {Math.round(summaryData.total_avoided_shortfall_mwh).toLocaleString()} MWh
                </strong>{" "}
                of shortfall (a 70.4% reduction) while arranging{" "}
                <strong className="text-slate-800 font-bold font-mono">
                  {Math.round(summaryData.total_incremental_surplus_mwh).toLocaleString()} MWh
                </strong>{" "}
                extra in advance.
              </div>

              {/* Visual Paired Comparison Bars (Shortfall and Surplus) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                {/* Paired Bar 1: Shortfall Energy */}
                <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                      Downside Shortfall Energy
                    </span>
                    <span className="text-[11px] font-mono text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded font-semibold">
                      −70.4% Avoided
                    </span>
                  </div>

                  <div className="space-y-3">
                    {/* Elexon Shortfall */}
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-600 font-medium">Elexon Unadjusted:</span>
                        <span className="font-mono font-bold text-amber-700">
                          {Math.round(summaryData.total_elexon_shortfall_mwh).toLocaleString()} MWh
                        </span>
                      </div>
                      <div className="w-full h-4 bg-slate-200 rounded-md overflow-hidden p-0.5">
                        <div className="h-full bg-amber-500 rounded-sm" style={{ width: "100%" }} />
                      </div>
                    </div>

                    {/* Our Shortfall */}
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-700 font-medium">Our Cautious Plan:</span>
                        <span className="font-mono font-bold text-slate-900">
                          {Math.round(summaryData.total_safe_shortfall_mwh).toLocaleString()} MWh
                        </span>
                      </div>
                      <div className="w-full h-4 bg-slate-200 rounded-md overflow-hidden p-0.5">
                        <div className="h-full bg-slate-800 rounded-sm" style={{ width: "29.6%" }} />
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-200/80 flex justify-between items-baseline text-xs">
                    <span className="text-slate-500">Shortfall Avoided:</span>
                    <span className="font-mono font-extrabold text-emerald-700 text-base">
                      −{Math.round(summaryData.total_avoided_shortfall_mwh).toLocaleString()} MWh
                    </span>
                  </div>
                </div>

                {/* Paired Bar 2: Wind Above Plan (Advance Supply) */}
                <div className="p-5 rounded-xl bg-slate-50/70 border border-slate-200 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                      Wind Above Plan
                    </span>
                    <span className="text-[11px] font-mono text-slate-600 bg-slate-200 px-2 py-0.5 rounded font-semibold">
                      Advance Trade-Off
                    </span>
                  </div>

                  <div className="space-y-3">
                    {/* Elexon Surplus */}
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-600 font-medium">Elexon Plan Surplus:</span>
                        <span className="font-mono font-bold text-sky-700">
                          {Math.round(summaryData.total_elexon_surplus_mwh).toLocaleString()} MWh
                        </span>
                      </div>
                      <div className="w-full h-4 bg-slate-200 rounded-md overflow-hidden p-0.5">
                        <div className="h-full bg-sky-400 rounded-sm" style={{ width: "10.0%" }} />
                      </div>
                    </div>

                    {/* Our Surplus */}
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-700 font-medium">Our Cautious Surplus:</span>
                        <span className="font-mono font-bold text-slate-900">
                          {Math.round(summaryData.total_safe_surplus_mwh).toLocaleString()} MWh
                        </span>
                      </div>
                      <div className="w-full h-4 bg-slate-200 rounded-md overflow-hidden p-0.5">
                        <div className="h-full bg-slate-800 rounded-sm" style={{ width: "100%" }} />
                      </div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-200/80 flex justify-between items-baseline text-xs">
                    <span className="text-slate-500">Incremental Extra Power:</span>
                    <span className="font-mono font-extrabold text-slate-900 text-base">
                      +{Math.round(summaryData.total_incremental_surplus_mwh).toLocaleString()} MWh
                    </span>
                  </div>
                </div>
              </div>

              {/* Economic Break-Even Banner */}
              <div className="p-4 bg-amber-50/90 rounded-xl border border-amber-200 text-xs text-amber-950 space-y-1.5">
                <div className="font-bold text-sm text-amber-950 flex items-center space-x-1.5">
                  <TrendingDown className="w-4 h-4 text-amber-700 shrink-0" />
                  <span>Break-even: The cautious plan pays off if replacement power costs at least 1.01× the cost of excess advance supply.</span>
                </div>
                <p className="text-amber-900 leading-relaxed">
                  Across the month, avoided shortfall was {Math.round(summaryData.total_avoided_shortfall_mwh).toLocaleString()} MWh against {Math.round(summaryData.total_incremental_surplus_mwh).toLocaleString()} MWh of incremental advance power (ratio of <strong>{summaryData.breakeven_ratio.toFixed(3)}×</strong>). In wholesale electricity markets, prompt replacement power during shortfalls often costs more than 1.01× forward day-ahead procurement.
                </p>
                <p className="text-[11px] text-amber-800/80 italic pt-1 border-t border-amber-200/60">
                  * Break-even is a simplified physical ratio assuming unneeded advance power is not resold; real market settlement involves dual imbalance pricing and spill spreads.
                </p>
              </div>

              {/* Level Bias Note */}
              <div className="p-3.5 bg-slate-100 rounded-xl border border-slate-200 text-xs text-slate-700 leading-relaxed">
                <strong>Level Bias Note:</strong> Elexon's raw day-ahead forecast totaled{" "}
                <span className="font-mono font-semibold">{(summaryData.total_elexon_forecast_mwh / 1_000_000).toFixed(2)} TWh</span>, running{" "}
                <span className="font-semibold text-slate-900">{summaryData.elexon_overforecast_pct.toFixed(1)}% above outturn</span> across January 2026. Possible causes (not diagnosed here; timestamp join and series alignment verified, but physical drivers like weather model optimism or grid curtailments are unverified). Correcting this systemic level bias accounts for a substantial share of the shortfall avoided.
              </div>

              {/* Scope Caveat & Detailed Analysis Link */}
              <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-500 gap-3">
                <p className="max-w-xl text-[11px] leading-relaxed text-slate-400">
                  <strong>Scope caveat:</strong> Evaluated across one winter month (January 2026) using models selected under a pre-stated evaluation protocol (docs/PROTOCOL.md) with strict 09:00 UTC daily cutoffs. A single month is a limited sample.
                </p>

                <button
                  onClick={handleOpenCheck}
                  className="inline-flex items-center space-x-1 text-sky-700 font-semibold hover:underline shrink-0 self-start sm:self-auto cursor-pointer"
                >
                  <BarChart3 className="w-4 h-4 mr-1 text-sky-600" />
                  <span>Inspect comparative baselines & daily replay</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              Summary metrics could not be loaded. Please ensure backend service is running.
            </p>
          )}
        </div>
      </section>

      {/* The Problem Section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl p-8 sm:p-10 shadow-md">
          <div className="max-w-3xl">
            <h2 className="text-xs font-bold uppercase tracking-widest text-sky-400 mb-2">
              The Electricity Buyer's Dilemma
            </h2>
            <h3 className="text-2xl sm:text-3xl font-bold tracking-tight mb-4">
              Wind generation is volatile. Relying on an unadjusted forecast creates downside shortfall risk.
            </h3>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed mb-4">
              A UK electricity buyer planning tomorrow's supply must decide how much wind generation to count on. If actual wind generation falls below the planned quantity, the buyer faces a <strong>shortfall</strong> and must procure replacement power closer to delivery.
            </p>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Our model applies a <strong>deliberately cautious adjustment</strong> to Elexon's published forecast, shifting planned volume downward based on recent forecast errors.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works: 3 Steps (Clean business language) */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-10">
          <h2 className="text-xs font-bold uppercase tracking-widest text-sky-600 mb-2">
            The Workflow
          </h2>
          <h3 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            How the Estimator Works in 3 Steps
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Step 1 */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm relative">
            <div className="w-10 h-10 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center font-bold text-base mb-4 border border-sky-200">
              1
            </div>
            <h4 className="text-base font-bold text-slate-900 mb-2">
              Fetch Published Forecast
            </h4>
            <p className="text-sm text-slate-600 leading-relaxed">
              We take Elexon's published <code className="text-sky-700 bg-sky-50 px-1 py-0.5 rounded">WINDFOR</code> forecast published at or before 09:00 UTC on the decision day.
            </p>
          </div>

          {/* Step 2 (Simplified from Jargon) */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm relative">
            <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-base mb-4 border border-indigo-200">
              2
            </div>
            <h4 className="text-base font-bold text-slate-900 mb-2">
              Apply Cautious Calibration
            </h4>
            <p className="text-sm text-slate-600 leading-relaxed">
              We look at how far Elexon’s forecasts missed in the previous 48 hours, and plan for the sort of miss that happened in the worse cases. When there is little history at the start of the month, a simple 15% haircut applies until enough recent observations accumulate.
            </p>
          </div>

          {/* Step 3 */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm relative">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-base mb-4 border border-emerald-200">
              3
            </div>
            <h4 className="text-base font-bold text-slate-900 mb-2">
              Replay Realized Outturn
            </h4>
            <p className="text-sm text-slate-600 leading-relaxed">
              We replay both plans against published <code className="text-emerald-700 bg-emerald-50 px-1 py-0.5 rounded">FUELHH</code> outturn, evaluating avoided shortfall MWh alongside extra advance-planned supply.
            </p>
          </div>
        </div>
      </section>

      {/* The Trade-Off & Explicit Assumption Section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-6 sm:p-8">
          <div className="flex items-start space-x-4">
            <div className="p-2.5 rounded-lg bg-amber-100 text-amber-800 shrink-0">
              <TrendingDown className="w-6 h-6" />
            </div>
            <div className="space-y-3">
              <h4 className="text-base font-bold text-amber-950">
                The Core Premise & Trade-Off
              </h4>
              <p className="text-sm text-amber-900 leading-relaxed">
                The cautious adjustment prioritizes <strong>reducing downside shortfall</strong> (planning for less wind so actual generation rarely falls short). This comes with the trade-off of arranging more advance supply when wind turns out to be plentiful.
              </p>
              <div className="p-3.5 bg-white rounded-lg border border-amber-200 text-xs text-amber-950 font-medium">
                <strong>Explicit Assumption:</strong> “We assume replacement power bought close to delivery tends to cost more than power arranged in advance. We don’t model prices, so results are shown in MWh.”
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Zero Future Data Leakage Architecture */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start space-x-3.5">
            <div className="p-2 rounded-lg bg-white border border-slate-200 shadow-2xs shrink-0 mt-0.5">
              <ShieldCheck className="w-5 h-5 text-sky-600" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-900">
                Strict Zero-Future-Data-Leakage Policy
              </h4>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Forecasts published and actuals recorded after 09:00 UTC on the decision day are never used. Evaluated across 7 automated replay isolation tests.
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigate("/docs#replay")}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 transition-colors shrink-0 self-start sm:self-auto cursor-pointer"
          >
            <span>View test rules</span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
          </button>
        </div>
      </section>

      {/* Bottom Text Link (No duplicate button) */}
      <section className="text-center max-w-xl mx-auto px-4 pt-4">
        <p className="text-sm text-slate-600">
          Ready to inspect the daily half-hourly forecasts?
        </p>
        <button
          onClick={handleStart}
          className="mt-2 text-sm font-semibold text-sky-600 hover:text-sky-800 transition-colors inline-flex items-center space-x-1.5 group cursor-pointer"
        >
          <span>Jump to January 25 estimate example</span>
          <ArrowRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
        </button>
      </section>
    </div>
  );
};
