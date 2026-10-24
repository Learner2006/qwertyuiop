"""Central backend configuration for the Wind Day-Ahead Estimator.
Frozen parameters according to specification.
"""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    PRODUCT_NAME: str = "Wind Day-Ahead Estimator"
    ONE_LINE_PITCH: str = "Elexon forecasts wind. We estimate how much of it a buyer can safely rely on."
    
    # Historical calibration parameters
    LOOKBACK_HOURS: int = 48
    BLEND_THRESHOLD_OBSERVATIONS: int = 96
    DEFAULT_PERCENTILE: float = 75.0
    MIN_PERCENTILE: float = 60.0
    MAX_PERCENTILE: float = 90.0
    COLD_START_HAIRCUT: float = 0.15
    DECISION_CUTOFF_HOUR_UTC: int = 9
    DECISION_CUTOFF_MINUTE_UTC: int = 0
    
    # Error band quantiles
    ERROR_BAND_LOWER_QUANTILE: float = 10.0
    ERROR_BAND_UPPER_QUANTILE: float = 90.0
    
    # Date bounds
    MIN_DECISION_DATE: str = "2026-01-01"
    MAX_DECISION_DATE: str = "2026-01-30"
    
    # Units and constants
    DT_HOURS: float = 0.5  # Half-hour interval duration
    MW_PER_GW: float = 1000.0
    
    # Data path
    DATA_PATH: str = os.getenv(
        "CACHED_DATASET_PATH",
        os.path.join(os.path.dirname(__file__), "data", "jan2026.parquet")
    )
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]


settings = Settings()
