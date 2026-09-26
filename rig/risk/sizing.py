"""Fixed-dollar risk sizing and the per-trade hard-rule checks."""
from __future__ import annotations

import math

from rig.config import ALLOWED_RISK_USD, MIN_REWARD_RISK


def validate_trade(direction: str, entry: float, stop: float | None, target: float,
                   min_rr: float = MIN_REWARD_RISK) -> str | None:
    """Return a rejection reason, or None if the trade may be simulated."""
    if stop is None or not math.isfinite(stop):
        return "no_stop"
    if direction == "long" and not (stop < entry < target):
        return "bad_geometry"
    if direction == "short" and not (target < entry < stop):
        return "bad_geometry"
    rr = abs(target - entry) / abs(entry - stop)
    if rr < max(min_rr, MIN_REWARD_RISK) - 1e-9:
        return "rr_below_min"
    return None


def position_size(entry: float, stop: float, risk_usd: float) -> float:
    """Units such that hitting the stop (before costs) loses exactly `risk_usd`."""
    if risk_usd not in ALLOWED_RISK_USD:
        raise ValueError(f"risk per trade must be one of {ALLOWED_RISK_USD}")
    dist = abs(entry - stop)
    if dist <= 0:
        raise ValueError("stop distance must be positive")
    return risk_usd / dist
