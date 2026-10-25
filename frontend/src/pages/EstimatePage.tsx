import React, { useEffect, useState } from "react";
import { fetchEstimate } from "../api/client";
import { APP_CONFIG } from "../config";
import { EstimateResponse } from "../types";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { DatePercentileBar } from "../components/DatePercentileBar";
import { ForecastChart } from "../components/ForecastChart";
import { EstimateDeepDive } from "../components/EstimateDeepDive";
import { ArrowRight, AlertCircle, Info, ShieldCheck, AlertTriangle, Scale } from "lucide-react";

interface EstimatePageProps {
  initialDate?: string;
  initialPercentile?: number;
  onNavigate: (path: string) => void;
  updateUrl: (date: string, percentile: number) => void;
}

function formatDateLong(dateStr: string): string {
  if (!dateStr) return "";
  const parts = dateStr.split("-").map(Number);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${parts[2]} ${months[parts[1] - 1]} ${parts[0]}`;
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

  const isEarlyMonth = decisionDate <= "2026-01-03";
  const targetDateFormatted = estimateData ? formatDateLong(estimateData.target_date) : formatDateLong(decisionDate);
  const decisionDateFormatted = formatDateLong(decisionDate);

  const appliedMargin = estimateData
    ? estimateData.elexon_headline_gw - estimateData.safe_headline_gw
    : 0;

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* 1. Hero Section with Prominent Result and Real Dates */}
      <div className="pb-6 border-b border-slate-200 space-y-4">
        {/* Real Dates & Cutoff Mapping */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          <div className="inline-flex items-center space-x-1.5 text-sky-900 bg-sky-50 px-3 py-1 rounded-md border border-sky-200">
            <span className="font-semibold">Decision: {decisionDateFormatted}, 09:00 UTC</span>
            <span>→</span>
            <span className="font-semibold">Target: delivery day, {targetDateFormatted}</span>
          </div>
          <span className="text-slate-400 hidden sm:inline">|</span>
          <span className="text-slate-500">Historical Replay (UTC)</span>
        </div>

        {/* Hero Headline with Big Results */}
        {isLoading && !estimateData ? (
          <div className="py-6 animate-pulse space-y-2">
            <div className="h-10 bg-slate-200 rounded w-1/2"></div>
            <div className="h-4 bg-slate-200 rounded w-1/3"></div>
          </div>
        ) : estimateData ? (
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            <div>
              <div className="flex flex-wrap items-baseline gap-x-4 gap-y-2">
                <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
                  Our estimate for {targetDateFormatted}:{" "}
                  <span className="text-slate-900 font-mono">
                    {estimateData.safe_headline_gw.toFixed(1)} GW
                  </span>
                </h1>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="inline-flex items-center space-x-2 bg-slate-100 text-slate-700 px-3 py-1 rounded-lg border border-slate-200 font-mono text-sm sm:text-base">
                    <span>Elexon forecast: <strong>{estimateData.elexon_headline_gw.toFixed(1)} GW</strong></span>
                    <span className="text-amber-700 font-semibold">({appliedMargin.toFixed(1)} GW margin)</span>
                  </div>
                </div>
              </div>
              <p className="text-sm text-slate-600 mt-2 max-w-3xl leading-relaxed">
                Raw Elexon day-ahead forecast alongside our cautious estimate adjusted for downside risk using strictly data known at the 09:00 UTC cutoff.
              </p>
            </div>
          </div>
        ) : null}
      </div>

      {/* Early-Month Limited History Banner (Jan 1-3) */}
      {isEarlyMonth && !isLoading && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start space-x-3 text-amber-950 text-xs">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block text-sm">Limited history on {decisionDateFormatted}</span>
            <p className="mt-0.5 leading-relaxed">
              Limited history: using a fixed 15% haircut (blended with available outturn until 48 hours accumulate).
            </p>
          </div>
        </div>
      )}

      {/* 2. Decision Date & Risk Percentile Controls (Below the Hero) */}
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

      {/* 3. Transparent Model Comparison Banner */}
      {estimateData && !errorMessage && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 sm:p-5 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-200">
            <div className="flex items-center space-x-2">
              <Scale className="w-4 h-4 text-sky-700" />
              <span className="font-bold text-xs uppercase tracking-wider text-slate-800">
                Headline Model vs Candidate Baselines for {targetDateFormatted}
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-mono">
              Comparing Headline (v1 Additive), Flat 15% Baseline, and v2 Proportional Variant
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            {/* Headline Plan v1 */}
            <div className="p-3.5 bg-white rounded-lg border-2 border-sky-600 shadow-2xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-900 text-sm">Headline Plan (v1 Additive)</span>
                <span className="bg-sky-100 text-sky-800 text-[10px] px-2 py-0.5 rounded font-bold">Active Headline</span>
              </div>
              <div className="text-xl font-bold font-mono text-sky-950">
                {estimateData.safe_headline_gw.toFixed(1)} GW
              </div>
              <p className="text-[11px] text-slate-600 leading-normal">
                Deducts empirical {estimateData.selected_percentile}th signed-error margin ({appliedMargin.toFixed(1)} GW). This headline drives the table, track record, and payoff calculator below.
              </p>
            </div>

            {/* Pre-set Flat 15% Baseline */}
            <div className="p-3.5 bg-white rounded-lg border border-slate-200 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800">Pre-Set Flat 15% Baseline</span>
                <span className="text-[10px] text-emerald-800 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded font-semibold">Beat both in Jan</span>
              </div>
              <div className="text-xl font-bold font-mono text-slate-900">
                {(estimateData.elexon_headline_gw * 0.85).toFixed(1)} GW
              </div>
              <p className="text-[11px] text-slate-600 leading-normal">
                Applies a static 15.0% haircut ({(estimateData.elexon_headline_gw * 0.15).toFixed(1)} GW margin). <strong>Honest evidence note:</strong> A pre-set flat 15% haircut beat both adaptive models over the full January replay (71.2% efficiency vs 49.6% v1 and 53.0% v2).
              </p>
            </div>

            {/* v2 Proportional Variant */}
            <div className="p-3.5 bg-white rounded-lg border border-slate-200 space-y-1">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800">v2 Proportional Variant</span>
                <span className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded font-medium">Post-v1 Variant</span>
              </div>
              <div className="text-xl font-bold font-mono text-slate-900">
                {(estimateData.v2_safe_headline_gw ?? (estimateData.elexon_headline_gw * (1 - (estimateData.v2_ratio ?? 0.15)))).toFixed(1)} GW
              </div>
              <p className="text-[11px] text-slate-600 leading-normal">
                Scales margin proportionally ({(((estimateData.v2_ratio ?? 0.15)) * 100).toFixed(1)}% cut). Formulated after observing v1's high additive cuts during calm weather transitions (e.g. Jan 13–14).
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 4. Main Detail Cards: Plan For vs Likely Range */}
      {estimateData && !errorMessage && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Card 1: Plan For (Cautious) */}
            <div className="bg-white rounded-xl border-2 border-slate-900 p-6 shadow-sm space-y-4">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
                  Recommended Action
                </span>
                <h3 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">
                  Plan for: <span className="font-mono">{estimateData.safe_headline_gw.toFixed(1)} GW</span> (cautious)
                </h3>
              </div>

              <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1.5 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">Elexon Unadjusted Forecast:</span>
                  <span className="font-mono font-semibold text-slate-900">{estimateData.elexon_headline_gw.toFixed(1)} GW</span>
                </div>
                <div className="flex justify-between items-center text-amber-800 font-medium">
                  <span>Applied Downward Margin:</span>
                  <span className="font-mono font-bold">{appliedMargin.toFixed(1)} GW</span>
                </div>
                <div className="pt-1.5 border-t border-slate-200/80 text-[11px] text-slate-500">
                  <button
                    onClick={() => onNavigate("/docs#replay")}
                    className="text-sky-700 hover:underline inline-block text-left cursor-pointer"
                  >
                    Margin from the previous 48h of errors (see Methodology)
                  </button>
                </div>
              </div>

              {/* History Used Indicator */}
              <div className="pt-2 border-t border-slate-100">
                <ConfidenceBadge
                  label={estimateData.confidence_label}
                  observationsCount={estimateData.historical_observations_count}
                  historyWeight={estimateData.history_weight}
                  methodologyType={estimateData.methodology_type}
                />
              </div>
            </div>

            {/* Card 2: Likely Range from the Last 48h of Errors */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 block">
                  Error Spread Context
                </span>
                <h3 className="text-xl sm:text-2xl font-bold text-slate-900 mt-1">
                  Likely range, from the last 48h of errors:{" "}
                  <span className="font-mono text-sky-800">
                    {estimateData.indicative_lower_headline_gw.toFixed(1)}–{estimateData.indicative_upper_headline_gw.toFixed(1)} GW
                  </span>
                </h3>
              </div>

              {/* Directional error context & Leakage Line */}
              <div className="p-3.5 bg-sky-50/60 rounded-lg border border-sky-200 space-y-2 text-xs text-sky-950">
                <div className="flex items-start space-x-2">
                  <Info className="w-4 h-4 text-sky-700 shrink-0 mt-0.5" />
                  <p className="leading-relaxed">
                    {estimateData.historical_observations_count === 0
                      ? "No calibration history available before decision cutoff (cold start); applying a fixed 15% margin."
                      : estimateData.error_distribution?.overforecast_pct === 100.0
                      ? `Elexon's forecast ran above FUELHH outturn in all of the last ${estimateData.historical_observations_count} half-hours (100% of calibration observations before the ${decisionDateFormatted} cutoff ran above metered actuals), which widens the cautionary margin.`
                      : `Elexon's forecast ran above FUELHH outturn in ${estimateData.error_distribution?.overforecast_count ?? 0} of the last ${estimateData.historical_observations_count} half-hours (${estimateData.error_distribution?.overforecast_pct ?? 0}% of calibration observations before the ${decisionDateFormatted} cutoff), which informs the cautionary margin.`}
                  </p>
                </div>
                <div className="pt-2 border-t border-sky-200/80 flex items-center space-x-1.5 text-[11px] font-mono text-sky-900">
                  <ShieldCheck className="w-3.5 h-3.5 text-sky-700 shrink-0" />
                  <span>No forecasts published or actuals recorded after 09:00 UTC on the decision day are used.</span>
                </div>
              </div>

              <p className="text-[11px] text-slate-400 italic">
                * Note: The likely range reflects historical 10th–90th error quantiles; our estimate sits conservatively near the bottom of this range to protect against shortfall.
              </p>
            </div>
          </div>

          {/* 4. Half-Hourly Forecast Chart */}
          <ForecastChart
            intervals={estimateData.intervals}
            targetDate={estimateData.target_date}
          />

          {/* 5. Deep-Dive: Evidence, Calibration, Trade-offs & Limits */}
          <EstimateDeepDive
            estimateData={estimateData}
            onPercentileChange={handlePercentileChange}
            onNavigateDocs={() => onNavigate("/docs#replay")}
          />

          {/* 6. Bottom Action Card (Single Button to Check Page) */}
          <div className="bg-slate-900 text-white rounded-xl p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-sm">
            <div>
              <h3 className="text-lg font-bold">
                Ready to evaluate actual performance?
              </h3>
              <p className="text-sm text-slate-300 mt-1">
                Replay this estimate against real Elexon FUELHH wind generation measurements for target date {targetDateFormatted} ({estimateData.target_date}).
              </p>
            </div>
            <button
              onClick={handleGoToCheck}
              className="inline-flex items-center space-x-2 px-6 py-3 rounded-lg text-sm font-semibold text-slate-900 bg-sky-400 hover:bg-sky-300 transition-colors shrink-0 cursor-pointer shadow-sm"
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
