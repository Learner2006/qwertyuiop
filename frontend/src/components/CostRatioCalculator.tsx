import React, { useState } from "react";
import { Calculator } from "lucide-react";

interface CostRatioCalculatorProps {
  avoidedMwh?: number;
  extraMwh?: number;
  contextLabel?: string;
  totalGenerationMwh?: number;
  avoidedMwhV1?: number;
  extraMwhV1?: number;
  avoidedMwhV2?: number;
  extraMwhV2?: number;
  avoidedMwhFlat15?: number;
  extraMwhFlat15?: number;
  title?: string;
  subtitle?: string;
  allowModelSelection?: boolean;
}

export const CostRatioCalculator: React.FC<CostRatioCalculatorProps> = ({
  avoidedMwh,
  extraMwh,
  contextLabel = "Completed Days to Cutoff",
  totalGenerationMwh = 6263226.5,
  avoidedMwhV1 = 627721.3,
  extraMwhV1 = 739465.9,
  avoidedMwhV2 = 1022627.7,
  extraMwhV2 = 905978.4,
  avoidedMwhFlat15 = 1016662.2,
  extraMwhFlat15 = 411934.4,
  title = "Where Does This Pay Off? Cost-Ratio Payoff Calculator",
  subtitle = "Evaluate net financial impact across completed delivery days without needing market price data.",
  allowModelSelection = false,
}) => {
  const [advancePrice, setAdvancePrice] = useState<number>(70);
  const [selectedModel, setSelectedModel] = useState<"v1" | "v2" | "flat15">("v1");
  const [volumeMode, setVolumeMode] = useState<"national" | "per100" | "custom">("national");
  const [customPortfolioMwh, setCustomPortfolioMwh] = useState<number>(10000);

  // Active base volume parameters
  const baseAvoidedMwh =
    avoidedMwh !== undefined && !allowModelSelection
      ? avoidedMwh
      : selectedModel === "v1"
      ? avoidedMwhV1
      : selectedModel === "v2"
      ? avoidedMwhV2
      : avoidedMwhFlat15;

  const baseExtraMwh =
    extraMwh !== undefined && !allowModelSelection
      ? extraMwh
      : selectedModel === "v1"
      ? extraMwhV1
      : selectedModel === "v2"
      ? extraMwhV2
      : extraMwhFlat15;

  // Scale volume depending on chosen volume scope
  let scaleFactor = 1.0;

  if (volumeMode === "per100") {
    // Normalised per 100 MWh delivered (100 / total generation across the completed period)
    scaleFactor = totalGenerationMwh > 0 ? 100.0 / totalGenerationMwh : 1.0 / 62632.265;
  } else if (volumeMode === "custom") {
    // Custom portfolio size scaled relative to national grid outturn
    scaleFactor = totalGenerationMwh > 0 ? customPortfolioMwh / totalGenerationMwh : customPortfolioMwh / 6263226.5;
  }

  const activeAvoidedMwh = baseAvoidedMwh * scaleFactor;
  const activeExtraMwh = baseExtraMwh * scaleFactor;

  const breakevenK = activeAvoidedMwh > 0 ? activeExtraMwh / activeAvoidedMwh : 1.0;
  const kValues = [1.0, 1.5, 2.0, 3.0];

  const calculateScenario = (k: number) => {
    const avoidedValue = activeAvoidedMwh * (k * advancePrice);
    const extraCost = activeExtraMwh * advancePrice;
    const netSavings = avoidedValue - extraCost;
    const netMwh = activeAvoidedMwh * k - activeExtraMwh;
    return {
      k,
      replacementPrice: k * advancePrice,
      avoidedValue,
      extraCost,
      netSavings,
      netMwh,
      isPositive: netSavings > 0,
    };
  };

  const formatCurrency = (val: number) => {
    const isNeg = val < 0;
    const absVal = Math.abs(val);
    if (volumeMode === "per100") {
      return `${isNeg ? "−£" : "+£"}${Math.round(absVal).toLocaleString()}`;
    }
    if (absVal >= 1_000_000) {
      return `${isNeg ? "−£" : "+£"}${(absVal / 1_000_000).toFixed(2)}M`;
    }
    if (absVal >= 1_000) {
      return `${isNeg ? "−£" : "+£"}${(absVal / 1_000).toFixed(1)}k`;
    }
    return `${isNeg ? "−£" : "+£"}${Math.round(absVal).toLocaleString()}`;
  };

  const formatMwh = (val: number) => {
    const isNeg = val < 0;
    const absVal = Math.abs(val);
    if (volumeMode === "per100") {
      return `${isNeg ? "−" : "+"}${absVal.toFixed(1)} MWh`;
    }
    if (absVal >= 1_000_000) {
      return `${isNeg ? "−" : "+"}${(absVal / 1_000_000).toFixed(2)}M MWh`;
    }
    if (absVal >= 1_000) {
      return `${isNeg ? "−" : "+"}${Math.round(absVal / 1_000).toLocaleString()}k MWh`;
    }
    return `${isNeg ? "−" : "+"}${Math.round(absVal).toLocaleString()} MWh`;
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-200 gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <Calculator className="w-5 h-5 text-sky-600" />
            <h3 className="text-base font-bold text-slate-900 tracking-tight">{title}</h3>
          </div>
          <p className="text-xs text-slate-600">{subtitle}</p>
        </div>

        {/* Optional Model Selector Tabs (Shown only when allowModelSelection=true, e.g. on CheckPage) */}
        {allowModelSelection && (
          <div className="flex items-center p-1 bg-slate-100 rounded-lg text-xs font-semibold self-start sm:self-auto">
            <button
              onClick={() => setSelectedModel("v1")}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                selectedModel === "v1"
                  ? "bg-white text-slate-900 shadow-xs font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              v1 Additive (Headline p75)
            </button>
            <button
              onClick={() => setSelectedModel("v2")}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                selectedModel === "v2"
                  ? "bg-white text-slate-900 shadow-xs font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              v2 Proportional (p75)
            </button>
            <button
              onClick={() => setSelectedModel("flat15")}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                selectedModel === "flat15"
                  ? "bg-white text-slate-900 shadow-xs font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Flat 15% Baseline
            </button>
          </div>
        )}
      </div>

      {/* Input Controls & Volume Scope Selector */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
        {/* Advance Price Input */}
        <div className="space-y-1.5">
          <label className="font-semibold text-slate-700 flex items-center space-x-1">
            <span>Advance Base Power Price (£/MWh)</span>
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 font-mono text-sm">
              £
            </span>
            <input
              type="number"
              min={10}
              max={300}
              step={5}
              value={advancePrice}
              onChange={(e) => setAdvancePrice(Math.max(1, Number(e.target.value) || 0))}
              className="w-full pl-7 pr-3 py-2 bg-white border border-slate-300 rounded-lg font-mono font-bold text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
          <span className="text-[11px] text-slate-500">
            Editable example: £70/MWh (adjust to match your day-ahead power contract)
          </span>
        </div>

        {/* Volume Scope Selector */}
        <div className="space-y-1.5">
          <label className="font-semibold text-slate-700 block">
            Volume Scope
          </label>
          <div className="flex rounded-lg border border-slate-300 p-0.5 bg-white text-[11px]">
            <button
              onClick={() => setVolumeMode("national")}
              className={`flex-1 py-1.5 rounded text-center transition-colors font-medium ${
                volumeMode === "national"
                  ? "bg-slate-900 text-white font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              National GB Total
            </button>
            <button
              onClick={() => setVolumeMode("per100")}
              className={`flex-1 py-1.5 rounded text-center transition-colors font-medium ${
                volumeMode === "per100"
                  ? "bg-slate-900 text-white font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Per 100 MWh
            </button>
            <button
              onClick={() => setVolumeMode("custom")}
              className={`flex-1 py-1.5 rounded text-center transition-colors font-medium ${
                volumeMode === "custom"
                  ? "bg-slate-900 text-white font-bold"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Your Portfolio
            </button>
          </div>
          {volumeMode === "custom" ? (
            <div className="flex items-center space-x-1.5 pt-1">
              <input
                type="number"
                min={100}
                step={500}
                value={customPortfolioMwh}
                onChange={(e) => setCustomPortfolioMwh(Math.max(1, Number(e.target.value) || 0))}
                className="w-24 px-2 py-1 bg-white border border-slate-300 rounded text-xs font-mono font-bold text-slate-900 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
              <span className="text-[11px] text-slate-500 font-mono">MWh delivered volume</span>
            </div>
          ) : volumeMode === "per100" ? (
            <span className="text-[11px] text-slate-500 block">
              Normalized payoff per 100 MWh delivered (removes GB grid scale)
            </span>
          ) : (
            <span className="text-[11px] text-slate-500 block">
              100% GB national transmission wind volume ({contextLabel})
            </span>
          )}
        </div>

        {/* Dynamic Break-Even Indicator */}
        <div className="space-y-1 bg-white p-3 rounded-lg border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-500 uppercase block">
            Break-Even Multiplier (k*)
          </span>
          <div className="flex items-baseline space-x-2">
            <span className="text-xl font-bold font-mono text-sky-800">{breakevenK.toFixed(3)}×</span>
            <span className="text-xs text-slate-500">
              (£{(breakevenK * advancePrice).toFixed(1)}/MWh)
            </span>
          </div>
          <p className="text-[11px] text-slate-600 leading-normal">
            {breakevenK > 1.0 ? (
              <>
                Net positive only when same-day replacement power costs more than{" "}
                <strong>{breakevenK.toFixed(2)}×</strong> advance power. On this page, the plan only pays off if replacement power costs more than about {breakevenK.toFixed(2)}× advance power.
              </>
            ) : (
              <>
                Net positive at equal price parity (k = 1.0×) and above (break-even at {breakevenK.toFixed(2)}×).
              </>
            )}
          </p>
        </div>
      </div>

      {/* Evaluated Volumes Snapshot */}
      <div className="flex flex-wrap items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs font-mono">
        <div className="flex items-center space-x-2">
          <span className="font-sans text-slate-500 font-semibold text-[11px] uppercase tracking-wider">
            Evaluated Energy ({volumeMode === "per100" ? "Per 100 MWh" : volumeMode === "custom" ? `${customPortfolioMwh.toLocaleString()} MWh Portfolio` : "National Total"}):
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <div>
            <span className="text-slate-500 font-sans text-[11px] mr-1.5">Avoided Shortfall:</span>
            <span className="font-bold text-emerald-700">+{formatMwh(activeAvoidedMwh)}</span>
          </div>
          <div>
            <span className="text-slate-500 font-sans text-[11px] mr-1.5">Extra Advance Supply:</span>
            <span className="font-bold text-slate-800">+{formatMwh(activeExtraMwh)}</span>
          </div>
        </div>
      </div>

      {/* Payoff Matrix Table Across k = 1, 1.5, 2, 3 */}
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="min-w-full text-xs divide-y divide-slate-200">
          <thead className="bg-slate-50 text-slate-700 font-semibold uppercase tracking-wider text-[11px]">
            <tr>
              <th className="px-4 py-3 text-left">Replacement Multiplier (k)</th>
              <th className="px-4 py-3 text-right">Same-Day Price</th>
              <th className="px-4 py-3 text-right">Avoided Shortfall Value</th>
              <th className="px-4 py-3 text-right">Advance Power Cost</th>
              <th className="px-4 py-3 text-right">Net Energy Position</th>
              <th className="px-4 py-3 text-right">Net Financial Position</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white font-mono">
            {kValues.map((k) => {
              const res = calculateScenario(k);
              const isBreakevenRow = k >= breakevenK;
              return (
                <tr key={k} className={isBreakevenRow ? "hover:bg-emerald-50/40" : "hover:bg-amber-50/40"}>
                  <td className="px-4 py-3 text-left font-sans">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-slate-900 text-sm font-mono">{k.toFixed(1)}×</span>
                      <span className="text-xs text-slate-500">
                        {k === 1.0
                          ? "(Equal price parity)"
                          : k === 1.5
                          ? "(Moderate premium +50%)"
                          : k === 2.0
                          ? "(High peak / tight margin 2×)"
                          : "(Stress / cash-out spike 3×)"}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-slate-700">
                    £{res.replacementPrice.toFixed(0)}/MWh
                  </td>
                  <td className="px-4 py-3 text-right text-emerald-700 font-semibold">
                    {formatCurrency(res.avoidedValue)}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-600">
                    {formatCurrency(res.extraCost)}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-700 font-bold">
                    {formatMwh(res.netMwh)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold font-mono ${
                        res.isPositive
                          ? "bg-emerald-100 text-emerald-900 border border-emerald-300"
                          : "bg-amber-100 text-amber-900 border border-amber-300"
                      }`}
                    >
                      {formatCurrency(res.netSavings)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Explanatory Footer */}
      <div className="text-[11px] text-slate-500 space-y-1 bg-slate-50 p-3 rounded-lg border border-slate-200">
        <p>
          <strong>How this calculation works:</strong> At decision time, planning with a cautious margin avoids <code className="bg-white px-1 py-0.5 rounded">ΔE_avoided</code> of shortfall that would otherwise be purchased same-day at price <code className="bg-white px-1 py-0.5 rounded">k × P_advance</code>, while requiring <code className="bg-white px-1 py-0.5 rounded">ΔE_advance</code> of replacement power arranged in advance at price <code className="bg-white px-1 py-0.5 rounded">P_advance</code>.
        </p>
        <p className="font-mono text-slate-600">
          Net Payoff = [Avoided MWh × (k × P_advance)] − [Extra Advance MWh × P_advance] = P_advance × [Avoided MWh × k − Extra Advance MWh].
        </p>
        <p className="text-slate-500 italic pt-1">
          Disclaimer: This calculator illustrates physical MWh trade-offs across historical delivery days replayed under illustrative price assumptions. Wholesale day-ahead and same-day imbalance prices vary continuously in real trading.
        </p>
      </div>
    </div>
  );
};
