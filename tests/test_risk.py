import pandas as pd
import pytest

from rig.risk.correlation import apply_no_stacking
from rig.risk.sizing import position_size, validate_trade

GROUPS = [["BTC", "ETH"], ["XAU/USD"]]


def ts(hhmm, day="2026-01-06"):
    return pd.Timestamp(f"{day} {hhmm}", tz="UTC")


def trade(sid, sym, fill, exit_, kz="london", day="2026-01-06"):
    return {"signal_id": sid, "symbol": sym, "killzone": kz,
            "fill_ts": ts(fill, day), "exit_ts": ts(exit_, day)}


def test_skips_correlated_signal_while_position_open():
    out = apply_no_stacking(pd.DataFrame([
        trade("a", "BTC", "07:30", "09:00"),
        trade("b", "ETH", "08:00", "08:30"),   # BTC still open, same group + window
    ]), GROUPS).set_index("signal_id")
    assert out.loc["a", "taken"]
    assert not out.loc["b", "taken"]
    assert out.loc["b", "skip_reason"].startswith("correlated_open: BTC")


def test_allows_after_first_position_closes():
    out = apply_no_stacking(pd.DataFrame([
        trade("a", "BTC", "07:30", "08:00"),
        trade("b", "ETH", "08:10", "09:00"),
    ]), GROUPS)
    assert out["taken"].all()


def test_allows_uncorrelated_or_other_window():
    out = apply_no_stacking(pd.DataFrame([
        trade("a", "BTC", "07:30", "14:00"),
        trade("b", "XAU/USD", "08:00", "09:00"),          # different group
        trade("c", "ETH", "12:45", "13:30", kz="ny_am"),   # different session window
    ]), GROUPS)
    assert out["taken"].all()


def test_skipped_trade_does_not_block_later_ones():
    out = apply_no_stacking(pd.DataFrame([
        trade("a", "BTC", "07:30", "08:00"),
        trade("b", "ETH", "07:45", "10:00"),  # skipped: BTC open
        trade("c", "ETH", "08:30", "09:00"),  # BTC closed; b was never opened
    ]), GROUPS).set_index("signal_id")
    assert list(out["taken"]) == [True, False, True]


def test_position_size_risks_exactly_the_configured_dollars():
    assert position_size(100.0, 98.0, 25) == pytest.approx(12.5)
    assert position_size(100.0, 98.0, 50) == pytest.approx(25.0)
    with pytest.raises(ValueError):
        position_size(100.0, 98.0, 100)


@pytest.mark.parametrize("args,reason", [
    (("long", 100, None, 110), "no_stop"),
    (("long", 100, 98, 102.9), "rr_below_min"),   # 1.45R
    (("short", 100, 98, 95), "bad_geometry"),     # stop below a short entry
    (("long", 100, 98, 103), None),               # exactly 1.5R
])
def test_validate_trade(args, reason):
    assert validate_trade(*args) == reason
