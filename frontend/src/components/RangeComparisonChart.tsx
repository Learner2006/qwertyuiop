import React, { useState } from "react";
import { Table } from "lucide-react";

interface RangeComparisonChartProps {
  elexonHeadlineGw: number;
  safeHeadlineGw: number;
  actualHeadlineGw: number;
  indicativeLowerGw: number;
  indicativeUpperGw: number;
}

export const RangeComparisonChart: React.FC<RangeComparisonChartProps> = ({
  elexonHeadlineGw,
  safeHeadlineGw,
  actualHeadlineGw,
  indicativeLowerGw,
  indicativeUpperGw,
}) => {
  const [showTable, setShowTable] = useState(false);

  // Determine scaling for custom SVG range comparison
  const allValues = [
    elexonHeadlineGw,
    safeHeadlineGw,
    actualHeadlineGw,
    indicativeLowerGw,
    indicativeUpperGw,
  ];
  const minVal = Math.max(0, Math.min(...allValues) * 0.85);
  const maxVal = Math.max(...allValues) * 1.15;
  const rangeSpan = maxVal - minVal || 1.0;

  const toPercent = (val: number) => {
    return Math.min(100, Math.max(0, ((val - minVal) / rangeSpan) * 100));
  };

  const actualLeft = toPercent(actualHeadlineGw);
  const elexonLeft = toPercent(elexonHeadlineGw);
  const safeLeft = toPercent(safeHeadlineGw);
  const bandLeft = toPercent(indicativeLowerGw);
  const bandWidth = Math.max(0, toPercent(indicativeUpperGw) - bandLeft);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 mb-6 gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900 tracking-tight">
            Daily Mean Generation & Range Comparison
          </h2>
          <p className="text-xs text-slate-500 font-mono">
            Shared axis in GW · Comparing daily averages against actual realized wind
          </p>
        </div>

        <button
          onClick={() => setShowTable(!showTable)}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 transition-colors self-start sm:self-auto"
        >
          <Table className="w-3.5 h-3.5 text-slate-500" />
          <span>{showTable ? "View Graphic" : "View Values Table"}</span>
        </button>
      </div>

      {!showTable ? (
        <div className="py-6 px-4">
          {/* Axis Scale Markers */}
          <div className="relative h-8 mb-4 border-b border-slate-300 text-xs text-slate-400 font-mono">
            <span className="absolute left-0 -bottom-5">{minVal.toFixed(1)} GW</span>
            <span className="absolute left-1/4 -bottom-5 transform -translate-x-1/2">
              {(minVal + rangeSpan * 0.25).toFixed(1)} GW
            </span>
            <span className="absolute left-1/2 -bottom-5 transform -translate-x-1/2">
              {(minVal + rangeSpan * 0.5).toFixed(1)} GW
            </span>
            <span className="absolute left-3/4 -bottom-5 transform -translate-x-1/2">
              {(minVal + rangeSpan * 0.75).toFixed(1)} GW
            </span>
            <span className="absolute right-0 -bottom-5">{maxVal.toFixed(1)} GW</span>
          </div>

          {/* Graphic tracks container */}
          <div className="relative pt-6 pb-8 space-y-6">
            {/* Vertical Reference: Actual Realized Wind */}
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-emerald-600 z-20 pointer-events-none transition-all duration-300"
              style={{ left: `${actualLeft}%` }}
            >
              <div className="absolute -top-7 left-1/2 transform -translate-x-1/2 bg-emerald-700 text-white text-[11px] font-bold font-mono px-2 py-0.5 rounded shadow whitespace-nowrap">
                Actual: {actualHeadlineGw.toFixed(3)} GW
              </div>
            </div>

            {/* Track 1: Safe Estimate + Indicative Band */}
            <div className="relative h-14 bg-slate-50 rounded-lg border border-slate-200 p-2 flex items-center">
              <span className="w-32 text-xs font-semibold text-slate-800 shrink-0">
                Our Safe Estimate
              </span>

              <div className="relative flex-1 h-8">
                {/* Indicative Range Band */}
                <div
                  className="absolute top-1 bottom-1 bg-sky-100 border border-sky-300 rounded opacity-80"
                  style={{ left: `${bandLeft}%`, width: `${bandWidth}%` }}
                  title={`Indicative Band: ${indicativeLowerGw.toFixed(3)} - ${indicativeUpperGw.toFixed(3)} GW`}
                >
                  <span className="absolute -bottom-5 left-0 text-[10px] text-sky-700 font-mono">
                    p10: {indicativeLowerGw.toFixed(2)}
                  </span>
                  <span className="absolute -bottom-5 right-0 text-[10px] text-sky-700 font-mono">
                    p90: {indicativeUpperGw.toFixed(2)}
                  </span>
                </div>

                {/* Safe Point Marker */}
                <div
                  className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10"
                  style={{ left: `${safeLeft}%` }}
                >
                  <div className="w-5 h-5 rounded-full bg-slate-900 border-2 border-white shadow flex items-center justify-center text-[10px] text-white font-bold" />
                  <span className="absolute -top-5 left-1/2 -translate-x-1/2 text-xs font-bold font-mono text-slate-900 whitespace-nowrap">
                    {safeHeadlineGw.toFixed(3)} GW
                  </span>
                </div>
              </div>
            </div>

            {/* Track 2: Raw Elexon Forecast */}
            <div className="relative h-14 bg-slate-50 rounded-lg border border-slate-200 p-2 flex items-center">
              <span className="w-32 text-xs font-semibold text-sky-800 shrink-0">
                Elexon Forecast
              </span>

              <div className="relative flex-1 h-8">
                {/* Point Marker */}
                <div
                  className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10"
                  style={{ left: `${elexonLeft}%` }}
                >
                  <div className="w-5 h-5 rounded-full bg-sky-600 border-2 border-white shadow flex items-center justify-center text-[10px] text-white font-bold" />
                  <span className="absolute -top-5 left-1/2 -translate-x-1/2 text-xs font-bold font-mono text-sky-700 whitespace-nowrap">
                    {elexonHeadlineGw.toFixed(3)} GW
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Legend */}
          <div className="mt-8 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex items-center space-x-5">
              <div className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full bg-slate-900" />
                <span className="text-slate-700 font-medium">Safe Estimate Point</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full bg-sky-600" />
                <span className="text-slate-700 font-medium">Elexon Forecast Point</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-4 h-3 rounded bg-sky-100 border border-sky-300" />
                <span className="text-slate-700 font-medium">Indicative Range Band (p10–p90)</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <span className="w-3 h-0.5 bg-emerald-600" />
                <span className="text-emerald-700 font-bold">Actual Wind Marker</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Accessible Table */
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full text-left text-xs divide-y divide-slate-200">
            <thead className="bg-slate-50 text-slate-700 font-semibold uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">Metric</th>
                <th className="px-4 py-3">Daily Average (GW)</th>
                <th className="px-4 py-3">Indicative Range (GW)</th>
                <th className="px-4 py-3">Delta vs Actual (GW)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white font-mono">
              <tr>
                <td className="px-4 py-2.5 font-bold text-slate-900">Actual Realized Wind</td>
                <td className="px-4 py-2.5 text-emerald-700 font-bold">{actualHeadlineGw.toFixed(3)}</td>
                <td className="px-4 py-2.5 text-slate-400">—</td>
                <td className="px-4 py-2.5 text-slate-400">0.000</td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 font-semibold text-slate-900">Our Safe Estimate</td>
                <td className="px-4 py-2.5 text-slate-900 font-bold">{safeHeadlineGw.toFixed(3)}</td>
                <td className="px-4 py-2.5 text-sky-700">
                  [{indicativeLowerGw.toFixed(3)} – {indicativeUpperGw.toFixed(3)}]
                </td>
                <td className="px-4 py-2.5 text-slate-700">
                  {(safeHeadlineGw - actualHeadlineGw).toFixed(3)}
                </td>
              </tr>
              <tr>
                <td className="px-4 py-2.5 font-semibold text-sky-800">Elexon Raw Forecast</td>
                <td className="px-4 py-2.5 text-sky-700 font-bold">{elexonHeadlineGw.toFixed(3)}</td>
                <td className="px-4 py-2.5 text-slate-400">—</td>
                <td className="px-4 py-2.5 text-slate-700">
                  {(elexonHeadlineGw - actualHeadlineGw).toFixed(3)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      <p className="text-[11px] text-slate-500 mt-4 italic">
        Note: The indicative range band reflects historical empirical error quantiles. It is not a guaranteed confidence interval.
      </p>
    </div>
  );
};
