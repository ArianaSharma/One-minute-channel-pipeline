"""Ground-truth labels for Jev's Noul questions, computed from candles *after* the signal.

These are for scoring calibration only and are never shown to Jev.
  direction_agrees:   close `horizon` after the signal is beyond the MSS close in the
                      trade's direction
  sweep_is_genuine:   price stays inside the sweep's extreme for `horizon`
  target_before_stop: from the signal time, the target is touched before the stop
                      (same-bar tie -> stop), within `max_hold`
Returns None for a label when there isn't enough data after the signal.
"""
from __future__ import annotations

import pandas as pd


def compute_labels(direction: str, sweep_extreme: float, mss_close: float, stop: float,
                   target: float, ts: pd.Timestamp, bars: pd.DataFrame, bar: pd.Timedelta,
                   horizon: pd.Timedelta, max_hold: pd.Timedelta) -> dict:
    short = direction == "short"
    after = bars[bars["ts"] >= ts]
    out: dict = {"direction_agrees": None, "sweep_is_genuine": None, "target_before_stop": None}

    window = after[after["ts"] + bar <= ts + horizon]
    if len(after) and after["ts"].iloc[-1] + bar >= ts + horizon and len(window):
        last_close = window["close"].iloc[-1]
        out["direction_agrees"] = int(last_close < mss_close if short else last_close > mss_close)
        out["sweep_is_genuine"] = int(window["high"].max() < sweep_extreme if short
                                      else window["low"].min() > sweep_extreme)

    for r in after[after["ts"] < ts + max_hold].itertuples():
        hit_stop = r.high >= stop if short else r.low <= stop
        hit_target = r.low <= target if short else r.high >= target
        if hit_stop:
            out["target_before_stop"] = 0
            break
        if hit_target:
            out["target_before_stop"] = 1
            break
    return out
