"""Twelve Data time_series (optional; used only when TWELVEDATA_API_KEY is set).

Documented behaviour (twelvedata.com/docs):
  GET https://api.twelvedata.com/time_series
  auth: header "Authorization: apikey <key>" (recommended over the query param,
        and it keeps the key out of URLs and logs)
  interval: 1min, 5min, 15min, 30min, 45min, 1h, ...
  outputsize: 1..5000; start_date/end_date "YYYY-MM-DD HH:MM:SS"; timezone
  response: {"meta": {...}, "values": [{datetime, open, high, low, close, volume}], "status": "ok"}
  error:    {"code": 400, "message": "...", "status": "error"}
  default order is desc (newest first), so we page backwards from end_date.
"""
from __future__ import annotations

import logging
import time

import pandas as pd
import requests

from rig.data.http import DataFetchError, request_json
from rig.data.intervals import interval_timedelta

log = logging.getLogger(__name__)

TD_INTERVALS = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h"}
MAX_OUTPUTSIZE = 5000


def parse_values(values: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ts": pd.to_datetime([v["datetime"] for v in values], utc=True),
            "open": [float(v["open"]) for v in values],
            "high": [float(v["high"]) for v in values],
            "low": [float(v["low"]) for v in values],
            "close": [float(v["close"]) for v in values],
            # FX/metals often have no volume field
            "volume": [float(v.get("volume") or 0.0) for v in values],
        }
    )


def fetch_candles(
    symbol: str,
    interval: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    api_key: str,
    base_url: str,
    session: requests.Session | None = None,
    pause_s: float = 8.0,
    now: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Download closed bars in [start, end], paging backwards 5000 bars at a time."""
    session = session or requests.Session()
    headers = {"Authorization": f"apikey {api_key}"}
    fmt = "%Y-%m-%d %H:%M:%S"
    frames: list[pd.DataFrame] = []
    cursor_end = end
    while cursor_end >= start:
        params = {
            "symbol": symbol,
            "interval": TD_INTERVALS[interval],
            "start_date": start.strftime(fmt),
            "end_date": cursor_end.strftime(fmt),
            "timezone": "UTC",
            "outputsize": MAX_OUTPUTSIZE,
        }
        data = request_json(session, "GET", f"{base_url}/time_series", params=params, headers=headers)
        if data.get("status") == "error":
            if frames:  # paged past the start of available history
                break
            raise DataFetchError(f"Twelve Data error {data.get('code')}: {data.get('message')}")
        values = data.get("values") or []
        if not values:
            break
        page = parse_values(values)
        frames.append(page)
        oldest = page["ts"].min()
        if len(values) < MAX_OUTPUTSIZE or oldest <= start:
            break
        cursor_end = oldest - pd.Timedelta(seconds=1)
        if pause_s:
            time.sleep(pause_s)

    if not frames:
        return parse_values([])
    df = pd.concat(frames, ignore_index=True).drop_duplicates("ts")
    now = now if now is not None else pd.Timestamp.now(tz="UTC")
    df = df[df["ts"] + interval_timedelta(interval) <= now]  # drop the forming bar
    return df.sort_values("ts").reset_index(drop=True)
