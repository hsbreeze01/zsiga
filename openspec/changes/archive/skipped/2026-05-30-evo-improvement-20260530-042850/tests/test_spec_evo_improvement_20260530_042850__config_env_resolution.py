"""Tests for _resolve_env_vars environment variable resolution.

Spec: config-env-resolution
Change: evo-improvement-20260530-042850
"""

from zsiga.config import _resolve_env_vars


class TestResolveExistingEnvVar:
    """Spec: config-env-resolution — Resolve existing env var."""

    def test_resolves_existing_var(self, monkeypatch):
        monkeypatch.setenv("TEST_RESOLVE_VAR", "resolved_value")
        assert _resolve_env_vars("${TEST_RESOLVE_VAR}") == "resolved_value"


class TestResolveMissingEnvVar:
    """Spec: config-env-resolution — Resolve missing env var."""

    def test_missing_var_returns_empty(self, monkeypatch):
        monkeypatch.delenv("NONEXISTENT_ZSIGA_VAR_XYZ", raising=False)
        assert _resolve_env_vars("${NONEXISTENT_ZSIGA_VAR_XYZ}") == ""


class TestResolveDictRecursively:
    """Spec: config-env-resolution — Resolve dict values recursively."""

    def test_dict_resolution(self, monkeypatch):
        monkeypatch.setenv("DICT_TEST_VAR", "from_env")
        result = _resolve_env_vars({"key": "${DICT_TEST_VAR}", "other": "plain"})
        assert result == {"key": "from_env", "other": "plain"}


class TestResolveListRecursively:
    """Spec: config-env-resolution — Resolve list values recursively."""

    def test_list_resolution(self, monkeypatch):
        monkeypatch.setenv("LIST_TEST_VAR", "list_val")
        result = _resolve_env_vars(["${LIST_TEST_VAR}", "static", 42])
        assert result == ["list_val", "static", 42]


class TestPlainStringPassthrough:
    """Spec: config-env-resolution — Plain string passthrough."""

    def test_plain_string(self):
        assert _resolve_env_vars("just_a_string") == "just_a_string"

    def test_string_with_dollar_no_braces(self):
        assert _resolve_env_vars("$NOT_A_PATTERN") == "$NOT_A_PATTERN"

    def test_string_with_partial_braces(self):
        assert _resolve_env_vars("${incomplete") == "${incomplete"


class TestNonStringPassthrough:
    """Spec: config-env-resolution — Non-string passthrough."""

    def test_int_passthrough(self):
        assert _resolve_env_vars(42) == 42

    def test_bool_passthrough(self):
        assert _resolve_env_vars(True) is True

    def test_none_passthrough(self):
        assert _resolve_env_vars(None) is None

    def test_float_passthrough(self):
        assert _resolve_env_vars(3.14) == 3.14


class TestNestedStructureResolution:
    """Spec: config-env-resolution — Nested structure resolution."""

    def test_nested_dict_list(self, monkeypatch):
        monkeypatch.setenv("NESTED_VAR", "deep_value")
        result = _resolve_env_vars({"outer": [{"inner": "${NESTED_VAR}"}]})
        assert result == {"outer": [{"inner": "deep_value"}]}
