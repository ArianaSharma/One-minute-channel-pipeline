"""Fees and slippage, both applied against the trader."""
from __future__ import annotations


def slipped(price: float, side: str, slippage_bps: float) -> float:
    """side='buy' pays more, side='sell' receives less."""
    adj = slippage_bps / 10_000
    return price * (1 + adj) if side == "buy" else price * (1 - adj)


def fee(notional: float, fee_bps: float) -> float:
    return abs(notional) * fee_bps / 10_000
