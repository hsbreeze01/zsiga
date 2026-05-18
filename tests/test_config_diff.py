"""Tests for config_diff module."""

from zsiga.config_diff import compare_configs


def test_identical_configs_empty_diff():
    """Identical configs produce empty diff."""
    cfg = {"model": {"name": "gpt-4"}, "budget": {"max_tokens": 8000}}
    result = compare_configs(cfg, cfg)
    assert result == {"changed": [], "details": {}}


def test_model_name_changed():
    """Model name change is detected."""
    old = {"model": {"name": "gpt-4"}}
    new = {"model": {"name": "gpt-4o"}}
    result = compare_configs(old, new)
    assert "model.name" in result["changed"]
    assert result["details"]["model.name"] == {"old": "gpt-4", "new": "gpt-4o"}


def test_budget_max_tokens_changed():
    """Budget max_tokens change is detected."""
    old = {"budget": {"max_tokens": 8000}}
    new = {"budget": {"max_tokens": 16000}}
    result = compare_configs(old, new)
    assert "budget.max_tokens" in result["changed"]
    assert result["details"]["budget.max_tokens"] == {"old": 8000, "new": 16000}


def test_transport_type_changed():
    """Transport type change is detected."""
    old = {"transport": {"type": "stdio"}}
    new = {"transport": {"type": "http"}}
    result = compare_configs(old, new)
    assert "transport.type" in result["changed"]
    assert result["details"]["transport.type"] == {"old": "stdio", "new": "http"}


def test_key_removed():
    """Key present in old but missing in new is reported with new=None."""
    old = {"model": {"name": "gpt-4", "temperature": 0.7}}
    new = {"model": {"name": "gpt-4"}}
    result = compare_configs(old, new)
    assert "model.temperature" in result["changed"]
    assert result["details"]["model.temperature"] == {"old": 0.7, "new": None}


def test_key_added():
    """Key present in new but missing in old is reported with old=None."""
    old = {"budget": {"max_tokens": 8000}}
    new = {"budget": {"max_tokens": 8000, "max_cost": 5.0}}
    result = compare_configs(old, new)
    assert "budget.max_cost" in result["changed"]
    assert result["details"]["budget.max_cost"] == {"old": None, "new": 5.0}


def test_unrelated_section_ignored():
    """Changes in non-watched sections are not reported."""
    old = {"logging": {"level": "INFO"}}
    new = {"logging": {"level": "DEBUG"}}
    result = compare_configs(old, new)
    assert result == {"changed": [], "details": {}}


def test_dot_notation_deep_nested():
    """Deeply nested keys are flattened with dot notation."""
    old = {"transport": {"http": {"port": 8080}}}
    new = {"transport": {"http": {"port": 9090}}}
    result = compare_configs(old, new)
    assert "transport.http.port" in result["changed"]
    assert result["details"]["transport.http.port"] == {"old": 8080, "new": 9090}


def test_changed_list_sorted_alphabetically():
    """Multiple changes are sorted alphabetically."""
    old = {"model": {"name": "gpt-4"}, "budget": {"max_tokens": 8000}}
    new = {"model": {"name": "gpt-4o"}, "budget": {"max_tokens": 16000}}
    result = compare_configs(old, new)
    assert result["changed"] == ["budget.max_tokens", "model.name"]


def test_missing_section_in_one_config():
    """Section missing entirely from one config reports all keys."""
    old = {"model": {"name": "gpt-4", "temperature": 0.7}}
    new = {}
    result = compare_configs(old, new)
    assert "model.name" in result["changed"]
    assert "model.temperature" in result["changed"]
    assert result["details"]["model.name"] == {"old": "gpt-4", "new": None}
    assert result["details"]["model.temperature"] == {"old": 0.7, "new": None}


def test_empty_input_dicts():
    """Empty dicts produce empty diff."""
    result = compare_configs({}, {})
    assert result == {"changed": [], "details": {}}
