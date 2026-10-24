import React, { useEffect, useState } from "react";
import { fetchEstimate } from "../api/client";
import { APP_CONFIG } from "../config";
import { EstimateResponse } from "../types";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { DatePercentileBar } from "../components/DatePercentileBar";
import { ForecastChart } from "../components/ForecastChart";
import { ArrowRight, ShieldCheck, AlertCircle, Info } from "lucide-react";

interface EstimatePageProps {
  initialDate?: string;
  initialPercentile?: number;
  onNavigate: (path: string) => void;
  updateUrl: (date: string, percentile: number) => void;
}

export const EstimatePage: React.FC<EstimatePageProps> = ({
  initialDate = APP_CONFIG.defaultDecisionDate,
  initialPercentile = APP_CONFIG.defaultPercentile,
  onNavigate,
  updateUrl,
}) => {
  const [decisionDate, setDecisionDate] = useState<string>(initialDate);
  const [percentile, setPercentile] = useState<number>(initialPercentile);
  const [estimateData, setEstimateData] = useState<EstimateResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Sync state if props change from URL
  useEffect(() => {
    if (initialDate && initialDate !== decisionDate) setDecisionDate(initialDate);
    if (initialPercentile && initialPercentile !== percentile) setPercentile(initialPercentile);
  }, [initialDate, initialPercentile]);

  // Load estimate data
  useEffect(() => {
    let isCancelled = false;
    setIsLoading(true);
    setErrorMessage(null);

    fetchEstimate(decisionDate, percentile)
      .then((data) => {
        if (!isCancelled) {
          setEstimateData(data);
          setIsLoading(false);
          updateUrl(decisionDate, percentile);
        }
      })
      .catch((err) => {
        if (!isCancelled) {
          setErrorMessage(err.message || "Failed to load estimate.");
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

  const handleGoToCheck = () => {
    onNavigate(`/jan25/check?date=${encodeURIComponent(decisionDate)}&percentile=${percentile}`);
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between pb-6 border-b border-slate-200 gap-4">
        <div>
          <div className="inline-flex items-center space-x-1.5 text-xs text-sky-800 bg-sky-50 px-2.5 py-1 rounded border border-sky-200 font-mono mb-2">
            <span>Historical Replay</span>
            <span>·</span>
            <span>January 2026 (UTC)</span>
            <span>·</span>
            <span>Decision Cutoff: 09:00 UTC</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Estimated wind for tomorrow
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Raw Elexon day-ahead forecast alongside our cautious estimate adjusted for downside risk.
          </p>
        </div>

        {/* CTA to Check Page */}
        {estimateData && !errorMessage && (
          <button
            onClick={handleGoToCheck}
            className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-amber-600 hover:bg-amber-700 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 shrink-0 self-start md:self-auto"
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Check how we did</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </button>
        )}
      </div>

      {/* Date & Percentile Bar */}
      <DatePercentileBar
        decisionDate={decisionDate}
        targetDate={estimateData?.target_date || ""}
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
            <h3 className="text-sm font-bold">Request Failed</h3>
            <p className="text-sm">{errorMessage}</p>
            <p className="text-xs text-red-700">Please choose a valid decision date between 2026-01-01 and 2026-01-30.</p>
          </div>
        </div>
      )}

      {/* Main Headline Cards */}
      {estimateData && !errorMessage && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card 1: Our Safe Estimate */}
            <div className="bg-white rounded-xl border-2 border-slate-900 p-6 shadow-sm relative overflow-hidden">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
                    Our Safe Estimate (Planned)
                  </span>
                  <div className="flex items-baseline space-x-2 mt-2">
                    <span className="text-4xl font-extrabold text-slate-900 font-mono tracking-tight">
                      {estimateData.safe_headline_gw.toFixed(3)}
                    </span>
                    <span className="text-lg font-semibold text-slate-500">GW</span>
                  </div>
                  <span className="text-xs text-slate-400 block mt-0.5">
                    Daily arithmetic average across 48 intervals
                  </span>
                </div>

                <div className="text-right">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                    Indicative Range (p10–p90)
                  </span>
                  <span className="text-sm font-bold font-mono text-sky-800 bg-sky-50 px-2.5 py-1 rounded border border-sky-200 inline-block mt-2">
                    {estimateData.indicative_lower_headline_gw.toFixed(2)} – {estimateData.indicative_upper_headline_gw.toFixed(2)} GW
                  </span>
                </div>
              </div>

              <div className="mt-6 pt-5 border-t border-slate-100">
                <ConfidenceBadge
                  label={estimateData.confidence_label}
                  observationsCount={estimateData.historical_observations_count}
                  historyWeight={estimateData.history_weight}
                  methodologyType={estimateData.methodology_type}
                />
              </div>
            </div>

            {/* Card 2: Raw Elexon Forecast */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-sky-700 block">
                    Elexon Unadjusted Forecast
                  </span>
                  <div className="flex items-baseline space-x-2 mt-2">
                    <span className="text-4xl font-extrabold text-sky-900 font-mono tracking-tight">
                      {estimateData.elexon_headline_gw.toFixed(3)}
                    </span>
                    <span className="text-lg font-semibold text-sky-600">GW</span>
                  </div>
                  <span className="text-xs text-slate-400 block mt-0.5">
                    Daily arithmetic average across same 48 intervals
                  </span>
                </div>

                <div className="text-right">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                    Applied Downward Margin
                  </span>
                  <span className="text-sm font-bold font-mono text-amber-800 bg-amber-50 px-2.5 py-1 rounded border border-amber-200 inline-block mt-2">
                    -{(estimateData.elexon_headline_gw - estimateData.safe_headline_gw).toFixed(3)} GW
                  </span>
                </div>
              </div>

              <div className="mt-6 pt-5 border-t border-slate-100 text-xs text-slate-500 flex items-start space-x-2">
                <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <p>
                  Official unadjusted WINDFOR day-ahead forecast. Our estimate intentionally lowers this figure to safeguard against downside shortfall risk.
                </p>
              </div>
            </div>
          </div>

          {/* Half-Hourly Chart */}
          <ForecastChart
            intervals={estimateData.intervals}
            targetDate={estimateData.target_date}
          />

          {/* Bottom Action Card */}
          <div className="bg-slate-900 text-white rounded-xl p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-sm">
            <div>
              <h3 className="text-lg font-bold">
                Ready to evaluate actual performance?
              </h3>
              <p className="text-sm text-slate-300 mt-1">
                Replay this estimate against real Elexon FUELHH wind generation measurements for target date {estimateData.target_date}.
              </p>
            </div>
            <button
              onClick={handleGoToCheck}
              className="inline-flex items-center space-x-2 px-6 py-3 rounded-lg text-sm font-semibold text-slate-900 bg-sky-400 hover:bg-sky-300 transition-colors shrink-0"
            >
              <span>View Reliability Check</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </>
      )}
    </div>
  );
};
