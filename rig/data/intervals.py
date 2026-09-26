"""Interval names used across the rig ("1m", "5m", "15m", "1h")."""
from __future__ import annotations

import pandas as pd

INTERVAL_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}


def interval_ms(interval: str) -> int:
    return INTERVAL_MINUTES[interval] * 60_000


def interval_timedelta(interval: str) -> pd.Timedelta:
    return pd.Timedelta(minutes=INTERVAL_MINUTES[interval])
