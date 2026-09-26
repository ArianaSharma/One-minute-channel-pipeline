"""Glue between the CLI, the SQLite log, and the rig's components.

detect -> signals table (candidates + skipped with reasons)
score  -> jev_calls table (one battery per candidate signal)
sim    -> trades + labels tables
eval   -> decisions table + reports/
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from collections import Counter

import pandas as pd

from rig.config import resolve
from rig.data import load_candles
from rig.risk.news import NewsCalendar
from rig.risk.sizing import validate_trade
from rig.setups import detect_signals

log = logging.getLogger(__name__)


def data_source(cfg: dict) -> str:
    return cfg["data"]["source"]


def db_path(cfg: dict):
    return resolve(cfg["db_path"].format(source=data_source(cfg)))


def symbols_for(cfg: dict) -> list[str]:
    src = data_source(cfg)
    if src == "synthetic":
        return list(cfg["data"]["synthetic"]["symbols"])
    if src == "hyperliquid":
        return list(cfg["data"]["hyperliquid"]["coins"])
    raise ValueError(f"unknown data source {src!r}")


def candle_source(cfg: dict, symbol: str) -> str:
    """Twelve Data symbols live in their own cache folder."""
    src = data_source(cfg)
    if src == "hyperliquid" and symbol in cfg["data"]["twelvedata"]["symbols"]:
        return "twelvedata"
    return src


def all_symbols(cfg: dict) -> list[str]:
    syms = symbols_for(cfg)
    if data_source(cfg) == "hyperliquid":
        cache_dir = resolve(cfg["data"]["cache_dir"])
        for s in cfg["data"]["twelvedata"]["symbols"]:
            from rig.data.cache import cache_path
            if cache_path(cache_dir, "twelvedata", s, "5m").exists():
                syms.append(s)
    return syms


def load_frames(cfg: dict, symbol: str, intervals=("5m", "15m", "1h")) -> dict[str, pd.DataFrame]:
    cache_dir = resolve(cfg["data"]["cache_dir"])
    src = candle_source(cfg, symbol)
    return {i: load_candles(cache_dir, src, symbol, i) for i in intervals}


def snapshot_hash(snapshot: dict) -> str:
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- detect

def run_detect(cfg: dict, conn: sqlite3.Connection) -> Counter:
    news = NewsCalendar.from_config(cfg)
    min_rr = cfg["risk"]["min_reward_risk"]
    summary: Counter = Counter()
    for symbol in all_symbols(cfg):
        try:
            frames = load_frames(cfg, symbol)
        except FileNotFoundError as exc:
            print(f"skip {symbol}: {exc}")
            continue
        stats: Counter = Counter()
        signals = detect_signals(symbol, frames["15m"], frames["5m"], frames["1h"], cfg, stats)
        for s in signals:
            status, reason = "candidate", None
            hit = news.check(symbol, s.ts)
            bad = validate_trade(s.direction, s.entry, s.stop, s.target, min_rr)
            if bad:
                status, reason = "skipped", bad
            elif hit:
                status, reason = "skipped", hit.reason()
            summary[f"{status}"] += 1
            if reason:
                summary[f"skip:{reason.split(':')[0]}"] += 1
            _upsert_signal(conn, s, status, reason)
        conn.commit()
        print(f"{symbol:8} signals {len(signals):4}  detector stats {dict(stats)}")
    return summary


def _upsert_signal(conn, s, status, reason) -> None:
    conn.execute(
        """INSERT INTO signals (id, symbol, ts_utc, direction, killzone, entry, stop, target,
               reward_risk, target_type, zone_kind, sweep_extreme, mss_close, snapshot,
               snapshot_hash, status, skip_reason)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
               entry=excluded.entry, stop=excluded.stop, target=excluded.target,
               reward_risk=excluded.reward_risk, target_type=excluded.target_type,
               zone_kind=excluded.zone_kind, sweep_extreme=excluded.sweep_extreme,
               mss_close=excluded.mss_close, snapshot=excluded.snapshot,
               snapshot_hash=excluded.snapshot_hash, status=excluded.status,
               skip_reason=excluded.skip_reason""",
        (s.id, s.symbol, s.ts.isoformat(), s.direction, s.killzone, s.entry, s.stop, s.target,
         s.reward_risk, s.target_type, s.zone_kind, s.sweep_extreme, s.mss_close,
         json.dumps(s.snapshot), snapshot_hash(s.snapshot), status, reason),
    )


def load_signals(conn: sqlite3.Connection, status: str | None = "candidate") -> pd.DataFrame:
    q = "SELECT * FROM signals" + (" WHERE status = ?" if status else "") + " ORDER BY ts_utc"
    df = pd.read_sql_query(q, conn, params=(status,) if status else ())
    df["ts"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df


# ---------------------------------------------------------------- score

def run_score(cfg: dict, conn: sqlite3.Connection, mode: str, limit: int | None = None,
              rescore: bool = False) -> Counter:
    from datetime import datetime, timezone

    from rig.jev_client import BATTERY, get_client
    from rig.jev_client.base import dumps

    client = get_client(cfg, mode)
    signals = load_signals(conn, "candidate")
    done = {
        (r["signal_id"], r["snapshot_hash"])
        for r in conn.execute("SELECT signal_id, snapshot_hash FROM jev_calls "
                              "WHERE mode = ? AND error IS NULL", (mode,))
    }
    todo = [s for s in signals.itertuples() if rescore or (s.id, s.snapshot_hash) not in done]
    if limit:
        todo = todo[:limit]
    summary: Counter = Counter()
    for s in todo:
        result = client.ask(json.loads(s.snapshot), BATTERY)
        conn.execute(
            """INSERT INTO jev_calls (signal_id, snapshot_hash, mode, model, request_id, questions,
                   answers, latency_ms, input_tokens, output_tokens, cost_usd, error, created_utc)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (s.id, s.snapshot_hash, client.mode, result.model, result.request_id, dumps(BATTERY),
             dumps(result.answers) if result.answers is not None else None, result.latency_ms,
             result.input_tokens, result.output_tokens, result.cost_usd, result.error,
             datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        summary["ok" if result.ok else "error"] += 1
        summary["cost_usd_x1e6"] += int((result.cost_usd or 0) * 1e6)
    client.close()
    return summary


def latest_answers(conn: sqlite3.Connection, mode: str) -> pd.DataFrame:
    """Most recent successful battery per signal (matching the current snapshot)."""
    from rig.jev_client.base import parse

    rows = conn.execute(
        """SELECT j.signal_id, j.answers, j.latency_ms, j.cost_usd, j.model
           FROM jev_calls j JOIN signals s ON s.id = j.signal_id AND s.snapshot_hash = j.snapshot_hash
           WHERE j.mode = ? AND j.error IS NULL
           ORDER BY j.id""", (mode,)).fetchall()
    latest = {r["signal_id"]: r for r in rows}
    records = []
    for sid, r in latest.items():
        rec = {"signal_id": sid, "jev_model": r["model"], "latency_ms": r["latency_ms"],
               "cost_usd": r["cost_usd"]}
        rec.update({k: v for k, v in parse(json.loads(r["answers"])).items()
                    if not k.endswith("_probabilities")})
        records.append(rec)
    return pd.DataFrame(records)
