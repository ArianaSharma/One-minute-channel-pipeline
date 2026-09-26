"""SQLite log store. Tables are created up front; later phases fill them in."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    command     TEXT NOT NULL,
    started_utc TEXT NOT NULL,
    finished_utc TEXT,
    status      TEXT,
    detail      TEXT
);

CREATE TABLE IF NOT EXISTS signals (
    id           TEXT PRIMARY KEY,
    symbol       TEXT NOT NULL,
    ts_utc       TEXT NOT NULL,
    direction    TEXT NOT NULL,
    killzone     TEXT,
    entry        REAL NOT NULL,
    stop         REAL NOT NULL,
    target       REAL NOT NULL,
    reward_risk  REAL NOT NULL,
    snapshot     TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'candidate',
    skip_reason  TEXT
);

CREATE TABLE IF NOT EXISTS jev_calls (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id     TEXT NOT NULL REFERENCES signals(id),
    mode          TEXT NOT NULL,
    model         TEXT,
    request_id    TEXT,
    questions     TEXT NOT NULL,
    answers       TEXT,
    latency_ms    REAL,
    input_tokens  INTEGER,
    output_tokens INTEGER,
    cost_usd      REAL,
    error         TEXT,
    created_utc   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trades (
    signal_id    TEXT PRIMARY KEY REFERENCES signals(id),
    filled       INTEGER NOT NULL,
    fill_ts_utc  TEXT,
    exit_ts_utc  TEXT,
    outcome      TEXT,
    r_multiple   REAL,
    pnl_usd      REAL,
    fees_usd     REAL
);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn
