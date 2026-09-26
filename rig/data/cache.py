"""Local parquet cache for candles so backtests never re-download.

One file per (source, symbol, interval). Every frame uses the same columns:
ts (bar open, tz-aware UTC), open, high, low, close, volume.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

CANDLE_COLUMNS = ["ts", "open", "high", "low", "close", "volume"]


def cache_path(cache_dir: str | Path, source: str, symbol: str, interval: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9]+", "_", symbol).strip("_")
    return Path(cache_dir) / source / f"{safe}_{interval}.parquet"


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce types, sort, drop duplicate bars and malformed rows."""
    if df.empty:
        return pd.DataFrame(columns=CANDLE_COLUMNS).astype(
            {"open": float, "high": float, "low": float, "close": float, "volume": float}
        ).assign(ts=pd.to_datetime([], utc=True))
    out = df[CANDLE_COLUMNS].copy()
    out["ts"] = pd.to_datetime(out["ts"], utc=True)
    for col in CANDLE_COLUMNS[1:]:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype(float)
    out = out.drop_duplicates("ts", keep="last").sort_values("ts").reset_index(drop=True)

    bad = (
        out[["open", "high", "low", "close"]].isna().any(axis=1)
        | (out["high"] < out[["open", "close"]].max(axis=1))
        | (out["low"] > out[["open", "close"]].min(axis=1))
    )
    if bad.any():
        log.warning("dropping %d malformed candle rows", int(bad.sum()))
        out = out[~bad].reset_index(drop=True)
    return out


def read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return normalize(pd.DataFrame(columns=CANDLE_COLUMNS))
    return normalize(pd.read_parquet(path))


def merge_and_write(path: Path, new: pd.DataFrame) -> pd.DataFrame:
    """Merge new bars into the cache file (new rows win) and write atomically."""
    merged = normalize(pd.concat([read(path), new], ignore_index=True))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    merged.to_parquet(tmp, index=False)
    tmp.replace(path)
    return merged


def load_candles(cache_dir: str | Path, source: str, symbol: str, interval: str) -> pd.DataFrame:
    path = cache_path(cache_dir, source, symbol, interval)
    if not path.exists():
        raise FileNotFoundError(
            f"no cached candles for {source}/{symbol}/{interval}; run `python -m rig fetch` first"
        )
    return read(path)
