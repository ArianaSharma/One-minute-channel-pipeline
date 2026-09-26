"""Seeded synthetic candles for offline and mock-mode runs.

Not market data. It only exists so the pipeline can run end to end without
network access. Returns are fat-tailed, busier in the London/NY sessions, and
correlated across symbols. Each symbol is generated at 1m and resampled up, so
all timeframes agree with each other.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from rig.data.cache import normalize

START_PRICES = {"BTC": 60_000.0, "ETH": 3_000.0}
DEFAULT_START = pd.Timestamp("2026-01-05", tz="UTC")
BASE_VOL_1M = 0.0004  # ~0.04% per minute at the quietest hours


def _session_vol_multiplier(minute_of_day: np.ndarray) -> np.ndarray:
    hour = minute_of_day / 60.0
    mult = np.full(hour.shape, 0.7)
    mult[(hour >= 7) & (hour < 12.5)] = 1.3   # London
    mult[(hour >= 12.5) & (hour < 16)] = 1.6  # NY AM
    mult[(hour >= 16) & (hour < 21)] = 1.1
    return mult


def generate_1m(
    symbols: list[str],
    days: int,
    seed: int,
    correlation: float = 0.8,
    start: pd.Timestamp = DEFAULT_START,
) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    n = days * 24 * 60
    ts = pd.date_range(start, periods=n, freq="1min", tz="UTC")
    vol = BASE_VOL_1M * _session_vol_multiplier(np.asarray(ts.hour * 60 + ts.minute))

    # Correlated fat-tailed shocks (Student-t, df=4, scaled to unit variance).
    k = len(symbols)
    corr = np.full((k, k), correlation)
    np.fill_diagonal(corr, 1.0)
    chol = np.linalg.cholesky(corr)
    shocks = rng.standard_t(4, size=(n, k)) / np.sqrt(2.0)
    shocks = shocks @ chol.T

    # Slow drift regimes so there is trend and chop, not just noise.
    regime_len = 6 * 60
    drift = np.repeat(rng.normal(0, 0.00002, size=n // regime_len + 1), regime_len)[:n]

    out: dict[str, pd.DataFrame] = {}
    for j, sym in enumerate(symbols):
        rets = drift + vol * shocks[:, j]
        close = START_PRICES.get(sym, 100.0) * np.exp(np.cumsum(rets))
        open_ = np.concatenate([[close[0] / np.exp(rets[0])], close[:-1]])
        wick = np.abs(rng.normal(0, 0.5, size=(n, 2))) * vol[:, None] * close[:, None]
        high = np.maximum(open_, close) + wick[:, 0]
        low = np.minimum(open_, close) - wick[:, 1]
        volume = rng.gamma(2.0, 5.0, size=n) * _session_vol_multiplier(
            np.asarray(ts.hour * 60 + ts.minute)
        )
        out[sym] = normalize(
            pd.DataFrame({"ts": ts, "open": open_, "high": high, "low": low,
                          "close": close, "volume": volume})
        )
    return out


def resample(df_1m: pd.DataFrame, interval: str) -> pd.DataFrame:
    rule = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h"}[interval]
    if rule == "1min":
        return df_1m.copy()
    agg = (
        df_1m.set_index("ts")
        .resample(rule, label="left", closed="left")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna()
        .reset_index()
    )
    return normalize(agg)
