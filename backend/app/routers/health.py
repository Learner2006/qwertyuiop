"""Health endpoint for Wind Day-Ahead Estimator."""

from fastapi import APIRouter
from app.config import settings
from app.schemas import HealthResponse
from app.services.prepare import DataManager

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health():
    try:
        dm = DataManager.get_instance()
        meta = dm.get_dataset_metadata()
        return HealthResponse(
            status="healthy",
            product_name=settings.PRODUCT_NAME,
            dataset_available=meta.get("available", False),
            dataset_records_count=meta.get("count", 0),
            date_coverage_start=meta.get("start"),
            date_coverage_end=meta.get("end"),
            version="1.0.0"
        )
    except Exception as e:
        return HealthResponse(
            status="degraded",
            product_name=settings.PRODUCT_NAME,
            dataset_available=False,
            dataset_records_count=0,
            version="1.0.0"
        )
