import pandas as pd
import pytest

from rig.data import cache, hyperliquid, synthetic, twelvedata
from rig.data.http import DataFetchError

MIN = 60_000


def hl_candle(t_ms, price=100.0, interval_ms=MIN):
    return {"t": t_ms, "T": t_ms + interval_ms - 1, "s": "BTC", "i": "1m",
            "o": str(price), "h": str(price + 1), "l": str(price - 1), "c": str(price), "v": "1.5", "n": 3}


# ---------- cache ----------

def test_cache_merge_dedupes_and_new_rows_win(tmp_path):
    path = cache.cache_path(tmp_path, "hyperliquid", "BTC", "1m")
    ts = pd.date_range("2026-01-01", periods=3, freq="1min", tz="UTC")
    first = pd.DataFrame({"ts": ts, "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 1.0})
    cache.merge_and_write(path, first)

    revised = first.iloc[[2]].assign(close=1.9)
    extra = pd.DataFrame({"ts": [ts[-1] + pd.Timedelta(minutes=1)], "open": 1.0, "high": 2.0,
                          "low": 0.5, "close": 1.2, "volume": 1.0})
    merged = cache.merge_and_write(path, pd.concat([revised, extra]))

    assert len(merged) == 4
    assert merged["ts"].is_monotonic_increasing
    assert merged.loc[2, "close"] == 1.9
    assert len(cache.load_candles(tmp_path, "hyperliquid", "BTC", "1m")) == 4


def test_cache_drops_malformed_rows(tmp_path):
    ts = pd.date_range("2026-01-01", periods=2, freq="1min", tz="UTC")
    df = pd.DataFrame({"ts": ts, "open": [1.0, 1.0], "high": [2.0, 0.9],  # 2nd: high < open
                       "low": [0.5, 0.5], "close": [1.5, 0.8], "volume": [1.0, 1.0]})
    assert len(cache.normalize(df)) == 1


def test_load_missing_cache_explains_what_to_do(tmp_path):
    with pytest.raises(FileNotFoundError, match="rig fetch"):
        cache.load_candles(tmp_path, "hyperliquid", "BTC", "1m")


# ---------- hyperliquid ----------

def test_hyperliquid_pages_500_at_a_time_and_drops_forming_candle(fake_session):
    start = 1_700_000_000_000
    all_candles = [hl_candle(start + i * MIN) for i in range(1200)]
    now_ms = start + 1199 * MIN + 30_000  # last candle is still forming

    def handler(method, url, kw):
        req = kw["json"]["req"]
        assert kw["json"]["type"] == "candleSnapshot"
        rows = [c for c in all_candles if req["startTime"] <= c["t"] <= req["endTime"]]
        return rows[:500]

    sess = fake_session(handler)
    df = hyperliquid.fetch_candles("BTC", "1m", start, now_ms, base_url="u",
                                   session=sess, pause_s=0, now_ms=now_ms)
    assert len(sess.calls) == 3
    assert len(df) == 1199
    assert df["ts"].is_unique and df["ts"].is_monotonic_increasing
    assert list(df.columns) == cache.CANDLE_COLUMNS


def test_hyperliquid_retries_then_raises(fake_session, monkeypatch):
    monkeypatch.setattr("rig.data.http.time.sleep", lambda s: None)
    from tests.conftest import FakeResponse
    sess = fake_session(lambda m, u, k: FakeResponse(None, status=503))
    with pytest.raises(DataFetchError, match="HTTP 503"):
        hyperliquid.fetch_candles("BTC", "1m", 0, MIN * 10, base_url="u",
                                  session=sess, pause_s=0, now_ms=MIN * 100)
    assert len(sess.calls) == 4


# ---------- twelve data ----------

def td_values(times):
    return [{"datetime": t.strftime("%Y-%m-%d %H:%M:%S"), "open": "1", "high": "2",
             "low": "0.5", "close": "1.5"} for t in times]


def test_twelvedata_pages_backwards_and_sends_key_in_header_only(fake_session, monkeypatch):
    monkeypatch.setattr(twelvedata, "MAX_OUTPUTSIZE", 100)
    start = pd.Timestamp("2026-01-01", tz="UTC")
    times = pd.date_range(start, periods=250, freq="5min", tz="UTC")

    def handler(method, url, kw):
        p = kw["params"]
        assert "apikey" not in p
        assert kw["headers"]["Authorization"] == "apikey SECRET123"
        end = pd.Timestamp(p["end_date"], tz="UTC")
        sel = [t for t in times if t <= end][::-1][: p["outputsize"]]  # newest first
        return {"status": "ok", "values": td_values(sel)}

    sess = fake_session(handler)
    df = twelvedata.fetch_candles("XAU/USD", "5m", start, times[-1] + pd.Timedelta(hours=1),
                                  api_key="SECRET123", base_url="u", session=sess, pause_s=0)
    assert len(sess.calls) == 3
    assert len(df) == 250
    assert (df["volume"] == 0).all()  # FX/metals: no volume field


def test_twelvedata_error_does_not_leak_key(fake_session):
    sess = fake_session(lambda m, u, k: {"status": "error", "code": 401, "message": "bad key"})
    with pytest.raises(DataFetchError) as exc:
        twelvedata.fetch_candles("XAU/USD", "5m", pd.Timestamp("2026-01-01", tz="UTC"),
                                 pd.Timestamp("2026-01-02", tz="UTC"),
                                 api_key="SECRET123", base_url="u", session=sess, pause_s=0)
    assert "SECRET123" not in str(exc.value)


# ---------- synthetic ----------

def test_synthetic_is_deterministic_and_timeframes_agree():
    a = synthetic.generate_1m(["BTC", "ETH"], days=2, seed=1)
    b = synthetic.generate_1m(["BTC", "ETH"], days=2, seed=1)
    pd.testing.assert_frame_equal(a["BTC"], b["BTC"])

    one = a["BTC"]
    h = synthetic.resample(one, "1h")
    assert len(h) == 48
    first_hour = one.iloc[:60]
    assert h.loc[0, "high"] == first_hour["high"].max()
    assert h.loc[0, "low"] == first_hour["low"].min()
    assert h.loc[0, "open"] == first_hour["open"].iloc[0]
    assert h.loc[0, "close"] == first_hour["close"].iloc[-1]
