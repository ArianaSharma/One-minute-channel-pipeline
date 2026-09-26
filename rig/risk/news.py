"""Red-folder rule: no signal from N minutes before to N minutes after a high-impact release.

Reads data/news_events.csv (timestamp_utc, currency, event, impact). Only rows with
impact == "High" (case-insensitive) block. Each instrument maps to the currencies whose
news it reacts to (config risk.news_currencies, default USD).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ["timestamp_utc", "currency", "event", "impact"]


@dataclass(frozen=True)
class NewsHit:
    event: str
    currency: str
    at: pd.Timestamp

    def reason(self) -> str:
        return f"news_block: {self.currency} {self.event} at {self.at:%Y-%m-%d %H:%M} UTC"


class NewsCalendar:
    def __init__(self, events: pd.DataFrame, block_minutes: float = 2.0,
                 currencies: dict[str, list[str]] | None = None):
        missing = set(REQUIRED_COLUMNS) - set(events.columns)
        if missing:
            raise ValueError(f"news file is missing columns: {sorted(missing)}")
        ev = events.copy()
        ev["timestamp_utc"] = pd.to_datetime(ev["timestamp_utc"], utc=True)
        ev = ev[ev["impact"].astype(str).str.strip().str.lower() == "high"]
        self.events = ev.sort_values("timestamp_utc").reset_index(drop=True)
        self.window = pd.Timedelta(minutes=block_minutes)
        self.currencies = currencies or {}

    @classmethod
    def from_config(cls, cfg: dict, root: Path | None = None) -> "NewsCalendar":
        from rig.config import resolve
        risk = cfg["risk"]
        path = resolve(risk["news_file"])
        if not path.exists():
            raise FileNotFoundError(f"red-folder calendar not found: {path}")
        return cls(pd.read_csv(path), risk.get("news_block_minutes", 2),
                   risk.get("news_currencies"))

    def currencies_for(self, symbol: str) -> list[str]:
        return self.currencies.get(symbol, ["USD"])

    def check(self, symbol: str, ts: pd.Timestamp) -> NewsHit | None:
        """Return the blocking event if `ts` is within +/- window of one, inclusive."""
        ev = self.events
        near = ev[(ev["timestamp_utc"] >= ts - self.window) & (ev["timestamp_utc"] <= ts + self.window)
                  & ev["currency"].isin(self.currencies_for(symbol))]
        if near.empty:
            return None
        row = near.iloc[0]
        return NewsHit(str(row["event"]), str(row["currency"]), row["timestamp_utc"])
