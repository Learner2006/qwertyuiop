/** Central frontend configuration */

export const APP_CONFIG = {
  productName: "Wind Day-Ahead Estimator",
  pitch: "Elexon forecasts wind. We estimate how much of it a buyer can safely rely on.",
  disclosure: "Historical replay · January 2026 · UTC · Not a live trading recommendation",
  defaultDecisionDate: "2026-01-25",
  defaultPercentile: 75,
  minPercentile: 60,
  maxPercentile: 90,
  minDate: "2026-01-01",
  maxDate: "2026-01-30",
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "",
};
