import React from "react";

interface ConfidenceBadgeProps {
  label: "Low" | "Medium" | "High";
  observationsCount: number;
  historyWeight: number;
  methodologyType: "cold_start" | "blended" | "data_driven";
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  label,
  observationsCount,
  historyWeight,
  methodologyType,
}) => {
  const getBadgeStyle = () => {
    switch (label) {
      case "High":
        return "bg-emerald-50 text-emerald-800 border-emerald-200";
      case "Medium":
        return "bg-sky-50 text-sky-800 border-sky-200";
      case "Low":
      default:
        return "bg-amber-50 text-amber-800 border-amber-200";
    }
  };

  const getBadgeLabel = () => {
    if (observationsCount >= 96) {
      return "Full history (48h)";
    }
    if (observationsCount > 0) {
      return `Partial history (${observationsCount} of 96 slots)`;
    }
    return "No history (Cold start 15%)";
  };

  const getMethodologyDescription = () => {
    if (methodologyType === "cold_start" || observationsCount === 0) {
      return "Cold-start: using fixed 15% haircut (0 half-hours available).";
    }
    if (methodologyType === "blended" || observationsCount < 96) {
      const pct = Math.round(historyWeight * 100);
      return `Blended calibration: ${pct}% data-driven margin (w = min(1.0, ${observationsCount}/96)), ${100 - pct}% fixed 15% haircut.`;
    }
    return "Data-driven: 100% empirical error quantiles from previous 48h (see Methodology).";
  };

  const hours = Math.round(observationsCount / 2);

  return (
    <div className="flex flex-col space-y-1.5">
      <div className="flex flex-wrap items-center gap-2">
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getBadgeStyle()}`}
        >
          {getBadgeLabel()}
        </span>
        <span className="text-xs text-slate-700 font-mono font-medium">
          History used: {observationsCount} of 96 half-hours ({hours}h)
        </span>
      </div>
      <p className="text-xs text-slate-500 leading-relaxed">
        {getMethodologyDescription()}
      </p>
    </div>
  );
};
