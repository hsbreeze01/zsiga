"""Tests for _find_config and _resolve_env_vars environment variable resolution.

Spec: config-env-resolution
Change: evo-improvement-20260530-045307
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from zsiga.config import _find_config, _resolve_env_vars


# ---------------------------------------------------------------------------
# _find_config scenarios
# ---------------------------------------------------------------------------


class TestFindConfigInCurrentDir:
    """Scenario: Find config in current directory."""

    def test_finds_in_current_dir(self, tmp_path, monkeypatch):
        config_file = tmp_path / "zsiga.yaml"
        config_file.write_text("dummy: true")
        monkeypatch.chdir(tmp_path)
        with patch.object(Path, "home", return_value=tmp_path / "nonexistent_home"):
            result = _find_config()
        assert result == Path("zsiga.yaml")
        assert result.exists()


class TestFindConfigInHomeDir:
    """Scenario: Find config in home directory fallback."""

    def test_falls_back_to_home(self, tmp_path, monkeypatch):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.chdir(empty_dir)
        home_dir = tmp_path / "home"
        zsiga_dir = home_dir / ".zsiga"
        zsiga_dir.mkdir(parents=True)
        (zsiga_dir / "zsiga.yaml").write_text("dummy: true")
        with patch.object(Path, "home", return_value=home_dir):
            result = _find_config()
        assert result == zsiga_dir / "zsiga.yaml"


class TestFindConfigRaisesFileNotFound:
    """Scenario: Raise FileNotFoundError when no config exists."""

    def test_raises_when_no_config(self, tmp_path, monkeypatch):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        monkeypatch.chdir(empty_dir)
        with patch.object(Path, "home", return_value=tmp_path / "no_home"):
            with pytest.raises(FileNotFoundError, match="zsiga.yaml not found"):
                _find_config()


# ---------------------------------------------------------------------------
# _resolve_env_vars scenarios
# ---------------------------------------------------------------------------


class TestResolveExistingEnvVar:
    """Scenario: Resolve existing environment variable."""

    def test_resolves_existing_var(self, monkeypatch):
        monkeypatch.setenv("TEST_RESOLVE_VAR", "resolved_value")
        assert _resolve_env_vars("${TEST_RESOLVE_VAR}") == "resolved_value"


class TestResolveMissingEnvVar:
    """Scenario: Missing environment variable returns empty string."""

    def test_missing_var_returns_empty(self, monkeypatch):
        monkeypatch.delenv("NONEXISTENT_ZSIGA_VAR_XYZ", raising=False)
        assert _resolve_env_vars("${NONEXISTENT_ZSIGA_VAR_XYZ}") == ""


class TestResolveDictRecursively:
    """Scenario: Resolve dict values recursively."""

    def test_dict_resolution(self, monkeypatch):
        monkeypatch.setenv("DICT_TEST_VAR", "from_env")
        result = _resolve_env_vars({"key": "${DICT_TEST_VAR}", "other": "plain"})
        assert result == {"key": "from_env", "other": "plain"}


class TestResolveListRecursively:
    """Scenario: Resolve list values recursively."""

    def test_list_resolution(self, monkeypatch):
        monkeypatch.setenv("LIST_TEST_VAR", "list_val")
        result = _resolve_env_vars(["${LIST_TEST_VAR}", "static", 42])
        assert result == ["list_val", "static", 42]


class TestPlainStringPassthrough:
    """Scenario: Plain string passthrough."""

    def test_plain_string(self):
        assert _resolve_env_vars("just_a_string") == "just_a_string"

    def test_string_with_dollar_no_braces(self):
        assert _resolve_env_vars("$NOT_A_PATTERN") == "$NOT_A_PATTERN"

    def test_string_with_partial_braces(self):
        assert _resolve_env_vars("${incomplete") == "${incomplete"


class TestNonStringPassthrough:
    """Scenario: Non-string value passthrough."""

    def test_int_passthrough(self):
        assert _resolve_env_vars(42) == 42

    def test_bool_passthrough(self):
        assert _resolve_env_vars(True) is True

    def test_none_passthrough(self):
        assert _resolve_env_vars(None) is None

    def test_float_passthrough(self):
        assert _resolve_env_vars(3.14) == 3.14


class TestNestedStructureResolution:
    """Scenario: Nested structure resolution."""

    def test_nested_dict_list(self, monkeypatch):
        monkeypatch.setenv("NESTED_VAR", "deep_value")
        result = _resolve_env_vars({"outer": [{"inner": "${NESTED_VAR}"}]})
        assert result == {"outer": [{"inner": "deep_value"}]}
