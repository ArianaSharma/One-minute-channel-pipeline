"""Trading metrics, Brier score, reliability tables, and a bootstrap CI."""
from __future__ import annotations

import numpy as np
import pandas as pd


def trade_metrics(trades: pd.DataFrame) -> dict:
    """trades: taken, resolved trades with r_multiple, pnl_usd, exit_ts."""
    n = len(trades)
    if n == 0:
        return {"trades": 0, "hit_rate": None, "expectancy_r": None, "total_r": 0.0,
                "pnl_usd": 0.0, "profit_factor": None, "max_drawdown_r": 0.0,
                "max_drawdown_usd": 0.0}
    t = trades.sort_values("exit_ts")
    r = t["r_multiple"].to_numpy()
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    return {
        "trades": n,
        "hit_rate": float((r > 0).mean()),
        "expectancy_r": float(r.mean()),
        "total_r": float(r.sum()),
        "pnl_usd": float(t["pnl_usd"].sum()),
        "profit_factor": float(wins / losses) if losses > 0 else None,
        "max_drawdown_r": max_drawdown(r),
        "max_drawdown_usd": max_drawdown(t["pnl_usd"].to_numpy()),
    }


def max_drawdown(increments) -> float:
    """Largest peak-to-trough fall of the cumulative sum (as a positive number)."""
    equity = np.concatenate([[0.0], np.cumsum(increments)])
    return float((np.maximum.accumulate(equity) - equity).max())


def brier(p, y) -> float:
    p, y = np.asarray(p, float), np.asarray(y, float)
    return float(np.mean((p - y) ** 2))


def brier_report(p, y) -> dict:
    """Brier score, the base-rate reference (always predicting the mean), and skill."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    if len(y) == 0:
        return {"n": 0, "brier": None, "base_rate": None, "brier_reference": None, "skill": None}
    bs = brier(p, y)
    ref = brier(np.full_like(y, y.mean()), y)
    return {"n": int(len(y)), "brier": bs, "base_rate": float(y.mean()), "brier_reference": ref,
            "skill": (1 - bs / ref) if ref > 0 else None}


def reliability_table(p, y, bins: int = 10) -> pd.DataFrame:
    p, y = np.asarray(p, float), np.asarray(y, float)
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    rows = []
    for b in range(bins):
        m = idx == b
        rows.append({"bin_low": edges[b], "bin_high": edges[b + 1], "count": int(m.sum()),
                     "mean_predicted": float(p[m].mean()) if m.any() else None,
                     "observed_rate": float(y[m].mean()) if m.any() else None})
    return pd.DataFrame(rows)


def bootstrap_diff(a, b, samples: int = 5000, seed: int = 0, ci: float = 0.95) -> dict:
    """CI for mean(b) - mean(a), resampling each arm's trades independently.

    B's trades are a subset of A's, so the arms are not independent; treating them as
    independent makes this interval wider (more conservative), not narrower.
    """
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return {"diff": None, "low": None, "high": None, "p_b_not_better": None}
    rng = np.random.default_rng(seed)
    ma = rng.choice(a, (samples, len(a))).mean(axis=1)
    mb = rng.choice(b, (samples, len(b))).mean(axis=1)
    d = mb - ma
    lo, hi = np.quantile(d, [(1 - ci) / 2, 1 - (1 - ci) / 2])
    return {"diff": float(b.mean() - a.mean()), "low": float(lo), "high": float(hi),
            "p_b_not_better": float((d <= 0).mean())}
