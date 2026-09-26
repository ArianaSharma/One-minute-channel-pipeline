"""Session and killzone windows (UTC, from config)."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# Which session's high/low each killzone hunts.
KILLZONE_REFERENCE = {"london": "asia", "ny_am": "london"}


@dataclass(frozen=True)
class Window:
    name: str
    start: pd.Timestamp
    end: pd.Timestamp

    def contains(self, ts: pd.Timestamp) -> bool:
        return self.start <= ts < self.end


def _at(day: pd.Timestamp, hhmm: str) -> pd.Timestamp:
    h, m = (int(x) for x in hhmm.split(":"))
    return day + pd.Timedelta(hours=h, minutes=m)


def window(day: pd.Timestamp, name: str, spec: list[str]) -> Window:
    """`day` is a UTC midnight; spec is ["HH:MM", "HH:MM"]."""
    return Window(name, _at(day, spec[0]), _at(day, spec[1]))


def killzone_plan(day: pd.Timestamp, cfg: dict) -> list[tuple[Window, Window]]:
    """(killzone, reference session) pairs for one UTC day."""
    plan = []
    for kz_name, kz_spec in cfg["killzones"].items():
        ref_name = KILLZONE_REFERENCE.get(kz_name)
        if ref_name is None:
            raise ValueError(f"no reference session defined for killzone {kz_name!r}")
        kz = window(day, kz_name, kz_spec)
        ref = window(day, ref_name, cfg["sessions"][ref_name])
        if ref.end > kz.start:
            raise ValueError(f"session {ref_name} must end before killzone {kz_name} starts")
        plan.append((kz, ref))
    return plan
