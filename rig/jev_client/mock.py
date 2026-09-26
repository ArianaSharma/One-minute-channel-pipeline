"""Mock Jev: random but plausibly-shaped answers, deterministic per snapshot.

It only ever sees the snapshot (never outcomes), so in mock mode the Jev-filtered arm
should perform like a random subset of the rule-based arm, and Brier scores should sit
near chance. That makes mock runs a leakage check for the whole pipeline.
Answers use the documented response shape so the rest of the rig can't tell the difference.
"""
from __future__ import annotations

import hashlib
import json
import time

import numpy as np

from rig.jev_client.base import JevResult, parse, token_cost


def _confidence(probs: np.ndarray) -> float:
    # Same shape of statistic the docs describe: 1.0 when all mass is on one option,
    # 0.0 when spread evenly.
    n = len(probs)
    return float(np.clip((n * probs.max() - 1) / (n - 1), 0.0, 1.0))


class MockJevClient:
    mode = "mock"

    def __init__(self, cfg: dict):
        self.price = cfg["jev"]["price_per_mtok_input_usd"]

    def ask(self, state: dict, questions: dict) -> JevResult:
        start = time.perf_counter()
        blob = json.dumps(state, sort_keys=True)
        seed = int(hashlib.sha256(blob.encode()).hexdigest()[:16], 16)
        rng = np.random.default_rng(seed)
        answers = {}
        for name, q in questions.items():
            if q["type"] == "noul":
                answers[name] = {"type": "noul", "noul": round(float(rng.beta(2.0, 2.0)), 4)}
            elif q["type"] == "choice":
                opts = list(q["criteria"])
                probs = rng.dirichlet(np.full(len(opts), 0.6))
                answers[name] = {
                    "type": "choice",
                    "choice": opts[int(probs.argmax())],
                    "probabilities": {o: round(float(p), 4) for o, p in zip(opts, probs)},
                    "confidence": round(_confidence(probs), 4),
                }
            else:  # score
                levels = q["criteria"]
                probs = rng.dirichlet(np.full(len(levels), 0.8))
                answers[name] = {
                    "type": "score",
                    "score": round(float(np.dot(np.arange(len(levels)), probs)), 4),
                    "legend": {str(i): lvl for i, lvl in enumerate(levels)},
                    "probabilities": {str(i): round(float(p), 4) for i, p in enumerate(probs)},
                    "confidence": round(_confidence(probs), 4),
                }
        input_tokens = (len(blob) + len(json.dumps(questions))) // 4  # rough estimate
        result = JevResult(self.mode, "mock-jev", answers, (time.perf_counter() - start) * 1000,
                           input_tokens=input_tokens, output_tokens=0,
                           cost_usd=token_cost(input_tokens, self.price))
        result.parsed = parse(answers)
        return result

    def close(self) -> None:
        pass
