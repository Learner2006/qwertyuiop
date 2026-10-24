import React, { useEffect, useState } from "react";
import { fetchCheck } from "../api/client";
import { APP_CONFIG } from "../config";
import { CheckResponse } from "../types";
import { DatePercentileBar } from "../components/DatePercentileBar";
import { RangeComparisonChart } from "../components/RangeComparisonChart";
import { ForecastVsActualChart } from "../components/ForecastVsActualChart";
import { ShortfallComparisonBars } from "../components/ShortfallComparisonBars";
import { ArrowLeft, AlertCircle } from "lucide-react";

interface CheckPageProps {
  initialDate?: string;
  initialPercentile?: number;
  onNavigate: (path: string) => void;
  updateUrl: (date: string, percentile: number) => void;
}

export const CheckPage: React.FC<CheckPageProps> = ({
  initialDate = APP_CONFIG.defaultDecisionDate,
  initialPercentile = APP_CONFIG.defaultPercentile,
  onNavigate,
  updateUrl,
}) => {
  const [decisionDate, setDecisionDate] = useState<string>(initialDate);
  const [percentile, setPercentile] = useState<number>(initialPercentile);
  const [checkData, setCheckData] = useState<CheckResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sync state if props change from URL
  useEffect(() => {
    if (initialDate && initialDate !== decisionDate) setDecisionDate(initialDate);
    if (initialPercentile && initialPercentile !== percentile) setPercentile(initialPercentile);
  }, [initialDate, initialPercentile]);

  // Load check data
  useEffect(() => {
    let isCancelled = false;
    setIsLoading(true);
    setErrorMessage(null);

    fetchCheck(decisionDate, percentile)
      .then((data) => {
        if (!isCancelled) {
          setCheckData(data);
          setIsLoading(false);
          updateUrl(decisionDate, percentile);
        }
      })
      .catch((err) => {
        if (!isCancelled) {
          setErrorMessage(err.message || "Failed to load reliability check.");
          setIsLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [decisionDate, percentile]);

  const handleDateChange = (newDate: string) => {
    setDecisionDate(newDate);
  };

  const handlePercentileChange = (newPercentile: number) => {
    setPercentile(newPercentile);
  };

  const handleBackToEstimate = () => {
    onNavigate(`/jan25?date=${encodeURIComponent(decisionDate)}&percentile=${percentile}`);
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <button
            onClick={handleBackToEstimate}
            className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Estimate</span>
          </button>
          <div className="inline-flex items-center space-x-1.5 text-xs text-amber-900 bg-amber-50 px-2.5 py-0.5 rounded border border-amber-200 font-mono mb-2 ml-3">
            <span>Reliability Replay</span>
            <span>·</span>
            <span>Elexon FUELHH Outturn</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Did the cautious estimate reduce shortfall?
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Comparing Elexon's original forecast and our safe estimate against actual half-hourly wind generation observations.
          </p>
        </div>

        {/* Back Button */}
        <button
          onClick={handleBackToEstimate}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 transition-colors shrink-0 self-start md:self-auto"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Edit decision parameters</span>
        </button>
      </div>

      {/* Date & Percentile Controls */}
      <DatePercentileBar
        decisionDate={decisionDate}
        targetDate={checkData?.target_date || ""}
        percentile={percentile}
        onDateChange={handleDateChange}
        onPercentileChange={handlePercentileChange}
        isLoading={isLoading}
      />

      {/* Error State */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-red-900 flex items-start space-x-3.5">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="text-sm font-bold">Reliability Check Failed</h3>
            <p className="text-sm">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Check Content */}
      {checkData && !errorMessage && (
        <>
          {/* Section 13.3, 13.4, 13.5: Shortfall Comparison & Dynamic Sentence */}
          <ShortfallComparisonBars checkData={checkData} />

          {/* Section 13.1: Range Comparison Graphic */}
          <RangeComparisonChart
            elexonHeadlineGw={checkData.elexon_headline_gw}
            safeHeadlineGw={checkData.safe_headline_gw}
            actualHeadlineGw={checkData.actual_headline_gw}
            indicativeLowerGw={checkData.indicative_lower_headline_gw}
            indicativeUpperGw={checkData.indicative_upper_headline_gw}
          />

          {/* Section 13.2: Forecast vs Actual Half-Hourly Chart with Amber Shading */}
          <ForecastVsActualChart
            intervals={checkData.intervals}
            targetDate={checkData.target_date}
          />

          {/* Methodology Notes Card */}
          <div className="bg-slate-50 rounded-xl border border-slate-200 p-6 text-xs text-slate-600 space-y-2">
            <h4 className="font-semibold text-slate-900 uppercase tracking-wider text-[11px]">
              Notes on Evaluation Methodology
            </h4>
            <ul className="list-disc list-inside space-y-1 text-slate-500">
              {checkData.methodology_notes.map((note, idx) => (
                <li key={idx}>{note}</li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
};
