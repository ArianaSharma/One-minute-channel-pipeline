"""Shared result type, parsing, and client selection (JEV_MODE=mock|live)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Protocol

from rig.config import env


@dataclass
class JevResult:
    mode: str
    model: str | None
    answers: dict | None            # documented answer objects keyed by question name
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    request_id: str | None = None
    error: str | None = None
    parsed: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.error is None and self.answers is not None


class JevClient(Protocol):
    mode: str

    def ask(self, state: dict, questions: dict) -> JevResult: ...


def parse(answers: dict) -> dict:
    """Flatten the battery's answers into the fields the filter and eval use."""
    reg = answers["regime"]
    qual = answers["setup_quality"]
    return {
        "regime": reg["choice"],
        "regime_confidence": float(reg["confidence"]),
        "regime_probabilities": reg["probabilities"],
        "setup_quality": float(qual["score"]),
        "setup_quality_confidence": float(qual["confidence"]),
        "setup_quality_probabilities": qual["probabilities"],
        "direction_agrees": float(answers["direction_agrees"]["noul"]),
        "sweep_is_genuine": float(answers["sweep_is_genuine"]["noul"]),
        "target_before_stop": float(answers["target_before_stop"]["noul"]),
        # Nouls carry no confidence (docs.typesafe.ai/confidence), so the gate uses the
        # weaker of the two answers that do.
        "confidence": min(float(reg["confidence"]), float(qual["confidence"])),
    }


def token_cost(input_tokens: int | None, price_per_mtok: float) -> float | None:
    # Jev bills input tokens only; output tokens are free (docs.typesafe.ai/models).
    return None if input_tokens is None else input_tokens * price_per_mtok / 1_000_000


def jev_mode() -> str:
    mode = (env("JEV_MODE") or "mock").lower()
    if mode not in ("mock", "live"):
        raise ValueError("JEV_MODE must be 'mock' or 'live'")
    return mode


def get_client(cfg: dict, mode: str | None = None) -> JevClient:
    mode = mode or jev_mode()
    if mode == "live":
        from rig.jev_client.live import LiveJevClient
        return LiveJevClient(cfg)
    from rig.jev_client.mock import MockJevClient
    return MockJevClient(cfg)


def dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str)
