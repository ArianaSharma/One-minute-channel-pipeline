"""Load config.yaml and enforce the hard-rule limits on it."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config.yaml"

ALLOWED_RISK_USD = (25, 50)
MIN_REWARD_RISK = 1.5


class ConfigError(ValueError):
    pass


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Read the YAML config, load .env into the environment, and validate."""
    load_dotenv(ROOT / ".env")
    path = Path(path) if path else DEFAULT_CONFIG
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}
    validate(cfg)
    return cfg


def validate(cfg: dict[str, Any]) -> None:
    risk = cfg.get("risk", {})
    if risk.get("risk_per_trade_usd") not in ALLOWED_RISK_USD:
        raise ConfigError(f"risk.risk_per_trade_usd must be one of {ALLOWED_RISK_USD}")
    if float(risk.get("min_reward_risk", 0)) < MIN_REWARD_RISK:
        raise ConfigError(f"risk.min_reward_risk must be >= {MIN_REWARD_RISK}")
    if float(risk.get("news_block_minutes", 0)) < 2:
        raise ConfigError("risk.news_block_minutes must be >= 2")
    frac = float(cfg.get("eval", {}).get("holdout_fraction", 0))
    if not 0 < frac < 1:
        raise ConfigError("eval.holdout_fraction must be between 0 and 1")


def resolve(path: str | Path) -> Path:
    """Paths in config are relative to the repo root."""
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def env(name: str) -> str | None:
    """Read a secret from the environment. Never log the returned value."""
    value = os.environ.get(name, "").strip()
    return value or None
