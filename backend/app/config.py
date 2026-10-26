"""Central backend configuration for the Wind Day-Ahead Estimator.
Frozen parameters according to specification.
"""

import json
import os
from typing import List, Optional
from pydantic import BaseModel


def parse_cors_origins(val: Optional[str], env: str = "development") -> List[str]:
    """Parses CORS origins supporting comma-separated strings or JSON arrays.
    Fails fast in production if origins are empty or contain wildcard '*'."""
    if not val:
        origins = [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:3000",
        ]
    else:
        v = val.strip()
        if v.startswith("[") and v.endswith("]"):
            try:
                origins = json.loads(v)
            except Exception:
                origins = [x.strip().strip('"').strip("'") for x in v[1:-1].split(",") if x.strip()]
        else:
            origins = [x.strip().strip('"').strip("'") for x in v.split(",") if x.strip()]

    if env == "production":
        if not origins or "*" in origins:
            raise ValueError("In production, CORS_ORIGINS must not be empty or contain wildcard '*'")

    return origins


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
    ACTUALS_PUBLICATION_LAG_HOURS: float = 1.0  # 1-hour publication lag for metered outturns
    
    # Error band quantiles
    ERROR_BAND_LOWER_QUANTILE: float = 10.0
    ERROR_BAND_UPPER_QUANTILE: float = 90.0
    
    # Date bounds
    MIN_DECISION_DATE: str = "2026-01-01"
    MAX_DECISION_DATE: str = "2026-01-30"
    
    # Units and constants
    DT_HOURS: float = 0.5  # Half-hour interval duration
    MW_PER_GW: float = 1000.0
    MWH_FACTOR: float = 500.0  # 1000.0 * 0.5
    FULL_MONTH_SLOTS: int = 1440
    SLOTS_PER_DAY: int = 48
    
    # Data path
    DATA_PATH: str = os.getenv(
        "CACHED_DATASET_PATH",
        os.path.join(os.path.dirname(__file__), "data", "jan2026.parquet")
    )
    
    # Environment and CORS
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: list = parse_cors_origins(
        os.getenv("CORS_ORIGINS"),
        os.getenv("ENVIRONMENT", "development"),
    )


settings = Settings()
