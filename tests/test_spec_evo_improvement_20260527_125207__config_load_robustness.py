"""
Tests for config-load-robustness spec.
Change: evo-improvement-20260527-125207
Spec: config-load-robustness.md
"""
import pytest
import yaml

from zsiga.config import load_config


def _write_yaml(tmp_path, content: str):
    """Write content to a YAML file in tmp_path and return its path."""
    p = tmp_path / "zsiga.yaml"
    p.write_text(content)
    return str(p)


# ---------------------------------------------------------------------------
# Scenario: Empty file raises ValueError
# ---------------------------------------------------------------------------
def test_empty_file_raises_value_error(tmp_path):
    """Empty YAML file SHALL raise ValueError mentioning 'empty'."""
    path = _write_yaml(tmp_path, "")
    with pytest.raises(ValueError, match="empty"):
        load_config(path=path)


# ---------------------------------------------------------------------------
# Scenario: Whitespace-only file raises ValueError
# ---------------------------------------------------------------------------
def test_whitespace_only_file_raises_value_error(tmp_path):
    """Whitespace-only YAML file SHALL raise ValueError mentioning 'empty'."""
    path = _write_yaml(tmp_path, "   \n\n  ")
    with pytest.raises(ValueError, match="empty"):
        load_config(path=path)


# ---------------------------------------------------------------------------
# Scenario: Malformed YAML raises ValueError not YAMLError
# ---------------------------------------------------------------------------
def test_malformed_yaml_raises_value_error(tmp_path):
    """Malformed YAML SHALL raise ValueError (not YAMLError)."""
    path = _write_yaml(tmp_path, "{unclosed bracket")
    with pytest.raises(ValueError, match="yaml|parse|malformed"):
        load_config(path=path)
    # Also confirm it is NOT yaml.YAMLError at the top level
    with pytest.raises(ValueError):
        try:
            load_config(path=path)
        except yaml.YAMLError:
            pytest.fail("Should have raised ValueError, not yaml.YAMLError")


# ---------------------------------------------------------------------------
# Scenario: Missing agent key raises ValueError mentioning agent
# ---------------------------------------------------------------------------
def test_missing_agent_key_raises_value_error(tmp_path):
    """YAML missing 'agent' key SHALL raise ValueError mentioning 'agent'."""
    data = {"targets": {"default": {"path": "/tmp"}}}
    path = _write_yaml(tmp_path, yaml.dump(data))
    with pytest.raises(ValueError, match="agent"):
        load_config(path=path)


# ---------------------------------------------------------------------------
# Scenario: Missing llm subkey under agent raises ValueError mentioning llm
# ---------------------------------------------------------------------------
def test_missing_llm_subkey_raises_value_error(tmp_path):
    """YAML missing 'agent.llm' key SHALL raise ValueError mentioning 'llm'."""
    data = {"agent": {"provider": "openai"}, "targets": {"default": {"path": "/tmp"}}}
    path = _write_yaml(tmp_path, yaml.dump(data))
    with pytest.raises(ValueError, match="llm"):
        load_config(path=path)
