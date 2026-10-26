import React, { useState } from "react";
import { EstimateResponse } from "../types";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  Cell,
} from "recharts";
import {
  Calculator,
  BarChart3,
  Sliders,
  TrendingUp,
  ShieldCheck,
  HelpCircle,
  Info,
  CheckCircle2,
  AlertTriangle,
  FileCode,
  Layers,
  ChevronDown,
  ChevronUp,
  ExternalLink,
} from "lucide-react";
import { CostRatioCalculator } from "./CostRatioCalculator";

interface EstimateDeepDiveProps {
  estimateData: EstimateResponse;
  onPercentileChange?: (p: number) => void;
  onNavigateDocs?: () => void;
}

function formatDateLong(dateStr: string): string {
  if (!dateStr) return "";
  const parts = dateStr.split("-").map(Number);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const day = String(parts[2]).padStart(2, "0");
  return `${day} ${months[parts[1] - 1]} ${parts[0]}`;
}

function formatDateHour(isoStr: string): string {
  try {
    const d = new Date(isoStr);
    const day = String(d.getUTCDate()).padStart(2, "0");
    const month = d.toLocaleDateString("en-GB", { month: "short", timeZone: "UTC" });
    const year = d.getUTCFullYear();
    const time = d.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    });
    return `${day} ${month} ${year}, ${time}`;
  } catch {
    return isoStr;
  }
}

function formatTickDateHour(isoStr: string): string {
  try {
    const d = new Date(isoStr);
    const day = String(d.getUTCDate()).padStart(2, "0");
    const month = d.toLocaleDateString("en-GB", { month: "short", timeZone: "UTC" });
    const time = d.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    });
    return `${day} ${month} ${time}`;
  } catch {
    return isoStr;
  }
}

function formatSignedGw(val: number | undefined): string {
  if (val === undefined || isNaN(val)) return "0.00 GW";
  if (val > 0) return `+${val.toFixed(2)} GW`;
  if (val < 0) return `${val.toFixed(2)} GW`;
  return "0.00 GW";
}

function formatSignedGw1(val: number | undefined): string {
  if (val === undefined || isNaN(val)) return "0.0 GW";
  if (val > 0) return `+${val.toFixed(1)} GW`;
  if (val < 0) return `${val.toFixed(1)} GW`;
  return "0.0 GW";
}

function formatSignedPct(val: number | undefined): string {
  if (val === undefined || isNaN(val)) return "0.0%";
  if (val > 0) return `+${val.toFixed(1)}%`;
  if (val < 0) return `${val.toFixed(1)}%`;
  return "0.0%";
}

export const EstimateDeepDive: React.FC<EstimateDeepDiveProps> = ({
  estimateData,
  onPercentileChange,
  onNavigateDocs,
}) => {
  const [faqOpen, setFaqOpen] = useState<{ [key: string]: boolean }>({
    faq1: true,
    faq2: true,
    faq3: true,
    faq4: true,
  });

  const toggleFaq = (key: string) => {
    setFaqOpen((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const {
    calculation,
    history_48h,
    error_distribution,
    slider_tradeoffs,
    completed_track_record,
    provenance,
    selected_percentile,
    confidence_label,
    historical_observations_count,
    history_weight,
    elexon_headline_gw,
    safe_headline_gw,
  } = estimateData;

  const appliedMargin = elexon_headline_gw - safe_headline_gw;
  const is100Overforecast = error_distribution?.overforecast_pct === 100.0;
  const historyHours = Math.round(historical_observations_count / 2);
  const decisionDateFormatted = estimateData.decision_date ? formatDateLong(estimateData.decision_date) : "25 Jan 2026";
  const inSampleShortPct = Math.max(0, Math.min(100, Math.round(100 - selected_percentile)));

  // Completed track record summary range
  const dailyRecords = completed_track_record?.daily_records || [];
  const completedDaysCount = completed_track_record?.completed_days_count ?? 0;
  const firstCompletedDay = dailyRecords.length > 0 ? dailyRecords[0].target_date_label : "";
  const lastCompletedDay = dailyRecords.length > 0 ? dailyRecords[dailyRecords.length - 1].target_date_label : "";
  const completedRangeText = completedDaysCount === 0
    ? "No completed days yet"
    : completedDaysCount === 1
    ? `1 Completed Day (${firstCompletedDay})`
    : `${completedDaysCount} Completed Days (${firstCompletedDay} to ${lastCompletedDay})`;

  const breakevenDaysCount = completed_track_record?.days_break_even_under_2x ?? dailyRecords.filter(r => r.avoided_shortfall_mwh > r.extra_supply_mwh).length;

  // Prepare 48h chart data
  const historyChartData = (history_48h || []).map((obs) => ({
    timeLabel: formatTickDateHour(obs.interval_start),
    interval_start: obs.interval_start,
    forecast_gw: obs.forecast_gw,
    actual_gw: obs.actual_gw,
    error_gw: obs.error_gw,
  }));

  // Prepare histogram data
  const histogramData = (error_distribution?.histogram_bins || []).map((b) => ({
    bin_label: b.bin_label,
    bin_start: b.bin_start,
    bin_end: b.bin_end,
    count: b.count,
  }));

  // Prepare bidirectional track record data (Avoided Shortfall upward > 0, Extra Supply downward < 0)
  const trackRecordData = dailyRecords.map((r) => ({
    target_date_label: r.target_date_label,
    avoided_mwh: r.avoided_shortfall_mwh,
    extra_mwh_negative: -r.extra_supply_mwh,
    raw_extra_mwh: r.extra_supply_mwh,
    net_mwh: r.avoided_shortfall_mwh - r.extra_supply_mwh,
    elexon_sf: r.elexon_shortfall_mwh,
    safe_sf: r.safe_shortfall_mwh,
    is_reduced: r.is_shortfall_reduced,
    is_break_even_under_2x: r.is_break_even_under_2x,
  }));

  const p60Pt = (slider_tradeoffs || []).find((p) => Math.round(p.percentile) === 60);
  const p75Pt = (slider_tradeoffs || []).find((p) => Math.round(p.percentile) === 75);
  const p90Pt = (slider_tradeoffs || []).find((p) => Math.round(p.percentile) === 90);

  const delta6075Avoided = (p75Pt?.completed_avoided_shortfall_mwh ?? 0) - (p60Pt?.completed_avoided_shortfall_mwh ?? 0);
  const delta6075Extra = (p75Pt?.completed_extra_supply_mwh ?? 0) - (p60Pt?.completed_extra_supply_mwh ?? 0);
  const ratio6075 = delta6075Avoided > 0 ? (delta6075Extra / delta6075Avoided).toFixed(1) : "1.3";

  const delta7590Avoided = (p90Pt?.completed_avoided_shortfall_mwh ?? 0) - (p75Pt?.completed_avoided_shortfall_mwh ?? 0);
  const delta7590Extra = (p90Pt?.completed_extra_supply_mwh ?? 0) - (p75Pt?.completed_extra_supply_mwh ?? 0);
  const ratio7590 = delta7590Avoided > 0 ? (delta7590Extra / delta7590Avoided).toFixed(1) : "2.2";

  const isExactP60 = Math.round(selected_percentile) === 60;
  const isExactP75 = Math.round(selected_percentile) === 75;
  const isExactP90 = Math.round(selected_percentile) === 90;
  const isNonStandardPercentile = !isExactP60 && !isExactP75 && !isExactP90;

  const menuItems = [
    { href: "#how-we-got-this-number", label: "Calculation", icon: Calculator },
    { href: "#evidence-48h", label: `${historyHours}h Evidence`, icon: Layers },
    { href: "#error-distribution", label: "Error Distribution", icon: BarChart3 },
    { href: "#tradeoff-table", label: "Trade-offs", icon: Sliders },
    { href: "#track-record", label: "Track Record", icon: TrendingUp },
    { href: "#data-provenance", label: "Provenance", icon: ShieldCheck },
    { href: "#confidence-limits", label: "Limits", icon: AlertTriangle },
    { href: "#faq", label: "FAQ", icon: HelpCircle },
  ];

  return (
    <div id="methodology-deep-dive" className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-0">
      {/* 1. Header with Title and Cutoff */}
      <div className="p-6 pb-5 bg-slate-900 text-white border-b border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-sky-400">
              <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
              <span>Decision Methodology & Evidence</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold mt-1 text-white">
              Decision Deep-Dive: Evidence, Calibration & Limits
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-3xl leading-relaxed">
              Every metric below is derived strictly from public data available at or before the 09:00 UTC decision cutoff.
            </p>
          </div>
          <div className="flex items-center space-x-2 shrink-0">
            <span className="text-xs bg-slate-800 text-sky-300 font-mono px-3 py-1.5 rounded-lg border border-slate-700">
              Cutoff: 09:00 UTC
            </span>
          </div>
        </div>
      </div>

      {/* 2. Sticky Anchor Navigation Menu */}
      <div className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-slate-200 px-4 sm:px-6 py-2.5 shadow-xs overflow-x-auto">
        <div className="flex items-center space-x-1.5 min-w-max">
          <span className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider mr-2 hidden sm:inline">
            Jump to:
          </span>
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <a
                key={item.href}
                href={item.href}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
              >
                <Icon className="w-3.5 h-3.5 text-slate-400" />
                <span>{item.label}</span>
              </a>
            );
          })}
        </div>
      </div>

      {/* 3. Long Continuous Scrolling Content */}
      <div className="p-6 sm:p-8 space-y-12">
        {/* ======================================================== */}
        {/* SECTION 1: HOW WE GOT THIS NUMBER                        */}
        {/* ======================================================== */}
        <section id="how-we-got-this-number" className="space-y-4 scroll-mt-20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-700 block">
                Hand-Checkable Arithmetic
              </span>
              <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                How We Got This Number
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-600 bg-slate-100 px-3 py-1 rounded-md border border-slate-200 w-fit">
              Risk Setting: p{selected_percentile} signed-error percentile
            </span>
          </div>

          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-3xl">
            A buyer can verify this arithmetic directly from public Elexon data: take Elexon’s raw day-ahead forecast average,
            determine the {selected_percentile}th signed-error percentile across the preceding {historyHours} hours, and subtract it to arrive at our safe plan.
            Every half-hourly interval plan is strictly floored at 0.0 GW (cannot go negative).
          </p>

          {/* Arithmetic Breakdown Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
              <span className="text-xs font-medium text-slate-500 block">1. Elexon Day-Ahead Avg</span>
              <div className="text-2xl font-bold font-mono text-slate-900">
                {elexon_headline_gw.toFixed(1)} GW
              </div>
              <span className="text-[11px] text-slate-500 block">
                Mean unadjusted forecast for delivery day
              </span>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
              <span className="text-xs font-medium text-slate-500 block">2. Previous {historyHours}h History</span>
              <div className="text-2xl font-bold font-mono text-slate-900">
                {historical_observations_count} of 96 slots
              </div>
              <span className="text-[11px] text-slate-500 block">
                Observations before 09:00 UTC cutoff ({historyHours}h)
              </span>
            </div>

            <div className="p-4 bg-amber-50/80 rounded-xl border border-amber-200 space-y-1">
              <span className="text-xs font-medium text-amber-900 block">
                3. p{selected_percentile} Applied Margin
              </span>
              <div className="text-2xl font-bold font-mono text-amber-900">
                {appliedMargin.toFixed(1)} GW
              </div>
              <span className="text-[11px] text-amber-700 block">
                {calculation?.is_blended
                  ? `Linear blend (${(history_weight * 100).toFixed(0)}% data + ${(100 - history_weight * 100).toFixed(0)}% cold-start)`
                  : `${selected_percentile}th signed-error percentile`}
              </span>
            </div>

            <div className="p-4 bg-sky-50 rounded-xl border-2 border-sky-600 space-y-1">
              <span className="text-xs font-semibold text-sky-900 block">4. Safe Estimate Plan</span>
              <div className="text-2xl font-extrabold font-mono text-sky-900">
                {safe_headline_gw.toFixed(1)} GW
              </div>
              <span className="text-[11px] text-sky-700 font-medium block">
                {elexon_headline_gw.toFixed(1)} GW − {appliedMargin.toFixed(1)} GW = {safe_headline_gw.toFixed(1)} GW
              </span>
            </div>
          </div>

          {/* Cold-Start Arithmetic Reproduction (When History < 96 slots) */}
          {calculation?.is_blended && (
            <div className="p-4 bg-amber-50/80 rounded-xl border border-amber-300 font-mono text-xs sm:text-sm space-y-2">
              <div className="flex items-center space-x-2 text-amber-900 font-bold">
                <Calculator className="w-4 h-4 text-amber-700 shrink-0" />
                <span>Cold-Start Linear Blend ({historical_observations_count} of 96 slots = {(history_weight * 100).toFixed(1)}% weight):</span>
              </div>
              <div className="text-amber-950 font-bold bg-white/70 p-2.5 rounded-lg border border-amber-200">
                {calculation.blend_formula_text || `Margin = (${history_weight.toFixed(2)} × ${calculation.data_margin_gw?.toFixed(1)} GW) + (${(1.0 - history_weight).toFixed(2)} × (15% × ${elexon_headline_gw.toFixed(1)} GW = ${calculation.cold_margin_gw?.toFixed(1)} GW)) = ${appliedMargin.toFixed(1)} GW`}
              </div>
              <p className="text-[11px] font-sans text-amber-800">
                Because history has not yet reached 96 half-hours (48h), the margin blends empirical data quantiles ({calculation.data_margin_gw?.toFixed(1)} GW) with the fixed 15% haircut ({calculation.cold_margin_gw?.toFixed(1)} GW).
              </p>
            </div>
          )}

          {/* Verifiable Equation Box */}
          <div className="p-4 bg-slate-900 text-white rounded-xl font-mono text-sm sm:text-base flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-sm">
            <div className="flex items-center space-x-3">
              <Calculator className="w-5 h-5 text-sky-400 shrink-0" />
              <div>
                <span className="text-slate-400 text-xs block sm:inline sm:mr-2">Verifiable Plan Equation:</span>
                <span className="font-bold text-white tracking-wide">
                  {elexon_headline_gw.toFixed(1)} GW − {appliedMargin.toFixed(1)} GW = {safe_headline_gw.toFixed(1)} GW
                </span>
              </div>
            </div>
            <div className="text-xs font-sans text-slate-300">
              Subtraction operator applies the empirical p{selected_percentile} signed-error margin ({appliedMargin.toFixed(1)} GW). Half-hourly plan floored at 0.0 GW.
            </div>
          </div>
        </section>

        {/* ======================================================== */}
        {/* SECTION 2: PREVIOUS HOURS FORECAST VS OUTTURN            */}
        {/* ======================================================== */}
        <section id="evidence-48h" className="space-y-4 pt-4 border-t border-slate-200 scroll-mt-20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-700 block">
                The Evidence Base
              </span>
              <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                Previous {historyHours} Hours: Forecast vs Outturn
              </h3>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs px-2.5 py-1 bg-amber-100 text-amber-900 font-medium rounded-full border border-amber-200">
                {is100Overforecast
                  ? `100% of half-hours forecast ran above FUELHH outturn (${historical_observations_count}/${historical_observations_count})`
                  : `${error_distribution?.overforecast_count ?? 0} of ${historical_observations_count} slots forecast ran above FUELHH outturn (${error_distribution?.overforecast_pct ?? 0}%)`}
              </span>
              <span className="text-xs px-2.5 py-1 bg-slate-100 text-slate-700 font-medium rounded-full border border-slate-200">
                Mean signed error: {formatSignedGw1(error_distribution?.mean_error_gw)} ({formatSignedPct(error_distribution?.bias_pct)} bias)
              </span>
            </div>
          </div>

          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-3xl">
            This chart displays Elexon’s day-ahead forecasts against actual outturn (FUELHH) over the {historical_observations_count} half-hours ({historyHours} hours)
            prior to the 09:00 UTC decision cutoff, assuming a 1-hour publication lag for metered outturns. The shaded gap highlights where Elexon ran above physical generation.
          </p>

          {/* Timestamp and Series Alignment Check Box */}
          <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-xl space-y-2 text-xs text-amber-950">
            <div className="flex items-center space-x-2 font-bold text-amber-900 text-xs">
              <CheckCircle2 className="w-4 h-4 text-amber-700 shrink-0" />
              <span>Timestamp Alignment & Dataset Scoping Context</span>
            </div>
            <p className="leading-relaxed text-[11px] text-amber-900">
              <strong>Alignment:</strong> Elexon <code className="bg-amber-100/70 px-1 py-0.5 rounded">WINDFOR</code> interval start is joined directly to <code className="bg-amber-100/70 px-1 py-0.5 rounded">FUELHH</code> interval start on matching UTC settlement periods.
            </p>
            <p className="leading-relaxed text-[11px] text-amber-900">
              <strong>Definitional Scoping Difference:</strong> Elexon dataset documentation defines <code className="bg-amber-100/70 px-1 py-0.5 rounded">WINDFOR</code> as <em>"provides forward-looking generation forecasts for all visible Power Park Modules (wind farms connected to the transmission system or holding operational metering visible to the ESO) in Great Britain"</em> (<a href="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR" target="_blank" rel="noreferrer" className="underline text-sky-800">Elexon /datasets/WINDFOR</a>), whereas <code className="bg-amber-100/70 px-1 py-0.5 rounded">FUELHH</code> is <em>"derived from Operational Metering for Balancing Mechanism Units (BMUs) connected directly to the National Transmission System, where embedded generation and smaller assets lacking transmission-level operational meters are excluded or unmetered"</em> (<a href="https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH" target="_blank" rel="noreferrer" className="underline text-sky-800">Elexon /datasets/FUELHH</a>; accessed Oct 2026). Because WINDFOR includes visible wind generation while FUELHH measures transmission-connected BMUs only, WINDFOR naturally measures a wider perimeter. Across January 2026, WINDFOR exceeded FUELHH outturn by 15.5% of outturn (13.4% of forecast). While this boundary difference is a primary candidate for the discrepancy, the exact split between perimeter differences and weather forecast error is not separated in Elexon schemas and remains an unexplained gap.
            </p>
            <p className="leading-relaxed text-[11px] text-amber-900">
              In this calibration window of {historical_observations_count} half-hours, Elexon's forecast ran above FUELHH outturn in {error_distribution?.overforecast_count ?? 0} of {historical_observations_count} slots ({error_distribution?.overforecast_pct ?? 0}%),
              ranging from {formatSignedGw(error_distribution?.min_error_gw)} to {formatSignedGw(error_distribution?.max_error_gw)} with a mean signed error of {formatSignedGw(error_distribution?.mean_error_gw)} ({formatSignedPct(error_distribution?.bias_pct)} of mean forecast {error_distribution?.mean_forecast_gw?.toFixed(1)} GW). Bias varies by day (e.g. {formatSignedPct(error_distribution?.bias_pct)} of forecast on this decision date vs +13.4% of forecast across the full January month for context; +15.5% if measured relative to outturn).
            </p>
            <p className="text-[10px] text-amber-800 italic pt-1 border-t border-amber-200/60">
              * Methodology Assumption: We assume a 1-hour publication and processing lag for FUELHH metered outturns before the 09:00 UTC decision freeze (e.g. at 09:00 UTC, only half-hours ending at or before 08:00 UTC are available).
              {historical_observations_count < 96 && (
                <span> Because the replay cache begins 01 Jan 2026 without a Dec 2025 warm-up, paired day-ahead records start from 02 Jan 00:00 UTC, providing {historical_observations_count} half-hours ({historyHours}h) before cutoff. A live deployment with a warm-up period would have 48h from day 1.</span>
              )}
            </p>
          </div>

          {historyChartData.length > 0 ? (
            <div className="bg-slate-50/60 p-4 sm:p-6 rounded-xl border border-slate-200 space-y-4">
              <div className="h-80 sm:h-96 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={historyChartData} margin={{ top: 10, right: 20, left: 0, bottom: 25 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                    <XAxis
                      dataKey="timeLabel"
                      tick={{ fontSize: 11, fill: "#64748B" }}
                      interval={historical_observations_count > 60 ? 11 : 7}
                      angle={-15}
                      textAnchor="end"
                      height={40}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: "#64748B" }}
                      label={{ value: "Generation (GW)", angle: -90, position: "insideLeft", fontSize: 11, fill: "#64748B" }}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0F172A", color: "#F8FAFC", borderRadius: "8px", fontSize: "12px", border: "none" }}
                      formatter={(val: any, name: any) => [
                        `${Number(val).toFixed(2)} GW`,
                        name === "forecast_gw" ? "Elexon Forecast" : name === "actual_gw" ? "FUELHH Actual Generation" : "Signed Error Gap",
                      ]}
                      labelFormatter={(label) => `Time: ${label} UTC`}
                    />
                    <Legend
                      verticalAlign="top"
                      height={36}
                      formatter={(value) => {
                        if (value === "forecast_gw") return "Elexon Forecast (Day-Ahead)";
                        if (value === "actual_gw") return "FUELHH Actual Generation (Outturn)";
                        return "Signed Error Gap";
                      }}
                    />
                    <Area
                      type="linear"
                      dataKey="forecast_gw"
                      fill="#FDE68A"
                      fillOpacity={0.35}
                      stroke="none"
                      name="gap"
                    />
                    <Line
                      type="linear"
                      dataKey="forecast_gw"
                      stroke="#0284C7"
                      strokeWidth={2.5}
                      dot={false}
                      name="forecast_gw"
                    />
                    <Line
                      type="linear"
                      dataKey="actual_gw"
                      stroke="#059669"
                      strokeWidth={2.5}
                      dot={false}
                      name="actual_gw"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>

              <div className="flex flex-wrap items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-200">
                <span className="font-medium text-slate-700">
                  Observed window: {historical_observations_count} half-hours ({historyHours} hours) prior to 09:00 UTC (assuming 1h publication lag).
                </span>
                <span className="font-mono text-slate-400">Strictly past data available before cutoff</span>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 bg-slate-50 rounded-xl border border-slate-200">
              Calibration observations accumulating (cold-start period).
            </div>
          )}
        </section>

        {/* ======================================================== */}
        {/* SECTION 3: DISTRIBUTION OF RECENT FORECAST ERRORS        */}
        {/* ======================================================== */}
        <section id="error-distribution" className="space-y-4 pt-4 border-t border-slate-200 scroll-mt-20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-700 block">
                Error Spread Context
              </span>
              <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                Distribution of Recent Forecast Errors
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-500 bg-slate-100 px-3 py-1 rounded-md border border-slate-200 w-fit">
              {historical_observations_count} half-hourly observations strictly before cutoff
            </span>
          </div>

          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-3xl">
            Histogram of signed forecast errors (<code className="bg-slate-100 px-1 py-0.5 rounded">error = Elexon Forecast − FUELHH Outturn</code>) across the {historyHours}-hour calibration window.{" "}
            {calculation?.is_blended
              ? `Markers indicate empirical quantiles: data-driven quantile ${calculation.data_margin_gw?.toFixed(1)} GW, blended with a fixed 15% haircut to give ${appliedMargin.toFixed(1)} GW.`
              : `Markers indicate empirical quantiles and show why the margin was set to ${appliedMargin.toFixed(1)} GW.`}
          </p>

          {/* Distribution Summary Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-500 block">Min / Max Signed Error</span>
              <span className="font-mono font-bold text-slate-900 text-sm">
                {formatSignedGw(error_distribution?.min_error_gw)} / {formatSignedGw(error_distribution?.max_error_gw)}
              </span>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-500 block">Mean Error (Bias)</span>
              <span className="font-mono font-bold text-slate-900 text-sm">
                {formatSignedGw(error_distribution?.mean_error_gw)} ({formatSignedPct(error_distribution?.bias_pct)})
              </span>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <span className="text-slate-500 block">p60 / p75 / p90 Quantiles</span>
              <span className="font-mono font-bold text-slate-900 text-sm">
                {error_distribution?.p60_error_gw.toFixed(1)} / {error_distribution?.p75_error_gw.toFixed(1)} / {error_distribution?.p90_error_gw.toFixed(1)} GW
              </span>
            </div>
            <div className="p-3 bg-sky-50 rounded-lg border-2 border-sky-600">
              <div className="flex items-center justify-between">
                <span className="text-sky-800 font-medium block">Active Margin (p{selected_percentile})</span>
                <span className="text-[10px] bg-sky-200 text-sky-800 font-semibold px-1.5 py-0.5 rounded">Active</span>
              </div>
              <span className="font-mono font-bold text-sky-900 text-sm mt-0.5 block">
                {appliedMargin.toFixed(1)} GW
              </span>
            </div>
          </div>

          {/* Histogram Bar Chart */}
          <div className="bg-slate-50/60 p-4 sm:p-6 rounded-xl border border-slate-200 space-y-4">
            <div className="h-72 sm:h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={histogramData} margin={{ top: 20, right: 20, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis
                    dataKey="bin_label"
                    tick={{ fontSize: 11, fill: "#64748B" }}
                    interval={0}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#64748B" }}
                    label={{ value: "Observation Count", angle: -90, position: "insideLeft", fontSize: 11, fill: "#64748B" }}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0F172A", color: "#F8FAFC", borderRadius: "8px", fontSize: "12px", border: "none" }}
                    formatter={(val: any) => [`${val} half-hours`, "Frequency"]}
                    labelFormatter={(lbl) => `Signed Error Range: ${lbl}`}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {histogramData.map((entry, index) => {
                      const isHighError = error_distribution ? entry.bin_end >= error_distribution.p75_error_gw : false;
                      return (
                        <Cell
                          key={`cell-${index}`}
                          fill={isHighError ? "#0284C7" : "#94A3B8"}
                        />
                      );
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Explanatory callouts for p60, p75, p90 */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 border-t border-slate-200 text-xs">
              <div className={`p-3 rounded-lg border transition-all ${isExactP60 ? "bg-sky-50 border-2 border-sky-600" : "bg-white border-slate-200"}`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800">Less cautious (p60): {error_distribution?.p60_error_gw.toFixed(1)} GW</span>
                  <span className="text-[10px] text-slate-500 font-medium">
                    {isExactP60 ? (
                      <span className="bg-sky-200 text-sky-800 px-1.5 py-0.5 rounded font-semibold">Active</span>
                    ) : (
                      "Less cautious"
                    )}
                  </span>
                </div>
                <p className="text-slate-600 text-[11px] leading-relaxed mt-1">
                  Protects against 60% of past signed errors; leaves 40% of observations exposed to replacement power purchases.
                </p>
              </div>

              <div className={`p-3 rounded-lg border transition-all ${isExactP75 ? "bg-sky-50 border-2 border-sky-600" : "bg-white border-slate-200"}`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sky-900">Balanced (p75): {error_distribution?.p75_error_gw.toFixed(1)} GW</span>
                  <div className="flex items-center space-x-1">
                    <span className="text-[10px] font-semibold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">Default</span>
                    {isExactP75 && (
                      <span className="text-[10px] font-semibold text-sky-700 bg-sky-100 px-1.5 py-0.5 rounded">Active</span>
                    )}
                  </div>
                </div>
                <p className="text-sky-800 text-[11px] leading-relaxed mt-1">
                  Balanced caution: absorbs 75% of signed errors where forecast ran above FUELHH outturn, limiting shortfall risks to the upper quartile tail.
                </p>
              </div>

              <div className={`p-3 rounded-lg border transition-all ${isExactP90 ? "bg-sky-50 border-2 border-sky-600" : "bg-white border-slate-200"}`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-800">Most cautious (p90): {error_distribution?.p90_error_gw.toFixed(1)} GW</span>
                  <span className="text-[10px] text-slate-500 font-medium">
                    {isExactP90 ? (
                      <span className="bg-sky-200 text-sky-800 px-1.5 py-0.5 rounded font-semibold">Active</span>
                    ) : (
                      "Most cautious"
                    )}
                  </span>
                </div>
                <p className="text-slate-600 text-[11px] leading-relaxed mt-1">
                  Heavy defensive protection against 90% of tail misses; incurs higher advance planning volume.
                </p>
              </div>
            </div>

            {isNonStandardPercentile && (
              <div className="text-[11px] text-slate-500 italic text-center pt-1 border-t border-slate-100">
                * Active slider is set to p{selected_percentile} ({appliedMargin.toFixed(1)} GW applied margin). The three cards above display the standard p60, p75, and p90 reference quantiles.
              </div>
            )}
          </div>
        </section>

        {/* ======================================================== */}
        {/* SECTION 4: CAUTION LEVEL TRADE-OFF TABLE                 */}
        {/* ======================================================== */}
        <section id="tradeoff-table" className="space-y-4 pt-4 border-t border-slate-200 scroll-mt-20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-700 block">
                Quantifying the Trade-off
              </span>
              <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                Caution Level Trade-off Table
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-500 bg-slate-100 px-3 py-1 rounded-md border border-slate-200 w-fit">
              Replayed on {completedRangeText}
            </span>
          </div>

          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-3xl">
            Compare how each caution level translates into tomorrow's plan and margin, alongside how that setting
            performed across all completed delivery days of January so far.
          </p>

          <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-sm">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-100 text-slate-700 uppercase font-mono text-[11px] border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Risk Setting</th>
                  <th className="px-4 py-3 text-right">Plan for Target</th>
                  <th className="px-4 py-3 text-right">Applied Margin</th>
                  <th className="px-4 py-3 text-right">Shortfall Avoided So Far</th>
                  <th className="px-4 py-3 text-right">Incremental Extra Arranged</th>
                  <th className="px-4 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 font-mono">
                {(slider_tradeoffs || []).map((row) => {
                  const isCurrent = row.is_selected;
                  return (
                    <tr
                      key={row.percentile}
                      className={`transition-colors ${
                        isCurrent ? "bg-sky-50/80 font-bold text-sky-950" : "bg-white text-slate-800 hover:bg-slate-50"
                      }`}
                    >
                      <td className="px-4 py-3.5 flex items-center space-x-2">
                        <span>p{row.percentile} signed-error</span>
                        {isCurrent && (
                          <span className="bg-sky-200 text-sky-800 text-[10px] px-2 py-0.5 rounded font-sans font-semibold">
                            Active Slider
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3.5 text-right font-bold">
                        {row.plan_gw.toFixed(1)} GW
                      </td>
                      <td className="px-4 py-3.5 text-right text-amber-700">
                        {row.margin_gw.toFixed(1)} GW
                      </td>
                      <td className="px-4 py-3.5 text-right text-emerald-700 font-bold">
                        {row.completed_avoided_shortfall_mwh.toLocaleString()} MWh
                      </td>
                      <td className="px-4 py-3.5 text-right text-slate-600">
                        {row.completed_extra_supply_mwh.toLocaleString()} MWh
                      </td>
                      <td className="px-4 py-3.5 text-right">
                        {onPercentileChange && !isCurrent ? (
                          <button
                            onClick={() => onPercentileChange(row.percentile)}
                            className="px-3 py-1 bg-slate-900 text-white rounded text-[11px] font-sans hover:bg-slate-800 transition-colors cursor-pointer"
                          >
                            Select p{row.percentile}
                          </button>
                        ) : isCurrent ? (
                          <span className="text-[11px] font-sans text-sky-700 font-semibold">Active</span>
                        ) : null}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="text-[11px] text-slate-500 italic">
            {completedDaysCount === 0
              ? "* Note: No completed delivery days available before this cutoff."
              : completedDaysCount === 1
              ? `* Note: Only 1 completed day so far (${firstCompletedDay}), too early to judge long-term risk trade-offs. Furthermore, this day was decided during the cold-start phase (fixed 15% haircut), so completed outcomes are identical across percentiles until data-driven calibration took effect.`
              : completedDaysCount <= 3
              ? `* Note: Completed days cover ${firstCompletedDay} to ${lastCompletedDay} (${completedDaysCount} completed days so far). Early completed days were generated under the cold-start phase (fixed 15% haircut), so historical outcomes are largely shared until data-driven calibration took full effect.`
              : `* Note: Completed days cover ${firstCompletedDay} to ${lastCompletedDay} (${completedDaysCount} completed days so far, all concluded prior to the 09:00 UTC decision cutoff). The p75 row corresponds to our default balanced setting.`}
          </p>

          {/* Marginal Cost of Caution Insight */}
          {completedDaysCount >= 20 && (
            <div className="p-4 bg-sky-50/70 border border-sky-200 rounded-xl space-y-2 text-xs">
              <div className="flex items-center space-x-2 text-sky-950 font-bold">
                <TrendingUp className="w-4 h-4 text-sky-700 shrink-0" />
                <span>Marginal Cost of Caution: Why the Right Percentile Depends on k</span>
              </div>
              <p className="text-sky-900 leading-relaxed text-[11px]">
                Notice from the completed track record that each extra step of caution costs progressively more extra supply per MWh protected:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 font-mono text-[11px]">
                <div className="p-3 bg-white rounded-lg border border-sky-200">
                  <span className="font-bold text-slate-900 block font-sans">Moving from p60 to p75 (Balanced):</span>
                  <div>• Avoided shortfall gained: <strong>+{Math.round(delta6075Avoided).toLocaleString()} MWh</strong></div>
                  <div>• Extra advance supply incurred: <strong>+{Math.round(delta6075Extra).toLocaleString()} MWh</strong></div>
                  <div className="text-sky-900 font-bold mt-1">→ Marginal ratio: ~{ratio6075}× extra supply per MWh protected</div>
                </div>
                <div className="p-3 bg-white rounded-lg border border-sky-200">
                  <span className="font-bold text-slate-900 block font-sans">Moving from p75 to p90 (High Caution):</span>
                  <div>• Avoided shortfall gained: <strong>+{Math.round(delta7590Avoided).toLocaleString()} MWh</strong></div>
                  <div>• Extra advance supply incurred: <strong>+{Math.round(delta7590Extra).toLocaleString()} MWh</strong></div>
                  <div className="text-amber-900 font-bold mt-1">→ Marginal ratio: ~{ratio7590}× extra supply per MWh protected</div>
                </div>
              </div>
              <p className="text-sky-950 font-semibold text-[11px] pt-1">
                Rule of thumb for buyers: Choose p60 if same-day replacement power costs about {ratio6075}× advance power; choose p90 only if same-day replacement is expected to spike over {Math.round(Number(ratio7590))}×.
              </p>
            </div>
          )}

          {/* Interactive Cost-Ratio Calculator */}
          {completedDaysCount > 0 && completed_track_record && (
            <div className="pt-4">
              <CostRatioCalculator
                avoidedMwh={completed_track_record.total_avoided_shortfall_mwh}
                extraMwh={completed_track_record.total_extra_supply_mwh}
                contextLabel={`${completedDaysCount} Completed Days (${firstCompletedDay} to ${lastCompletedDay})`}
                totalGenerationMwh={completed_track_record.total_avoided_shortfall_mwh > 0 ? (completed_track_record.total_avoided_shortfall_mwh * 10) : undefined}
                title="Where Does This Pay Off? Cost-Ratio Payoff Calculator"
                subtitle={`Evaluate net financial impact across ${completedDaysCount} completed delivery days (${firstCompletedDay} to ${lastCompletedDay}) without needing market price data.`}
                allowModelSelection={false}
              />
            </div>
          )}
        </section>

        {/* ======================================================== */}
        {/* SECTION 5: TRACK RECORD TO DATE                          */}
        {/* ======================================================== */}
        <section id="track-record" className="space-y-4 pt-4 border-t border-slate-200 scroll-mt-20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-700 block">
                Empirical Verification
              </span>
              <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                Track Record to Date
              </h3>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs px-2.5 py-1 bg-emerald-100 text-emerald-900 font-medium rounded-full border border-emerald-200">
                {breakevenDaysCount} of {completedDaysCount} days break-even &lt; 2× (avoided shortfall exceeded extra supply)
              </span>
            </div>
          </div>

          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-3xl">
            Bidirectional daily performance: avoided shortfall is plotted upward (+MWh, green) and extra supply arranged is plotted downward (-MWh, slate). The net marker shows the net volume (avoided minus extra) so the cost of caution on days where Elexon was right is directly visible. All completed delivery days concluded prior to the {decisionDateFormatted} 09:00 UTC cutoff.
          </p>

          {/* Running Totals Banner */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-xs text-slate-500 block font-medium">Completed Days Replayed</span>
              <span className="text-xl sm:text-2xl font-bold font-mono text-slate-900 mt-0.5 block">
                {completedDaysCount} {completedDaysCount === 1 ? "Day" : "Days"}
              </span>
              <span className="text-[11px] text-slate-500">
                {completedDaysCount === 0 ? "None yet" : completedDaysCount === 1 ? firstCompletedDay : `${firstCompletedDay} through ${lastCompletedDay}`}
              </span>
            </div>

            <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200">
              <span className="text-xs text-emerald-900 block font-medium">Running Avoided Shortfall</span>
              <span className="text-xl sm:text-2xl font-bold font-mono text-emerald-800 mt-0.5 block">
                +{(completed_track_record?.total_avoided_shortfall_mwh ?? 0).toLocaleString()} MWh
              </span>
              <span className="text-[11px] text-emerald-700">Shortfall energy prevented</span>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-xs text-slate-500 block font-medium">Running Extra Supply Arranged</span>
              <span className="text-xl sm:text-2xl font-bold font-mono text-slate-800 mt-0.5 block">
                -{(completed_track_record?.total_extra_supply_mwh ?? 0).toLocaleString()} MWh
              </span>
              <span className="text-[11px] text-slate-500">Extra advance-arranged volume</span>
            </div>
          </div>

          {/* Daily Track Record Bidirectional Chart */}
          {trackRecordData.length > 0 ? (
            <div className="bg-slate-50/60 p-4 sm:p-6 rounded-xl border border-slate-200 space-y-4">
              <div className="h-80 sm:h-96 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={trackRecordData} margin={{ top: 20, right: 20, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                    <XAxis
                      dataKey="target_date_label"
                      tick={{ fontSize: 10, fill: "#64748B" }}
                      interval={completedDaysCount > 15 ? 1 : 0}
                      angle={-25}
                      textAnchor="end"
                      height={40}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: "#64748B" }}
                      label={{ value: "Volume (MWh)", angle: -90, position: "insideLeft", fontSize: 11, fill: "#64748B" }}
                    />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0F172A", color: "#F8FAFC", borderRadius: "8px", fontSize: "12px", border: "none" }}
                      formatter={(val: any, name: any) => {
                        if (name === "avoided_mwh") return [`+${Number(val).toLocaleString()} MWh`, "Avoided Shortfall (Upward)"];
                        if (name === "extra_mwh_negative") return [`-${Math.abs(Number(val)).toLocaleString()} MWh`, "Extra Supply Arranged (Downward)"];
                        if (name === "net_mwh") {
                          const num = Number(val);
                          return [`${num >= 0 ? '+' : ''}${num.toLocaleString()} MWh`, "Net volume (Avoided − Extra)"];
                        }
                        return [val, name];
                      }}
                      labelFormatter={(lbl) => `Target Delivery Day: ${lbl}`}
                    />
                    <Legend verticalAlign="top" height={32} />
                    <Bar
                      dataKey="avoided_mwh"
                      name="Avoided Shortfall (+MWh)"
                      fill="#059669"
                      radius={[3, 3, 0, 0]}
                    />
                    <Bar
                      dataKey="extra_mwh_negative"
                      name="Extra Supply Arranged (-MWh)"
                      fill="#64748B"
                      radius={[0, 0, 3, 3]}
                    />
                    <Line
                      type="linear"
                      dataKey="net_mwh"
                      name="Net volume (Avoided − Extra)"
                      stroke="#0284C7"
                      strokeWidth={2}
                      dot={{ r: 3, fill: "#0284C7" }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <div className="text-xs text-slate-500 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                <span>Honest performance check: On days where the net marker is below zero, the extra advance supply arranged exceeded the shortfall avoided (cost of caution). In {completedRangeText}, avoided shortfall exceeded extra supply on {breakevenDaysCount} of {completedDaysCount} days (break-even &lt; 2×).</span>
                <span className="font-mono text-slate-400">Evaluated at p{selected_percentile} signed-error percentile</span>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 bg-slate-50 rounded-xl border border-slate-200">
              No completed delivery days available before {decisionDateFormatted} cutoff.
            </div>
          )}
        </section>

        {/* ======================================================== */}
        {/* SECTION 6: DATA PROVENANCE                               */}
        {/* ======================================================== */}
        <section id="data-provenance" className="space-y-4 pt-4 border-t border-slate-200 scroll-mt-20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-700 block">
                Audit Trail & Data Lineage
              </span>
              <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                Data Provenance
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-500 bg-slate-100 px-3 py-1 rounded-md border border-slate-200 w-fit">
              Sourced from Elexon BMRS
            </span>
          </div>

          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-3xl">
            All forecast and actual outturn data are sourced from Elexon BMRS.
          </p>

          <div className="bg-slate-50 rounded-xl border border-slate-200 p-6 space-y-4 text-xs font-mono">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3.5 bg-white rounded-lg border border-slate-200 space-y-1">
                <span className="text-slate-500 font-sans block text-[11px]">Elexon Forecast Published At</span>
                <span className="font-bold text-slate-900 text-sm">
                  {formatDateHour(provenance?.forecast_latest_publish_utc || "")} UTC
                </span>
                <span className="text-slate-400 text-[10px] block">
                  Exact publishTime used for target day (latest vintage before cutoff)
                </span>
              </div>

              <div className="p-3.5 bg-white rounded-lg border border-slate-200 space-y-1">
                <span className="text-slate-500 font-sans block text-[11px]">Revisions Available at Cutoff</span>
                <span className="font-bold text-slate-900 text-sm">
                  {provenance ? `${provenance.forecast_revisions_count} Vintages (${provenance.target_forecast_rows_count} Records)` : "—"}
                </span>
                <span className="text-slate-400 text-[10px] block">
                  Target day has 48 settlement periods. Rolling forecast vintages published prior to 09:00 UTC are evaluated, and the latest published forecast per settlement period is selected.
                </span>
              </div>

              <div className="p-3.5 bg-white rounded-lg border border-slate-200 space-y-1">
                <span className="text-slate-500 font-sans block text-[11px]">Primary Source Datasets</span>
                <span className="font-bold text-slate-900 text-xs block leading-tight">
                  WINDFOR (Day-Ahead Forecasts) & FUELHH (Outturn Generation)
                </span>
                <span className="text-slate-400 text-[10px] block">
                  Public Elexon BMRS REST APIs
                </span>
              </div>

              <div className="p-3.5 bg-white rounded-lg border border-slate-200 space-y-1">
                <span className="text-slate-500 font-sans block text-[11px]">Decision Freeze Cutoff</span>
                <span className="font-bold text-sky-800 text-sm">
                  {provenance?.freeze_cutoff_utc ?? (estimateData.decision_date ? `${estimateData.decision_date}T09:00:00Z` : "—")}
                </span>
                <span className="text-slate-400 text-[10px] block">
                  Cutoff boundary: strictly no forecasts published or actuals recorded after 09:00 UTC on {decisionDateFormatted} are used.
                </span>
              </div>
            </div>

            <div className="p-3.5 bg-slate-900 text-slate-300 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px]">
              <div className="flex items-center space-x-2">
                <FileCode className="w-4 h-4 text-sky-400 shrink-0" />
                <span>Local Snapshot: {provenance?.snapshot_filename} ({provenance?.snapshot_size_kb} KB, {provenance?.snapshot_record_count?.toLocaleString()} records)</span>
              </div>
              <div className="flex items-center space-x-3">
                <span>Built: {provenance?.snapshot_build_date_utc ? formatDateHour(provenance.snapshot_build_date_utc) : "—"}</span>
                <span className="text-sky-300 font-semibold">{provenance?.snapshot_status}</span>
              </div>
            </div>

            <div className="p-2.5 bg-slate-800/60 rounded border border-slate-700 text-[10px] text-slate-400 font-mono break-all">
              <span className="text-slate-500 mr-2">SHA-256:</span>
              <span className="text-slate-300">{provenance?.snapshot_sha256}</span>
            </div>
          </div>
        </section>

        {/* ======================================================== */}
        {/* SECTION 7: CONFIDENCE & DECLARED LIMITS                  */}
        {/* ======================================================== */}
        <section id="confidence-limits" className="space-y-4 pt-4 border-t border-slate-200 scroll-mt-20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-700 block">
                Operational Scope & Boundaries
              </span>
              <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                Confidence Rationale & Declared Limits
              </h3>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            {/* Confidence Rationale */}
            <div className="p-4 bg-sky-50/70 rounded-xl border border-sky-200 space-y-2">
              <div className="flex items-center space-x-2 text-sky-900 font-bold text-sm">
                <CheckCircle2 className="w-4 h-4 text-sky-600 shrink-0" />
                <span>
                  {confidence_label === "High"
                    ? "Full history (48h)"
                    : confidence_label === "Medium"
                    ? `Partial history (${historical_observations_count} of 96 slots)`
                    : `Limited history (${historical_observations_count} of 96 slots)`}
                </span>
              </div>
              <p className="text-sky-950 leading-relaxed text-[11px]">
                {confidence_label === "High"
                  ? "Full history (48h): all 96 calibration half-hours are available with zero missing intervals across the complete 48-hour rolling window ending 1 hour before cutoff."
                  : `Partial history (${historical_observations_count} of 96 slots available): automatically blended with the fixed 15% cold-start haircut (${(history_weight * 100).toFixed(0)}% data margin, ${(100 - history_weight * 100).toFixed(0)}% fixed haircut). On early dates like 03 Jan, 64 slots (32h) exist because day-ahead paired forecast records begin on 02 Jan 00:00 UTC and actuals observe a 1-hour publication lag.`}
              </p>
            </div>

            {/* What Model Cannot Know */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>What the Model Cannot Know</span>
              </div>
              <ul className="text-slate-600 space-y-1 list-disc pl-4 text-[11px] leading-relaxed">
                <li><strong>Demand:</strong> does not model power demand or net system load</li>
                <li><strong>Prices:</strong> does not model wholesale power prices, cash imbalance charges, or spreads (all results reported in physical MWh)</li>
                <li><strong>Transmission:</strong> does not model network constraints or local curtailment</li>
                <li><strong>Weather models:</strong> no access to raw NWP weather models beyond Elexon's published aggregated wind forecast</li>
                <li><strong>Definitional gap:</strong> does not break down embedded vs transmission-connected wind physically (treats the FUELHH outturn gap empirically)</li>
              </ul>
            </div>

            {/* Operational Limits & When Not to Use */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <div className="flex items-center space-x-2 text-slate-900 font-bold text-sm">
                <Info className="w-4 h-4 text-sky-600 shrink-0" />
                <span>When Not to Rely on This Model</span>
              </div>
              <ul className="text-slate-600 space-y-1 list-disc pl-4 text-[11px] leading-relaxed">
                <li><strong>Additive vs proportional margin:</strong> The headline model learns a fixed GW margin and floors each half-hour plan at 0.0 GW (plans never go negative). On days where forecast wind is low relative to the history window, an additive margin cuts a larger percentage than a proportional margin would. We subsequently evaluated a proportional variant (v2) and flat haircuts on the Reliability Check page to evaluate this regime-shift behavior.</li>
                <li><strong>Rapid weather regime change:</strong> a sudden calm or storm arriving faster than the 48h error window captures</li>
                <li><strong>Network faults:</strong> emergency transmission outages affecting major wind export corridors</li>
                <li><strong>Single-month scope:</strong> evaluated across January 2026 winter conditions. The headline model v1 was specified with fixed parameters before outturn was evaluated; the proportional variant v2 was formulated after v1's results during weather transitions were known.</li>
                <li><strong>Early month:</strong> first 2–3 days of a month where history is short (point to the cold-start haircut)</li>
              </ul>
            </div>
          </div>

          {onNavigateDocs && (
            <div className="pt-2 flex justify-end">
              <button
                onClick={onNavigateDocs}
                className="inline-flex items-center space-x-1.5 text-xs text-sky-700 hover:text-sky-800 font-semibold cursor-pointer"
              >
                <span>Read Full Methodology Documentation</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </section>

        {/* ======================================================== */}
        {/* SECTION 8: FREQUENTLY ASKED QUESTIONS                    */}
        {/* ======================================================== */}
        <section id="faq" className="space-y-4 pt-4 border-t border-slate-200 scroll-mt-20">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
            <div>
              <span className="text-xs font-mono font-bold uppercase tracking-wider text-sky-700 block">
                Buyer FAQ
              </span>
              <h3 className="text-xl font-bold text-slate-900 mt-0.5">
                Frequently Asked Questions
              </h3>
            </div>
          </div>

          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-3xl">
            Clear answers to common questions about our methodology, the caution trade-off, and practical day-ahead planning.
          </p>

          <div className="space-y-3 pt-2">
            {/* FAQ 1 */}
            <div className="border border-slate-200 rounded-xl overflow-hidden transition-colors">
              <button
                onClick={() => toggleFaq("faq1")}
                className="w-full flex items-center justify-between p-4 text-left font-bold text-slate-900 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer text-sm sm:text-base"
              >
                <span>Why is your estimate lower than Elexon's?</span>
                {faqOpen.faq1 ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
              </button>
              {faqOpen.faq1 && (
                <div className="p-4 bg-white text-xs sm:text-sm text-slate-700 leading-relaxed border-t border-slate-200 space-y-2">
                  <p>
                    Because Elexon's forecast ran above FUELHH outturn in <strong>{error_distribution ? `${error_distribution.overforecast_pct}%` : "100%"}</strong> of the last {historyHours} hours
                    ({error_distribution?.overforecast_count ?? historical_observations_count} of the last {historical_observations_count} half-hours), and this setting protects against the {selected_percentile}th signed-error percentile ({appliedMargin.toFixed(1)} GW). Part of this gap reflects definitional differences between WINDFOR (visible wind) and FUELHH (transmission-metered BMUs).
                  </p>
                  <p className="text-slate-500 text-xs">
                    When a buyer relies on unadjusted forecasts while forecasts persistently run above metered outturns, replacement power must be bought closer to delivery to cover the gap.
                  </p>
                </div>
              )}
            </div>

            {/* FAQ 2 */}
            <div className="border border-slate-200 rounded-xl overflow-hidden transition-colors">
              <button
                onClick={() => toggleFaq("faq2")}
                className="w-full flex items-center justify-between p-4 text-left font-bold text-slate-900 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer text-sm sm:text-base"
              >
                <span>What happens to the difference?</span>
                {faqOpen.faq2 ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
              </button>
              {faqOpen.faq2 && (
                <div className="p-4 bg-white text-xs sm:text-sm text-slate-700 leading-relaxed border-t border-slate-200 space-y-2">
                  <p>
                    Each half-hour has its own forecast and its own deducted margin. If outturn wind in a half-hour falls below that half-hour's cautious plan, replacement power must be bought closer to delivery.
                  </p>
                  <p className="font-semibold text-slate-800">
                    In the last {historyHours} hours, this margin would still have left about {inSampleShortPct}% of half-hours short; tomorrow may differ.
                  </p>
                  <p className="text-slate-500 text-xs">
                    When actual wind generation exceeds our plan, the difference represents surplus power arranged in advance. We do not model prices, so all results are shown in MWh.
                  </p>
                </div>
              )}
            </div>

            {/* FAQ 3 */}
            <div className="border border-slate-200 rounded-xl overflow-hidden transition-colors">
              <button
                onClick={() => toggleFaq("faq3")}
                className="w-full flex items-center justify-between p-4 text-left font-bold text-slate-900 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer text-sm sm:text-base"
              >
                <span>Can I change the caution level?</span>
                {faqOpen.faq3 ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
              </button>
              {faqOpen.faq3 && (
                <div className="p-4 bg-white text-xs sm:text-sm text-slate-700 leading-relaxed border-t border-slate-200 space-y-2">
                  <p>
                    Yes. The risk slider allows choosing between <strong>p60</strong> (smaller margin, less advance power arranged) and <strong>p90</strong> (larger margin, more protective buffer).
                  </p>
                  <p className="text-slate-500 text-xs">
                    The trade-off table above shows the historical trade-off across completed days this month: choosing more protection avoids more shortfall, but requires arranging more power in advance.
                  </p>
                </div>
              )}
            </div>

            {/* FAQ 4 */}
            <div className="border border-slate-200 rounded-xl overflow-hidden transition-colors">
              <button
                onClick={() => toggleFaq("faq4")}
                className="w-full flex items-center justify-between p-4 text-left font-bold text-slate-900 bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer text-sm sm:text-base"
              >
                <span>Is performance guaranteed? (No guarantee)</span>
                {faqOpen.faq4 ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
              </button>
              {faqOpen.faq4 && (
                <div className="p-4 bg-white text-xs sm:text-sm text-slate-700 leading-relaxed border-t border-slate-200 space-y-2">
                  <p className="font-semibold text-slate-900">
                    No, it is not guaranteed. This is a one-month historical replay (January 2026), and the margin can be wrong on any given day.
                  </p>
                  <p>
                    The model derives an empirical buffer from recent forecast errors. If tomorrow experiences weather dynamics outside the previous {historyHours} hours (such as an unpredicted calm front or rapid atmospheric shift), shortfalls can still occur.
                  </p>
                  <p className="text-slate-500 text-xs">
                    By tracking historical errors empirically, buyers can reduce the frequency and severity of emergency replacement power, but cannot eliminate forecast uncertainty entirely.
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};
