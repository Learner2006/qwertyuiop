"""Fetch service module for live Elexon BMRS API data."""

import os
import sys

try:
    from backend.scripts.fetch_data import fetch_fuelhh_range, fetch_windfor_range, process_and_save
except ImportError:
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from scripts.fetch_data import fetch_fuelhh_range, fetch_windfor_range, process_and_save

__all__ = ["fetch_fuelhh_range", "fetch_windfor_range", "process_and_save"]
