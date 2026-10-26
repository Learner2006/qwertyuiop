"""Fetch service wrapper for Elexon BMRS API data."""

import sys
import os

try:
    from backend.scripts.fetch_data import fetch_fuelhh_jan2026, fetch_windfor_jan2026, process_and_save
except ImportError:
    try:
        from scripts.fetch_data import fetch_fuelhh_jan2026, fetch_windfor_jan2026, process_and_save
    except ImportError:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        from backend.scripts.fetch_data import fetch_fuelhh_jan2026, fetch_windfor_jan2026, process_and_save

__all__ = ["fetch_fuelhh_jan2026", "fetch_windfor_jan2026", "process_and_save"]
