"""`rig fetch`: download candles into the parquet cache, only asking for new bars."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from rig.config import env, resolve
from rig.data import cache, hyperliquid, synthetic, twelvedata
from rig.data.intervals import interval_ms, interval_timedelta

log = logging.getLogger(__name__)


@dataclass
class FetchResult:
    source: str
    symbol: str
    interval: str
    new_rows: int
    total_rows: int
    first: pd.Timestamp | None
    last: pd.Timestamp | None
    error: str | None = None

    def line(self) -> str:
        if self.error:
            return f"{self.source:12} {self.symbol:8} {self.interval:4} ERROR {self.error}"
        span = f"{self.first:%Y-%m-%d %H:%M} -> {self.last:%Y-%m-%d %H:%M}" if self.total_rows else "empty"
        return (f"{self.source:12} {self.symbol:8} {self.interval:4} "
                f"+{self.new_rows:<6} total {self.total_rows:<7} {span} UTC")


def _result(source, symbol, interval, new, merged) -> FetchResult:
    first = merged["ts"].iloc[0] if len(merged) else None
    last = merged["ts"].iloc[-1] if len(merged) else None
    return FetchResult(source, symbol, interval, len(new), len(merged), first, last)


def fetch_hyperliquid(cfg: dict, coins: list[str], intervals: list[str]) -> list[FetchResult]:
    hl = cfg["data"]["hyperliquid"]
    cache_dir = resolve(cfg["data"]["cache_dir"])
    now_ms = int(pd.Timestamp.now(tz="UTC").timestamp() * 1000)
    results = []
    for coin in coins:
        for interval in intervals:
            path = cache.cache_path(cache_dir, "hyperliquid", coin, interval)
            existing = cache.read(path)
            if len(existing):
                # re-request the last couple of bars in case the final one was revised
                start_ms = int(existing["ts"].iloc[-1].timestamp() * 1000) - 2 * interval_ms(interval)
            else:
                start_ms = hyperliquid.default_start_ms(interval, now_ms)
            try:
                new = hyperliquid.fetch_candles(
                    coin, interval, start_ms, now_ms,
                    base_url=hl["base_url"], pause_s=hl.get("request_pause_s", 0.25), now_ms=now_ms,
                )
            except Exception as exc:  # keep going for the other series
                results.append(FetchResult("hyperliquid", coin, interval, 0, len(existing),
                                           None, None, error=str(exc)))
                continue
            merged = cache.merge_and_write(path, new)
            results.append(_result("hyperliquid", coin, interval, new, merged))
    return results


def fetch_twelvedata(cfg: dict, symbols: list[str], intervals: list[str]) -> list[FetchResult]:
    api_key = env("TWELVEDATA_API_KEY")
    if not api_key:
        log.info("TWELVEDATA_API_KEY not set; skipping Twelve Data")
        return []
    td = cfg["data"]["twelvedata"]
    cache_dir = resolve(cfg["data"]["cache_dir"])
    now = pd.Timestamp.now(tz="UTC").floor("min")
    results = []
    for symbol in symbols:
        for interval in intervals:
            path = cache.cache_path(cache_dir, "twelvedata", symbol, interval)
            existing = cache.read(path)
            if len(existing):
                start = existing["ts"].iloc[-1] - 2 * interval_timedelta(interval)
            else:
                start = now - pd.Timedelta(days=td.get("history_days", 180))
            try:
                new = twelvedata.fetch_candles(
                    symbol, interval, start, now, api_key=api_key, base_url=td["base_url"],
                    pause_s=td.get("request_pause_s", 8.0), now=now,
                )
            except Exception as exc:
                results.append(FetchResult("twelvedata", symbol, interval, 0, len(existing),
                                           None, None, error=str(exc)))
                continue
            merged = cache.merge_and_write(path, new)
            results.append(_result("twelvedata", symbol, interval, new, merged))
    return results


def build_synthetic(cfg: dict, intervals: list[str]) -> list[FetchResult]:
    syn = cfg["data"]["synthetic"]
    cache_dir = resolve(cfg["data"]["cache_dir"])
    series = synthetic.generate_1m(syn["symbols"], syn["days"], syn["seed"], syn.get("correlation", 0.8))
    results = []
    for symbol, df_1m in series.items():
        for interval in intervals:
            df = synthetic.resample(df_1m, interval)
            path = cache.cache_path(cache_dir, "synthetic", symbol, interval)
            path.unlink(missing_ok=True)  # deterministic: rebuild from the seed every time
            merged = cache.merge_and_write(path, df)
            results.append(_result("synthetic", symbol, interval, df, merged))
    return results
