"""Single entry point: python -m rig fetch|detect|score|sim|eval|review"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone

from rig import db
from rig.config import env, load_config, resolve

NOT_YET = {
    "detect": "Phase 2 (setup detector)",
    "score": "Phase 4 (Jev client)",
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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rig", description="Jev ICT/SMC research rig (paper/sim only)")
    p.add_argument("--config", help="path to config.yaml (default: repo root)")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)

    f = sub.add_parser("fetch", help="download candles into the local parquet cache")
    f.add_argument("--source", choices=["auto", "hyperliquid", "twelvedata", "synthetic"],
                   default="auto", help="auto = Hyperliquid, plus Twelve Data if its key is set")
    f.add_argument("--symbols", nargs="+", help="override the symbols in config")
    f.add_argument("--intervals", nargs="+", choices=["1m", "5m", "15m", "1h"])

    for name, phase in NOT_YET.items():
        sub.add_parser(name, help=f"not built yet: {phase}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    cfg = load_config(args.config)

    if args.command in NOT_YET:
        print(f"`rig {args.command}` is not built yet: {NOT_YET[args.command]}")
        return 2

    conn = db.connect(resolve(cfg["db_path"]))
    started = datetime.now(timezone.utc).isoformat()
    run_id = conn.execute("INSERT INTO runs (command, started_utc) VALUES (?, ?)",
                          (args.command, started)).lastrowid
    conn.commit()
    status = "error"
    try:
        code = {"fetch": cmd_fetch}[args.command](args, cfg)
        status = "ok" if code == 0 else "partial"
        return code
    finally:
        conn.execute("UPDATE runs SET finished_utc = ?, status = ? WHERE id = ?",
                     (datetime.now(timezone.utc).isoformat(), status, run_id))
        conn.commit()
        conn.close()
