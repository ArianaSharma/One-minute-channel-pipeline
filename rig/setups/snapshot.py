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


def _bucket(x, edges, labels):
    if x is None:
        return "unknown"
    for edge, label in zip(edges, labels):
        if x < edge:
            return label
    return labels[-1]


def describe(direction: str, setup: dict, ctx: dict) -> dict:
    """Plain-language reading of the numbers, computed in code.

    Jev 1.13 is documented as weak at numeric comparison ("keep the arithmetic in code"),
    so the judgement-relevant facts are also given as named buckets.
    """
    out = {
        "trade": f"{direction} after a sweep of the {setup['reference_session']} session "
                 f"{'high' if direction == 'short' else 'low'}",
        "sweep_depth": _bucket(setup.get("sweep_depth_atr"), [0.5, 1.5], ["shallow", "moderate", "deep"]),
        "displacement": _bucket(setup.get("displacement_atr"), [2, 4], ["weak", "moderate", "strong"]),
        "structure_shift_speed": _bucket(setup.get("mss_bars_after_sweep"), [4, 9], ["fast", "normal", "slow"]),
        "entry_zone": "fair value gap" if setup["entry_zone"] == "fvg" else "order block",
        "reward_to_risk": f"{setup['reward_risk']:.1f} to 1",
    }
    if ctx.get("available", True) and "ema20_vs_ema50_pct" in ctx:
        spread, slope = ctx["ema20_vs_ema50_pct"] or 0.0, ctx["ema20_slope_6h_pct"] or 0.0
        if spread > 0.3 and slope > 0:
            trend = "uptrend"
        elif spread < -0.3 and slope < 0:
            trend = "downtrend"
        else:
            trend = "sideways"
        out["trend_1h"] = trend
        out["trade_vs_1h_trend"] = (
            "with trend" if (trend == "uptrend" and direction == "long")
            or (trend == "downtrend" and direction == "short")
            else "counter trend" if trend != "sideways" else "no clear trend"
        )
        out["volatility_1h"] = _bucket(ctx.get("atr14_pct"), [0.4, 1.0], ["low", "normal", "high"])
        out["price_in_24h_range"] = _bucket(ctx.get("position_in_24h_range"), [0.25, 0.75],
                                            ["near the low", "middle", "near the high"])
    else:
        out["trend_1h"] = "not enough history"
    return out


def build_snapshot(signal: "Signal", df5_upto: pd.DataFrame, df1h: pd.DataFrame,
                   setup_extra: dict) -> dict:
    recent = df5_upto.tail(12)
    ctx = hourly_context(df1h, signal.ts)
    setup = {
        "direction": signal.direction,
        "entry_zone": signal.zone_kind,
        "entry": sig(signal.entry),
        "stop": sig(signal.stop),
        "target": sig(signal.target),
        "target_type": signal.target_type,
        "reward_risk": sig(signal.reward_risk, 3),
        **{k: _round_extra(k, v) for k, v in setup_extra.items()},
    }
    return {
        "instrument": signal.symbol,
        "time_utc": signal.ts.strftime("%Y-%m-%d %H:%M"),
        "weekday": signal.ts.day_name(),
        "killzone": signal.killzone,
        "summary": describe(signal.direction, setup, ctx),
        "setup": setup,
        "context_1h": ctx,
        "day": day_context(df1h, signal.ts),
        "recent_5m_bars": {
            "columns": ["time", "open", "high", "low", "close"],
            "rows": [[r.ts.strftime("%H:%M"), sig(r.open), sig(r.high), sig(r.low), sig(r.close)]
                     for r in recent.itertuples()],
        },
    }
