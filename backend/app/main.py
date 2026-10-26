"""FastAPI entry point for the Wind Day-Ahead Estimator backend."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import check, estimate, health, summary, validation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("main")

app = FastAPI(
    title=settings.PRODUCT_NAME,
    description="Elexon forecasts wind. We estimate how much of it a buyer can safely rely on.",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/api")
app.include_router(estimate.router, prefix="/api")
app.include_router(check.router, prefix="/api")
app.include_router(summary.router, prefix="/api")
app.include_router(validation.router, prefix="/api")


@app.get("/")
def root():
    return {
        "product": settings.PRODUCT_NAME,
        "pitch": settings.ONE_LINE_PITCH,
        "docs": "/docs",
        "health": "/api/health",
    }
