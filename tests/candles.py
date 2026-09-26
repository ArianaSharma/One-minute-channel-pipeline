"""Helpers for building hand-made candle sequences in tests."""
import pandas as pd

from rig.data.synthetic import resample

DAY = pd.Timestamp("2026-01-06", tz="UTC")  # a Tuesday


def flat_day(o=101.0, h=101.3, l=100.7, c=101.0):
    ts = pd.date_range(DAY, periods=288, freq="5min", tz="UTC")
    return pd.DataFrame({"ts": ts, "open": o, "high": h, "low": l, "close": c, "volume": 1.0})


def set_bars(df, bars):
    """bars: {"HH:MM": (o, h, l, c)} applied to the 5m frame."""
    df = df.copy()
    for hhmm, (o, h, l, c) in bars.items():
        t = DAY + pd.Timedelta(hours=int(hhmm[:2]), minutes=int(hhmm[3:]))
        df.loc[df["ts"] == t, ["open", "high", "low", "close"]] = [o, h, l, c]
    return df


# Asia range 100..102, then in the London killzone: a swing low at 07:15 (100.8),
# a 15m sweep of the Asia high at 07:30 (wick to 102.5, close 101.9 < 102),
# and a displacement that closes below the swing low at 07:50 (MSS).
# That leaves a bearish FVG [101.45, 101.8] overlapping the OTE band.
SHORT_SETUP = {
    "03:00": (101.0, 102.0, 100.7, 101.0),
    "04:00": (101.0, 101.3, 100.0, 101.0),
    "07:00": (101.0, 101.4, 100.9, 101.3),
    "07:05": (101.3, 101.6, 101.2, 101.5),
    "07:10": (101.5, 101.7, 101.1, 101.2),
    "07:15": (101.2, 101.3, 100.8, 100.9),
    "07:20": (100.9, 101.4, 100.9, 101.3),
    "07:25": (101.3, 101.8, 101.2, 101.7),
    "07:30": (101.7, 102.5, 101.6, 101.9),
    "07:35": (101.9, 102.2, 101.8, 101.95),
    "07:40": (101.95, 102.0, 101.8, 101.9),
    "07:45": (101.9, 101.95, 101.3, 101.4),
    "07:50": (101.4, 101.45, 100.6, 100.7),
}


def after(df, hhmm, o, h, l, c):
    """Set every bar from hhmm to the end of the day."""
    t = DAY + pd.Timedelta(hours=int(hhmm[:2]), minutes=int(hhmm[3:]))
    df = df.copy()
    df.loc[df["ts"] >= t, ["open", "high", "low", "close"]] = [o, h, l, c]
    return df


def frames(df5):
    return resample(df5, "15m"), df5, resample(df5, "1h")


def short_setup_5m():
    df = flat_day()
    df = after(df, "07:55", 100.7, 100.9, 100.5, 100.7)
    return set_bars(df, SHORT_SETUP)
