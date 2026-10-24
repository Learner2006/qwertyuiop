"""Fetch service wrapper for Elexon BMRS API data."""

from backend.scripts.fetch_data import fetch_fuelhh_jan2026, fetch_windfor_jan2026, process_and_save

__all__ = ["fetch_fuelhh_jan2026", "fetch_windfor_jan2026", "process_and_save"]
