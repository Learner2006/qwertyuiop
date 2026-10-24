import React from "react";
import { CheckResponse } from "../types";
import { ShieldCheck, TrendingDown, PackagePlus, Gauge, AlertCircle } from "lucide-react";

interface ShortfallComparisonBarsProps {
  checkData: CheckResponse;
}

export const ShortfallComparisonBars: React.FC<ShortfallComparisonBarsProps> = ({ checkData }) => {
  const {
    elexon_shortfall_mwh,
    safe_shortfall_mwh,
    saved_shortfall_mwh,
    extra_advance_planned_mwh,
    elexon_mae_gw,
    safe_mae_gw,
    indicative_range_coverage,
    headline_result,
  } = checkData;

  const maxSf = Math.max(elexon_shortfall_mwh, safe_shortfall_mwh, 1.0);
  const elexonPct = (elexon_shortfall_mwh / maxSf) * 100;
  const safePct = (safe_shortfall_mwh / maxSf) * 100;

  const isSavedPositive = saved_shortfall_mwh > 0;
  const isSavedNegative = saved_shortfall_mwh < 0;

  return (
    <div className="space-y-6 mb-8">
      {/* Dynamic Headline Result Banner */}
      <div
        className={`p-5 rounded-xl border ${
          isSavedPositive
            ? "bg-emerald-50 border-emerald-200 text-emerald-950"
            : isSavedNegative
            ? "bg-amber-50 border-amber-200 text-amber-950"
            : "bg-slate-50 border-slate-200 text-slate-900"
        } flex items-start space-x-3.5 shadow-sm`}
      >
        <div className="p-2 rounded-lg bg-white/80 shadow-xs shrink-0 mt-0.5">
          {isSavedPositive ? (
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
          ) : (
            <AlertCircle className="w-5 h-5 text-amber-600" />
          )}
        </div>
        <div>
          <h3 className="text-base font-bold tracking-tight">
            {headline_result}
          </h3>
          <p className="text-xs opacity-85 mt-1 leading-relaxed">
            Avoided shortfall energy comparison based on historical Elexon BMRS outturn replay. This evaluates physical energy exposure (MWh), not cash savings.
          </p>
        </div>
      </div>

      {/* Shortfall Comparison Bars Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-6">
          Day-Ahead Shortfall Energy Comparison (MWh)
        </h3>

        <div className="space-y-6">
          {/* Elexon Shortfall Bar */}
          <div>
            <div className="flex justify-between items-center text-xs mb-1.5 font-medium">
              <span className="text-slate-700">Elexon Unadjusted Forecast Shortfall:</span>
              <span className="font-mono font-bold text-amber-700 text-sm">
                {elexon_shortfall_mwh.toLocaleString()} MWh
              </span>
            </div>
            <div className="w-full h-5 bg-slate-100 rounded-lg overflow-hidden border border-slate-200 p-0.5">
              <div
                className="h-full bg-amber-500 rounded-md transition-all duration-500"
                style={{ width: `${Math.max(2, elexonPct)}%` }}
              />
            </div>
          </div>

          {/* Our Safe Estimate Shortfall Bar */}
          <div>
            <div className="flex justify-between items-center text-xs mb-1.5 font-medium">
              <span className="text-slate-700 font-semibold">Our Cautious Estimate Shortfall:</span>
              <span className="font-mono font-bold text-slate-900 text-sm">
                {safe_shortfall_mwh.toLocaleString()} MWh
              </span>
            </div>
            <div className="w-full h-5 bg-slate-100 rounded-lg overflow-hidden border border-slate-200 p-0.5">
              <div
                className="h-full bg-slate-800 rounded-md transition-all duration-500"
                style={{ width: `${Math.max(2, safePct)}%` }}
              />
            </div>
          </div>

          {/* Avoided Shortfall Energy Metric */}
          <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="text-xs text-slate-500 block">Avoided Shortfall Energy:</span>
              <span className="text-xs text-slate-400">
                Formula: elexon_shortfall_mwh − our_shortfall_mwh
              </span>
            </div>
            <div className="text-right">
              <span
                className={`text-xl font-bold font-mono ${
                  isSavedPositive
                    ? "text-emerald-600"
                    : isSavedNegative
                    ? "text-amber-600"
                    : "text-slate-600"
                }`}
              >
                {isSavedPositive ? `+${saved_shortfall_mwh.toLocaleString()}` : saved_shortfall_mwh.toLocaleString()} MWh
              </span>
              <span className="block text-[11px] text-slate-400">
                {isSavedPositive ? "Reduced downside exposure" : (isSavedNegative ? "Higher shortfall on this day" : "Equal shortfall")}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Trade-Off and Accuracy Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Additional Advance-Planned Energy Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center space-x-2 text-sky-700 mb-2">
            <PackagePlus className="w-4 h-4" />
            <h4 className="text-xs font-semibold uppercase tracking-wider">
              Additional Advance Wind
            </h4>
          </div>
          <div className="text-xl font-bold font-mono text-slate-900 mt-1">
            {extra_advance_planned_mwh.toLocaleString()} MWh
          </div>
          <p className="text-xs text-slate-500 mt-2 leading-relaxed">
            Actual wind generation above our planned estimate. Illustrates the trade-off of caution; not a measure of thermal procurement cost.
          </p>
        </div>

        {/* Forecast Accuracy (MAE) Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center space-x-2 text-slate-700 mb-2">
            <Gauge className="w-4 h-4" />
            <h4 className="text-xs font-semibold uppercase tracking-wider">
              Forecast Error (MAE)
            </h4>
          </div>
          <div className="flex items-baseline space-x-3 mt-1 font-mono">
            <div>
              <span className="text-xs text-slate-400 block">Our MAE:</span>
              <span className="text-lg font-bold text-slate-900">{safe_mae_gw.toFixed(3)} GW</span>
            </div>
            <div className="text-slate-300">vs</div>
            <div>
              <span className="text-xs text-slate-400 block">Elexon:</span>
              <span className="text-base font-semibold text-sky-700">{elexon_mae_gw.toFixed(3)} GW</span>
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-2 leading-relaxed">
            Reducing shortfall shifts bias downward and does not necessarily optimize symmetric MAE.
          </p>
        </div>

        {/* Indicative Range Coverage Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center space-x-2 text-indigo-700 mb-2">
            <TrendingDown className="w-4 h-4" />
            <h4 className="text-xs font-semibold uppercase tracking-wider">
              Range Empirical Coverage
            </h4>
          </div>
          <div className="text-xl font-bold font-mono text-slate-900 mt-1">
            {(indicative_range_coverage * 100).toFixed(1)}%
          </div>
          <p className="text-xs text-slate-500 mt-2 leading-relaxed">
            Fraction of actual half-hourly points falling within the 10th–90th historical error quantiles on this target day.
          </p>
        </div>
      </div>
    </div>
  );
};
