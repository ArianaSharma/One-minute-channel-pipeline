"""Arm B policy: take a signal only if Jev's answers pass every gate.

Order of checks:
  no answer                      -> skip ("no_jev_answer")
  confidence < min_confidence    -> escalate (logged, NOT traded)
  regime == crisis               -> skip
  setup_quality < min            -> skip
  target_before_stop < threshold -> skip
  otherwise                      -> take
confidence = min(regime confidence, setup_quality confidence); Nouls carry none.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FilterParams:
    min_confidence: float = 0.60
    min_setup_quality: float = 2.0
    target_before_stop_threshold: float = 0.55

    @classmethod
    def from_config(cls, cfg: dict, threshold: float | None = None) -> "FilterParams":
        f = cfg["filter"]
        return cls(f["min_confidence"], f["min_setup_quality"],
                   threshold if threshold is not None else f["target_before_stop_threshold"])


def decide(answers: dict | None, p: FilterParams) -> tuple[str, str | None]:
    """Returns (action, reason) with action in {take, skip, escalate}."""
    if not answers:
        return "skip", "no_jev_answer"
    if answers["confidence"] < p.min_confidence:
        return "escalate", f"confidence {answers['confidence']:.2f} < {p.min_confidence:.2f}"
    if answers["regime"] == "crisis":
        return "skip", "regime_crisis"
    if answers["setup_quality"] < p.min_setup_quality:
        return "skip", f"setup_quality {answers['setup_quality']:.2f} < {p.min_setup_quality}"
    if answers["target_before_stop"] < p.target_before_stop_threshold:
        return "skip", (f"target_before_stop {answers['target_before_stop']:.2f} < "
                        f"{p.target_before_stop_threshold:.2f}")
    return "take", None
