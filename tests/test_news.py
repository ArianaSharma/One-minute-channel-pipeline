import pandas as pd
import pytest

from rig.risk.news import NewsCalendar

T = pd.Timestamp("2026-03-11 12:30", tz="UTC")  # CPI


@pytest.fixture
def cal():
    events = pd.DataFrame({
        "timestamp_utc": ["2026-03-11T12:30:00Z", "2026-03-11T14:00:00Z", "2026-03-12T09:00:00Z"],
        "currency": ["USD", "USD", "EUR"],
        "event": ["CPI", "Crude Oil Inventories", "ECB Rate Decision"],
        "impact": ["High", "Medium", "HIGH"],
    })
    return NewsCalendar(events, block_minutes=2)


@pytest.mark.parametrize("offset_s", [-120, -60, 0, 60, 120])
def test_blocks_within_two_minutes_inclusive(cal, offset_s):
    hit = cal.check("BTC", T + pd.Timedelta(seconds=offset_s))
    assert hit is not None and hit.event == "CPI"
    assert "news_block" in hit.reason()


@pytest.mark.parametrize("offset_s", [-121, 121, 3600])
def test_allows_outside_the_window(cal, offset_s):
    assert cal.check("BTC", T + pd.Timedelta(seconds=offset_s)) is None


def test_ignores_non_high_impact(cal):
    assert cal.check("BTC", pd.Timestamp("2026-03-11 14:00", tz="UTC")) is None


def test_only_blocks_currencies_the_instrument_trades_on():
    events = pd.DataFrame({"timestamp_utc": ["2026-03-12T09:00:00Z"], "currency": ["EUR"],
                           "event": ["ECB"], "impact": ["High"]})
    t = pd.Timestamp("2026-03-12 09:00", tz="UTC")
    assert NewsCalendar(events).check("BTC", t) is None
    assert NewsCalendar(events, currencies={"BTC": ["USD", "EUR"]}).check("BTC", t) is not None


def test_repo_calendar_loads_and_has_known_events():
    from rig.config import load_config
    cal = NewsCalendar.from_config(load_config())
    assert len(cal.events) > 50
    assert cal.check("BTC", pd.Timestamp("2026-03-11 12:31", tz="UTC")).event == "CPI"
    # FOMC statement is 14:00 ET = 18:00 UTC in March after the DST switch
    assert cal.check("ETH", pd.Timestamp("2026-03-18 18:00", tz="UTC")) is not None


def test_missing_columns_is_an_error():
    with pytest.raises(ValueError, match="missing columns"):
        NewsCalendar(pd.DataFrame({"timestamp_utc": [], "event": []}))
