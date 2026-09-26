"""`rig review`: send the latest eval summary + trade log to Claude and save a markdown review.

This module is read-only with respect to the rig. The ONLY thing it writes is a new
markdown file under reports/. It never edits code, config.yaml, thresholds, the news
calendar, or the database; its output is advice for a human to read.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from rig.config import env

MODEL_DEFAULT = "claude-opus-5-5"

SYSTEM_PROMPT = """You review a paper-trading research rig for a discretionary ICT/SMC trader.
The rig detects rule-based setups (liquidity sweep of the prior session high/low, 5m market
structure shift, entry at an FVG or order block in the 62-79% OTE zone, London and NY AM
killzones only), asks TypeSafe's Jev model a battery of typed questions about each setup, and
compares arm A (every rule-based signal) against arm B (only signals Jev's answers pass).

Hard rules the rig follows, which your suggestions must respect:
- Research and paper trading only. Never suggest live trading, order placement, or exchange keys.
- Every trade has a stop at entry, at least 1.5R, and fixed $25 (or $50) risk.
- No signals within 2 minutes of a high-impact news release. No correlated stacking.
- Nothing is tuned on the holdout. If a holdout result is present, treat it as final and do not
  propose changes justified by it; say what a future, fresh holdout would need instead.

Your role is to suggest. A human decides. Be concrete and honest about sample size: say when a
difference is within noise (use the bootstrap interval and trade counts you are given). If the
data is synthetic or Jev ran in mock mode, say plainly that the numbers only test the pipeline.

Jev primitives, for any new question you propose: Choice (pick one option from a set, returns
probabilities + confidence), Score (ordered rubric levels, returns an expected score +
confidence), Noul (yes/no, returns a probability, no confidence). Jev is weak at arithmetic
and numeric comparison, so questions should be semantic judgements about named fields of the
snapshot, and numbers should be bucketed in code.

Write the review in Markdown with exactly these sections:
## Summary
## What worked
## What didn't
## What's miscalibrated
## Suggested new Jev questions
(for each: name, primitive, instructions, criteria, and what outcome label would grade it)
## Suggested experiments
(each must be testable on train data only, with the expected sign of the effect)
## Caveats"""


def collect_inputs(report_dir: Path) -> dict:
    summaries = {}
    for split in ("train", "holdout"):
        p = report_dir / f"summary_{split}.json"
        if p.exists():
            summaries[split] = json.loads(p.read_text())
    if not summaries:
        raise FileNotFoundError(f"no eval summaries in {report_dir}; run `rig eval` first")
    trade_logs = {}
    for split in summaries:
        p = report_dir / f"trades_{split}.csv"
        if p.exists():
            trade_logs[split] = p.read_text()
    return {"summaries": summaries, "trade_logs": trade_logs}


def build_user_message(inputs: dict) -> str:
    parts = ["Here are this week's eval summaries (JSON) and trade logs (CSV).", ""]
    for split, s in inputs["summaries"].items():
        parts += [f"<eval_summary split=\"{split}\">", json.dumps(s, indent=1, default=str),
                  "</eval_summary>", ""]
    for split, csv in inputs["trade_logs"].items():
        parts += [f"<trade_log split=\"{split}\">", csv.strip(), "</trade_log>", ""]
    parts.append("Write the review.")
    return "\n".join(parts)


def run_review(cfg: dict, report_dir: Path, dry_run: bool = False, client=None) -> Path:
    inputs = collect_inputs(report_dir)
    user_message = build_user_message(inputs)
    model = cfg.get("review", {}).get("model", MODEL_DEFAULT)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = report_dir / f"review_{stamp}.md"

    if dry_run:
        out = report_dir / f"review_{stamp}_DRY_RUN.md"
        out.write_text(
            f"# Review (dry run: no API call made)\n\nModel that would be called: `{model}`\n\n"
            f"## System prompt\n\n```text\n{SYSTEM_PROMPT}\n```\n\n"
            f"## User message ({len(user_message):,} characters)\n\n```text\n{user_message}\n```\n")
        return out

    if client is None:
        import anthropic
        if not env("ANTHROPIC_API_KEY"):
            raise RuntimeError("rig review needs ANTHROPIC_API_KEY in the environment (.env); "
                               "or run `rig review --dry-run` to see what would be sent")
        client = anthropic.Anthropic()

    # Claude Opus 5.5: thinking is always on (adaptive); effort defaults to medium, so set it.
    # `fallbacks: "default"` re-runs a classifier-declined request on Anthropic's recommended
    # fallback model server-side. Streamed because the trade log can make the input long.
    with client.beta.messages.stream(
        model=model,
        max_tokens=32000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        output_config={"effort": "high"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        message = stream.get_final_message()

    header = (f"# Weekly review ({stamp})\n\n_Generated by `{message.model}` from "
              f"{', '.join(inputs['summaries'])} eval results. Suggestions only: nothing in the "
              f"rig was changed._\n\n")
    if message.stop_reason == "refusal":
        category = getattr(getattr(message, "stop_details", None), "category", None)
        out.write_text(header + f"> The model declined to write this review "
                                f"(refusal category: {category}). No review was produced.\n")
        return out
    text = "\n".join(b.text for b in message.content if b.type == "text")
    if message.stop_reason == "max_tokens":
        text += "\n\n> Note: the review hit the output limit and may be cut off.\n"
    out.write_text(header + text + "\n")
    return out
