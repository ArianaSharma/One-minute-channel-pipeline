import copy
from collections import Counter

import pandas as pd
import pytest

from rig.config import load_config
from rig.data import synthetic
from rig.setups import detect_signals
from tests.candles import DAY, after, frames, set_bars, short_setup_5m


@pytest.fixture
def cfg():
    return copy.deepcopy(load_config())


def run(df5, cfg, symbol="BTC"):
    stats = Counter()
    df15, df5, df1h = frames(df5)
    return detect_signals(symbol, df15, df5, df1h, cfg, stats), stats


def test_detects_the_textbook_short(cfg):
    sigs, stats = run(short_setup_5m(), cfg)
    assert len(sigs) == 1, stats
    s = sigs[0]
    assert s.direction == "short"
    assert s.killzone == "london"
    assert s.ts == DAY + pd.Timedelta(hours=7, minutes=55)  # close of the 07:50 MSS bar
    assert s.zone_kind == "fvg"
    # OTE of leg 102.5 -> 100.6 is [101.778, 102.101]; FVG is [101.45, 101.8]
    assert s.entry == pytest.approx(100.6 + 0.62 * 1.9)
    assert s.stop > 102.5
    assert s.target == 100.0 and s.target_type == "opposing_liquidity"
    assert s.reward_risk >= 1.5
    assert s.snapshot["setup"]["reference_high"] == 102.0
    assert s.snapshot["setup"]["swept_level"] == "reference_high"


def test_mirror_image_long_is_detected(cfg):
    # Reflect every price around 101 so the short becomes a long.
    df = short_setup_5m()
    mirrored = df.assign(open=202 - df["open"], close=202 - df["close"],
                         high=202 - df["low"], low=202 - df["high"])
    sigs, _ = run(mirrored, cfg)
    assert [s.direction for s in sigs] == ["long"]
    assert sigs[0].target == 102.0
    assert sigs[0].entry == pytest.approx(202 - (100.6 + 0.62 * 1.9))


def test_no_signal_outside_killzone(cfg):
    cfg["killzones"]["london"] = ["08:00", "10:00"]  # sweep happens at 07:30
    sigs, _ = run(short_setup_5m(), cfg)
    assert sigs == []


def test_sweep_without_structure_shift_gives_nothing(cfg):
    df = short_setup_5m()
    df = after(df, "07:50", 101.2, 101.5, 100.9, 101.2)  # never closes below 100.8
    sigs, stats = run(df, cfg)
    assert sigs == []
    assert stats["no_mss"] >= 1


def test_close_back_above_swept_level_invalidates(cfg):
    df = set_bars(short_setup_5m(), {"07:45": (101.9, 102.3, 101.85, 102.2)})
    sigs, stats = run(df, cfg)
    assert stats["sweep_invalidated"] >= 1
    # The 07:30 sweep is dead. The 07:45 bar (wick to 102.3, 15m close 100.7) is a *new*
    # sweep, so any short must come from that one, not the invalidated first sweep.
    shorts = [s for s in sigs if s.direction == "short"]
    assert all(s.ts > DAY + pd.Timedelta(hours=8) for s in shorts)


def test_order_block_fallback_when_no_fvg_in_ote(cfg):
    cfg["setup"]["ote_low"], cfg["setup"]["ote_high"] = 0.90, 0.95  # above the FVG
    sigs, _ = run(short_setup_5m(), cfg)
    assert len(sigs) == 1 and sigs[0].zone_kind == "ob"


def test_rejects_when_reward_risk_too_small(cfg):
    cfg["risk"]["min_reward_risk"] = 3.0  # liquidity target gives ~2.3R, fallback is 2R
    sigs, stats = run(short_setup_5m(), cfg)
    assert sigs == []
    assert stats["rr_below_min"] == 1


def test_fixed_r_fallback_when_liquidity_too_close(cfg):
    df = set_bars(short_setup_5m(), {"04:00": (101.0, 101.3, 101.2, 101.0)})
    df.loc[df["ts"] < DAY + pd.Timedelta(hours=7), "low"] = 101.2  # Asia low now 101.2
    df.loc[df["ts"] < DAY + pd.Timedelta(hours=7), ["open", "close"]] = 101.25
    df.loc[df["ts"] < DAY + pd.Timedelta(hours=7), "high"] = 101.3
    df = set_bars(df, {"03:00": (101.25, 102.0, 101.2, 101.25)})
    sigs, _ = run(df, cfg)
    short = [s for s in sigs if s.direction == "short"]
    assert len(short) == 1
    s = short[0]
    assert s.target_type == "fixed_r"
    assert s.reward_risk == pytest.approx(2.0)


def test_no_lookahead_on_synthetic_data(cfg):
    """Cutting the data at each signal's time must reproduce that exact signal."""
    series = synthetic.generate_1m(["BTC"], days=6, seed=3)["BTC"]
    df5, df15, df1h = (synthetic.resample(series, i) for i in ("5m", "15m", "1h"))
    full = detect_signals("BTC", df15, df5, df1h, cfg)
    assert len(full) >= 3
    for s in full:
        cut = [d[d["ts"] + pd.Timedelta(td) <= s.ts] for d, td in
               ((df15, "15min"), (df5, "5min"), (df1h, "1h"))]
        again = {x.id: x for x in detect_signals("BTC", cut[0], cut[1], cut[2], cfg)}
        assert s.id in again
        assert again[s.id].to_row() == s.to_row()
