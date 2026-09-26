"""Price-structure primitives: ATR, fractal swings, fair value gaps, order blocks, OTE.

Everything here is computed per bar from data up to and including that bar,
except swing pivots, which need `k` bars on the right and so are only
*confirmed* k bars later. Callers must respect `swing_confirmed_at`.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()


def swing_points(df: pd.DataFrame, k: int = 2) -> tuple[np.ndarray, np.ndarray]:
    """Boolean arrays marking fractal swing highs/lows (k bars each side)."""
    high, low = df["high"].to_numpy(), df["low"].to_numpy()
    n = len(df)
    sh = np.zeros(n, dtype=bool)
    sl = np.zeros(n, dtype=bool)
    for i in range(k, n - k):
        left_h, right_h = high[i - k:i], high[i + 1:i + k + 1]
        left_l, right_l = low[i - k:i], low[i + 1:i + k + 1]
        sh[i] = high[i] > left_h.max() and high[i] >= right_h.max()
        sl[i] = low[i] < left_l.min() and low[i] <= right_l.min()
    return sh, sl


def swing_confirmed_at(i: int, k: int = 2) -> int:
    """Index of the bar whose close confirms a pivot at bar i."""
    return i + k


@dataclass(frozen=True)
class Zone:
    kind: str       # "fvg" | "ob"
    low: float
    high: float
    index: int      # bar index where the zone is complete

    def overlap(self, lo: float, hi: float) -> tuple[float, float] | None:
        a, b = max(self.low, lo), min(self.high, hi)
        return (a, b) if a < b else None


def fair_value_gaps(df: pd.DataFrame, start: int, end: int, direction: str) -> list[Zone]:
    """3-candle FVGs whose third candle lies in [start+2, end].

    bearish (short): candle1.low > candle3.high -> gap [c3.high, c1.low]
    bullish (long):  candle1.high < candle3.low -> gap [c1.high, c3.low]
    """
    high, low = df["high"].to_numpy(), df["low"].to_numpy()
    zones = []
    for c in range(max(start + 2, 2), end + 1):
        a = c - 2
        if direction == "short" and low[a] > high[c]:
            zones.append(Zone("fvg", float(high[c]), float(low[a]), c))
        elif direction == "long" and high[a] < low[c]:
            zones.append(Zone("fvg", float(high[a]), float(low[c]), c))
    return zones


def order_block(df: pd.DataFrame, extreme_idx: int, direction: str, lookback: int = 5) -> Zone | None:
    """Last opposite-colour candle at or before the extreme that started the displacement.

    short: last up-close candle (close > open); long: last down-close candle.
    Zone is that candle's full range.
    """
    o, c = df["open"].to_numpy(), df["close"].to_numpy()
    h, l = df["high"].to_numpy(), df["low"].to_numpy()
    for i in range(extreme_idx, max(extreme_idx - lookback, -1), -1):
        if (direction == "short" and c[i] > o[i]) or (direction == "long" and c[i] < o[i]):
            return Zone("ob", float(l[i]), float(h[i]), i)
    return None


def ote_zone(leg_high: float, leg_low: float, direction: str,
             lo_frac: float = 0.62, hi_frac: float = 0.79) -> tuple[float, float]:
    """Optimal trade entry band: a 62-79% retracement of the MSS leg."""
    rng = leg_high - leg_low
    if direction == "short":  # leg ran down from the high; retrace back up
        return leg_low + lo_frac * rng, leg_low + hi_frac * rng
    return leg_high - hi_frac * rng, leg_high - lo_frac * rng
