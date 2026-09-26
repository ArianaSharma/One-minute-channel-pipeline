"""Bar-by-bar paper engine for one signal.

1. Pending: a limit order at `entry`, live from the signal time until `entry_expiry`.
   If price reaches the target before ever touching the entry, the setup is 'missed'.
2. Filled: walk bars until the stop or target is touched, or `max_hold` elapses.
   Conservative rules:
     - stop and target inside the same bar -> the stop was hit first
     - on the fill bar itself, the stop can be hit but the target never counts
3. Costs: the entry and the target are resting limit orders (maker fee, no slippage); the
   stop and a timeout exit are market orders (taker fee + slippage against us).
   R multiple = net P&L / risk dollars, so a clean stop-out is slightly worse than -1R.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from rig.risk.sizing import position_size
from rig.sim.fees import fee, slipped


@dataclass
class SimParams:
    risk_usd: float = 25.0
    maker_fee_bps: float = 1.5
    taker_fee_bps: float = 4.5
    slippage_bps: float = 1.0
    entry_expiry: pd.Timedelta = pd.Timedelta(minutes=60)
    max_hold: pd.Timedelta = pd.Timedelta(hours=24)

    @classmethod
    def from_config(cls, cfg: dict) -> "SimParams":
        s = cfg["sim"]
        return cls(
            risk_usd=cfg["risk"]["risk_per_trade_usd"],
            maker_fee_bps=s["maker_fee_bps"],
            taker_fee_bps=s["taker_fee_bps"],
            slippage_bps=s["slippage_bps"],
            entry_expiry=pd.Timedelta(minutes=5 * s["entry_expiry_bars"]),
            max_hold=pd.Timedelta(hours=s.get("max_hold_hours", 24)),
        )


@dataclass
class SimResult:
    filled: bool
    outcome: str                 # target | stop | timeout | no_fill | missed | data_end
    fill_ts: pd.Timestamp | None = None
    fill_price: float | None = None
    exit_ts: pd.Timestamp | None = None
    exit_price: float | None = None
    quantity: float | None = None
    pnl_usd: float | None = None
    fees_usd: float | None = None
    r_multiple: float | None = None


def simulate(direction: str, entry: float, stop: float, target: float, ts: pd.Timestamp,
             bars: pd.DataFrame, p: SimParams) -> SimResult:
    """`bars` are OHLC with `ts` = bar open; only bars opening at/after `ts` are used."""
    short = direction == "short"
    b = bars[(bars["ts"] >= ts) & (bars["ts"] <= ts + p.entry_expiry + p.max_hold)]
    hi, lo, ts_arr = b["high"].to_numpy(), b["low"].to_numpy(), list(b["ts"])
    close = b["close"].to_numpy()

    def touched_stop(i):
        return hi[i] >= stop if short else lo[i] <= stop

    def touched_target(i):
        return lo[i] <= target if short else hi[i] >= target

    # --- pending order
    fill_i = None
    for i in range(len(b)):
        if ts_arr[i] >= ts + p.entry_expiry:
            return SimResult(False, "no_fill")
        if (short and hi[i] >= entry) or (not short and lo[i] <= entry):
            fill_i = i
            break
        if touched_target(i):
            return SimResult(False, "missed")
    if fill_i is None:
        return SimResult(False, "data_end")

    qty = position_size(entry, stop, p.risk_usd)
    fill_ts = ts_arr[fill_i]

    def close_out(i, price, outcome):
        entry_px = entry  # resting limit: fills at its price
        market_exit = outcome in ("stop", "timeout")
        exit_px = slipped(price, "buy" if short else "sell", p.slippage_bps) if market_exit else price
        gross = qty * ((entry_px - exit_px) if short else (exit_px - entry_px))
        fees = (fee(qty * entry_px, p.maker_fee_bps)
                + fee(qty * exit_px, p.taker_fee_bps if market_exit else p.maker_fee_bps))
        pnl = gross - fees
        return SimResult(True, outcome, fill_ts, entry, ts_arr[i], price, qty, pnl, fees,
                         pnl / p.risk_usd)

    if touched_stop(fill_i):
        return close_out(fill_i, stop, "stop")

    # --- open position
    for i in range(fill_i + 1, len(b)):
        if ts_arr[i] >= fill_ts + p.max_hold:
            return close_out(i - 1, float(close[i - 1]), "timeout")
        if touched_stop(i):
            return close_out(i, stop, "stop")
        if touched_target(i):
            return close_out(i, target, "target")
    return SimResult(True, "data_end", fill_ts, entry, quantity=qty)
