export interface HealthResponse {
  status: string;
  product_name: string;
  dataset_available: boolean;
  dataset_records_count: number;
  date_coverage_start?: string;
  date_coverage_end?: string;
  version: string;
}

export interface FlatHaircutBenchmark {
  haircut_percent: number;
  shortfall_mwh: number;
  avoided_shortfall_mwh: number;
  surplus_mwh: number;
  incremental_surplus_mwh: number;
  mae_gw: number;
}

export interface ModelBenchmark {
  name: string;
  description: string;
  cut_volume_mwh: number;
  cut_volume_pct: number;
  avoided_shortfall_mwh: number;
  extra_supply_mwh: number;
  efficiency_pct: number;
  breakeven_ratio: number;
  mae_gw: number;
}

export interface PercentileSweepPoint {
  percentile: number;
  cut_volume_mwh: number;
  cut_volume_pct: number;
  avoided_shortfall_mwh: number;
  extra_supply_mwh: number;
  efficiency_pct: number;
  breakeven_ratio: number;
  mae_gw: number;
}

export interface MonthSummaryResponse {
  decision_dates_count: number;
  total_target_intervals: number;
  period_start: string;
  period_end: string;
  target_start: string;
  target_end: string;
  percentile: number;
  
  total_actual_wind_mwh: number;
  total_elexon_forecast_mwh: number;
  elexon_overforecast_pct: number;

  // Shortfall comparison (before -> after)
  total_elexon_shortfall_mwh: number;
  total_safe_shortfall_mwh: number;
  total_avoided_shortfall_mwh: number;
  elexon_shortfall_pct_of_wind: number;
  safe_shortfall_pct_of_wind: number;
  avoided_shortfall_pct_of_wind: number;

  // Surplus comparison (before -> after)
  total_elexon_surplus_mwh: number;
  total_safe_surplus_mwh: number;
  total_incremental_surplus_mwh: number;
  total_extra_advance_planned_mwh: number;
  elexon_surplus_pct_of_wind: number;
  safe_surplus_pct_of_wind: number;
  incremental_surplus_pct_of_wind: number;

  // Volume cut and efficiency comparison
  total_volume_cut_mwh: number;
  safe_efficiency_pct: number;
  matched_flat_efficiency_pct: number;
  breakeven_ratio: number;

  // Cold start vs Mature split
  cold_start_days: number;
  cold_start_intervals: number;
  cold_start_avoided_shortfall_mwh: number;
  cold_start_incremental_surplus_mwh: number;
  cold_start_ratio: number;

  mature_days: number;
  mature_intervals: number;
  mature_avoided_shortfall_mwh: number;
  mature_incremental_surplus_mwh: number;
  mature_breakeven_ratio: number;

  // Baseline models for comparative analysis
  flat_15_benchmark: ModelBenchmark;
  rolling_mean_benchmark: ModelBenchmark;
  rolling_mean_ratio_benchmark?: ModelBenchmark;
  v1_additive_benchmark?: ModelBenchmark;
  v2_proportional_benchmark?: ModelBenchmark;

  // First-half vs Second-half (out-of-sample) benchmarks
  first_half_v1?: ModelBenchmark;
  first_half_v2?: ModelBenchmark;
  first_half_flat15?: ModelBenchmark;
  second_half_v1?: ModelBenchmark;
  second_half_v2?: ModelBenchmark;
  second_half_flat15?: ModelBenchmark;

  percentile_sweep: PercentileSweepPoint[];

  // Accuracy (MAE)
  elexon_mae_gw: number;
  safe_mae_gw: number;

  // Matched flat baseline (same total margin MWh as our model)
  matched_haircut_percent: number;
  matched_haircut_shortfall_mwh: number;
  matched_haircut_avoided_mwh: number;
  matched_haircut_incremental_surplus_mwh: number;

  // Flat haircut trade-off curve (0% to 30%)
  flat_benchmarks: FlatHaircutBenchmark[];

  days_shortfall_reduced: number;
  days_shortfall_increased: number;
  days_breakeven_count?: number;
  summary_sentence: string;
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

export interface CalculationStep {
  elexon_day_ahead_avg_gw: number;
  historical_observations_count: number;
  percentile: number;
  error_margin_gw: number;
  safe_plan_gw: number;
  formula_text: string;
  history_weight?: number;
  data_margin_gw?: number;
  cold_margin_gw?: number;
  is_blended?: boolean;
  blend_formula_text?: string | null;
}

export interface History48hObservation {
  interval_start: string;
  forecast_gw: number;
  actual_gw: number;
  error_gw: number;
}

export interface HistogramBin {
  bin_start: number;
  bin_end: number;
  count: number;
  bin_label: string;
}

export interface ErrorDistribution {
  min_error_gw: number;
  max_error_gw: number;
  mean_error_gw: number;
  p10_error_gw: number;
  p50_error_gw: number;
  p60_error_gw: number;
  p75_error_gw: number;
  p90_error_gw: number;
  overforecast_count: number;
  total_count: number;
  overforecast_pct: number;
  histogram_bins: HistogramBin[];
  mean_forecast_gw?: number;
  bias_pct?: number;
}

export interface SliderTradeoffPoint {
  percentile: number;
  label: string;
  plan_gw: number;
  margin_gw: number;
  completed_avoided_shortfall_mwh: number;
  completed_extra_supply_mwh: number;
  is_selected: boolean;
}

export interface CompletedTrackRecordDay {
  decision_date: string;
  target_date: string;
  target_date_label: string;
  elexon_shortfall_mwh: number;
  safe_shortfall_mwh: number;
  avoided_shortfall_mwh: number;
  extra_supply_mwh: number;
  is_shortfall_reduced: boolean;
  is_breakeven?: boolean;
}

export interface CompletedTrackRecord {
  completed_days_count: number;
  total_avoided_shortfall_mwh: number;
  total_extra_supply_mwh: number;
  days_reduced_count: number;
  days_increased_count: number;
  days_breakeven_count?: number;
  daily_records: CompletedTrackRecordDay[];
}

export interface ProvenanceMetadata {
  forecast_latest_publish_utc: string;
  forecast_revisions_count: number;
  target_forecast_rows_count: number;
  source_forecast_dataset: string;
  source_actuals_dataset: string;
  freeze_cutoff_utc: string;
  snapshot_filename: string;
  snapshot_size_kb: number;
  snapshot_build_date_utc: string;
  snapshot_status: string;
  snapshot_sha256?: string;
}

export interface EstimateResponse {
  decision_date: string;
  target_date: string;
  decision_cutoff_utc: string;
  selected_percentile: number;
  elexon_headline_gw: number;
  safe_headline_gw: number;
  v2_safe_headline_gw?: number;
  v2_ratio?: number;
  flat15_safe_headline_gw?: number;
  flat15_safe_shortfall_mwh?: number;
  flat15_saved_shortfall_mwh?: number;
  flat15_safe_surplus_mwh?: number;
  flat15_incremental_surplus_mwh?: number;
  flat15_ratio?: number;
  indicative_lower_headline_gw: number;
  indicative_upper_headline_gw: number;
  confidence_label: "Low" | "Medium" | "High";
  historical_observations_count: number;
  history_weight: number;
  methodology_type: "cold_start" | "blended" | "data_driven";
  valid_intervals_count: number;
  intervals: EstimateInterval[];
  calculation?: CalculationStep;
  history_48h?: History48hObservation[];
  error_distribution?: ErrorDistribution;
  slider_tradeoffs?: SliderTradeoffPoint[];
  completed_track_record?: CompletedTrackRecord;
  provenance?: ProvenanceMetadata;
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
  elexon_surplus_mwh?: number;
  safe_surplus_mwh?: number;
  incremental_surplus_mwh?: number;
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
  elexon_surplus_mwh?: number;
  safe_surplus_mwh?: number;
  incremental_surplus_mwh?: number;
  extra_advance_planned_mwh: number;
  v2_safe_headline_gw?: number;
  v2_safe_shortfall_mwh?: number;
  v2_saved_shortfall_mwh?: number;
  v2_safe_surplus_mwh?: number;
  v2_incremental_surplus_mwh?: number;
  v2_ratio?: number;
  flat15_safe_headline_gw?: number;
  flat15_safe_shortfall_mwh?: number;
  flat15_saved_shortfall_mwh?: number;
  flat15_safe_surplus_mwh?: number;
  flat15_incremental_surplus_mwh?: number;
  flat15_ratio?: number;
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
