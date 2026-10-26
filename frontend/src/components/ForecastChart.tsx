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
import { EstimateInterval } from "../types";
import { Table } from "lucide-react";

interface ForecastChartProps {
  intervals: EstimateInterval[];
  targetDate: string;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({ intervals, targetDate }) => {
  const [showTable, setShowTable] = useState(false);

  const chartData = intervals.map((int) => {
    const timeStr = int.interval_start.substring(11, 16); // e.g. "14:30"
    return {
      time: timeStr,
      fullTime: `${int.interval_start} (SP ${int.settlement_period})`,
      settlementPeriod: int.settlement_period,
      elexonForecast: int.elexon_forecast_gw,
      safeEstimate: int.safe_estimate_gw,
      indicativeLower: int.indicative_lower_gw,
      indicativeUpper: int.indicative_upper_gw,
      appliedMargin: int.applied_margin_gw,
      rangeBand: [int.indicative_lower_gw, int.indicative_upper_gw],
    };
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 mb-6 gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900 tracking-tight">
            Half-Hourly Wind Generation Forecast
          </h2>
          <p className="text-xs text-slate-500 font-mono">
            Target date: {targetDate} · 48 Settlement Periods · UTC
          </p>
        </div>

        <button
          onClick={() => setShowTable(!showTable)}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 transition-colors self-start sm:self-auto cursor-pointer"
        >
          <Table className="w-3.5 h-3.5 text-slate-500" />
          <span>{showTable ? "View Chart" : "View Accessible Table"}</span>
        </button>
      </div>

      {!showTable ? (
        <div className="h-[420px] w-full">
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
                    const data = payload[0].payload;
                    return (
                      <div className="bg-slate-900/95 text-white p-3 rounded-lg shadow-xl text-xs font-mono space-y-1 border border-slate-700 z-50">
                        <div className="text-slate-400 font-semibold border-b border-slate-800 pb-1 mb-1">
                          {data.time} UTC (SP {data.settlementPeriod})
                        </div>
                        <div className="flex justify-between gap-4 text-sky-300">
                          <span>Elexon Forecast:</span>
                          <span className="font-bold">{data.elexonForecast.toFixed(1)} GW</span>
                        </div>
                        <div className="flex justify-between gap-4 text-emerald-300">
                          <span>Our Safe Estimate:</span>
                          <span className="font-bold">{data.safeEstimate.toFixed(1)} GW</span>
                        </div>
                        <div className="flex justify-between gap-4 text-amber-300">
                          <span>Applied Margin:</span>
                          <span>-{data.appliedMargin.toFixed(1)} GW</span>
                        </div>
                        <div className="flex justify-between gap-4 text-slate-400 pt-1 border-t border-slate-800">
                          <span>Empirical Range [p10–p90]:</span>
                          <span>
                            [{data.indicativeLower.toFixed(1)} – {data.indicativeUpper.toFixed(1)}] GW (not a probability interval)
                          </span>
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

              {/* Empirical Error Range Area */}
              <Area
                type="linear"
                dataKey="rangeBand"
                name="Empirical [p10, p90] range (realised coverage 55.8% in Jan 2026, not a probability interval)"
                fill="#e0f2fe"
                stroke="#bae6fd"
                strokeDasharray="2 2"
                opacity={0.6}
              />

              {/* Elexon Raw Forecast */}
              <Line
                type="linear"
                dataKey="elexonForecast"
                name="Elexon Forecast (Raw)"
                stroke="#0284c7"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                activeDot={{ r: 5 }}
              />

              {/* Safe Estimate */}
              <Line
                type="linear"
                dataKey="safeEstimate"
                name="Safe Estimate (Our Plan)"
                stroke="#0f172a"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 6, fill: "#0f172a" }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      ) : (
        /* Accessible Data Table */
        <div className="overflow-x-auto max-h-[420px] rounded-lg border border-slate-200">
          <table className="min-w-full text-left text-xs divide-y divide-slate-200">
            <thead className="bg-slate-50 sticky top-0 text-slate-700 font-semibold uppercase tracking-wider">
              <tr>
                <th className="px-3 py-2.5">SP</th>
                <th className="px-3 py-2.5">UTC Interval</th>
                <th className="px-3 py-2.5">Elexon (GW)</th>
                <th className="px-3 py-2.5">Safe Estimate (GW)</th>
                <th className="px-3 py-2.5">Applied Margin (GW)</th>
                <th className="px-3 py-2.5">Typical Error Range (GW)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white font-mono">
              {intervals.map((int) => (
                <tr key={int.interval_start} className="hover:bg-slate-50">
                  <td className="px-3 py-2 font-medium text-slate-500">{int.settlement_period}</td>
                  <td className="px-3 py-2 text-slate-900">{int.interval_start.substring(11, 16)}</td>
                  <td className="px-3 py-2 text-sky-700 font-semibold">{int.elexon_forecast_gw.toFixed(1)}</td>
                  <td className="px-3 py-2 text-slate-900 font-bold">{int.safe_estimate_gw.toFixed(1)}</td>
                  <td className="px-3 py-2 text-amber-700">-{int.applied_margin_gw.toFixed(1)}</td>
                  <td className="px-3 py-2 text-slate-600">
                    [{int.indicative_lower_gw.toFixed(1)} – {int.indicative_upper_gw.toFixed(1)}]
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs text-slate-500 gap-2">
        <span>Units: Gigawatts (GW). Displayed band shows typical error range from the last 48h of outturn (see Methodology).</span>
      </div>
    </div>
  );
};
