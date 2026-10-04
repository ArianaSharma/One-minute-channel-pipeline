# HMM Regime Trader: Spec, Architecture and Plan

Status: **DRAFT, waiting for approval.** No code gets written until the spec (§1), architecture (§2) and plan (§3) are approved and the open questions (§4) are answered.

Phases: brainstorm → **spec → architecture → plan** (approval gate) → test-first build → review against spec → ship (paper only).

---

## 1. Spec

### 1.1 Goal
A regime-aware trading system for a single liquid asset. A Gaussian HMM estimates the market state on every candle. Deterministic code turns those state probabilities into positions, inside hard risk limits that no model can override. Opus 5.5 runs offline at night. It researches, writes playbooks and audits results, and it has no authority over orders.

### 1.2 Non-negotiables (enforced by tests)
| # | Rule | How it is enforced |
|---|------|--------------------|
| N1 | No lookahead | Features at decision time *t* use only candles with close time < *t*. A **mutation test** perturbs every candle ≥ *t* and asserts that the decision at *t* comes out byte-identical. |
| N2 | Filtered probabilities only | We implement our own forward filter, `α_t ∝ B(o_t) · Aᵀ α_{t-1}`. `hmmlearn`'s `predict_proba` / `predict` are **smoothed** (forward-backward) or Viterbi. They are banned from `decide/` and `backtest/` by a lint test that greps imports and calls. |
| N3 | Hard limits live in code | `risk/limits.py` loads from `config/limits.yaml`, which is read-only to the LLM layer. Every order goes through `risk.check(order) -> Approve / Reject(reason)`. No code path reaches the broker without going through it, and a test enforces this. |
| N4 | Secrets | Keys are read from `.env` only, via `pydantic-settings`. `.env` is in `.gitignore`. A log redaction filter is covered by a test. Keys are never printed, committed or sent to the LLM. |
| N5 | External text is data | Headlines, feeds and fills are passed to Opus inside delimited data blocks. Opus output is parsed against a strict schema, and any free text is ignored by the executor. |
| N6 | Deterministic | There is a fixed seed for every HMM fit. With the same inputs and seed, a backtest produces identical results, and a test checks this. |

### 1.3 State engine (features)
Features are computed per candle *t* from data strictly before *t*:
- `r1`: 1-bar log return
- `rv20`: 20-bar realized volatility (std of log returns)
- `range`: (high − low) / close, log-transformed
- `volr`: volume / 20-bar median volume, log-transformed
- `trend`: **proposed:** 20-bar log-price slope ÷ `rv20` (a scale-free trend strength)

Standardization uses an **expanding-window** mean/std that is frozen at each refit. There are no full-sample z-scores anywhere. Inputs are clipped at ±5σ.

### 1.4 HMM
- `hmmlearn.GaussianHMM`, `covariance_type="full"` (falls back to `"diag"` if the fit is degenerate), and ≥ 3 years of training data.
- **K ∈ {2..5}** is chosen by BIC plus out-of-sample log-likelihood on the last 20% of the training window. If two candidates score within tolerance (ΔBIC < 10 or ΔOOS-LL < 1%), the smaller K wins.
- **20 restarts** with seeds `base_seed + i`. The fit with the best training log-likelihood is kept.
- Reports cover the transition matrix, per-state mean return and vol, and expected duration `1 / (1 − A_ii)`.
- **Auto-labelling** is deterministic and depends on the state's (mean, vol) rank:
  - `CRASH`: highest vol and negative mean
  - `STRESS`: elevated vol and mean ≤ 0
  - `CALM_UP`: low vol and positive mean
  - `CHOP`: everything else

  When K < 4, some labels go unused.

### 1.5 Switching rules (proposed defaults in brackets)
1. A challenger takes over only when its filtered probability is above **0.70**,
2. and it holds that lead for **3** consecutive candles.
3. **Cooldown: 5** candles after any switch.
4. If `P(next ∈ {STRESS, CRASH}) = (Aᵀα_t)[stress∪crash]` is above **0.25**, size is cut to **50%** immediately (this bypasses hysteresis).
5. If the top-2 filtered probabilities are within **0.15** of each other, the state is *uncertain* and size is 0.
6. If the model throws, the data is stale (last candle older than 1.5× the timeframe), or the feature contains NaN: **flat**.

Every switch is logged as JSONL with the timestamp, full probability vector, rule fired and reason.

### 1.6 Playbooks
`playbooks/<STATE>.md` holds human-readable reasoning plus a **YAML front-matter block that the code actually reads**:
```yaml
state: CALM_UP
style: trend_following
entry: {signal: "trend > 0.5"}
exit:  {signal: "trend < 0"}
stop_atr: 2.0
take_profit_atr: null
max_size_frac: 1.0        # fraction of the risk-limit max, so it cannot exceed it
invalidation: "close < 50-bar low"
```
Signals come from a **fixed whitelist grammar** (feature, comparator, number). Opus cannot inject arbitrary code. The defaults are CALM_UP trend-following, CHOP mean reversion, STRESS at 0.25× size or stand aside, and CRASH flat (hard-coded, so a playbook cannot override it).

### 1.7 Sizing
`size = min(limits.max_position, quarter_kelly × p_active × (1 − H(α)/log K))`
- Kelly inputs (μ, σ²) come from the active state's training-window statistics. They are shrunk 50% toward zero because HMM state means are noisy.
- Size is 0 in CRASH and in uncertain states.
- **Calibration**: per-state Brier score plus a reliability curve (10 bins) computed on out-of-sample filtered probabilities against realized next-state labels. Labels come from a later refit's *smoothed* path, which is only allowed in evaluation. If calibration is worse than climatology, sizing falls back to a flat 0.25× multiplier.

### 1.8 Refit and drift
- Walk-forward refits every **30** days on an expanding window. New states are matched to old ones with the Hungarian algorithm on standardized (μ, σ), so labels stay stable.
- Drift alarm: any |Δ A_ij| > **0.15**, any state-mean shift > **1σ**, or live log-likelihood per bar < the 5th percentile of the training distribution for 5 bars. When the alarm fires, **new entries are frozen**, existing exits still run, and an alert goes out.
- Opus can *propose* config changes as a diff. The harness re-runs the full backtest gates before anything is merged, and a human approves.

### 1.9 Backtest and acceptance gates
- Walk-forward with refits, costs of **1 bp commission + 2 bp slippage** per side (configurable), next-bar-open fills, and no partial-bar fills.
- Data spans ≥ 2 years out of sample covering several regimes, for example 2020 crash, 2022 bear and 2023–24 bull for SPY.
- Reports cover each state and the full system against **buy-and-hold** and the **best single static strategy** (the best fixed playbook applied in every state, chosen on in-sample data).
- **Gates (all OOS, after costs):** Sharpe > 1.5, max DD < 15%, hit rate > 55%, t-stat > 2.0, beats both baselines.
- **Extra guard against overfitting:** the final 6 months are a **locked holdout** that is evaluated once per candidate config. The Deflated Sharpe Ratio is reported with the number of configs tried.
- The winner is written to `strategy.md` along with the config hash.

> Honest expectation: these gates are strict for a single-asset regime system. A likely outcome is **"no config passes"**. In that case the system stays in paper trading and says so. It does not loosen the gates.

### 1.10 Risk rules (code, checked before every order)
| Limit | Proposed default |
|---|---|
| Max position (notional) | 100% of equity, 1× gross |
| Leverage cap per state | CALM_UP 1.0×, CHOP 0.5×, STRESS 0.25×, CRASH 0× |
| Daily loss limit | −2% of start-of-day equity → flat and halted until next session |
| Max drawdown | −10% from peak → **kill switch**: flatten, halt and require a manual re-arm |
| Manual approval | Any single order above **$[X]** notional (to be set by you) |
| Mode | **Paper only.** Live trading requires a config flag, the §1.12 checklist passing, and you typing a confirmation. |

The kill switch is tested by injecting a synthetic drawdown and asserting that the system flattens and that no further orders are sent.

### 1.11 Nightly Opus loop
1. Reads the day's fills, switch log and wrong-state calls (where the filtered top state disagreed with the next-day smoothed state).
2. Writes a root-cause note and **exactly one** new rule per loss to `journal/YYYY-MM-DD.md`.
3. Can propose small edits to features, playbooks and `strategy.md` as a patch.
4. The harness re-runs the backtest gates, and a patch ships **only if the gates still pass**. A human merges it. Opus never grades its own output; the gates do.

### 1.12 Go-live checklist (`final_check`)
This is generated automatically and must be all green:
- Paper results match the backtest (tracking error bound, same decisions on replay).
- The no-lookahead test passes, and the filtered-only lint passes.
- The kill switch fired in testing.
- No hard limit is read from model output (static check).
- State labels stayed stable across the last 3 refits.
- The report ends with **"WHAT COULD BLOW UP THIS ACCOUNT?"**, and live trading is refused until every item is resolved.

---

## 2. Architecture

```
            ┌───────────────────────── Layer 1: Opus 5.5 (nightly, offline) ─────────────────────────┐
            │ research/  → feature proposals, playbook YAML, journal, config diffs (never orders)    │
            └───────────────────────────────┬────────────────────────────────────────────────────────┘
                                            │ patches → harness re-runs backtest gates → human merge
┌──────────── Layer 2: HMM (every candle) ──▼──────────┐   ┌──────── Layer 3: deterministic code ───────┐
│ data/ → features/ → hmm/filter.py (forward α_t)      │──▶│ decide/switching.py (hysteresis, cooldown) │
│                     hmm/fit.py (offline, seeded)     │   │ decide/sizing.py (¼ Kelly × conf × entropy)│
│                     hmm/labels.py (Hungarian match)  │   │ risk/limits.py  ◀── config/limits.yaml     │
└──────────────────────────────────────────────────────┘   │ exec/broker.py (Alpaca paper) only via risk│
                                                           └───────────────┬────────────────────────────┘
                                         logs/*.jsonl ◀────────────────────┤
                                         dashboard/ (Streamlit, read-only) ┘ alerts/ (Telegram)
```

```
hmm-regime-trader/
  pyproject.toml   .env.example   .gitignore
  config/{settings.yaml, limits.yaml}
  src/regime/
    data/        alpaca_client.py, store.py (parquet cache)
    features/    pipeline.py
    hmm/         fit.py, select.py, filter.py, labels.py, drift.py
    decide/      switching.py, sizing.py, playbook.py (YAML + whitelist grammar)
    risk/        limits.py, killswitch.py
    exec/        broker.py, paper.py
    backtest/    walkforward.py, costs.py, metrics.py, baselines.py, calibration.py
    research/    opus_nightly.py (Claude API, structured output, no broker import)
    alerts/      telegram.py
    live/        runner.py (candle loop, systemd/supervisor managed)
  dashboard/app.py
  playbooks/  strategy.md  journal/
  tests/      (one failing test per module first)
```

Two boundary tests: `research/` must never import `exec/` or `risk/`, and `exec/broker.py` must only be callable through `risk.check`.

---

## 3. Plan (test-first; each step = failing test → code → review → commit)

| Step | Deliverable | Key failing test written first |
|---|---|---|
| 0 | Scaffold, `.env.example`, settings, log redaction | secret never appears in log output |
| 1 | Data loader + parquet cache (Alpaca bars) | bars are monotonic, no duplicates, staleness detected |
| 2 | Feature pipeline | **lookahead mutation test**; expanding z-score only |
| 3 | Forward filter | matches the hand-computed α on a 2-state toy model; no smoothed API used |
| 4 | Fit + K selection + labels | seed determinism; smaller-K tie-break; label ordering |
| 5 | Switching rules | table-driven tests for each of rules 1–6 |
| 6 | Sizing + calibration | CRASH → 0; uncertain → 0; entropy monotonic; Brier on known data |
| 7 | Risk limits + kill switch | order over the limit is rejected; DD breach flattens and halts |
| 8 | Walk-forward backtest + baselines + metrics + holdout | reproduces a known synthetic regime series |
| 9 | Refit label matching + drift freeze | permuted states map back; drift freezes entries |
| 10 | Paper broker + live runner | dry-run loop end to end against recorded candles |
| 11 | Dashboard + Telegram alerts | renders from fixture logs |
| 12 | Opus nightly loop (structured, sandboxed) | output schema validation; no exec import |
| 13 | `final_check` report | blocks live mode while any item is red |
| 14 | Deploy guide (systemd on a VPS or Mac mini) | — |

---

## 4. Open questions (please answer before Step 0)

1. **Venue / asset / timeframe.** Proposed default: **Alpaca paper, SPY, daily bars** (Alpaca history starts around 2016, which covers the 2020 crash and the 2022 bear). Hourly is the alternative. 1-minute bars are **not** recommended: HMM regimes are mostly noise at that scale, and costs dominate.
2. **Trend feature.** Is the slope ÷ vol proposal OK, or do you prefer something like a 20/100 MA spread?
3. **Manual approval threshold** ($ notional), **cooldown N**, and **drift tolerance**. Are the defaults above acceptable?
4. **Deploy target.** Vercel can't host a 24/7 candle loop (it is serverless with time-limited functions). The recommendation is a small **VPS with systemd** (`Restart=always`) or a Mac mini with `launchd`.
5. **Repo.** This repo currently holds the One Minute Channel video pipeline. Should the trader live in `hmm-regime-trader/` here, or in a new repo (recommended)?
6. **AgenKit.** I haven't installed or verified the tool at agenkit.xyz. Please confirm it is a tool you trust and how it installs (package name / repo). Until then, the same six-phase gated flow is run manually through this document.
7. **Keys.** Please **don't paste keys into chat**. Copy `.env.example` to `.env` on the machine that runs the bot and fill it in there. Use paper keys first. Alpaca API keys can't withdraw funds through the trading API. If you later use a crypto exchange, create a trade-only key with an IP allow-list and withdrawals disabled.
