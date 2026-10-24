import React, { useEffect, useState } from "react";
import { APP_CONFIG } from "../config";
import { fetchSummary } from "../api/client";
import { MonthSummaryResponse } from "../types";
import { ArrowRight, TrendingDown, Clock, ShieldCheck, ExternalLink } from "lucide-react";

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
            className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 border border-transparent text-base font-semibold rounded-xl text-white bg-sky-600 hover:bg-sky-700 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500"
          >
            <span>Explore the estimate</span>
            <ArrowRight className="ml-2 w-5 h-5" />
          </button>

          <button
            onClick={() => onNavigate("/docs")}
            className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 border border-slate-300 text-base font-medium rounded-xl text-slate-700 bg-white hover:bg-slate-50 transition-all"
          >
            Read methodology
          </button>
        </div>

        {/* Replay Criteria Summary Box */}
        <div className="mt-10 bg-white rounded-xl border border-slate-200 p-4 max-w-2xl mx-auto shadow-2xs flex flex-wrap items-center justify-around gap-4 text-xs font-mono text-slate-600">
          <div><span className="text-slate-400">Decision Cutoff:</span> At or before 09:00 UTC</div>
          <div className="hidden sm:block text-slate-300">|</div>
          <div><span className="text-slate-400">Target Horizon:</span> D+1 (24 Hours)</div>
          <div className="hidden sm:block text-slate-300">|</div>
          <div><span className="text-slate-400">Dataset:</span> January 2026 Elexon</div>
        </div>
      </section>

      {/* Real Proof on the Landing Page: January 2026 Replay Evidence */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="bg-white rounded-2xl border-2 border-slate-900 p-6 sm:p-8 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-3">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-sky-700 block">
                Historical Replay Evidence
              </span>
              <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 tracking-tight mt-0.5">
                Real Outturn Proof Across January 2026
              </h2>
            </div>
            <span className="text-xs font-mono text-slate-500 bg-slate-50 px-2.5 py-1 rounded border border-slate-200 self-start sm:self-auto">
              30 Decision Days Replayed (UTC)
            </span>
          </div>

          <div className="mt-6">
            {isLoadingSummary ? (
              <div className="py-8 text-center text-sm text-slate-500 font-mono animate-pulse">
                Computing January 2026 outturn metrics from cached Elexon dataset...
              </div>
            ) : summaryData ? (
              <div className="space-y-6">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-slate-900 text-base sm:text-lg font-medium leading-relaxed">
                  Across Jan 2026, planning with our estimate would have avoided{" "}
                  <strong className="text-emerald-700 font-bold font-mono">
                    {Math.round(summaryData.total_avoided_shortfall_mwh).toLocaleString()} MWh
                  </strong>{" "}
                  of shortfall (and arranged{" "}
                  <strong className="text-slate-800 font-bold font-mono">
                    {Math.round(summaryData.total_extra_advance_planned_mwh).toLocaleString()} MWh
                  </strong>{" "}
                  extra in advance).
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200">
                    <span className="font-bold text-emerald-900 block text-sm">
                      Avoided Shortfall Energy
                    </span>
                    <div className="text-2xl font-extrabold font-mono text-emerald-800 mt-1">
                      +{Math.round(summaryData.total_avoided_shortfall_mwh).toLocaleString()} MWh
                    </div>
                    <p className="text-emerald-700 mt-1">
                      Our estimate reduced unadjusted Elexon shortfall from{" "}
                      {Math.round(summaryData.total_elexon_shortfall_mwh).toLocaleString()} MWh down to{" "}
                      {Math.round(summaryData.total_safe_shortfall_mwh).toLocaleString()} MWh.
                    </p>
                  </div>

                  <div className="p-4 rounded-lg bg-slate-100 border border-slate-200">
                    <span className="font-bold text-slate-900 block text-sm">
                      Additional Advance-Planned Wind
                    </span>
                    <div className="text-2xl font-extrabold font-mono text-slate-900 mt-1">
                      {Math.round(summaryData.total_extra_advance_planned_mwh).toLocaleString()} MWh
                    </div>
                    <p className="text-slate-600 mt-1">
                      Actual wind generation above our planned quantity. Demonstrates the cost-side trade-off of caution.
                    </p>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-500 pt-2 gap-2">
                  <span>
                    Computed dynamically from 1,488 half-hourly Elexon FUELHH actuals and WINDFOR forecasts.
                  </span>
                  <button
                    onClick={() => onNavigate(`/jan25/check?date=${APP_CONFIG.defaultDecisionDate}&percentile=${APP_CONFIG.defaultPercentile}`)}
                    className="text-sky-700 font-semibold hover:underline inline-flex items-center space-x-1"
                  >
                    <span>Inspect daily replay</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                Summary metrics could not be loaded. Please ensure backend service is running.
              </p>
            )}
          </div>
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
              We take Elexon's official <code className="text-sky-700 bg-sky-50 px-1 py-0.5 rounded">WINDFOR</code> forecast published at or before 09:00 UTC on the decision day.
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
              We replay both plans against official <code className="text-emerald-700 bg-emerald-50 px-1 py-0.5 rounded">FUELHH</code> outturn, evaluating avoided shortfall MWh alongside extra advance-planned supply.
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
                The cautious adjustment prioritizes <strong>reducing downside shortfall</strong> (planning for less wind so actual generation rarely falls short). This comes with the trade-off of potentially arranging more advance supply than necessary when wind turns out to be plentiful.
              </p>
              <div className="p-3 bg-white/80 rounded-lg border border-amber-200/80 text-xs text-amber-950 font-medium">
                <strong>Explicit Assumption:</strong> “We assume replacement power bought close to delivery tends to cost more than power arranged in advance. We don’t model prices, so results are shown in MWh.”
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* No Future Data Leakage Backed Guarantee */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start space-x-3.5">
            <div className="p-2 rounded-lg bg-white border border-slate-200 shadow-2xs shrink-0 mt-0.5">
              <ShieldCheck className="w-5 h-5 text-sky-600" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-900">
                Backed No-Future-Data-Leakage Guarantee
              </h4>
              <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                Forecasts published and actuals recorded after 09:00 UTC on the decision day are never used. Verified by automated replay isolation tests.
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigate("/docs")}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 transition-colors shrink-0 self-start sm:self-auto"
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
          className="mt-2 text-sm font-semibold text-sky-600 hover:text-sky-800 transition-colors inline-flex items-center space-x-1.5 group"
        >
          <span>Jump to January 25 estimate example</span>
          <ArrowRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
        </button>
      </section>
    </div>
  );
};
