import copy

import pytest

from rig.config import ConfigError, load_config, validate


def test_repo_config_is_valid():
    cfg = load_config()
    assert cfg["risk"]["risk_per_trade_usd"] == 25
    assert cfg["risk"]["min_reward_risk"] >= 1.5


@pytest.mark.parametrize(
    "key,value",
    [("risk_per_trade_usd", 100), ("risk_per_trade_usd", 10),
     ("min_reward_risk", 1.2), ("news_block_minutes", 1)],
)
def test_hard_rule_limits_are_enforced(key, value):
    cfg = copy.deepcopy(load_config())
    cfg["risk"][key] = value
    with pytest.raises(ConfigError):
        validate(cfg)


def test_fifty_dollar_risk_is_allowed():
    cfg = copy.deepcopy(load_config())
    cfg["risk"]["risk_per_trade_usd"] = 50
    validate(cfg)
