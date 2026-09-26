# Jev ICT/SMC research rig (Phase 1: research and paper only)

Tests whether TypeSafe AI's **Jev** model (a "System One" model that returns typed answers
with calibrated probabilities) can improve rule-based ICT/SMC setups.

**No live trading.** Nothing in this repo places, modifies or cancels orders, and a test
guards against it. The hard rules are in [CLAUDE.md](CLAUDE.md).

```
fetch ─► detect ─► score ─► sim ─► eval (train) ─► … ─► eval --holdout (once) ─► review
candles  setups    Jev      paper   A vs B,            final, locked            Claude
         + news    battery  trades  threshold,                                  suggests
         gate                       calibration
```

## Setup

```bash
uv venv && uv pip install -e ".[dev]"      # or: python -m venv .venv && pip install -e ".[dev]"
source .venv/bin/activate
cp .env.example .env                        # keys are optional for mock mode
python -m pytest                            # 85 tests, ~10 s
```

`.env` (gitignored; keys are only ever read from the environment):

| Variable | Needed for |
|---|---|
| `JEV_MODE` | `mock` (default, no key) or `live` |
| `TYPESAFE_API_KEY` | `JEV_MODE=live` |
| `TWELVEDATA_API_KEY` | optional XAU/USD and NAS100 (`NDX`) candles |
| `ANTHROPIC_API_KEY` | `rig review` (not needed for `--dry-run`) |

## Run end to end in mock mode (no keys, no network)

```bash
export JEV_MODE=mock
R="python -m rig --data-source synthetic"
$R fetch --source synthetic     # 365 days of seeded synthetic BTC/ETH candles
$R detect                       # find setups, apply red-folder gate, log to SQLite
$R score                        # mock Jev battery for every candidate
$R sim                          # bar-by-bar paper sim + calibration labels
$R eval                         # train: pick threshold, A vs B, Brier, plots
$R eval --holdout               # holdout: ONCE, frozen threshold, then locked
$R review --dry-run             # the exact prompt the weekly review would send
```

Output goes to `reports/synthetic_mock/`. A committed copy of one such run is in
[`reports/sample/`](reports/sample/): open `eval_train.md` and `eval_holdout.md`.

**How to read a mock run.** Mock answers are random (seeded from the snapshot only, never
from outcomes), so arm B is a random subset of arm A and every Brier score should be at or
worse than the base-rate reference. In the sample, the threshold picked on train made B
look +0.36R better than A. On the holdout the same frozen threshold gave −0.21R. That's
noise, and it's why the holdout rule exists.

## Run with real data

```bash
python -m rig fetch                        # Hyperliquid BTC/ETH (+ Twelve Data if key set)
python -m rig detect
JEV_MODE=live python -m rig score --limit 5    # try a few calls first
JEV_MODE=live python -m rig score
python -m rig sim
JEV_MODE=live python -m rig eval
# ... only when you're finished iterating on train:
JEV_MODE=live python -m rig eval --holdout
JEV_MODE=live python -m rig review
```

Real runs log to `data/rig_hyperliquid.db` and report to `reports/hyperliquid_live/`, kept
apart from mock runs.

### Data limits you need to know about

- **Hyperliquid serves only the most recent 5,000 candles per interval**: about 3.5 days of
  1m, 17 days of 5m, 52 days of 15m. The detector needs 5m and 15m, so a first fetch
  gives you about 2.5 weeks of setups. The cache only appends, so **run `rig fetch` at least
  weekly** (1m every few days if you want 1m sim precision) and history builds up.
  The sim falls back to 5m bars when 1m bars are missing.
- **Sample size decides everything.** With 2 symbols and 2 killzones, expect roughly
  0.5–1 signal per symbol per day, and far fewer filled trades. In the 365-day sample,
  arm A had 172 train trades and the bootstrap interval on B − A was still about ±1.3R wide.
  Don't read anything into a few dozen trades.
- **Tight ICT stops make costs large in R.** At Hyperliquid base-tier fees (1.5 bp maker,
  4.5 bp taker, 1 bp slippage on market exits), a stop-out averages about −1.4R in the sample.
  Adjust `sim:` in `config.yaml` for your tier.

## What each part does

| Folder | Role |
|---|---|
| `rig/data/` | Hyperliquid `candleSnapshot` (info endpoint only), optional Twelve Data, synthetic candles, parquet cache |
| `rig/setups/` | Detector: prior-session sweep (15m) → MSS (5m) → FVG/OB in the 62–79% OTE zone, killzones only. Builds the snapshot sent to Jev, including a plain-language `summary`, because TypeSafe documents that Jev 1.13 is weak at numeric comparison |
| `rig/risk/` | Red-folder gate (±2 min, `data/news_events.csv`), no correlated stacking, $25/$50 sizing, 1.5R minimum |
| `rig/jev_client/` | One `system_one` call per signal via the official `typesafe-sdk`, model pinned to `jev-1.13.0`. Logs every question, answer, probability, confidence, latency, token count, cost and request ID. `mock.py` has the same shape and needs no key |
| `rig/sim/` | Limit entry with expiry. Stop wins same-bar ties, and the fill bar never counts a target. Maker/taker fees and slippage. Outcome labels for calibration |
| `rig/filter/` | Arm B: escalate if confidence < 0.60 (not traded), skip crisis, quality < 2, or target_before_stop < threshold |
| `rig/eval/` | Time split with an embargo, threshold chosen on train only, one-shot holdout lock, metrics, Brier with base-rate reference, reliability plots, bootstrap CI |
| `rig/review/` | Weekly review by `claude-opus-5-5`. Writes one markdown file and changes nothing else (tested) |

### Jev battery (one call per signal)

| Key | Primitive | Used for |
|---|---|---|
| `regime` | Choice: trending_up, trending_down, ranging, volatile_chop, crisis | skip if crisis |
| `direction_agrees` | Noul | calibration |
| `setup_quality` | Score 0–3 | take only if ≥ 2 |
| `sweep_is_genuine` | Noul | calibration |
| `target_before_stop` | Noul | take only if ≥ threshold (chosen on train) |

**Confidence:** in TypeSafe's API, Noul answers carry no confidence; only Choice and Score
do. The gate therefore uses `min(regime.confidence, setup_quality.confidence)`.

**Calibration labels** (computed from candles after the signal, never shown to Jev):
- `direction_agrees`: whether the close 4h later is beyond the MSS close in the trade's direction.
- `sweep_is_genuine`: whether price stays inside the sweep extreme for those 4h.
- `target_before_stop`: whether the target is touched before the stop within 24h.

### Holdout discipline

`rig eval` uses only train data, embargoed so no train trade can overlap the holdout (last
25% of the candle span). It saves the chosen threshold to `threshold.json`.
`rig eval --holdout` reuses that threshold untouched, writes the report, and creates
`holdout_lock.json`. Any later `--holdout` run only points you back to the stored result.
Re-running train afterwards is allowed, but the report is stamped with a warning.

### Red-folder calendar

`data/news_events.csv` holds 97 high-impact USD events (CPI, NFP, PPI, GDP, Core PCE, FOMC
statement and press conference). They were built by `data/build_news_events.py` from the
BLS, Federal Reserve and BEA schedule tables, converted from ET to UTC with daylight saving
handled. It covers **Dec 2025 – Dec 2026** (FOMC: 2025–2026). Extend it before testing on
data outside that range. The FMP connector was the first choice, but its economic calendar
needs a paid FMP plan.

## Logs

Everything is in SQLite (`data/rig_<source>.db`):
- `signals`: every candidate, and every skipped signal with its reason
- `jev_calls`: the full battery and answers, latency, tokens and cost
- `trades`: sim results
- `labels`: calibration labels
- `decisions`: every take, skip or escalate per arm, with its reason
- `runs`: each command run

Each eval also writes `trades_<split>.csv`.
