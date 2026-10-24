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

  const getMethodologyDescription = () => {
    if (methodologyType === "cold_start") {
      return "Cold-start: 15% fixed haircut applied (0 historical observations in January 2026 lookback)";
    }
    if (methodologyType === "blended") {
      const pct = Math.round(historyWeight * 100);
      return `Blended calibration: ${pct}% empirical error margin, ${100 - pct}% cold-start haircut`;
    }
    return "Data-driven: 100% empirical signed-error percentile margin from 96 historical half-hourly observations (48h lookback)";
  };

  return (
    <div className="flex flex-col space-y-1">
      <div className="flex items-center space-x-2">
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getBadgeStyle()}`}
        >
          {label} Calibration Coverage
        </span>
        <span className="text-xs text-slate-500 font-mono">
          {observationsCount} / 96 observations
        </span>
      </div>
      <p className="text-xs text-slate-500 italic">
        {getMethodologyDescription()}
      </p>
    </div>
  );
};
