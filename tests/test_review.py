import hashlib
import json
from types import SimpleNamespace

import pytest

from rig.config import ROOT, load_config
from rig.review.weekly import SYSTEM_PROMPT, run_review


def _write_eval(d):
    d.mkdir(parents=True, exist_ok=True)
    (d / "summary_train.json").write_text(json.dumps({"split": "train", "arm_a": {"trades": 10}}))
    (d / "trades_train.csv").write_text("id,outcome\nBTC-1,target\n")


class FakeStream:
    def __init__(self, message):
        self.message = message

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get_final_message(self):
        return self.message


class FakeClient:
    def __init__(self, message):
        self.calls = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))
        self._message = message

    def _stream(self, **kwargs):
        self.calls.append(kwargs)
        return FakeStream(self._message)


def _msg(text, stop="end_turn"):
    return SimpleNamespace(model="claude-opus-5-5", stop_reason=stop, stop_details=None,
                           content=[SimpleNamespace(type="thinking", thinking=""),
                                    SimpleNamespace(type="text", text=text)])


def _repo_fingerprint():
    files = [ROOT / "config.yaml", ROOT / "data" / "news_events.csv", *sorted((ROOT / "rig").rglob("*.py"))]
    return {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}


def test_review_writes_only_a_markdown_file(tmp_path):
    d = tmp_path / "synthetic_mock"
    _write_eval(d)
    before_files = set(d.iterdir())
    before_repo = _repo_fingerprint()
    client = FakeClient(_msg("## Summary\nLooks like noise."))

    out = run_review(load_config(), d, client=client)

    assert set(d.iterdir()) - before_files == {out}
    assert out.suffix == ".md" and "Looks like noise." in out.read_text()
    assert "Suggestions only" in out.read_text()
    assert _repo_fingerprint() == before_repo  # no code/config/news changes

    call = client.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["output_config"] == {"effort": "high"}
    assert call["fallbacks"] == "default"
    assert "thinking" not in call  # adaptive by default; can't be disabled on Opus 5.5
    assert call["system"] == SYSTEM_PROMPT
    assert "BTC-1,target" in call["messages"][0]["content"]


def test_refusal_is_reported_not_crashed(tmp_path):
    d = tmp_path / "r"
    _write_eval(d)
    out = run_review(load_config(), d, client=FakeClient(_msg("", stop="refusal")))
    assert "declined" in out.read_text()


def test_dry_run_needs_no_key_and_shows_the_prompt(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    d = tmp_path / "r"
    _write_eval(d)
    out = run_review(load_config(), d, dry_run=True)
    assert "DRY_RUN" in out.name and "BTC-1,target" in out.read_text()


def test_missing_key_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    d = tmp_path / "r"
    _write_eval(d)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        run_review(load_config(), d)


def test_system_prompt_forbids_live_trading_and_holdout_tuning():
    assert "Never suggest live trading" in SYSTEM_PROMPT
    assert "Nothing is tuned on the holdout" in SYSTEM_PROMPT
