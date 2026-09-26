"""The ICT setup detector.

For each UTC day and killzone:
  1. levels:  high/low of the reference session (Asia for London, London for NY AM), 15m bars
  2. sweep:   a 15m bar inside the killzone wicks beyond a level and closes back inside
  3. MSS:     within `mss_max_bars` 5m bars after the sweep closes, a 5m close breaks the most
              recent confirmed swing point that formed before the sweep extreme. A 5m close back
              beyond the swept level first invalidates the sweep.
  4. entry:   a 5m FVG inside the MSS leg (or, failing that, the order block) overlapping the
              62-79% OTE band; entry = the edge of the overlap price reaches first
  5. risk:    stop beyond the sweep extreme + buffer*ATR; target = opposite side of the reference
              range if that gives >= min R:R, else a fixed R multiple

The signal time is the close of the MSS bar and must be inside the killzone. Only bars that
have closed by the signal time are used (tests/test_detector.py checks this).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from rig.setups import structure
from rig.setups.sessions import Window, killzone_plan
from rig.setups.snapshot import build_snapshot

FIVE_MIN = pd.Timedelta(minutes=5)
FIFTEEN_MIN = pd.Timedelta(minutes=15)


@dataclass
class Signal:
    id: str
    symbol: str
    ts: pd.Timestamp            # signal time = close of the MSS bar (UTC)
    direction: str              # "long" | "short"
    killzone: str
    entry: float
    stop: float
    target: float
    reward_risk: float
    target_type: str            # "opposing_liquidity" | "fixed_r"
    zone_kind: str              # "fvg" | "ob"
    sweep_extreme: float = 0.0  # the swept wick's extreme (used to label sweep_is_genuine)
    mss_close: float = 0.0      # close of the MSS bar (used to label direction_agrees)
    snapshot: dict = field(repr=False, default_factory=dict)

    @property
    def risk_per_unit(self) -> float:
        return abs(self.entry - self.stop)

    def to_row(self) -> dict:
        row = asdict(self)
        row["ts"] = self.ts.isoformat()
        return row


@dataclass
class DetectorParams:
    ote_low: float = 0.62
    ote_high: float = 0.79
    fallback_target_r: float = 2.0
    min_reward_risk: float = 1.5
    mss_max_bars: int = 12
    swing_k: int = 2
    swing_lookback_bars: int = 36
    stop_buffer_atr: float = 0.1

    @classmethod
    def from_config(cls, cfg: dict) -> "DetectorParams":
        s = cfg.get("setup", {})
        return cls(
            ote_low=s.get("ote_low", 0.62),
            ote_high=s.get("ote_high", 0.79),
            fallback_target_r=s.get("fallback_target_r", 2.0),
            min_reward_risk=cfg["risk"]["min_reward_risk"],
            mss_max_bars=s.get("mss_max_bars", 12),
            swing_k=s.get("swing_k", 2),
            swing_lookback_bars=s.get("swing_lookback_bars", 36),
            stop_buffer_atr=s.get("stop_buffer_atr", 0.1),
        )


class _Frame:
    """5m data as numpy arrays plus precomputed ATR and swings."""

    def __init__(self, df5: pd.DataFrame, k: int):
        self.df = df5.reset_index(drop=True)
        self.ts = pd.DatetimeIndex(self.df["ts"])
        self.open = self.df["open"].to_numpy()
        self.high = self.df["high"].to_numpy()
        self.low = self.df["low"].to_numpy()
        self.close = self.df["close"].to_numpy()
        self.atr = structure.atr(self.df).to_numpy()
        self.swing_high, self.swing_low = structure.swing_points(self.df, k)
        self.k = k

    def first_index_at_or_after(self, t: pd.Timestamp) -> int:
        return int(self.ts.searchsorted(t, side="left"))


def detect_signals(
    symbol: str,
    df15: pd.DataFrame,
    df5: pd.DataFrame,
    df1h: pd.DataFrame,
    cfg: dict,
    stats: Counter | None = None,
) -> list[Signal]:
    params = DetectorParams.from_config(cfg)
    stats = stats if stats is not None else Counter()
    f5 = _Frame(df5, params.swing_k)
    df15 = df15.reset_index(drop=True)
    ts15 = pd.DatetimeIndex(df15["ts"])
    days = pd.DatetimeIndex(f5.ts.normalize().unique())

    signals: list[Signal] = []
    for day in days:
        for kz, ref in killzone_plan(day, cfg):
            ref_bars = df15[(ts15 >= ref.start) & (ts15 < ref.end)]
            expected = (ref.end - ref.start) / FIFTEEN_MIN
            if len(ref_bars) < 0.8 * expected:
                stats["incomplete_reference_session"] += 1
                continue
            level_high, level_low = float(ref_bars["high"].max()), float(ref_bars["low"].min())
            kz_bars = df15[(ts15 >= kz.start) & (ts15 + FIFTEEN_MIN <= kz.end)]

            for direction in ("short", "long"):
                for _, bar in kz_bars.iterrows():
                    swept = (
                        bar["high"] > level_high and bar["close"] < level_high
                        if direction == "short"
                        else bar["low"] < level_low and bar["close"] > level_low
                    )
                    if not swept:
                        continue
                    stats["sweeps"] += 1
                    sig = _build(symbol, direction, bar, kz, ref, level_high, level_low,
                                 f5, df1h, params, stats)
                    if sig is not None:
                        signals.append(sig)
                        break  # at most one signal per symbol, killzone and direction
    signals.sort(key=lambda s: s.ts)
    stats["signals"] += len(signals)
    return signals


def _build(symbol, direction, sweep_bar, kz: Window, ref: Window, level_high, level_low,
           f5: _Frame, df1h, p: DetectorParams, stats: Counter) -> Signal | None:
    short = direction == "short"
    sweep_start = sweep_bar["ts"]
    sweep_close_time = sweep_start + FIFTEEN_MIN
    i0 = f5.first_index_at_or_after(sweep_start)
    i_first = f5.first_index_at_or_after(sweep_close_time)
    if i0 >= i_first or i_first >= len(f5.ts):
        stats["missing_5m_bars"] += 1
        return None

    # Sweep extreme among the 5m bars that make up the 15m sweep bar.
    seg = slice(i0, i_first)
    ext_idx = i0 + int(np.argmax(f5.high[seg]) if short else np.argmin(f5.low[seg]))
    ext = f5.high[ext_idx] if short else f5.low[ext_idx]

    mss_idx, mss_level = None, None
    for j in range(i_first, min(i_first + p.mss_max_bars, len(f5.ts))):
        if f5.ts[j] + FIVE_MIN > kz.end:
            break
        # A close back beyond the swept level means continuation, not a sweep.
        if (short and f5.close[j] > level_high) or (not short and f5.close[j] < level_low):
            stats["sweep_invalidated"] += 1
            return None
        if short and f5.high[j] > ext:
            ext, ext_idx = f5.high[j], j
        elif not short and f5.low[j] < ext:
            ext, ext_idx = f5.low[j], j

        level = _structure_level(f5, ext_idx, j, short, p)
        if level is not None and ((short and f5.close[j] < level) or (not short and f5.close[j] > level)):
            mss_idx, mss_level = j, level
            break
    if mss_idx is None:
        stats["no_mss"] += 1
        return None
    j = mss_idx

    leg_high = ext if short else float(f5.high[ext_idx:j + 1].max())
    leg_low = float(f5.low[ext_idx:j + 1].min()) if short else ext
    ote_lo, ote_hi = structure.ote_zone(leg_high, leg_low, direction, p.ote_low, p.ote_high)

    zone, overlap = None, None
    for z in reversed(structure.fair_value_gaps(f5.df, ext_idx, j, direction)):
        overlap = z.overlap(ote_lo, ote_hi)
        if overlap:
            zone = z
            break
    if zone is None:
        ob = structure.order_block(f5.df, ext_idx, direction)
        overlap = ob.overlap(ote_lo, ote_hi) if ob else None
        zone = ob if overlap else None
    if zone is None:
        stats["no_zone_in_ote"] += 1
        return None

    entry = overlap[0] if short else overlap[1]  # the edge price reaches first on the retrace
    if (short and entry <= f5.close[j]) or (not short and entry >= f5.close[j]):
        stats["entry_already_passed"] += 1
        return None

    atr_j = float(f5.atr[j])
    stop = ext + p.stop_buffer_atr * atr_j if short else ext - p.stop_buffer_atr * atr_j
    risk = abs(stop - entry)
    if risk <= 0:
        stats["zero_risk"] += 1
        return None

    opposing = level_low if short else level_high
    liq_reward = (entry - opposing) if short else (opposing - entry)
    if liq_reward >= p.min_reward_risk * risk:
        target, target_type = opposing, "opposing_liquidity"
    else:
        target = entry - p.fallback_target_r * risk if short else entry + p.fallback_target_r * risk
        target_type = "fixed_r"
    rr = abs(target - entry) / risk
    if rr < p.min_reward_risk - 1e-9:
        stats["rr_below_min"] += 1
        return None

    signal_ts = f5.ts[j] + FIVE_MIN
    sig = Signal(
        id=f"{symbol}-{signal_ts:%Y%m%dT%H%M}-{kz.name}-{direction}",
        symbol=symbol, ts=signal_ts, direction=direction, killzone=kz.name,
        entry=float(entry), stop=float(stop), target=float(target), reward_risk=float(rr),
        target_type=target_type, zone_kind=zone.kind,
        sweep_extreme=float(ext), mss_close=float(f5.close[j]),
    )
    sweep_atr = float(f5.atr[i_first - 1]) or atr_j
    body = abs(sweep_bar["close"] - sweep_bar["open"])
    wick = (sweep_bar["high"] - max(sweep_bar["open"], sweep_bar["close"]) if short
            else min(sweep_bar["open"], sweep_bar["close"]) - sweep_bar["low"])
    sig.snapshot = build_snapshot(
        sig, f5.df.iloc[: j + 1], df1h,
        setup_extra={
            "reference_session": ref.name,
            "reference_high": level_high,
            "reference_low": level_low,
            "swept_level": "reference_high" if short else "reference_low",
            "sweep_depth_atr": abs(ext - (level_high if short else level_low)) / sweep_atr,
            "sweep_wick_to_body": wick / body if body > 0 else None,
            "mss_level": float(mss_level),
            "mss_bars_after_sweep": j - i_first + 1,
            "displacement_atr": (leg_high - leg_low) / atr_j if atr_j else None,
            "atr_5m": atr_j,
        },
    )
    return sig


def _structure_level(f5: _Frame, ext_idx: int, j: int, short: bool, p: DetectorParams) -> float | None:
    """Most recent swing point before the sweep extreme that is confirmed by bar j."""
    swings = f5.swing_low if short else f5.swing_high
    lo = max(0, ext_idx - p.swing_lookback_bars)
    for i in range(ext_idx - 1, lo - 1, -1):
        if swings[i] and structure.swing_confirmed_at(i, f5.k) <= j:
            return float(f5.low[i] if short else f5.high[i])
    return None
