"""No correlated stacking.

Walk trades in fill order. A trade is skipped when another position is open (filled,
not yet exited) on an instrument in the same correlation group *and* in the same
session window (same killzone, same UTC day).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class OpenPosition:
    signal_id: str
    symbol: str
    group: str
    window: tuple[str, pd.Timestamp]
    exit_ts: pd.Timestamp


def group_of(symbol: str, groups: list[list[str]]) -> str:
    for i, members in enumerate(groups):
        if symbol in members:
            return f"group{i}"
    return f"solo:{symbol}"  # ungrouped instruments only clash with themselves


def apply_no_stacking(trades: pd.DataFrame, groups: list[list[str]]) -> pd.DataFrame:
    """trades needs: signal_id, symbol, killzone, fill_ts, exit_ts (filled trades only).

    Returns a copy with `taken` (bool) and `skip_reason` columns.
    """
    out = trades.sort_values(["fill_ts", "signal_id"]).copy()
    out["taken"] = True
    out["skip_reason"] = None
    open_pos: list[OpenPosition] = []
    for idx, t in out.iterrows():
        open_pos = [p for p in open_pos if p.exit_ts > t["fill_ts"]]
        g = group_of(t["symbol"], groups)
        window = (t["killzone"], pd.Timestamp(t["fill_ts"]).normalize())
        clash = next((p for p in open_pos if p.group == g and p.window == window), None)
        if clash:
            out.at[idx, "taken"] = False
            out.at[idx, "skip_reason"] = f"correlated_open: {clash.symbol} ({clash.signal_id})"
            continue
        open_pos.append(OpenPosition(t["signal_id"], t["symbol"], g, window, t["exit_ts"]))
    return out
