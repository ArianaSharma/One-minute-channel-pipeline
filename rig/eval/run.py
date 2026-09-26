"""`rig eval` (train) and `rig eval --holdout` (once, at the end).

Split: by signal time over the span of cached 5m candles. The last `holdout_fraction`
is the holdout. Train signals within one trade-lifetime (entry expiry + max hold) of the
boundary are dropped so no train trade can overlap the holdout.

Train:   choose the target_before_stop threshold for arm B (best train expectancy with at
         least `min_train_trades` trades), save it, and report.
Holdout: refuses to run twice. Uses the saved threshold as-is, reports, and writes a lock.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from rig import pipeline
from rig.config import resolve
from rig.eval import metrics, plots
from rig.filter import FilterParams, decide
from rig.jev_client.questions import NOUL_QUESTIONS
from rig.risk.correlation import apply_no_stacking

RESOLVED = ("target", "stop", "timeout")
JEV_FIELDS = ["regime", "confidence", "setup_quality", "direction_agrees", "sweep_is_genuine",
              "target_before_stop"]


class HoldoutLocked(RuntimeError):
    pass


def config_hash(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:12]


def report_dir(cfg: dict, mode: str) -> Path:
    d = resolve(cfg["eval"].get("reports_dir", "reports")) / f"{pipeline.data_source(cfg)}_{mode}"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- data assembly

def build_frame(cfg: dict, conn: sqlite3.Connection, mode: str) -> pd.DataFrame:
    sig = pipeline.load_signals(conn, "candidate")
    trades = pd.read_sql_query("SELECT * FROM trades", conn)
    labels = pd.read_sql_query("SELECT * FROM labels", conn)
    answers = pipeline.latest_answers(conn, mode)
    df = sig.merge(trades, left_on="id", right_on="signal_id", how="left", suffixes=("", "_t"))
    df = df.merge(labels.add_prefix("label_"), left_on="id", right_on="label_signal_id", how="left")
    if not answers.empty:
        df = df.merge(answers.add_prefix("jev_"), left_on="id", right_on="jev_signal_id", how="left")
    for f in JEV_FIELDS + ["cost_usd", "latency_ms"]:
        if f"jev_{f}" not in df:
            df[f"jev_{f}"] = np.nan
    df["fill_ts"] = pd.to_datetime(df["fill_ts_utc"], utc=True)
    df["exit_ts"] = pd.to_datetime(df["exit_ts_utc"], utc=True)
    return df


def split_boundary(cfg: dict) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    starts, ends = [], []
    for s in pipeline.all_symbols(cfg):
        try:
            c = pipeline.load_frames(cfg, s, ("5m",))["5m"]
        except FileNotFoundError:
            continue
        starts.append(c["ts"].iloc[0])
        ends.append(c["ts"].iloc[-1])
    if not starts:
        raise RuntimeError("no cached candles; run `rig fetch` first")
    start, end = min(starts), max(ends)
    frac = cfg["eval"]["holdout_fraction"]
    return start, (start + (end - start) * (1 - frac)).floor("h"), end


def split_frame(cfg: dict, df: pd.DataFrame, split: str) -> tuple[pd.DataFrame, dict]:
    start, boundary, end = split_boundary(cfg)
    s = cfg["sim"]
    embargo = pd.Timedelta(minutes=5 * s["entry_expiry_bars"]) + pd.Timedelta(hours=s.get("max_hold_hours", 24))
    if split == "train":
        part = df[df["ts"] < boundary - embargo]
    else:
        part = df[df["ts"] >= boundary]
    info = {"data_start": start, "boundary": boundary, "data_end": end, "embargo": embargo}
    return part.copy(), info


# ---------------------------------------------------------------- arms

def run_arm(df: pd.DataFrame, arm: str, fp: FilterParams | None, groups) -> tuple[pd.DataFrame, list]:
    decisions, tradable = [], []
    for row in df.itertuples():
        if arm == "B":
            ans = None
            if pd.notna(row.jev_confidence):
                ans = {f: getattr(row, f"jev_{f}") for f in JEV_FIELDS}
            action, reason = decide(ans, fp)
            if action != "take":
                decisions.append((row.id, action, reason))
                continue
        if row.outcome not in RESOLVED:
            decisions.append((row.id, "skip", f"not_traded: {row.outcome}"))
            continue
        tradable.append(row.Index)
    trades = df.loc[tradable]
    if trades.empty:
        return trades.assign(taken=[]), decisions
    stacked = apply_no_stacking(trades.rename(columns={"id": "signal_id_"}).assign(
        signal_id=trades["id"]), groups)
    for r in stacked.itertuples():
        decisions.append((r.signal_id, "take" if r.taken else "skip", r.skip_reason))
    taken = df.loc[stacked.index[stacked["taken"].to_numpy()]]
    return taken, decisions


def choose_threshold(train: pd.DataFrame, cfg: dict, groups) -> tuple[float, list[dict], str]:
    grid = np.round(np.arange(0.30, 0.801, 0.05), 2)
    min_trades = cfg["eval"].get("min_train_trades", 20)
    rows = []
    for th in grid:
        taken, _ = run_arm(train, "B", FilterParams.from_config(cfg, float(th)), groups)
        m = metrics.trade_metrics(taken)
        rows.append({"threshold": float(th), "trades": m["trades"], "expectancy_r": m["expectancy_r"]})
    eligible = [r for r in rows if r["trades"] >= min_trades and r["expectancy_r"] is not None]
    if not eligible:
        default = cfg["filter"]["target_before_stop_threshold"]
        return default, rows, (f"no threshold left >= {min_trades} train trades; "
                               f"kept the config default {default}")
    best = max(eligible, key=lambda r: (r["expectancy_r"], r["trades"]))
    return best["threshold"], rows, f"best train expectancy with >= {min_trades} trades"


# ---------------------------------------------------------------- evaluate

def evaluate(cfg: dict, conn: sqlite3.Connection, mode: str, split: str) -> Path:
    out = report_dir(cfg, mode)
    lock_path = out / "holdout_lock.json"
    th_path = out / "threshold.json"
    groups = cfg["risk"]["correlation_groups"]
    notes = []

    if split == "holdout":
        if lock_path.exists():
            raise HoldoutLocked(str(lock_path))
        if not th_path.exists():
            raise RuntimeError("run `rig eval` on train first; the holdout uses its frozen threshold")
        frozen = json.loads(th_path.read_text())
        threshold, why = frozen["threshold"], f"frozen from train on {frozen['chosen_utc']}"
        if frozen["config_hash"] != config_hash(cfg):
            notes.append("Config changed since the train threshold was chosen. Reported as-is.")
    elif lock_path.exists():
        notes.append("WARNING: the holdout has already been evaluated. Anything changed after "
                     "seeing it can no longer be validated on it.")

    df = build_frame(cfg, conn, mode)
    part, info = split_frame(cfg, df, split)

    grid = None
    if split == "train":
        threshold, grid, why = choose_threshold(part, cfg, groups)
        th_path.write_text(json.dumps({
            "threshold": threshold, "reason": why, "grid": grid,
            "chosen_utc": datetime.now(timezone.utc).isoformat(), "config_hash": config_hash(cfg),
        }, indent=2))

    fp = FilterParams.from_config(cfg, threshold)
    taken_a, dec_a = run_arm(part, "A", None, groups)
    taken_b, dec_b = run_arm(part, "B", fp, groups)
    m_a, m_b = metrics.trade_metrics(taken_a), metrics.trade_metrics(taken_b)
    boot = metrics.bootstrap_diff(taken_a["r_multiple"], taken_b["r_multiple"],
                                  cfg["eval"]["bootstrap_samples"])

    calib = {}
    for q in NOUL_QUESTIONS:
        sub = part.dropna(subset=[f"jev_{q}", f"label_{q}"])
        rep = metrics.brier_report(sub[f"jev_{q}"], sub[f"label_{q}"])
        table = metrics.reliability_table(sub[f"jev_{q}"], sub[f"label_{q}"])
        png = out / f"reliability_{q}_{split}.png"
        plots.reliability_plot(table, q, split, rep, png)
        calib[q] = {**rep, "plot": png.name}
    plots.equity_plot({"A": taken_a, "B": taken_b}, split, out / f"equity_{split}.png")

    run_id = conn.execute("INSERT INTO runs (command, started_utc, status, detail) VALUES (?,?,?,?)",
                          (f"eval:{split}", datetime.now(timezone.utc).isoformat(), "ok",
                           json.dumps({"mode": mode, "threshold": threshold}))).lastrowid
    conn.executemany("INSERT INTO decisions VALUES (?,?,?,?,?,?)",
                     [(run_id, arm, split, sid, a, r) for arm, decs in (("A", dec_a), ("B", dec_b))
                      for sid, a, r in decs])
    conn.commit()

    trade_log = _trade_log(part, dec_a, dec_b)
    trade_log.to_csv(out / f"trades_{split}.csv", index=False)

    summary = {
        "split": split, "mode": mode, "data_source": pipeline.data_source(cfg),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config_hash": config_hash(cfg),
        "period": {k: str(v) for k, v in info.items()},
        "signals_in_split": int(len(part)),
        "threshold": threshold, "threshold_reason": why, "threshold_grid": grid,
        "arm_a": m_a, "arm_b": m_b, "expectancy_diff_b_minus_a": boot,
        "decisions": {"A": _reason_counts(dec_a), "B": _reason_counts(dec_b)},
        "calibration": calib,
        "jev": _jev_summary(part),
        "notes": notes,
    }
    (out / f"summary_{split}.json").write_text(json.dumps(summary, indent=2, default=str))
    report = out / f"eval_{split}.md"
    report.write_text(render_markdown(summary, cfg))

    if split == "holdout":
        lock_path.write_text(json.dumps({"evaluated_utc": summary["generated_utc"],
                                         "threshold": threshold, "report": report.name,
                                         "config_hash": summary["config_hash"]}, indent=2))
    return report


def _reason_counts(decisions) -> dict:
    counts: dict = {}
    for _, action, reason in decisions:
        key = action if not reason else f"{action}: {reason.split(':')[0].split(' ')[0]}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def _trade_log(part: pd.DataFrame, dec_a, dec_b) -> pd.DataFrame:
    a = pd.DataFrame(dec_a, columns=["id", "arm_a_action", "arm_a_reason"])
    b = pd.DataFrame(dec_b, columns=["id", "arm_b_action", "arm_b_reason"])
    cols = ["id", "symbol", "ts_utc", "killzone", "direction", "zone_kind", "reward_risk",
            "outcome", "r_multiple", "pnl_usd"] + [f"jev_{f}" for f in JEV_FIELDS] + \
           [f"label_{q}" for q in NOUL_QUESTIONS]
    return part[cols].merge(a, on="id", how="left").merge(b, on="id", how="left")


def _jev_summary(part: pd.DataFrame) -> dict:
    scored = part.dropna(subset=["jev_confidence"])
    if scored.empty:
        return {"scored": 0}
    return {
        "scored": int(len(scored)),
        "regimes": scored["jev_regime"].value_counts().to_dict(),
        "mean_confidence": float(scored["jev_confidence"].mean()),
        "escalation_rate": float((scored["jev_confidence"] < 0.60).mean()),
        "mean_latency_ms": float(scored["jev_latency_ms"].mean()),
        "total_cost_usd": float(scored["jev_cost_usd"].sum()),
    }


# ---------------------------------------------------------------- markdown

def _f(x, fmt="{:.3f}"):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else fmt.format(x)


def render_markdown(s: dict, cfg: dict) -> str:
    a, b, d = s["arm_a"], s["arm_b"], s["expectancy_diff_b_minus_a"]
    risk = cfg["risk"]["risk_per_trade_usd"]
    title = "HOLDOUT (evaluated once, reported as-is)" if s["split"] == "holdout" else "Train"
    lines = [
        f"# Eval report: {title}",
        "",
        f"- Data source: `{s['data_source']}` · JEV_MODE: `{s['mode']}` · generated {s['generated_utc']}",
        f"- Period: {s['period']['data_start'][:16]} → {s['period']['data_end'][:16]} UTC; "
        f"holdout starts {s['period']['boundary'][:16]}",
        f"- Signals in this split: {s['signals_in_split']} · risk per trade ${risk} · config `{s['config_hash']}`",
        f"- target_before_stop threshold: **{s['threshold']}** ({s['threshold_reason']})",
    ]
    if s["mode"] == "mock" or s["data_source"] == "synthetic":
        lines += ["", "> **Pipeline check only.** Mock Jev answers are random and/or candles are "
                      "synthetic. Nothing here says anything about Jev or the market. Expect B ≈ A "
                      "and Brier ≈ or worse than the base-rate reference."]
    for n in s["notes"]:
        lines += ["", f"> {n}"]
    lines += [
        "", "## A vs B", "",
        "| Metric | A: all rule-based | B: Jev-filtered |", "|---|---|---|",
        f"| Trades | {a['trades']} | {b['trades']} |",
        f"| Hit rate | {_f(a['hit_rate'], '{:.1%}')} | {_f(b['hit_rate'], '{:.1%}')} |",
        f"| Expectancy (R, net) | {_f(a['expectancy_r'])} | {_f(b['expectancy_r'])} |",
        f"| Total R | {_f(a['total_r'], '{:+.2f}')} | {_f(b['total_r'], '{:+.2f}')} |",
        f"| P&L ($) | {_f(a['pnl_usd'], '{:+,.2f}')} | {_f(b['pnl_usd'], '{:+,.2f}')} |",
        f"| Profit factor | {_f(a['profit_factor'], '{:.2f}')} | {_f(b['profit_factor'], '{:.2f}')} |",
        f"| Max drawdown (R) | {_f(a['max_drawdown_r'], '{:.2f}')} | {_f(b['max_drawdown_r'], '{:.2f}')} |",
        f"| Max drawdown ($) | {_f(a['max_drawdown_usd'], '{:,.2f}')} | {_f(b['max_drawdown_usd'], '{:,.2f}')} |",
        "",
        f"**Expectancy difference B − A:** {_f(d['diff'], '{:+.3f}')} R, 95% bootstrap CI "
        f"[{_f(d['low'], '{:+.3f}')}, {_f(d['high'], '{:+.3f}')}]; "
        f"share of resamples where B is not better: {_f(d['p_b_not_better'], '{:.1%}')}.",
        "",
        f"![equity](equity_{s['split']}.png)",
        "", "## Calibration of Jev's Noul answers", "",
        "Brier: lower is better. The reference always predicts the base rate; skill > 0 means "
        "Jev beat it.", "",
        "| Question | n | Brier | Base-rate reference | Skill | Base rate |", "|---|---|---|---|---|---|",
    ]
    for q, c in s["calibration"].items():
        lines.append(f"| {q} | {c['n']} | {_f(c['brier'])} | {_f(c['brier_reference'])} | "
                     f"{_f(c['skill'], '{:+.3f}')} | {_f(c['base_rate'], '{:.1%}')} |")
    lines.append("")
    for q, c in s["calibration"].items():
        lines.append(f"![{q}]({c['plot']})")
    j = s["jev"]
    lines += ["", "## Jev usage", ""]
    if j.get("scored"):
        lines += [f"- Scored signals: {j['scored']} · mean confidence {j['mean_confidence']:.2f} · "
                  f"escalation rate {j['escalation_rate']:.1%}",
                  f"- Regimes: {j['regimes']}",
                  f"- Mean latency {j['mean_latency_ms']:.0f} ms · token cost ${j['total_cost_usd']:.6f}"]
    else:
        lines.append("- No Jev answers for this split (run `rig score`).")
    lines += ["", "## Decisions", "", "Every take / skip / escalate, with its reason "
              "(full log in the `decisions` table and the trades CSV).", ""]
    for arm in ("A", "B"):
        lines.append(f"- **Arm {arm}:** " + ", ".join(f"{k} ({v})" for k, v in s["decisions"][arm].items()))
    if s.get("threshold_grid"):
        lines += ["", "## Threshold search (train only)", "", "| Threshold | Trades | Expectancy (R) |",
                  "|---|---|---|"]
        for r in s["threshold_grid"]:
            lines.append(f"| {r['threshold']:.2f} | {r['trades']} | {_f(r['expectancy_r'])} |")
    lines += ["", f"Trade log: `trades_{s['split']}.csv`", ""]
    return "\n".join(lines)
