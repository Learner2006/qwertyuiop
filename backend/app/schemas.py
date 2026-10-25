"""Pydantic schemas for the Wind Day-Ahead Estimator API.
Strict validation and UTC ISO timestamps.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    product_name: str
    dataset_available: bool = True
    dataset_records_count: int
    date_coverage_start: Optional[str] = None
    date_coverage_end: Optional[str] = None
    version: str = "1.0.0"


class FlatHaircutBenchmark(BaseModel):
    haircut_percent: float
    shortfall_mwh: float
    avoided_shortfall_mwh: float
    surplus_mwh: float
    incremental_surplus_mwh: float
    mae_gw: float


class ModelBenchmark(BaseModel):
    name: str
    description: str
    cut_volume_mwh: float
    cut_volume_pct: float
    avoided_shortfall_mwh: float
    extra_supply_mwh: float
    efficiency_pct: float
    breakeven_ratio: float
    mae_gw: float


class PercentileSweepPoint(BaseModel):
    percentile: float
    cut_volume_mwh: float
    cut_volume_pct: float
    avoided_shortfall_mwh: float
    extra_supply_mwh: float
    efficiency_pct: float
    breakeven_ratio: float
    mae_gw: float


class MonthSummaryResponse(BaseModel):
    decision_dates_count: int  # 30
    total_target_intervals: int  # 1440
    period_start: str  # "2026-01-01"
    period_end: str    # "2026-01-30"
    target_start: str  # "2026-01-02"
    target_end: str    # "2026-01-31"
    percentile: float  # 75.0
    
    total_actual_wind_mwh: float  # 8,247,141.5
    total_elexon_forecast_mwh: float  # 9,523,977.0
    elexon_overforecast_pct: float  # 15.48%
    
    # Shortfall comparison (before -> after)
    total_elexon_shortfall_mwh: float
    total_safe_shortfall_mwh: float
    total_avoided_shortfall_mwh: float
    elexon_shortfall_pct_of_wind: float
    safe_shortfall_pct_of_wind: float
    avoided_shortfall_pct_of_wind: float
    
    # Surplus comparison (before -> after)
    total_elexon_surplus_mwh: float
    total_safe_surplus_mwh: float
    total_incremental_surplus_mwh: float
    total_extra_advance_planned_mwh: float  # Alias for incremental surplus
    elexon_surplus_pct_of_wind: float
    safe_surplus_pct_of_wind: float
    incremental_surplus_pct_of_wind: float

    # Volume cut and efficiency comparison
    total_volume_cut_mwh: float  # 1,959,295.7 MWh (20.57%)
    safe_efficiency_pct: float  # 49.82% (avoided_sf / cut_volume)
    matched_flat_efficiency_pct: float  # 60.47% (matched_avoided / cut_volume)
    breakeven_ratio: float  # 1.007

    # Phase 1 (Jan 1-3) vs Phase 2 (Jan 4-30) comparison
    cold_start_days: int = 3
    cold_start_intervals: int = 144
    cold_start_avoided_shortfall_mwh: float = 134810.1
    cold_start_incremental_surplus_mwh: float = 76914.2
    cold_start_ratio: float = 1.753  # avoided / extra

    mature_days: int = 27
    mature_intervals: int = 1296
    mature_avoided_shortfall_mwh: float = 841384.1
    mature_incremental_surplus_mwh: float = 906187.3
    mature_breakeven_ratio: float = 1.077  # extra / avoided

    # Baseline models for comparative analysis
    flat_15_benchmark: ModelBenchmark
    rolling_mean_benchmark: ModelBenchmark
    rolling_mean_ratio_benchmark: Optional[ModelBenchmark] = None
    v1_additive_benchmark: Optional[ModelBenchmark] = None
    v2_proportional_benchmark: Optional[ModelBenchmark] = None
    
    # First half vs Second half (out-of-sample test) splits
    first_half_v1: Optional[ModelBenchmark] = None
    first_half_v2: Optional[ModelBenchmark] = None
    first_half_flat15: Optional[ModelBenchmark] = None
    second_half_v1: Optional[ModelBenchmark] = None
    second_half_v2: Optional[ModelBenchmark] = None
    second_half_flat15: Optional[ModelBenchmark] = None
    
    percentile_sweep: List[PercentileSweepPoint]

    # Accuracy (MAE)
    elexon_mae_gw: float
    safe_mae_gw: float
    
    # Matched haircut baseline (flat haircut with same total margin MWh as our model)
    matched_haircut_percent: float
    matched_haircut_shortfall_mwh: float
    matched_haircut_avoided_mwh: float
    matched_haircut_incremental_surplus_mwh: float
    
    # Flat haircut trade-off curve (0% to 30%)
    flat_benchmarks: List[FlatHaircutBenchmark]
    
    days_shortfall_reduced: int
    days_shortfall_increased: int
    summary_sentence: str


class CalculationStep(BaseModel):
    elexon_day_ahead_avg_gw: float
    historical_observations_count: int
    percentile: float
    error_margin_gw: float
    safe_plan_gw: float
    formula_text: str
    history_weight: float = 1.0
    data_margin_gw: float = 0.0
    cold_margin_gw: float = 0.0
    is_blended: bool = False
    blend_formula_text: Optional[str] = None


class History48hObservation(BaseModel):
    interval_start: str
    forecast_gw: float
    actual_gw: float
    error_gw: float


class HistogramBin(BaseModel):
    bin_start: float
    bin_end: float
    count: int
    bin_label: str


class ErrorDistribution(BaseModel):
    min_error_gw: float
    max_error_gw: float
    mean_error_gw: float
    p10_error_gw: float
    p50_error_gw: float
    p60_error_gw: float
    p75_error_gw: float
    p90_error_gw: float
    overforecast_count: int
    total_count: int
    overforecast_pct: float
    histogram_bins: List[HistogramBin]
    mean_forecast_gw: float = 0.0
    bias_pct: float = 0.0


class SliderTradeoffPoint(BaseModel):
    percentile: float
    label: str
    plan_gw: float
    margin_gw: float
    completed_avoided_shortfall_mwh: float
    completed_extra_supply_mwh: float
    is_selected: bool


class CompletedTrackRecordDay(BaseModel):
    decision_date: str
    target_date: str
    target_date_label: str
    elexon_shortfall_mwh: float
    safe_shortfall_mwh: float
    avoided_shortfall_mwh: float
    extra_supply_mwh: float
    is_shortfall_reduced: bool
    is_breakeven: bool = False


class CompletedTrackRecord(BaseModel):
    completed_days_count: int
    total_avoided_shortfall_mwh: float
    total_extra_supply_mwh: float
    days_reduced_count: int
    days_increased_count: int
    days_breakeven_count: int = 0
    daily_records: List[CompletedTrackRecordDay]


class ProvenanceMetadata(BaseModel):
    forecast_latest_publish_utc: str
    forecast_revisions_count: int
    target_forecast_rows_count: int
    source_forecast_dataset: str = "Elexon BMRS WINDFOR (Day-Ahead Wind Forecast)"
    source_actuals_dataset: str = "Elexon BMRS FUELHH (Outturn Wind Generation)"
    freeze_cutoff_utc: str
    snapshot_filename: str = "jan2026.parquet"
    snapshot_size_kb: int = 253
    snapshot_build_date_utc: str = "2026-10-24T16:49:00Z"
    snapshot_status: str = "Replay cache"
    snapshot_sha256: str = "d997afe42e53663a4dbef2c597da8f515d5490d7fbb159370b28fbb5c9a95f98"


class EstimateInterval(BaseModel):
    interval_start: str = Field(..., description="UTC ISO-8601 start timestamp")
    settlement_period: int = Field(..., ge=1, le=48)
    elexon_forecast_gw: float
    safe_estimate_gw: float
    indicative_lower_gw: float
    indicative_upper_gw: float
    applied_margin_gw: float


class EstimateResponse(BaseModel):
    decision_date: str
    target_date: str
    decision_cutoff_utc: str
    selected_percentile: float
    
    # Headlines in GW
    elexon_headline_gw: float
    safe_headline_gw: float
    v2_safe_headline_gw: Optional[float] = None
    v2_ratio: Optional[float] = None
    indicative_lower_headline_gw: float
    indicative_upper_headline_gw: float
    
    # Methodology & calibration metadata
    confidence_label: str  # "Low", "Medium", "High"
    historical_observations_count: int
    history_weight: float
    methodology_type: str  # "cold_start", "blended", "data_driven"
    
    # Intervals
    valid_intervals_count: int
    intervals: List[EstimateInterval]

    # Hand-checkable calculation & drill-down metrics
    calculation: Optional[CalculationStep] = None
    history_48h: Optional[List[History48hObservation]] = None
    error_distribution: Optional[ErrorDistribution] = None
    slider_tradeoffs: Optional[List[SliderTradeoffPoint]] = None
    completed_track_record: Optional[CompletedTrackRecord] = None
    provenance: Optional[ProvenanceMetadata] = None
    
    dataset_version: str = "January 2026 Elexon BMRS Replay v1"


class CheckInterval(BaseModel):
    interval_start: str = Field(..., description="UTC ISO-8601 start timestamp")
    settlement_period: int = Field(..., ge=1, le=48)
    elexon_forecast_gw: float
    safe_estimate_gw: float
    actual_generation_gw: float
    indicative_lower_gw: float
    indicative_upper_gw: float
    elexon_shortfall_mwh: float
    safe_shortfall_mwh: float
    saved_mwh: float
    elexon_surplus_mwh: float
    safe_surplus_mwh: float
    incremental_surplus_mwh: float
    is_elexon_shortfall: bool
    is_safe_shortfall: bool


class CheckResponse(BaseModel):
    decision_date: str
    target_date: str
    decision_cutoff_utc: str
    selected_percentile: float
    
    # Headlines in GW
    elexon_headline_gw: float
    safe_headline_gw: float
    actual_headline_gw: float
    indicative_lower_headline_gw: float
    indicative_upper_headline_gw: float
    
    # Shortfall energy metrics in MWh
    elexon_shortfall_mwh: float
    safe_shortfall_mwh: float
    saved_shortfall_mwh: float
    
    # Surplus energy metrics in MWh (apples-to-apples)
    elexon_surplus_mwh: float
    safe_surplus_mwh: float
    incremental_surplus_mwh: float
    extra_advance_planned_mwh: float  # Alias for safe_surplus_mwh for backwards compatibility
    
    # v2 proportional metrics
    v2_safe_headline_gw: Optional[float] = None
    v2_safe_shortfall_mwh: Optional[float] = None
    v2_saved_shortfall_mwh: Optional[float] = None
    v2_safe_surplus_mwh: Optional[float] = None
    v2_incremental_surplus_mwh: Optional[float] = None
    v2_ratio: Optional[float] = None
    
    # Accuracy & coverage
    elexon_mae_gw: float
    safe_mae_gw: float
    indicative_range_coverage: float  # Fraction between 0 and 1
    
    # Calibration metadata
    confidence_label: str
    historical_observations_count: int
    history_weight: float
    methodology_type: str
    
    # Evaluation summary sentence
    headline_result: str
    
    # Metadata
    valid_intervals_count: int
    methodology_notes: List[str]
    intervals: List[CheckInterval]
