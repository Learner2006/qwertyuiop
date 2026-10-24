import React from "react";
import { APP_CONFIG } from "../config";
import { ArrowRight, TrendingDown, Clock } from "lucide-react";

interface LandingPageProps {
  onNavigate: (path: string) => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  const handleStart = () => {
    onNavigate(`/jan25?date=${APP_CONFIG.defaultDecisionDate}&percentile=${APP_CONFIG.defaultPercentile}`);
  };

  return (
    <div className="space-y-20 py-8">
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
        <div className="mt-12 bg-white rounded-xl border border-slate-200 p-4 max-w-2xl mx-auto shadow-2xs flex flex-wrap items-center justify-around gap-4 text-xs font-mono text-slate-600">
          <div><span className="text-slate-400">Decision Cutoff:</span> 09:00 UTC</div>
          <div className="hidden sm:block text-slate-300">|</div>
          <div><span className="text-slate-400">Target Horizon:</span> D+1 (24 Hours)</div>
          <div className="hidden sm:block text-slate-300">|</div>
          <div><span className="text-slate-400">Dataset:</span> January 2026 Elexon</div>
        </div>
      </section>

      {/* The Problem Section */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl p-8 sm:p-12 shadow-md">
          <div className="max-w-3xl">
            <h2 className="text-xs font-bold uppercase tracking-widest text-sky-400 mb-2">
              The Electricity Buyer's Dilemma
            </h2>
            <h3 className="text-2xl sm:text-3xl font-bold tracking-tight mb-4">
              Wind generation is volatile. Relying on an unadjusted forecast creates downside shortfall risk.
            </h3>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed mb-6">
              A UK electricity buyer planning tomorrow's supply must decide how much wind generation to count on. If actual wind generation falls below the planned quantity, the buyer faces a <strong>shortfall</strong> and must procure replacement power closer to delivery.
            </p>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Our model applies a <strong>deliberately cautious adjustment</strong> to Elexon's published forecast, shifting planned volume downward based on recent signed forecast errors. This application tests whether that cautious adjustment reliably reduces shortfall energy across a full historical month.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works: 3 Steps */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <h2 className="text-xs font-bold uppercase tracking-widest text-sky-600 mb-2">
            The Workflow
          </h2>
          <h3 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            How the Estimator Works in 3 Steps
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Step 1 */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm relative">
            <div className="w-10 h-10 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center font-bold text-base mb-4 border border-sky-200">
              1
            </div>
            <h4 className="text-base font-bold text-slate-900 mb-2">
              Fetch Published Forecast
            </h4>
            <p className="text-sm text-slate-600 leading-relaxed">
              We ingest Elexon's official <code className="text-sky-700 bg-sky-50 px-1 py-0.5 rounded">WINDFOR</code> forecast published at or before the 09:00 UTC day-ahead cutoff.
            </p>
          </div>

          {/* Step 2 */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm relative">
            <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold text-base mb-4 border border-indigo-200">
              2
            </div>
            <h4 className="text-base font-bold text-slate-900 mb-2">
              Apply Cautious Calibration
            </h4>
            <p className="text-sm text-slate-600 leading-relaxed">
              We compute recent historical signed errors over a 48-hour lookback, blending empirical error percentiles with a 15% cold-start haircut rule.
            </p>
          </div>

          {/* Step 3 */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm relative">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-base mb-4 border border-emerald-200">
              3
            </div>
            <h4 className="text-base font-bold text-slate-900 mb-2">
              Replay Actual Realized Outturn
            </h4>
            <p className="text-sm text-slate-600 leading-relaxed">
              We replay both plans against official <code className="text-emerald-700 bg-emerald-50 px-1 py-0.5 rounded">FUELHH</code> outturn, evaluating avoided shortfall MWh and trade-offs.
            </p>
          </div>
        </div>
      </section>

      {/* The Trade-Off Section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6">
        <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-6 sm:p-8">
          <div className="flex items-start space-x-4">
            <div className="p-2.5 rounded-lg bg-amber-100 text-amber-800 shrink-0">
              <TrendingDown className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-base font-bold text-amber-950 mb-1">
                Understanding the Fundamental Trade-Off
              </h4>
              <p className="text-sm text-amber-900 leading-relaxed">
                The cautious adjustment prioritizes <strong>reducing downside shortfall</strong> (planning for less wind so actual outcomes rarely fall short). However, this comes at the cost of <strong>potentially arranging more advance supply than necessary</strong> when actual wind turns out to be abundant.
              </p>
              <p className="text-xs text-amber-800/90 mt-3 italic">
                * Note: The product does not claim that this trade-off always improves financial outcomes. Results vary by date and weather regime and are evaluated purely in physical MWh.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="text-center max-w-xl mx-auto px-4">
        <h3 className="text-2xl font-bold text-slate-900 mb-4">
          Inspect Historical Replay Data
        </h3>
        <p className="text-sm text-slate-600 mb-6">
          Explore day-ahead estimates across all 30 decision dates of January 2026.
        </p>
        <button
          onClick={handleStart}
          className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-sm font-semibold rounded-lg text-white bg-sky-600 hover:bg-sky-700 transition-colors shadow-sm"
        >
          <span>Open January 25 Example</span>
          <ArrowRight className="ml-2 w-4 h-4" />
        </button>
      </section>
    </div>
  );
};
