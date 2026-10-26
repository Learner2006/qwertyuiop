"""Data preparation service for the Wind Day-Ahead Estimator.
Single source of truth for loading cached Elexon data, selecting forecasts
strictly at or before the decision cutoff, and assembling historical calibration observations.
"""

import datetime
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd

from app.config import settings


class DataManager:
    _instance: Optional["DataManager"] = None
    _df: Optional[pd.DataFrame] = None
    _actuals_df: Optional[pd.DataFrame] = None
    _forecasts_df: Optional[pd.DataFrame] = None
    _day_ahead_cache: Dict[pd.Timestamp, float] = {}

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or settings.DATA_PATH
        self._day_ahead_cache = {}
        self._file_meta = None
        self.load_data()

    @property
    def file_metadata(self) -> dict:
        if self._file_meta is None:
            if os.path.exists(self.data_path):
                import hashlib
                h = hashlib.sha256()
                with open(self.data_path, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
                sz = os.path.getsize(self.data_path)
                mt = os.path.getmtime(self.data_path)
                mtime_utc = datetime.datetime.fromtimestamp(mt, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                self._file_meta = {
                    "filename": os.path.basename(self.data_path),
                    "size_kb": int(round(sz / 1024.0)),
                    "build_date_utc": mtime_utc,
                    "sha256": h.hexdigest(),
                    "record_count": len(self._df) if self._df is not None else 0,
                }
            else:
                self._file_meta = {}
        return self._file_meta

    @classmethod
    def get_instance(cls, data_path: Optional[str] = None) -> "DataManager":
        if cls._instance is None:
            cls._instance = cls(data_path)
        return cls._instance

    def load_data(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Cached dataset not found at {self.data_path}")
        
        self._df = pd.read_parquet(self.data_path)
        self._actuals_df = self._df[self._df["record_type"] == "actual"].sort_values("interval_start").reset_index(drop=True)
        self._forecasts_df = self._df[self._df["record_type"] == "forecast"].sort_values("publish_time").reset_index(drop=True)
        self._precompute_day_ahead_forecasts()

    def _precompute_day_ahead_forecasts(self):
        """Precompute canonical day-ahead forecast for every half-hour target in dataset.
        For each decision date D at 09:00 UTC, the forecast for target D+1
        is the latest published version at or before 09:00 UTC on day D.
        """
        self._day_ahead_cache.clear()
        cutoff_time = datetime.time(
            settings.DECISION_CUTOFF_HOUR_UTC,
            settings.DECISION_CUTOFF_MINUTE_UTC
        )
        
        min_date = self._actuals_df["interval_start"].min().date()
        unique_target_dates = [
            d for d in sorted(self._actuals_df["interval_start"].dt.date.unique())
            if d > min_date
        ]
        for target_date in unique_target_dates:
            dec_date = target_date - datetime.timedelta(days=1)
            cutoff_dt = pd.Timestamp(datetime.datetime.combine(dec_date, cutoff_time), tz="UTC")
            
            # Target intervals for D+1
            t_start = pd.Timestamp(datetime.datetime.combine(target_date, datetime.time(0, 0)), tz="UTC")
            t_end = pd.Timestamp(datetime.datetime.combine(target_date, datetime.time(23, 30)), tz="UTC")
            
            # Fast filter for target intervals published at or before cutoff
            mask = (
                (self._forecasts_df["interval_start"] >= t_start)
                & (self._forecasts_df["interval_start"] <= t_end)
                & (self._forecasts_df["publish_time"] <= cutoff_dt)
            )
            target_fc = self._forecasts_df[mask]
            if not target_fc.empty:
                latest_versions = target_fc.sort_values("publish_time").groupby("interval_start").last()
                for istart, val in zip(latest_versions.index, latest_versions["generation_gw"]):
                    self._day_ahead_cache[istart] = float(val)

    def set_operational_parameters(
        self,
        cutoff_hour: Optional[int] = None,
        lag_hours: Optional[int] = None,
        lookback_hours: Optional[int] = None,
    ):
        """Temporarily updates operational parameters and refreshes precomputed forecast cache."""
        if cutoff_hour is not None:
            settings.DECISION_CUTOFF_HOUR_UTC = cutoff_hour
        if lag_hours is not None:
            settings.ACTUALS_PUBLICATION_LAG_HOURS = lag_hours
        if lookback_hours is not None:
            settings.LOOKBACK_HOURS = lookback_hours
            settings.BLEND_THRESHOLD_OBSERVATIONS = lookback_hours * 2
        self._precompute_day_ahead_forecasts()

    def reset_operational_parameters(self):
        """Resets operational parameters to config defaults."""
        settings.DECISION_CUTOFF_HOUR_UTC = 9
        settings.DECISION_CUTOFF_MINUTE_UTC = 0
        settings.ACTUALS_PUBLICATION_LAG_HOURS = 1
        settings.LOOKBACK_HOURS = 48
        settings.BLEND_THRESHOLD_OBSERVATIONS = 96
        self._precompute_day_ahead_forecasts()

    def get_dataset_metadata(self) -> dict:
        if self._actuals_df is None or len(self._actuals_df) == 0:
            return {"available": False, "count": 0}
        min_date = self._actuals_df["interval_start"].min().strftime("%Y-%m-%d")
        max_date = self._actuals_df["interval_start"].max().strftime("%Y-%m-%d")
        return {
            "available": True,
            "count": len(self._df),
            "start": min_date,
            "end": max_date,
        }

    def get_target_intervals(self, target_date: datetime.date) -> List[pd.Timestamp]:
        t_start = pd.Timestamp(datetime.datetime.combine(target_date, datetime.time(0, 0)), tz="UTC")
        t_end = pd.Timestamp(datetime.datetime.combine(target_date, datetime.time(23, 30)), tz="UTC")
        return list(pd.date_range(t_start, t_end, freq="30min"))

    def select_target_forecast(
        self,
        decision_date: datetime.date,
        target_date: datetime.date
    ) -> List[dict]:
        """Select latest eligible forecast for each interval of target date published at or before cutoff."""
        cutoff_dt = pd.Timestamp(
            datetime.datetime.combine(
                decision_date,
                datetime.time(settings.DECISION_CUTOFF_HOUR_UTC, settings.DECISION_CUTOFF_MINUTE_UTC)
            ),
            tz="UTC"
        )
        
        target_intervals = self.get_target_intervals(target_date)
        
        # Filter forecasts published strictly at or before cutoff
        eligible = self._forecasts_df[self._forecasts_df["publish_time"] <= cutoff_dt]
        target_fc = eligible[eligible["interval_start"].isin(target_intervals)]
        
        if target_fc.empty:
            raise ValueError(f"No eligible forecasts found for target date {target_date} before cutoff {cutoff_dt}")
        
        latest_versions = target_fc.sort_values("publish_time").groupby("interval_start").last()
        
        results = []
        for idx, istart in enumerate(target_intervals):
            if istart not in latest_versions.index:
                raise ValueError(f"Missing forecast for interval {istart} published before cutoff")
            row = latest_versions.loc[istart]
            results.append({
                "interval_start": istart,
                "settlement_period": idx + 1,
                "generation_gw": float(row["generation_gw"]),
                "generation_mw": float(row["generation_mw"]),
                "publish_time": row["publish_time"],
            })
        
        return results

    def get_calibration_observations(
        self,
        decision_date: datetime.date
    ) -> List[dict]:
        """Construct the calibration history strictly before decision cutoff.
        Uses valid historical half-hourly observations whose day-ahead forecast and actuals
        were published and available by the cutoff.
        """
        cutoff_dt = pd.Timestamp(
            datetime.datetime.combine(
                decision_date,
                datetime.time(settings.DECISION_CUTOFF_HOUR_UTC, settings.DECISION_CUTOFF_MINUTE_UTC)
            ),
            tz="UTC"
        )
        
        # Actuals available by cutoff, factoring in explicit physical recording & publication lag
        # Only intervals that concluded and published at least ACTUALS_PUBLICATION_LAG_HOURS before cutoff
        actuals_available_cutoff = cutoff_dt - pd.Timedelta(hours=settings.ACTUALS_PUBLICATION_LAG_HOURS)
        available_actuals = self._actuals_df[self._actuals_df["publish_time"] <= actuals_available_cutoff]
        
        # Fast slice of most recent available records (never need more than 3x blend threshold)
        if len(available_actuals) > settings.BLEND_THRESHOLD_OBSERVATIONS * 3:
            available_actuals = available_actuals.iloc[-settings.BLEND_THRESHOLD_OBSERVATIONS * 3:]

        # Match with canonical day-ahead forecast
        history = []
        for istart, act_gw in zip(available_actuals["interval_start"], available_actuals["generation_gw"]):
            if istart in self._day_ahead_cache:
                fc_gw = self._day_ahead_cache[istart]
                act_gw_val = float(act_gw)
                history.append({
                    "interval_start": istart,
                    "forecast_gw": fc_gw,
                    "actual_gw": act_gw_val,
                    "error_gw": fc_gw - act_gw_val,
                })
        
        # Sort and take at most BLEND_THRESHOLD_OBSERVATIONS (96)
        history.sort(key=lambda x: x["interval_start"])
        return history[-settings.BLEND_THRESHOLD_OBSERVATIONS:]

    def get_target_actuals(self, target_date: datetime.date) -> List[dict]:
        """Retrieve target-day actual observations (used ONLY by reliability check)."""
        target_intervals = self.get_target_intervals(target_date)
        sub_df = self._actuals_df[self._actuals_df["interval_start"].isin(target_intervals)]
        
        if len(sub_df) != 48:
            raise ValueError(f"Target actuals incomplete for date {target_date}: expected 48, found {len(sub_df)}")
        
        results = []
        for idx, istart in enumerate(target_intervals):
            matching = sub_df[sub_df["interval_start"] == istart]
            if matching.empty:
                raise ValueError(f"Missing actual for interval {istart}")
            row = matching.iloc[0]
            results.append({
                "interval_start": istart,
                "settlement_period": idx + 1,
                "generation_gw": float(row["generation_gw"]),
                "generation_mw": float(row["generation_mw"]),
                "publish_time": row["publish_time"],
            })
        return results
