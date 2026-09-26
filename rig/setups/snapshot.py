"""Compact market-state snapshot sent to Jev as `state`.

Only bars closed by the signal time go in. Kept to a few hundred tokens, well under
Jev's 32k-token state budget.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from rig.setups.detector import Signal

ONE_HOUR = pd.Timedelta(hours=1)


def sig(x: float | None, digits: int = 6) -> float | None:
    """Round to `digits` significant figures (keeps BTC and small-price assets readable)."""
    if x is None or not math.isfinite(x) or x == 0:
        return x
    return round(x, digits - 1 - int(math.floor(math.log10(abs(x)))))


def _pct(a: float, b: float) -> float | None:
    return sig(100.0 * (a / b - 1.0), 3) if b else None


def hourly_context(df1h: pd.DataFrame, as_of: pd.Timestamp) -> dict:
    closed = df1h[df1h["ts"] + ONE_HOUR <= as_of].tail(80)
    if len(closed) < 25:
        return {"available": False}
    c = closed["close"]
    ema20 = c.ewm(span=20, adjust=False).mean()
    ema50 = c.ewm(span=50, adjust=False).mean()
    last24 = closed.tail(24)
    hi, lo = last24["high"].max(), last24["low"].min()
    tr = pd.concat([closed["high"] - closed["low"],
                    (closed["high"] - c.shift()).abs(),
                    (closed["low"] - c.shift()).abs()], axis=1).max(axis=1)
    return {
        "change_24h_pct": _pct(c.iloc[-1], c.iloc[-25]),
        "ema20_vs_ema50_pct": _pct(ema20.iloc[-1], ema50.iloc[-1]),
        "ema20_slope_6h_pct": _pct(ema20.iloc[-1], ema20.iloc[-7]),
        "atr14_pct": sig(100.0 * tr.tail(14).mean() / c.iloc[-1], 3),
        "position_in_24h_range": sig((c.iloc[-1] - lo) / (hi - lo), 3) if hi > lo else None,
    }


def day_context(df1h: pd.DataFrame, as_of: pd.Timestamp) -> dict:
    today = as_of.normalize()
    closed = df1h[df1h["ts"] + ONE_HOUR <= as_of]
    prev = closed[(closed["ts"] >= today - pd.Timedelta(days=1)) & (closed["ts"] < today)]
    cur = closed[closed["ts"] >= today]
    out: dict = {}
    if len(prev):
        out["prior_day_high"] = sig(prev["high"].max())
        out["prior_day_low"] = sig(prev["low"].min())
    if len(cur):
        out["today_open"] = sig(cur["open"].iloc[0])
    return out


PRICE_KEYS = {"reference_high", "reference_low", "mss_level", "atr_5m"}


def _round_extra(key: str, value):
    if not isinstance(value, float):
        return value
    return sig(value) if key in PRICE_KEYS else sig(value, 4)


def build_snapshot(signal: "Signal", df5_upto: pd.DataFrame, df1h: pd.DataFrame,
                   setup_extra: dict) -> dict:
    recent = df5_upto.tail(12)
    return {
        "instrument": signal.symbol,
        "time_utc": signal.ts.strftime("%Y-%m-%d %H:%M"),
        "weekday": signal.ts.day_name(),
        "killzone": signal.killzone,
        "setup": {
            "direction": signal.direction,
            "entry_zone": signal.zone_kind,
            "entry": sig(signal.entry),
            "stop": sig(signal.stop),
            "target": sig(signal.target),
            "target_type": signal.target_type,
            "reward_risk": sig(signal.reward_risk, 3),
            **{k: _round_extra(k, v) for k, v in setup_extra.items()},
        },
        "context_1h": hourly_context(df1h, signal.ts),
        "day": day_context(df1h, signal.ts),
        "recent_5m_bars": {
            "columns": ["time", "open", "high", "low", "close"],
            "rows": [[r.ts.strftime("%H:%M"), sig(r.open), sig(r.high), sig(r.low), sig(r.close)]
                     for r in recent.itertuples()],
        },
    }
