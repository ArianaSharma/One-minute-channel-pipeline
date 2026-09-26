# CLAUDE.md — Jev ICT/SMC research rig

This repo holds a **Phase 1 research rig**: it tests whether TypeSafe AI's Jev model
can improve discretionary ICT/SMC trade setups. Research and paper trading only.

(`build.py` and `script.py` at the root belong to an unrelated video pipeline. Leave them alone.)

## Hard rules (follow these in every session, no exceptions)

1. **No live trading.** No code that places, modifies, or cancels real orders. No
   live-trading endpoints and no private exchange keys. Market data and paper/sim only.
2. **Secrets come from environment variables only** (`.env`, gitignored). Never
   hardcode, log, or print an API key, including in errors, reports, or test output.
3. **Every simulated trade** has a stop loss set at entry, a reward:risk of at least 1:1.5,
   and a fixed risk of **$25 per trade** (configurable to $50). Signals that fail any of
   these are rejected before the sim runs.
4. **Red-folder rule.** No signal may be taken from 2 minutes before to 2 minutes after
   a high-impact news release. Event times come from `data/news_events.csv`
   (`timestamp_utc, currency, event, impact`). Blocked signals are flagged, skipped, and logged.
5. **No correlated stacking.** If a signal fires on a correlated instrument in the same
   session window while another paper position is open, skip it and log the reason.
6. **Holdout discipline.** Nothing may be tuned on the holdout period (the last 25% of
   data). The holdout is evaluated once, at the end, and the result is reported as-is.
7. **Plan before code.** Before writing code for each phase, show the user a plan and
   wait for approval.

## Jev / TypeSafe integration rules

- Use the official TypeSafe Python SDK (`typesafe-sdk`) or the HTTP API exactly as
  documented at docs.typesafe.ai. Do not guess endpoints, field names, or primitive formats.
  If the docs can't be reached, stop and tell the user.
- `JEV_MODE=mock|live`. Mock mode must let the whole pipeline run with no key.
- Log every question, answer, probability, confidence, latency, and token cost.

## Review script

`rig review` only **suggests**. It must never change code, thresholds, rules, or config.

## Working in this repo

- Setup: `uv venv && uv pip install -e ".[dev]"`; tests: `python -m pytest` (must stay green).
- Offline end-to-end check: `JEV_MODE=mock python -m rig --data-source synthetic <fetch --source synthetic|detect|score|sim|eval>`.
- Mock and real runs use separate DBs (`data/rig_<source>.db`) and report folders
  (`reports/<source>_<mode>/`). `reports/sample/` is the committed mock example.
- Never delete or edit a `holdout_lock.json` to re-run a holdout.
