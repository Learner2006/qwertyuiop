"""Router for out-of-time validation summary data (Milestone R4)."""

import json
import os
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["validation"])

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
SUMMARY_FILE = os.path.join(DATA_DIR, "validation_summary.json")


@router.get("/validation")
def get_validation_summary():
    """Returns the out-of-time validation results dataset."""
    if not os.path.exists(SUMMARY_FILE):
        raise HTTPException(
            status_code=404,
            detail="Validation summary dataset not found.",
        )
    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
