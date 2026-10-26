"""Script to fetch public Elexon BMRS WINDFOR and FUELHH data.
Adheres to Elexon API limitations (max 7-day query window) and saves a clean,
reproducible Parquet file to backend/app/data/.
"""

import argparse
import datetime
import json
import logging
import os
import sys
import time
import urllib.request
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fetch_data")

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "data"))
JAN2026_FILE = os.path.join(OUTPUT_DIR, "jan2026.parquet")
VALIDATION_FILE = os.path.join(OUTPUT_DIR, "validation_2026-01-29_to_2026-09-30.parquet")


def fetch_url_json(url: str, retries: int = 5, timeout: int = 45) -> dict:
    headers = {"User-Agent": "WindDayAheadEstimator/1.0 (+https://elexon.co.uk)"}
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status}")
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.warning("Attempt %d failed for %s: %s", attempt, url, e)
            if attempt == retries:
                raise
            time.sleep(2 * attempt)
    return {}


def fetch_fuelhh_range(start_date: datetime.date, end_date: datetime.date) -> list:
    """Fetch actual wind generation from FUELHH for a date range in 7-day chunks."""
    logger.info("Fetching FUELHH data from %s to %s...", start_date, end_date)
    cur = start_date
    records = []

    while cur <= end_date:
        chunk_end = min(cur + datetime.timedelta(days=6), end_date)
        url = (
            f"{ELEXON_BASE_URL}/FUELHH"
            f"?settlementDateFrom={cur.isoformat()}&settlementDateTo={chunk_end.isoformat()}"
        )
        logger.info("Fetching FUELHH chunk: %s to %s", cur, chunk_end)
        payload = fetch_url_json(url)
        raw_items = payload.get("data", [])
        wind_items = [r for r in raw_items if r.get("fuelType") == "WIND"]
        records.extend(wind_items)
        cur = chunk_end + datetime.timedelta(days=1)

    logger.info("Total FUELHH wind records fetched: %d", len(records))
    return records


def fetch_windfor_range(start_date: datetime.date, end_date: datetime.date) -> list:
    """Fetch wind generation forecast from WINDFOR published across a date range in 7-day chunks."""
    logger.info("Fetching WINDFOR forecast records from %s to %s...", start_date, end_date)
    cur = start_date
    records = []

    while cur <= end_date:
        chunk_end = min(cur + datetime.timedelta(days=6), end_date)
        url = (
            f"{ELEXON_BASE_URL}/WINDFOR"
            f"?publishDateTimeFrom={cur.isoformat()}T00:00:00Z"
            f"&publishDateTimeTo={chunk_end.isoformat()}T23:59:59Z"
        )
        logger.info("Fetching WINDFOR chunk: %s to %s", cur, chunk_end)
        payload = fetch_url_json(url)
        raw_items = payload.get("data", [])
        records.extend(raw_items)
        cur = chunk_end + datetime.timedelta(days=1)

    logger.info("Total WINDFOR forecast records fetched: %d", len(records))
    return records


def process_and_save(fuelhh_records: list, windfor_records: list, output_path: str):
    """Normalize timestamps to UTC, convert MW to GW, expand hourly WINDFOR to half-hourly intervals,
    and save to Parquet.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    rows = []

    # 1. Process FUELHH actuals
    # Each FUELHH record is 30 minutes, representing a settlement period.
    for r in fuelhh_records:
        start_dt = pd.to_datetime(r["startTime"], utc=True)
        pub_dt = pd.to_datetime(r["publishTime"], utc=True)
        gen_mw = float(r["generation"])
        rows.append({
            "record_type": "actual",
            "interval_start": start_dt,
            "publish_time": pub_dt,
            "generation_mw": gen_mw,
            "generation_gw": gen_mw / 1000.0,
            "settlement_date": r.get("settlementDate"),
            "settlement_period": int(r.get("settlementPeriod", 0)),
        })

    # 2. Process WINDFOR forecasts
    # WINDFOR gives hourly forecasts. Expand each hour into two 30-min settlement intervals (:00 and :30)
    for r in windfor_records:
        start_dt = pd.to_datetime(r["startTime"], utc=True)
        pub_dt = pd.to_datetime(r["publishTime"], utc=True)
        gen_mw = float(r["generation"])
        gen_gw = gen_mw / 1000.0

        # Interval 1: start_dt (e.g. HH:00)
        rows.append({
            "record_type": "forecast",
            "interval_start": start_dt,
            "publish_time": pub_dt,
            "generation_mw": gen_mw,
            "generation_gw": gen_gw,
            "settlement_date": start_dt.strftime("%Y-%m-%d"),
            "settlement_period": None,
        })
        # Interval 2: start_dt + 30 min (e.g. HH:30)
        start_dt_30 = start_dt + pd.Timedelta(minutes=30)
        rows.append({
            "record_type": "forecast",
            "interval_start": start_dt_30,
            "publish_time": pub_dt,
            "generation_mw": gen_mw,
            "generation_gw": gen_gw,
            "settlement_date": start_dt_30.strftime("%Y-%m-%d"),
            "settlement_period": None,
        })

    df = pd.DataFrame(rows)
    # Deduplicate in case of duplicate API records
    df = df.drop_duplicates(subset=["record_type", "interval_start", "publish_time"])
    df = df.sort_values(by=["record_type", "interval_start", "publish_time"]).reset_index(drop=True)

    df.to_parquet(output_path, index=False)
    logger.info("Successfully saved %d rows to %s (File size: %.2f KB)",
                len(df), output_path, os.path.getsize(output_path) / 1024.0)


def main():
    parser = argparse.ArgumentParser(description="Fetch Elexon BMRS WINDFOR and FUELHH data for live or historical replay")
    parser.add_argument(
        "--dataset",
        choices=["jan2026", "validation"],
        default=None,
        help="Predefined dataset to fetch ('jan2026' or 'validation')",
    )
    parser.add_argument("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD) for custom/live date range")
    parser.add_argument("--end-date", type=str, default=None, help="End date (YYYY-MM-DD) for custom/live date range")
    parser.add_argument("--days", type=int, default=None, help="Fetch trailing N days up to today")
    parser.add_argument("--output", type=str, default=None, help="Custom output parquet path")
    args = parser.parse_args()

    if args.days is not None:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=args.days)
        output_file = args.output or os.path.join(OUTPUT_DIR, f"live_{start_date}_to_{end_date}.parquet")
    elif args.start_date and args.end_date:
        start_date = datetime.date.fromisoformat(args.start_date)
        end_date = datetime.date.fromisoformat(args.end_date)
        output_file = args.output or os.path.join(OUTPUT_DIR, f"live_{start_date}_to_{end_date}.parquet")
    elif args.dataset == "validation":
        start_date = datetime.date(2026, 1, 29)
        end_date = datetime.date(2026, 9, 30)
        output_file = args.output or VALIDATION_FILE
    else:
        # Default to jan2026
        start_date = datetime.date(2026, 1, 1)
        end_date = datetime.date(2026, 1, 31)
        output_file = args.output or JAN2026_FILE

    logger.info("Target fetch window: %s to %s -> saving to %s", start_date, end_date, output_file)
    fuelhh = fetch_fuelhh_range(start_date, end_date)
    windfor = fetch_windfor_range(start_date, end_date)
    process_and_save(fuelhh, windfor, output_file)


if __name__ == "__main__":
    main()
