"""Hyperliquid public info API: candleSnapshot (market data only, no key).

Documented behaviour (hyperliquid-docs, "Info endpoint"):
  POST https://api.hyperliquid.xyz/info
  {"type": "candleSnapshot", "req": {"coin", "interval", "startTime", "endTime"}}
  - only the most recent 5000 candles are available per interval
  - time-range responses return at most 500 elements; page by using the last
    returned timestamp as the next startTime
  - each candle: t (open ms), T (close ms), o/h/l/c/v (strings), n, s, i
"""
from __future__ import annotations

import logging
import time

import pandas as pd
import requests

from rig.data.http import request_json
from rig.data.intervals import interval_ms

log = logging.getLogger(__name__)

MAX_AVAILABLE_CANDLES = 5000


def parse_candles(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ts": pd.to_datetime([r["t"] for r in rows], unit="ms", utc=True),
            "open": [float(r["o"]) for r in rows],
            "high": [float(r["h"]) for r in rows],
            "low": [float(r["l"]) for r in rows],
            "close": [float(r["c"]) for r in rows],
            "volume": [float(r["v"]) for r in rows],
            "close_ms": [int(r["T"]) for r in rows],
        }
    )


def fetch_candles(
    coin: str,
    interval: str,
    start_ms: int,
    end_ms: int,
    *,
    base_url: str,
    session: requests.Session | None = None,
    pause_s: float = 0.25,
    now_ms: int | None = None,
) -> pd.DataFrame:
    """Download closed candles in [start_ms, end_ms], paging 500 at a time."""
    session = session or requests.Session()
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    step = interval_ms(interval)
    frames: list[pd.DataFrame] = []
    cursor = start_ms
    while cursor <= end_ms:
        body = {
            "type": "candleSnapshot",
            "req": {"coin": coin, "interval": interval, "startTime": cursor, "endTime": end_ms},
        }
        rows = request_json(session, "POST", base_url, json=body)
        if not rows:
            break
        frames.append(parse_candles(rows))
        last_open = max(int(r["t"]) for r in rows)
        if last_open < cursor:  # no progress; stop rather than loop forever
            break
        cursor = last_open + step
        if pause_s:
            time.sleep(pause_s)

    if not frames:
        return parse_candles([]).drop(columns="close_ms")
    df = pd.concat(frames, ignore_index=True).drop_duplicates("ts", keep="last")
    df = df[df["close_ms"] < now_ms]  # drop the candle that is still forming
    return df.drop(columns="close_ms").sort_values("ts").reset_index(drop=True)


def default_start_ms(interval: str, now_ms: int) -> int:
    """Earliest time worth asking for: Hyperliquid keeps only the last 5000 candles."""
    return now_ms - MAX_AVAILABLE_CANDLES * interval_ms(interval)
