"""The question battery asked for every candidate signal, in ONE system_one call.

Question dicts follow the documented wire format (docs.typesafe.ai/api):
  noul:   {"type": "noul",   "instructions": ..., "criteria": {"true": ..., "false": ...}}
  choice: {"type": "choice", "instructions": ..., "criteria": {option: description}}
  score:  {"type": "score",  "instructions": ..., "criteria": [level0, level1, ...]}
The SDK accepts these dicts directly. Instructions point at named fields of the state
(the snapshot) in backticks, and the judgement-relevant numbers are pre-bucketed in
`summary`, per TypeSafe's guidance to keep arithmetic in code.
"""
from __future__ import annotations

REGIMES = ["trending_up", "trending_down", "ranging", "volatile_chop", "crisis"]

SETUP_QUALITY_LEVELS = [
    "Poor: the sweep, structure shift, or entry zone is weak or unclear; a discretionary trader would pass.",
    "Weak: the pattern is present but at least one part is marginal or it fights the higher-timeframe context.",
    "Good: a clean sweep, a clear structure shift, and a sensible entry zone, with no major contradiction.",
    "Excellent: a textbook sweep of obvious liquidity, strong displacement, and an entry aligned with context.",
]

BATTERY: dict[str, dict] = {
    "regime": {
        "type": "choice",
        "instructions": "Using `summary`, `context_1h` and `recent_5m_bars`, which market regime is "
                        "this instrument in right now?",
        "criteria": {
            "trending_up": "Sustained upward movement on the 1h chart: higher highs and higher lows.",
            "trending_down": "Sustained downward movement on the 1h chart: lower highs and lower lows.",
            "ranging": "Price rotating between a clear high and low without directional progress.",
            "volatile_chop": "Large, fast swings in both directions with little follow-through.",
            "crisis": "Disorderly, extreme movement such as a crash, squeeze, or news shock, where "
                      "normal setups are unreliable.",
        },
    },
    "direction_agrees": {
        "type": "noul",
        "instructions": "Is `setup.direction` the right side of the market for the next few hours, "
                        "given `summary` and `context_1h`?",
        "criteria": {
            "true": "Price is more likely to move in the direction of `setup.direction`.",
            "false": "Price is more likely to move against `setup.direction`.",
        },
    },
    "setup_quality": {
        "type": "score",
        "instructions": "How good is this liquidity-sweep and structure-shift setup, as described in "
                        "`summary` and `setup`?",
        "criteria": SETUP_QUALITY_LEVELS,
    },
    "sweep_is_genuine": {
        "type": "noul",
        "instructions": "Was the move beyond the swept level (`setup.swept_level`) a genuine liquidity "
                        "grab that reverses, rather than the start of a move that continues through it?",
        "criteria": {
            "true": "A stop-run that reverses; price does not return beyond the sweep's extreme.",
            "false": "A breakout; price continues beyond the swept level.",
        },
    },
    "target_before_stop": {
        "type": "noul",
        "instructions": "Will price reach `setup.target` before it reaches `setup.stop`?",
        "criteria": {
            "true": "The target is hit first.",
            "false": "The stop is hit first.",
        },
    },
}

NOUL_QUESTIONS = [k for k, q in BATTERY.items() if q["type"] == "noul"]
