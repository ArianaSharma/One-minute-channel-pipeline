"""Guards for the CLAUDE.md hard rules that can be checked statically."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = sorted((ROOT / "rig").rglob("*.py"))

# Hyperliquid's trading endpoint is /exchange; the rig may only use /info.
FORBIDDEN = [
    r"api\.hyperliquid\.xyz/exchange",
    r"\bplace_?order\b", r"\bcancel_?order\b", r"\bmodify_?order\b",
    r"\bprivate_?key\b", r"\bsecret_?key\b", r"eth_account",
]


def test_no_order_placement_or_private_keys_in_code():
    for path in SOURCES:
        text = path.read_text()
        for pattern in FORBIDDEN:
            assert not re.search(pattern, text, re.I), f"{path.name} matches {pattern!r}"


def test_no_hardcoded_api_keys():
    key_like = re.compile(r"(sk-ant-[A-Za-z0-9_-]{10,}|ts_(live|test)_[A-Za-z0-9]{8,})")
    for path in [*SOURCES, ROOT / "config.yaml", ROOT / ".env.example"]:
        assert not key_like.search(path.read_text()), path.name


def test_env_file_is_gitignored():
    ignore = (ROOT / ".gitignore").read_text().splitlines()
    assert ".env" in ignore
