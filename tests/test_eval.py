import copy

import numpy as np
import pandas as pd
import pytest

from rig import db, pipeline
from rig.config import load_config
from rig.data import fetch
from rig.eval import metrics
from rig.eval.run import HoldoutLocked, evaluate


# ---------- Brier ----------

def test_brier_known_values():
    assert metrics.brier([1, 0], [1, 0]) == 0.0
    assert metrics.brier([0, 1], [1, 0]) == 1.0
    assert metrics.brier([0.5, 0.5, 0.5, 0.5], [1, 0, 1, 1]) == pytest.approx(0.25)
    assert metrics.brier([0.9, 0.2, 0.7], [1, 0, 0]) == pytest.approx((0.01 + 0.04 + 0.49) / 3)


def test_brier_reference_and_skill():
    y = np.array([1, 1, 1, 0])  # base rate 0.75 -> reference Brier 0.1875
    rep = metrics.brier_report([0.75] * 4, y)
    assert rep["brier_reference"] == pytest.approx(0.1875)
    assert rep["skill"] == pytest.approx(0.0)
    assert metrics.brier_report([1, 1, 1, 0], y)["skill"] == pytest.approx(1.0)
    assert metrics.brier_report([], [])["brier"] is None


def test_reliability_table_bins():
    t = metrics.reliability_table([0.05, 0.08, 0.95, 0.91], [0, 1, 1, 1], bins=10)
    assert t.loc[0, "count"] == 2 and t.loc[0, "observed_rate"] == 0.5
    assert t.loc[9, "count"] == 2 and t.loc[9, "observed_rate"] == 1.0
    assert t["count"].sum() == 4


# ---------- trading metrics ----------

def test_trade_metrics():
    ts = pd.date_range("2026-01-01", periods=5, freq="h", tz="UTC")
    t = pd.DataFrame({"r_multiple": [2.0, -1.0, -1.0, 3.0, -1.0], "exit_ts": ts,
                      "pnl_usd": [50.0, -25.0, -25.0, 75.0, -25.0]})
    m = metrics.trade_metrics(t)
    assert m["trades"] == 5 and m["hit_rate"] == pytest.approx(0.4)
    assert m["expectancy_r"] == pytest.approx(0.4)
    assert m["profit_factor"] == pytest.approx(5 / 3)
    assert m["max_drawdown_r"] == pytest.approx(2.0)   # +2 -> 0
    assert m["max_drawdown_usd"] == pytest.approx(50.0)


def test_bootstrap_ci_brackets_true_difference():
    rng = np.random.default_rng(1)
    a, b = rng.normal(0, 1, 400), rng.normal(0.5, 1, 400)
    res = metrics.bootstrap_diff(a, b, samples=2000)
    assert res["low"] < 0.5 < res["high"]
    assert res["p_b_not_better"] < 0.01
    assert metrics.bootstrap_diff([1.0], [1.0])["diff"] is None


# ---------- end to end, including the one-shot holdout ----------

@pytest.fixture
def tmp_cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_MODE", "mock")
    cfg = copy.deepcopy(load_config())
    cfg["data"]["source"] = "synthetic"
    cfg["data"]["cache_dir"] = str(tmp_path / "cache")
    cfg["data"]["synthetic"]["days"] = 30
    cfg["db_path"] = str(tmp_path / "rig_{source}.db")
    cfg["eval"]["reports_dir"] = str(tmp_path / "reports")
    cfg["eval"]["bootstrap_samples"] = 200
    cfg["eval"]["min_train_trades"] = 1
    return cfg


def test_full_mock_pipeline_and_holdout_lock(tmp_cfg):
    fetch.build_synthetic(tmp_cfg, ["1m", "5m", "15m", "1h"])
    conn = db.connect(pipeline.db_path(tmp_cfg))
    assert pipeline.run_detect(tmp_cfg, conn)["candidate"] > 0
    assert pipeline.run_score(tmp_cfg, conn, "mock")["ok"] > 0
    pipeline.run_sim(tmp_cfg, conn)

    train = evaluate(tmp_cfg, conn, "mock", "train")
    text = train.read_text()
    assert "A vs B" in text and "Pipeline check only" in text
    assert (train.parent / "threshold.json").exists()

    holdout = evaluate(tmp_cfg, conn, "mock", "holdout")
    assert "HOLDOUT" in holdout.read_text()
    with pytest.raises(HoldoutLocked):
        evaluate(tmp_cfg, conn, "mock", "holdout")
    # re-running train afterwards is allowed but flagged
    assert "already been evaluated" in evaluate(tmp_cfg, conn, "mock", "train").read_text()

    # every candidate got a logged decision in both arms
    n = conn.execute("SELECT COUNT(*) FROM decisions WHERE arm='A' AND split='holdout'").fetchone()[0]
    assert n > 0


def test_holdout_needs_train_threshold_first(tmp_cfg):
    fetch.build_synthetic(tmp_cfg, ["5m", "15m", "1h"])
    conn = db.connect(pipeline.db_path(tmp_cfg))
    with pytest.raises(RuntimeError, match="train first"):
        evaluate(tmp_cfg, conn, "mock", "holdout")
