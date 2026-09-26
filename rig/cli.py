"""Single entry point: python -m rig fetch|detect|score|sim|eval|review"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone

from rig import db
from rig.config import env, load_config

NOT_YET = {
    "sim": "Phase 5 (paper sim)",
    "eval": "Phase 7 (evaluation)",
    "review": "Phase 8 (weekly review)",
}


def cmd_fetch(args, cfg) -> int:
    from rig.data import fetch

    intervals = args.intervals or cfg["data"]["timeframes"]
    results = []
    if args.source == "synthetic":
        results += fetch.build_synthetic(cfg, intervals)
    else:
        if args.source in ("auto", "hyperliquid"):
            coins = args.symbols or cfg["data"]["hyperliquid"]["coins"]
            results += fetch.fetch_hyperliquid(cfg, coins, intervals)
        if args.source in ("auto", "twelvedata"):
            if not env("TWELVEDATA_API_KEY"):
                print("Twelve Data skipped: TWELVEDATA_API_KEY is not set")
            else:
                symbols = args.symbols or cfg["data"]["twelvedata"]["symbols"]
                results += fetch.fetch_twelvedata(cfg, symbols, intervals)
    for r in results:
        print(r.line())
    return 1 if any(r.error for r in results) else 0


def cmd_detect(args, cfg, conn) -> int:
    from rig import pipeline

    summary = pipeline.run_detect(cfg, conn)
    print("summary:", dict(summary))
    return 0


def cmd_score(args, cfg, conn) -> int:
    from rig import pipeline
    from rig.jev_client.base import jev_mode

    mode = jev_mode()
    summary = pipeline.run_score(cfg, conn, mode, limit=args.limit, rescore=args.rescore)
    cost = summary.pop("cost_usd_x1e6", 0) / 1e6
    print(f"JEV_MODE={mode}: {dict(summary)}  token cost ${cost:.6f}")
    return 1 if summary.get("error") else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rig", description="Jev ICT/SMC research rig (paper/sim only)")
    p.add_argument("--config", help="path to config.yaml (default: repo root)")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--data-source", choices=["hyperliquid", "synthetic"],
                   help="override data.source in config (synthetic = offline mock runs)")
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch", help="download candles into the local parquet cache")
    f.add_argument("--source", choices=["auto", "hyperliquid", "twelvedata", "synthetic"],
                   default="auto", help="auto = Hyperliquid, plus Twelve Data if its key is set")
    f.add_argument("--symbols", nargs="+", help="override the symbols in config")
    f.add_argument("--intervals", nargs="+", choices=["1m", "5m", "15m", "1h"])

    sub.add_parser("detect", help="find ICT setups in cached candles and log them")
    sc = sub.add_parser("score", help="ask Jev the question battery for each candidate (JEV_MODE)")
    sc.add_argument("--limit", type=int, help="score at most N signals (useful for a first live test)")
    sc.add_argument("--rescore", action="store_true", help="ask again even if already scored")

    for name, phase in NOT_YET.items():
        sub.add_parser(name, help=f"not built yet: {phase}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    cfg = load_config(args.config)
    if args.data_source:
        cfg["data"]["source"] = args.data_source

    if args.command in NOT_YET:
        print(f"`rig {args.command}` is not built yet: {NOT_YET[args.command]}")
        return 2

    from rig.pipeline import db_path
    conn = db.connect(db_path(cfg))
    started = datetime.now(timezone.utc).isoformat()
    run_id = conn.execute("INSERT INTO runs (command, started_utc) VALUES (?, ?)",
                          (args.command, started)).lastrowid
    conn.commit()
    status = "error"
    try:
        handler = {"fetch": cmd_fetch, "detect": cmd_detect, "score": cmd_score}[args.command]
        code = handler(args, cfg) if args.command == "fetch" else handler(args, cfg, conn)
        status = "ok" if code == 0 else "partial"
        return code
    finally:
        conn.execute("UPDATE runs SET finished_utc = ?, status = ? WHERE id = ?",
                     (datetime.now(timezone.utc).isoformat(), status, run_id))
        conn.commit()
        conn.close()
