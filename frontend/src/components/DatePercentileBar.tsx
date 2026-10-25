import React from "react";
import { APP_CONFIG } from "../config";
import { Calendar, Sliders, Clock, AlertTriangle } from "lucide-react";

interface DatePercentileBarProps {
  decisionDate: string;
  targetDate: string;
  percentile: number;
  onDateChange: (newDate: string) => void;
  onPercentileChange: (newPercentile: number) => void;
  isLoading?: boolean;
}

export const DatePercentileBar: React.FC<DatePercentileBarProps> = ({
  decisionDate,
  targetDate,
  percentile,
  onDateChange,
  onPercentileChange,
  isLoading = false,
}) => {
  const isDateOutOfRange =
    decisionDate < APP_CONFIG.minDate || decisionDate > APP_CONFIG.maxDate;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Date Selector */}
        <div className="lg:col-span-5 flex flex-col space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
            <Calendar className="w-3.5 h-3.5 text-sky-600" />
            <span>Select Decision Date (Cutoff 09:00 UTC)</span>
          </label>
          <div className="flex flex-wrap items-center gap-3">
            <input
              type="date"
              value={decisionDate}
              min={APP_CONFIG.minDate}
              max={APP_CONFIG.maxDate}
              onChange={(e) => onDateChange(e.target.value)}
              disabled={isLoading}
              className="px-3.5 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 bg-white font-medium focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-all outline-none"
            />
            {targetDate && (
              <div className="flex items-center text-xs font-medium text-slate-600 bg-slate-50 px-3 py-2 rounded-lg border border-slate-200">
                <span className="text-slate-400 mr-1.5">Target:</span>
                <span className="font-semibold text-slate-900">{targetDate}</span>
                <span className="ml-1 text-slate-400 font-mono">(D+1)</span>
              </div>
            )}
          </div>
          <span className="text-[11px] text-slate-500 font-mono">
            Permitted historical dates: January 1–30, 2026 only
          </span>
          {isDateOutOfRange && (
            <div className="flex items-center space-x-1.5 text-xs text-amber-700 bg-amber-50 p-2 rounded-md border border-amber-200">
              <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
              <span>Please choose a valid decision date between Jan 1 and Jan 30, 2026.</span>
            </div>
          )}
        </div>

        {/* Risk Percentile Slider */}
        <div className="lg:col-span-7 flex flex-col space-y-2 border-t lg:border-t-0 lg:border-l border-slate-100 pt-4 lg:pt-0 lg:pl-6">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
              <Sliders className="w-3.5 h-3.5 text-sky-600" />
              <span>Risk Caution Percentile (p)</span>
            </label>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-bold font-mono text-sky-700 bg-sky-50 border border-sky-200 px-2.5 py-0.5 rounded">
                p{percentile}
              </span>
              <span className="text-xs text-slate-400 font-mono">
                {percentile === 75 ? "(Default)" : ""}
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-4">
            <span className="text-xs font-mono text-slate-500 whitespace-nowrap">
              p60 (less cautious)
            </span>
            <input
              type="range"
              min={APP_CONFIG.minPercentile}
              max={APP_CONFIG.maxPercentile}
              step={1}
              value={percentile}
              onChange={(e) => onPercentileChange(Number(e.target.value))}
              disabled={isLoading}
              className="w-full h-2.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-sky-600 focus:outline-none"
            />
            <span className="text-xs font-mono text-slate-500 whitespace-nowrap text-right sm:text-left">
              p90 (most cautious)
            </span>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-slate-500 gap-1">
            <span>Higher percentile applies a wider downward margin, reducing shortfall risk.</span>
            {isLoading && (
              <span className="text-sky-600 font-medium animate-pulse flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span>Recalculating...</span>
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
