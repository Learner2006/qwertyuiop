import React, { useState } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { CheckInterval } from "../types";
import { Table, AlertTriangle } from "lucide-react";

interface ForecastVsActualChartProps {
  intervals: CheckInterval[];
  targetDate: string;
}

export const ForecastVsActualChart: React.FC<ForecastVsActualChartProps> = ({
  intervals,
  targetDate,
}) => {
  const [showTable, setShowTable] = useState(false);

  const chartData = intervals.map((int) => {
    const timeStr = int.interval_start.substring(11, 16);
    const a = int.actual_generation_gw;
    const ef = int.elexon_forecast_gw;
    const se = int.safe_estimate_gw;
    return {
      time: timeStr,
      settlementPeriod: int.settlement_period,
      elexonForecast: ef,
      safeEstimate: se,
      actualGeneration: a,
      elexonShortfallRange: ef > a ? [a, ef] : [a, a],
      safeShortfallRange: se > a ? [a, se] : [a, a],
      elexonShortfallMwh: int.elexon_shortfall_mwh,
      safeShortfallMwh: int.safe_shortfall_mwh,
      savedMwh: int.saved_mwh,
      isElexonShortfall: int.is_elexon_shortfall,
      isSafeShortfall: int.is_safe_shortfall,
      indicativeRange: [int.indicative_lower_gw, int.indicative_upper_gw],
    };
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 mb-6 gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900 tracking-tight flex items-center space-x-2">
            <span>Half-Hourly Forecasts vs Actual Generation</span>
            <span className="text-xs font-normal text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded flex items-center space-x-1">
              <AlertTriangle className="w-3 h-3 text-amber-600" />
              <span>Amber highlight indicates shortfall</span>
            </span>
          </h2>
          <p className="text-xs text-slate-500 font-mono">
            Target date: {targetDate} · 48 intervals · All power in GW · Shortfall in MWh
          </p>
        </div>

        <button
          onClick={() => setShowTable(!showTable)}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 transition-colors self-start sm:self-auto"
        >
          <Table className="w-3.5 h-3.5 text-slate-500" />
          <span>{showTable ? "View Chart" : "View Shortfall Table"}</span>
        </button>
      </div>

      {!showTable ? (
        <div className="h-[440px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={chartData}
              margin={{ top: 10, right: 30, left: 10, bottom: 25 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="time"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                interval={3}
                label={{
                  value: "Time (UTC)",
                  position: "insideBottom",
                  offset: -15,
                  fontSize: 12,
                  fill: "#64748b",
                }}
              />
              <YAxis
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                unit=" GW"
                domain={[0, "auto"]}
                label={{
                  value: "Generation (GW)",
                  angle: -90,
                  position: "insideLeft",
                  fontSize: 12,
                  fill: "#64748b",
                  offset: 0,
                }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload;
                    return (
                      <div className="bg-slate-900/95 text-white p-3.5 rounded-lg shadow-xl text-xs font-mono space-y-1.5 border border-slate-700 z-50 min-w-[240px]">
                        <div className="text-slate-400 font-semibold border-b border-slate-800 pb-1 flex justify-between">
                          <span>{d.time} UTC</span>
                          <span>SP {d.settlementPeriod}</span>
                        </div>
                        <div className="flex justify-between text-emerald-400 font-bold">
                          <span>Actual Generation:</span>
                          <span>{d.actualGeneration.toFixed(3)} GW</span>
                        </div>
                        <div className="flex justify-between text-sky-300">
                          <span>Elexon Forecast:</span>
                          <span>{d.elexonForecast.toFixed(3)} GW</span>
                        </div>
                        <div className="flex justify-between text-slate-200">
                          <span>Our Safe Estimate:</span>
                          <span>{d.safeEstimate.toFixed(3)} GW</span>
                        </div>

                        <div className="pt-2 border-t border-slate-800 space-y-1">
                          <div className="flex justify-between text-amber-300">
                            <span>Elexon Shortfall:</span>
                            <span className="font-bold">{d.elexonShortfallMwh.toFixed(1)} MWh</span>
                          </div>
                          <div className="flex justify-between text-amber-400">
                            <span>Our Shortfall:</span>
                            <span className="font-bold">{d.safeShortfallMwh.toFixed(1)} MWh</span>
                          </div>
                          <div className="flex justify-between text-emerald-300 pt-1 border-t border-slate-800">
                            <span>Avoided Shortfall:</span>
                            <span className="font-bold">{d.savedMwh > 0 ? `+${d.savedMwh.toFixed(1)}` : d.savedMwh.toFixed(1)} MWh</span>
                          </div>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                verticalAlign="top"
                height={36}
                formatter={(value) => (
                  <span className="text-xs text-slate-700 font-medium mr-4">{value}</span>
                )}
              />

              {/* Empirical Range Area */}
              <Area
                type="linear"
                dataKey="indicativeRange"
                name="Empirical [p10, p90] range (realised coverage 55.8% in Jan 2026, not a probability interval)"
                fill="#f0f9ff"
                stroke="#bae6fd"
                strokeDasharray="2 2"
                opacity={0.4}
              />

              {/* Shaded Shortfall Zones: Elexon & Safe Estimate */}
              <Area
                type="linear"
                dataKey="elexonShortfallRange"
                name="Elexon Shortfall Zone"
                fill="#fde68a"
                stroke="#f59e0b"
                strokeDasharray="2 2"
                opacity={0.35}
              />
              <Area
                type="linear"
                dataKey="safeShortfallRange"
                name="Our Shortfall Zone"
                fill="#fed7aa"
                stroke="#ea580c"
                strokeDasharray="2 2"
                opacity={0.4}
              />

              {/* Actual Wind Generation Line */}
              <Line
                type="linear"
                dataKey="actualGeneration"
                name="Actual Wind Generation"
                stroke="#059669"
                strokeWidth={3}
                dot={{ r: 2, fill: "#059669" }}
                activeDot={{ r: 6 }}
              />

              {/* Elexon Raw Forecast Line */}
              <Line
                type="linear"
                dataKey="elexonForecast"
                name="Elexon Forecast"
                stroke="#0284c7"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
              />

              {/* Our Safe Estimate Line */}
              <Line
                type="linear"
                dataKey="safeEstimate"
                name="Our Safe Estimate"
                stroke="#0f172a"
                strokeWidth={2.5}
                dot={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      ) : (
        /* Accessible Table with Shortfall Columns */
        <div className="overflow-x-auto max-h-[440px] rounded-lg border border-slate-200">
          <table className="min-w-full text-left text-xs divide-y divide-slate-200">
            <thead className="bg-slate-50 sticky top-0 text-slate-700 font-semibold uppercase tracking-wider">
              <tr>
                <th className="px-3 py-2.5">SP</th>
                <th className="px-3 py-2.5">Time (UTC)</th>
                <th className="px-3 py-2.5 text-emerald-800">Actual (GW)</th>
                <th className="px-3 py-2.5">Elexon (GW)</th>
                <th className="px-3 py-2.5">Safe (GW)</th>
                <th className="px-3 py-2.5 text-amber-800">Elexon Shortfall (MWh)</th>
                <th className="px-3 py-2.5 text-amber-800">Our Shortfall (MWh)</th>
                <th className="px-3 py-2.5 text-emerald-800">Saved MWh</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white font-mono">
              {intervals.map((int) => (
                <tr key={int.interval_start} className="hover:bg-slate-50">
                  <td className="px-3 py-2 text-slate-500">{int.settlement_period}</td>
                  <td className="px-3 py-2 text-slate-900">{int.interval_start.substring(11, 16)}</td>
                  <td className="px-3 py-2 text-emerald-700 font-bold">{int.actual_generation_gw.toFixed(3)}</td>
                  <td className="px-3 py-2 text-sky-700">{int.elexon_forecast_gw.toFixed(3)}</td>
                  <td className="px-3 py-2 text-slate-900 font-semibold">{int.safe_estimate_gw.toFixed(3)}</td>
                  <td className={`px-3 py-2 ${int.is_elexon_shortfall ? "text-amber-700 font-bold bg-amber-50/50" : "text-slate-400"}`}>
                    {int.elexon_shortfall_mwh.toFixed(1)}
                  </td>
                  <td className={`px-3 py-2 ${int.is_safe_shortfall ? "text-amber-700 font-bold bg-amber-50/50" : "text-slate-400"}`}>
                    {int.safe_shortfall_mwh.toFixed(1)}
                  </td>
                  <td className={`px-3 py-2 font-bold ${int.saved_mwh > 0 ? "text-emerald-700" : (int.saved_mwh < 0 ? "text-amber-700" : "text-slate-400")}`}>
                    {int.saved_mwh > 0 ? `+${int.saved_mwh.toFixed(1)}` : int.saved_mwh.toFixed(1)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs text-slate-500">
        <span>Shortfall formula: max(0, planned − actual) × 1000 × 0.5 hours.</span>
        <span className="font-mono text-[11px] text-slate-400">Amber color reserved for downside exposure</span>
      </div>
    </div>
  );
};
