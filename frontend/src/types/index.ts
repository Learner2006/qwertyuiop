export interface HealthResponse {
  status: string;
  product_name: string;
  dataset_available: boolean;
  dataset_records_count: number;
  date_coverage_start?: string;
  date_coverage_end?: string;
  version: string;
}

export interface EstimateInterval {
  interval_start: string;
  settlement_period: number;
  elexon_forecast_gw: number;
  safe_estimate_gw: number;
  indicative_lower_gw: number;
  indicative_upper_gw: number;
  applied_margin_gw: number;
}

export interface EstimateResponse {
  decision_date: string;
  target_date: string;
  decision_cutoff_utc: string;
  selected_percentile: number;
  elexon_headline_gw: number;
  safe_headline_gw: number;
  indicative_lower_headline_gw: number;
  indicative_upper_headline_gw: number;
  confidence_label: "Low" | "Medium" | "High";
  historical_observations_count: number;
  history_weight: number;
  methodology_type: "cold_start" | "blended" | "data_driven";
  valid_intervals_count: number;
  intervals: EstimateInterval[];
  dataset_version: string;
}

export interface CheckInterval {
  interval_start: string;
  settlement_period: number;
  elexon_forecast_gw: number;
  safe_estimate_gw: number;
  actual_generation_gw: number;
  indicative_lower_gw: number;
  indicative_upper_gw: number;
  elexon_shortfall_mwh: number;
  safe_shortfall_mwh: number;
  saved_mwh: number;
  is_elexon_shortfall: boolean;
  is_safe_shortfall: boolean;
}

export interface CheckResponse {
  decision_date: string;
  target_date: string;
  decision_cutoff_utc: string;
  selected_percentile: number;
  elexon_headline_gw: number;
  safe_headline_gw: number;
  actual_headline_gw: number;
  indicative_lower_headline_gw: number;
  indicative_upper_headline_gw: number;
  elexon_shortfall_mwh: number;
  safe_shortfall_mwh: number;
  saved_shortfall_mwh: number;
  extra_advance_planned_mwh: number;
  elexon_mae_gw: number;
  safe_mae_gw: number;
  indicative_range_coverage: number;
  confidence_label: "Low" | "Medium" | "High";
  historical_observations_count: number;
  history_weight: number;
  methodology_type: "cold_start" | "blended" | "data_driven";
  headline_result: string;
  valid_intervals_count: number;
  methodology_notes: string[];
  intervals: CheckInterval[];
}
