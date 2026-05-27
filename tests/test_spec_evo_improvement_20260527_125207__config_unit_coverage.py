"""
Tests for config-unit-coverage spec.
Change: evo-improvement-20260527-125207
Spec: config-unit-coverage.md
"""
from pathlib import Path

import pytest

from zsiga.config import _find_config, _resolve_env_vars


# ===================================================================
# _resolve_env_vars scenarios
# ===================================================================

# ---------------------------------------------------------------------------
# Scenario: Resolves dollar-brace VAR to environment value
# ---------------------------------------------------------------------------
def test_resolves_env_var_to_value(monkeypatch):
    """_resolve_env_vars('${VAR}') SHALL return the env var value."""
    monkeypatch.setenv("ZSIGA_TEST_HOST", "example.com")
    assert _resolve_env_vars("${ZSIGA_TEST_HOST}") == "example.com"


# ---------------------------------------------------------------------------
# Scenario: Missing env var resolves to empty string
# ---------------------------------------------------------------------------
def test_missing_env_var_resolves_to_empty_string(monkeypatch):
    """_resolve_env_vars('${NONEXISTENT}') SHALL return ''."""
    monkeypatch.delenv("ZSIGA_NONEXISTENT_9999", raising=False)
    assert _resolve_env_vars("${ZSIGA_NONEXISTENT_9999}") == ""


# ---------------------------------------------------------------------------
# Scenario: Non-string values pass through unchanged
# ---------------------------------------------------------------------------
def test_non_string_passes_through():
    """_resolve_env_vars(42) SHALL return 42 unchanged."""
    assert _resolve_env_vars(42) == 42


# ---------------------------------------------------------------------------
# Scenario: Nested dict values are resolved recursively
# ---------------------------------------------------------------------------
def test_nested_dict_resolved_recursively(monkeypatch):
    """Nested dict with ${VAR} SHALL be resolved recursively."""
    monkeypatch.setenv("ZSIGA_TEST_HOST", "myhost")
    result = _resolve_env_vars(
        {"server": {"host": "${ZSIGA_TEST_HOST}", "port": 8080}}
    )
    assert result == {"server": {"host": "myhost", "port": 8080}}


# ---------------------------------------------------------------------------
# Scenario: List values are resolved recursively
# ---------------------------------------------------------------------------
def test_list_resolved_recursively(monkeypatch):
    """List with ${VAR} SHALL be resolved recursively."""
    monkeypatch.setenv("ZSIGA_TEST_ITEM", "resolved")
    result = _resolve_env_vars(["${ZSIGA_TEST_ITEM}", "static", 123])
    assert result == ["resolved", "static", 123]


# ---------------------------------------------------------------------------
# Scenario: Plain string without placeholder passes through unchanged
# ---------------------------------------------------------------------------
def test_plain_string_passes_through():
    """_resolve_env_vars('hello world') SHALL return 'hello world'."""
    assert _resolve_env_vars("hello world") == "hello world"


# ===================================================================
# _find_config scenarios
# ===================================================================

# ---------------------------------------------------------------------------
# Scenario: Finds config in current directory
# ---------------------------------------------------------------------------
def test_finds_config_in_current_directory(tmp_path, monkeypatch):
    """_find_config() SHALL return Path('zsiga.yaml') when it exists in cwd."""
    config_file = tmp_path / "zsiga.yaml"
    config_file.write_text("dummy")
    monkeypatch.chdir(tmp_path)
    # Ensure home dir does NOT interfere
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "nonexistent_home")
    result = _find_config()
    assert isinstance(result, Path)
    assert result.name == "zsiga.yaml"
    assert result.exists()


# ---------------------------------------------------------------------------
# Scenario: Raises FileNotFoundError when no config exists
# ---------------------------------------------------------------------------
def test_raises_file_not_found_when_no_config(tmp_path, monkeypatch):
    """_find_config() SHALL raise FileNotFoundError mentioning 'zsiga.yaml'."""
    # Point home to a non-existent dir so it can't find config there either
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "nonexistent_home")
    with pytest.raises(FileNotFoundError, match="zsiga.yaml"):
        _find_config()
