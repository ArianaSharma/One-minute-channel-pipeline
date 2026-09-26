import json

import httpx2
import pytest

from rig.config import load_config
from rig.jev_client import BATTERY, get_client
from rig.jev_client.base import parse, token_cost
from rig.jev_client.mock import MockJevClient

STATE = {"instrument": "BTC", "summary": {"trade": "short"}, "setup": {"entry": 100.0}}

DOC_RESPONSE = {  # shape from docs.typesafe.ai/api "Response body"
    "model": "jev-1.13.0",
    "usage": {"input_tokens": 1200, "output_tokens": 40},
    "answers": {
        "regime": {"type": "choice", "choice": "ranging", "confidence": 0.62,
                   "probabilities": {"trending_up": 0.1, "trending_down": 0.1, "ranging": 0.7,
                                     "volatile_chop": 0.1, "crisis": 0.0}},
        "direction_agrees": {"type": "noul", "noul": 0.55},
        "setup_quality": {"type": "score", "score": 2.1, "confidence": 0.7,
                          "legend": {"0": "a", "1": "b", "2": "c", "3": "d"},
                          "probabilities": {"0": 0.05, "1": 0.1, "2": 0.55, "3": 0.3}},
        "sweep_is_genuine": {"type": "noul", "noul": 0.6},
        "target_before_stop": {"type": "noul", "noul": 0.48},
    },
}


def test_battery_matches_documented_primitive_formats():
    assert BATTERY["regime"]["type"] == "choice"
    assert list(BATTERY["regime"]["criteria"]) == [
        "trending_up", "trending_down", "ranging", "volatile_chop", "crisis"]
    assert BATTERY["setup_quality"]["type"] == "score"
    assert len(BATTERY["setup_quality"]["criteria"]) == 4  # levels 0..3; API allows 2..10
    for q in ("direction_agrees", "sweep_is_genuine", "target_before_stop"):
        assert BATTERY[q]["type"] == "noul"
        assert set(BATTERY[q]["criteria"]) == {"true", "false"}


def test_parse_uses_min_of_choice_and_score_confidence():
    p = parse(DOC_RESPONSE["answers"])
    assert p["regime"] == "ranging"
    assert p["setup_quality"] == 2.1
    assert p["confidence"] == pytest.approx(0.62)
    assert p["target_before_stop"] == 0.48


def test_token_cost_is_input_tokens_only():
    assert token_cost(1_000_000, 0.042) == pytest.approx(0.042)


def test_mock_is_deterministic_well_formed_and_blind_to_anything_but_state():
    c = MockJevClient(load_config())
    a, b = c.ask(STATE, BATTERY), c.ask(STATE, BATTERY)
    assert a.ok and a.answers == b.answers
    p = a.parsed
    assert p["regime"] in BATTERY["regime"]["criteria"]
    assert 0 <= p["setup_quality"] <= 3
    assert abs(sum(a.answers["regime"]["probabilities"].values()) - 1) < 1e-3
    for q in ("direction_agrees", "sweep_is_genuine", "target_before_stop"):
        assert 0 <= p[q] <= 1
    other = c.ask({**STATE, "instrument": "ETH"}, BATTERY)
    assert other.answers != a.answers


def test_mode_selection(monkeypatch):
    monkeypatch.setenv("JEV_MODE", "mock")
    assert get_client(load_config()).mode == "mock"
    monkeypatch.setenv("JEV_MODE", "live")
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="TYPESAFE_API_KEY"):
        get_client(load_config())


def _live(monkeypatch, handler):
    from rig.jev_client.live import LiveJevClient
    monkeypatch.setenv("TYPESAFE_API_KEY", "ts_test_SECRET123")
    return LiveJevClient(load_config(), transport=httpx2.MockTransport(handler))


def test_live_client_sends_documented_request_and_logs_usage(monkeypatch):
    seen = {}

    def handler(req):
        seen["url"], seen["auth"] = str(req.url), req.headers.get("authorization")
        seen["body"] = json.loads(req.content)
        return httpx2.Response(200, json=DOC_RESPONSE, headers={"x-typesafe-request-id": "req_1"})

    r = _live(monkeypatch, handler).ask(STATE, BATTERY)
    assert seen["url"] == "https://api.typesafe.ai/v1/systemone"
    assert seen["auth"] == "Bearer ts_test_SECRET123"
    assert seen["body"]["model"] == "jev-1.13.0"
    assert seen["body"]["state"] == STATE
    assert set(seen["body"]["questions"]) == set(BATTERY)
    assert r.ok and r.request_id == "req_1" and r.input_tokens == 1200
    assert r.cost_usd == pytest.approx(1200 * 0.042 / 1e6)
    assert r.parsed["regime"] == "ranging"


def test_live_client_error_never_contains_key(monkeypatch):
    r = _live(monkeypatch, lambda req: httpx2.Response(401, json={"error": "invalid key"})
              ).ask(STATE, BATTERY)
    assert not r.ok
    assert "401" in r.error and "SECRET123" not in r.error
