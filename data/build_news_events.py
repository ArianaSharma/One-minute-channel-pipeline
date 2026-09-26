"""Build data/news_events.csv from official US release schedules.

Sources (copied verbatim from the agencies' own schedule tables, 2026-09-26):
  BLS CPI   https://www.bls.gov/schedule/news_release/cpi.htm      (08:30 ET)
  BLS NFP   https://www.bls.gov/schedule/news_release/empsit.htm   (08:30 ET)
  BLS PPI   https://www.bls.gov/schedule/news_release/ppi.htm      (08:30 ET)
  Fed FOMC  https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
            statement 14:00 ET and press conference 14:30 ET on the meeting's second day
  BEA GDP / Personal Income & Outlays (PCE)  https://www.bea.gov/news/schedule/full

Coverage: BLS and BEA from Dec 2025 through Dec 2026; FOMC for 2025 and 2026.
Add rows (or re-run with more dates) when you extend the data range.
Run:  python data/build_news_events.py
"""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

# (date, ET time, event)
RELEASES = [
    # BLS Consumer Price Index
    *[(d, "08:30", "CPI") for d in [
        "2025-12-18", "2026-01-13", "2026-02-13", "2026-03-11", "2026-04-10", "2026-05-12",
        "2026-06-10", "2026-07-14", "2026-08-12", "2026-09-11", "2026-10-14", "2026-11-10",
        "2026-12-10"]],
    # BLS Employment Situation (Non-Farm Payrolls)
    *[(d, "08:30", "Non-Farm Payrolls") for d in [
        "2025-12-16", "2026-01-09", "2026-02-11", "2026-03-06", "2026-04-03", "2026-05-08",
        "2026-06-05", "2026-07-02", "2026-08-07", "2026-09-04", "2026-10-02", "2026-11-06",
        "2026-12-04"]],
    # BLS Producer Price Index
    *[(d, "08:30", "PPI") for d in [
        "2026-01-14", "2026-01-30", "2026-02-27", "2026-03-18", "2026-04-14", "2026-05-13",
        "2026-06-11", "2026-07-15", "2026-08-13", "2026-09-10", "2026-10-15", "2026-11-13",
        "2026-12-15"]],
    # BEA GDP (advance / second / third or updated estimate)
    *[(d, "08:30", "GDP") for d in [
        "2026-01-22", "2026-02-20", "2026-03-13", "2026-04-09", "2026-04-30", "2026-05-28",
        "2026-06-25", "2026-07-30", "2026-08-26", "2026-09-30", "2026-10-29", "2026-11-25",
        "2026-12-23"]],
    # BEA Personal Income and Outlays (Core PCE)
    ("2026-01-22", "10:00", "Core PCE"),
    *[(d, "08:30", "Core PCE") for d in [
        "2026-02-20", "2026-03-13", "2026-04-09", "2026-04-30", "2026-05-28", "2026-06-25",
        "2026-07-30", "2026-08-26", "2026-09-30", "2026-10-29", "2026-11-25", "2026-12-23"]],
]

# Second (decision) day of each FOMC meeting
FOMC_DECISION_DAYS = [
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17",
    "2025-10-29", "2025-12-10",
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17", "2026-07-29", "2026-09-16",
    "2026-10-28", "2026-12-09",
]
for d in FOMC_DECISION_DAYS:
    RELEASES.append((d, "14:00", "FOMC Statement / Rate Decision"))
    RELEASES.append((d, "14:30", "FOMC Press Conference"))


def to_utc(date: str, et_time: str) -> str:
    local = datetime.fromisoformat(f"{date}T{et_time}").replace(tzinfo=ET)
    return local.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    rows = sorted({(to_utc(d, t), "USD", ev, "High") for d, t, ev in RELEASES})
    out = Path(__file__).with_name("news_events.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp_utc", "currency", "event", "impact"])
        w.writerows(rows)
    print(f"wrote {len(rows)} events to {out}")


if __name__ == "__main__":
    main()
