import pandas as pd
import pytest

from rig.filter import FilterParams, decide
from rig.sim import SimParams, simulate
from rig.sim.labels import compute_labels

T0 = pd.Timestamp("2026-01-06 08:00", tz="UTC")
NO_COSTS = SimParams(risk_usd=25, maker_fee_bps=0, taker_fee_bps=0, slippage_bps=0,
                     entry_expiry=pd.Timedelta(minutes=10), max_hold=pd.Timedelta(hours=1))


def bars(rows, start=T0, step="1min"):
    """rows: list of (high, low); open/close set to the midpoint."""
    ts = pd.date_range(start, periods=len(rows), freq=step, tz="UTC")
    return pd.DataFrame({"ts": ts, "open": [(h + l) / 2 for h, l in rows],
                         "high": [h for h, _ in rows], "low": [l for _, l in rows],
                         "close": [(h + l) / 2 for h, l in rows], "volume": 1.0})


# long: entry 100, stop 98, target 104 (2R)
def run_long(rows, p=NO_COSTS):
    return simulate("long", 100.0, 98.0, 104.0, T0, bars(rows), p)


def test_long_hits_target():
    r = run_long([(101, 100), (102, 100.5), (104.5, 101)])
    assert r.filled and r.outcome == "target"
    assert r.r_multiple == pytest.approx(2.0)
    assert r.quantity == pytest.approx(25 / 2)


def test_long_hits_stop():
    r = run_long([(101, 99.8), (100, 97.5)])
    assert r.outcome == "stop" and r.r_multiple == pytest.approx(-1.0)


def test_stop_and_target_in_same_bar_assumes_stop():
    r = run_long([(100.5, 99.9), (105, 97)])
    assert r.outcome == "stop" and r.r_multiple == pytest.approx(-1.0)


def test_fill_bar_can_stop_out_but_never_counts_target():
    assert run_long([(100.2, 97.9)]).outcome == "stop"          # fill + stop in one bar
    r = run_long([(104.5, 99.9), (101, 99.5)] + [(101, 99.5)] * 70)
    assert r.outcome == "timeout"                                # target in fill bar ignored


def test_short_mirror():
    r = simulate("short", 100.0, 102.0, 96.0, T0,
                 bars([(100.1, 99.5), (99.8, 95.5)]), NO_COSTS)
    assert r.outcome == "target" and r.r_multiple == pytest.approx(2.0)


def test_no_fill_before_expiry():
    r = run_long([(102, 100.5)] * 20)  # never trades down to 100
    assert not r.filled and r.outcome == "no_fill"


def test_missed_when_target_reached_before_fill():
    r = run_long([(102, 100.5), (104.2, 101)])
    assert not r.filled and r.outcome == "missed"


def test_signal_time_excludes_earlier_bars():
    rows = [(101, 97)] + [(101, 99.9), (104.5, 101)]  # first bar is before the signal
    r = simulate("long", 100.0, 98.0, 104.0, T0 + pd.Timedelta(minutes=1), bars(rows), NO_COSTS)
    assert r.outcome == "target"


def test_costs_make_stop_worse_than_minus_one_r():
    p = SimParams(risk_usd=25, maker_fee_bps=1.5, taker_fee_bps=4.5, slippage_bps=1.0,
                  entry_expiry=pd.Timedelta(minutes=10), max_hold=pd.Timedelta(hours=1))
    stop = run_long([(101, 99.8), (100, 97.5)], p)
    win = run_long([(101, 100), (104.5, 101)], p)
    assert stop.r_multiple < -1.0
    assert win.r_multiple < 2.0
    # maker entry 1.5bp on 1250 notional + taker 4.5bp on slipped 98*(1-1bp) exit
    qty = 12.5
    exit_px = 98 * (1 - 1e-4)
    expected = (qty * (exit_px - 100) - qty * 100 * 1.5e-4 - qty * exit_px * 4.5e-4) / 25
    assert stop.r_multiple == pytest.approx(expected)


def test_risk_must_be_25_or_50():
    with pytest.raises(ValueError):
        run_long([(101, 99.5)], SimParams(risk_usd=100))


# ---------- labels ----------

def test_labels_from_future_bars():
    b = bars([(101, 99.5)] + [(103, 100.5)] * 30 + [(104.5, 102)], step="5min")
    lab = compute_labels("long", sweep_extreme=98.5, mss_close=100.0, stop=98.0, target=104.0,
                         ts=T0, bars=b, bar=pd.Timedelta(minutes=5),
                         horizon=pd.Timedelta(hours=2), max_hold=pd.Timedelta(hours=24))
    assert lab == {"direction_agrees": 1, "sweep_is_genuine": 1, "target_before_stop": 1}


def test_labels_are_none_without_enough_future():
    b = bars([(101, 99.5)] * 3, step="5min")
    lab = compute_labels("long", 98.5, 100.0, 98.0, 104.0, T0, b, pd.Timedelta(minutes=5),
                         pd.Timedelta(hours=4), pd.Timedelta(hours=24))
    assert lab["direction_agrees"] is None and lab["target_before_stop"] is None


# ---------- filter policy ----------

GOOD = {"confidence": 0.8, "regime": "trending_up", "setup_quality": 2.4, "target_before_stop": 0.7}


@pytest.mark.parametrize("change,action,reason", [
    ({}, "take", None),
    ({"confidence": 0.59}, "escalate", "confidence"),
    ({"regime": "crisis"}, "skip", "regime_crisis"),
    ({"setup_quality": 1.9}, "skip", "setup_quality"),
    ({"target_before_stop": 0.5}, "skip", "target_before_stop"),
])
def test_filter_policy(change, action, reason):
    got_action, got_reason = decide({**GOOD, **change}, FilterParams(0.60, 2.0, 0.55))
    assert got_action == action
    assert (got_reason is None) if reason is None else reason in got_reason


def test_low_confidence_escalates_even_in_crisis():
    assert decide({**GOOD, "confidence": 0.3, "regime": "crisis"}, FilterParams())[0] == "escalate"


def test_missing_answer_is_skipped():
    assert decide(None, FilterParams()) == ("skip", "no_jev_answer")
