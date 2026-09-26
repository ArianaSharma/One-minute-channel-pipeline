# Jev ICT/SMC research rig (Phase 1: research and paper only)

Tests whether TypeSafe AI's Jev model can improve rule-based ICT/SMC setups.
**No live trading. Ever.** See [CLAUDE.md](CLAUDE.md) for the hard rules.

> Status: Phases 0–1 (scaffolding + data) are built. Detect/score/sim/eval/review
> come in later phases; those commands currently print "not built yet".

## Setup

```bash
uv venv && uv pip install -e ".[dev]"      # or: python -m venv .venv && pip install -e ".[dev]"
cp .env.example .env                        # fill in keys only if you have them
```

## Data

```bash
python -m rig fetch                          # Hyperliquid BTC/ETH 1m/5m/15m/1h (+ Twelve Data if key set)
python -m rig fetch --source synthetic       # offline, seeded fake candles for mock runs
```

Candles are cached as parquet in `data/cache/<source>/`. Each run only asks for
bars newer than the cache, so history builds up over time.

**Hyperliquid only serves the most recent 5,000 candles per interval** (~3.5 days
of 1m, ~17 days of 5m, ~52 days of 15m). Run `rig fetch` at least every few days
(1m) / every two weeks (5m) to keep a gap-free history.

## Tests

```bash
python -m pytest
```
