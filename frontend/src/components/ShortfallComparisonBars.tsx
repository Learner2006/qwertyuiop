import React from "react";
import { CheckResponse } from "../types";
import { ShieldCheck, TrendingDown, PackagePlus, Gauge, AlertCircle } from "lucide-react";

interface ShortfallComparisonBarsProps {
  checkData: CheckResponse;
}

export const ShortfallComparisonBars: React.FC<ShortfallComparisonBarsProps> = ({ checkData }) => {
  const [modelMode, setModelMode] = React.useState<"flat15" | "v1" | "v2">("flat15");

  const effectiveSafeShortfall =
    modelMode === "flat15" && checkData.flat15_safe_shortfall_mwh !== undefined
      ? checkData.flat15_safe_shortfall_mwh
      : modelMode === "v2" && checkData.v2_safe_shortfall_mwh !== undefined
      ? checkData.v2_safe_shortfall_mwh
      : checkData.safe_shortfall_mwh;

  const effectiveSavedShortfall =
    modelMode === "flat15" && checkData.flat15_saved_shortfall_mwh !== undefined
      ? checkData.flat15_saved_shortfall_mwh
      : modelMode === "v2" && checkData.v2_saved_shortfall_mwh !== undefined
      ? checkData.v2_saved_shortfall_mwh
      : checkData.saved_shortfall_mwh;

  const effectiveSafeSurplus =
    modelMode === "flat15" && checkData.flat15_safe_surplus_mwh !== undefined
      ? checkData.flat15_safe_surplus_mwh
      : modelMode === "v2" && checkData.v2_safe_surplus_mwh !== undefined
      ? checkData.v2_safe_surplus_mwh
      : (checkData.safe_surplus_mwh ?? checkData.extra_advance_planned_mwh);

  const effectiveIncrementalSurplus =
    modelMode === "flat15" && checkData.flat15_incremental_surplus_mwh !== undefined
      ? checkData.flat15_incremental_surplus_mwh
      : modelMode === "v2" && checkData.v2_incremental_surplus_mwh !== undefined
      ? checkData.v2_incremental_surplus_mwh
      : Math.max(0, (checkData.safe_surplus_mwh ?? checkData.extra_advance_planned_mwh) - (checkData.elexon_surplus_mwh ?? 0));

  const {
    elexon_shortfall_mwh,
    elexon_surplus_mwh = 0,
    elexon_mae_gw,
    safe_mae_gw,
    indicative_range_coverage,
  } = checkData;

  const safe_shortfall_mwh = effectiveSafeShortfall;
  const saved_shortfall_mwh = effectiveSavedShortfall;
  const safe_surplus_mwh = effectiveSafeSurplus;
  const displayIncrementalSurplus = effectiveIncrementalSurplus;

  const maxSf = Math.max(elexon_shortfall_mwh, safe_shortfall_mwh, 1.0);
  const elexonSfPct = (elexon_shortfall_mwh / maxSf) * 100;
  const safeSfPct = (safe_shortfall_mwh / maxSf) * 100;

  const maxSurplus = Math.max(elexon_surplus_mwh, safe_surplus_mwh, 1.0);
  const elexonSurplusPct = (elexon_surplus_mwh / maxSurplus) * 100;
  const safeSurplusPct = (safe_surplus_mwh / maxSurplus) * 100;

  const isSavedPositive = saved_shortfall_mwh > 0;
  const isSavedNegative = saved_shortfall_mwh < 0;

  const dynamicHeadline =
    isSavedPositive
      ? `Our plan avoided ${Math.round(saved_shortfall_mwh).toLocaleString()} MWh of shortfall while requiring ${Math.round(displayIncrementalSurplus).toLocaleString()} MWh of incremental extra supply.`
      : isSavedNegative
      ? `Our plan increased shortfall by ${Math.round(Math.abs(saved_shortfall_mwh)).toLocaleString()} MWh while requiring ${Math.round(displayIncrementalSurplus).toLocaleString()} MWh of incremental extra supply.`
      : `Both methods produced the same shortfall energy, requiring ${Math.round(displayIncrementalSurplus).toLocaleString()} MWh of incremental extra supply.`;

  return (
    <div className="space-y-6 mb-8">
      {/* Model Version Selector (flat15 Headline vs v1 Declared vs v2 Proportional) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-slate-100 rounded-xl border border-slate-200">
        <div className="text-xs">
          <span className="font-bold text-slate-900 block">Evaluated Model Specification:</span>
          <span className="text-slate-500">
            {modelMode === "flat15"
              ? "Flat 15% Baseline: Pre-registered headline model (15% uniform haircut)."
              : modelMode === "v1"
              ? "v1: Original declared model (48h signed-error quantile floored at 0)."
              : `v2: Proportional margin model (${(((checkData.v2_ratio ?? 0.15)) * 100).toFixed(1)}% cut).`}
          </span>
        </div>
        <div className="inline-flex rounded-lg bg-white p-0.5 border border-slate-200 text-xs font-semibold shrink-0">
          <button
            onClick={() => setModelMode("flat15")}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              modelMode === "flat15"
                ? "bg-sky-600 text-white shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Flat 15% (Headline)
          </button>
          <button
            onClick={() => setModelMode("v1")}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              modelMode === "v1"
                ? "bg-sky-600 text-white shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            v1 (Additive p75)
          </button>
          <button
            onClick={() => setModelMode("v2")}
            className={`px-3 py-1.5 rounded-md transition-colors ${
              modelMode === "v2"
                ? "bg-sky-600 text-white shadow-2xs font-bold"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            v2 (Proportional p75)
          </button>
        </div>
      </div>

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
            {dynamicHeadline}
          </h3>
          <p className="text-xs opacity-85 mt-1 leading-relaxed">
            Avoided shortfall energy comparison based on historical Elexon FUELHH outturn replay. This evaluates physical energy exposure (MWh), not cash savings.
          </p>
        </div>
      </div>

      {/* Side-by-Side Shortfall and Surplus Apples-to-Apples Comparisons */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Shortfall Comparison Card */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Downside Shortfall Energy (MWh)
            </h3>
            <span className="text-[11px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
              Lower is safer
            </span>
          </div>

          <div className="space-y-5">
            {/* Elexon Shortfall Bar */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1.5 font-medium">
                <span className="text-slate-600">Elexon Unadjusted Shortfall:</span>
                <span className="font-mono font-bold text-amber-700 text-sm">
                  {Math.round(elexon_shortfall_mwh).toLocaleString()} MWh
                </span>
              </div>
              <div className="w-full h-4 bg-slate-100 rounded-lg overflow-hidden border border-slate-200 p-0.5">
                <div
                  className="h-full bg-amber-500 rounded-md transition-all duration-500"
                  style={{ width: `${Math.max(2, elexonSfPct)}%` }}
                />
              </div>
            </div>

            {/* Our Safe Estimate Shortfall Bar */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1.5 font-medium">
                <span className="text-slate-700 font-semibold">{modelMode === "flat15" ? "Flat 15% Shortfall:" : modelMode === "v2" ? "v2 Cautious Shortfall:" : "v1 Cautious Shortfall:"}</span>
                <span className="font-mono font-bold text-slate-900 text-sm">
                  {Math.round(safe_shortfall_mwh).toLocaleString()} MWh
                </span>
              </div>
              <div className="w-full h-4 bg-slate-100 rounded-lg overflow-hidden border border-slate-200 p-0.5">
                <div
                  className="h-full bg-slate-800 rounded-md transition-all duration-500"
                  style={{ width: `${Math.max(2, safeSfPct)}%` }}
                />
              </div>
            </div>

            {/* Avoided Shortfall Energy Metric */}
            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <div>
                <span className="text-xs font-medium text-slate-600 block">Avoided Shortfall:</span>
                <span className="text-[11px] text-slate-400">Elexon SF − Safe SF</span>
              </div>
              <div className="text-right">
                <span
                  className={`text-lg font-bold font-mono ${
                    isSavedPositive
                      ? "text-emerald-600"
                      : isSavedNegative
                      ? "text-amber-600"
                      : "text-slate-600"
                  }`}
                >
                  {isSavedPositive ? `+${Math.round(saved_shortfall_mwh).toLocaleString()}` : Math.round(saved_shortfall_mwh).toLocaleString()} MWh
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Surplus / Advance-Planned Wind Card (Apples-to-Apples) */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Wind Above Plan (MWh)
            </h3>
            <span className="text-[11px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
              Advance supply trade-off
            </span>
          </div>

          <div className="space-y-5">
            {/* Elexon Surplus Bar */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1.5 font-medium">
                <span className="text-slate-600">Elexon Plan Surplus:</span>
                <span className="font-mono font-bold text-sky-700 text-sm">
                  {Math.round(elexon_surplus_mwh).toLocaleString()} MWh
                </span>
              </div>
              <div className="w-full h-4 bg-slate-100 rounded-lg overflow-hidden border border-slate-200 p-0.5">
                <div
                  className="h-full bg-sky-400 rounded-md transition-all duration-500"
                  style={{ width: `${Math.max(2, elexonSurplusPct)}%` }}
                />
              </div>
            </div>

            {/* Our Safe Estimate Surplus Bar */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1.5 font-medium">
                <span className="text-slate-700 font-semibold">{modelMode === "flat15" ? "Flat 15% Surplus:" : modelMode === "v2" ? "v2 Plan Surplus:" : "v1 Plan Surplus:"}</span>
                <span className="font-mono font-bold text-slate-900 text-sm">
                  {Math.round(safe_surplus_mwh).toLocaleString()} MWh
                </span>
              </div>
              <div className="w-full h-4 bg-slate-100 rounded-lg overflow-hidden border border-slate-200 p-0.5">
                <div
                  className="h-full bg-slate-800 rounded-md transition-all duration-500"
                  style={{ width: `${Math.max(2, safeSurplusPct)}%` }}
                />
              </div>
            </div>

            {/* Incremental Advance Wind Metric */}
            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <div>
                <span className="text-xs font-medium text-slate-600 block">Incremental Extra Arranged:</span>
                <span className="text-[11px] text-slate-400">Replacement planned but not needed</span>
              </div>
              <div className="text-right">
                <span className="text-lg font-bold font-mono text-slate-800">
                  +{Math.round(displayIncrementalSurplus).toLocaleString()} MWh
                </span>
              </div>
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
              Incremental Advance Power
            </h4>
          </div>
          <div className="text-xl font-bold font-mono text-slate-900 mt-1">
            +{Math.round(displayIncrementalSurplus).toLocaleString()} MWh
          </div>
          <p className="text-xs text-slate-500 mt-2 leading-relaxed">
            Wind above cautious plan (replacement power planned in advance but not needed).
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
            Reducing shortfall shifts bias downward and does not optimize symmetric MAE.
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
