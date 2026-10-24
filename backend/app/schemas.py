"""Pydantic schemas for the Wind Day-Ahead Estimator API.
Strict validation and UTC ISO timestamps.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    product_name: str
    dataset_available: bool
    dataset_records_count: int
    date_coverage_start: Optional[str] = None
    date_coverage_end: Optional[str] = None
    version: str = "1.0.0"


class MonthSummaryResponse(BaseModel):
    decision_dates_count: int
    period_start: str
    period_end: str
    percentile: float
    total_elexon_shortfall_mwh: float
    total_safe_shortfall_mwh: float
    total_avoided_shortfall_mwh: float
    total_extra_advance_planned_mwh: float
    days_shortfall_reduced: int
    days_shortfall_increased: int
    summary_sentence: str


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
    
    # Energy metrics in MWh
    elexon_shortfall_mwh: float
    safe_shortfall_mwh: float
    saved_shortfall_mwh: float
    extra_advance_planned_mwh: float
    
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
