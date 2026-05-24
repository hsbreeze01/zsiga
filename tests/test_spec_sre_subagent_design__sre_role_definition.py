"""Tests for SRE role definition spec — sre-role-definition.md"""
import importlib
import pytest


def _get_roles_module():
    try:
        return importlib.import_module("zsiga.roles")
    except ModuleNotFoundError:
        return None


def _get_role(name):
    mod = _get_roles_module()
    if mod is None:
        return None
    fn = getattr(mod, "get_role", None)
    if fn is None:
        return None
    return fn(name)


# ---------------------------------------------------------------------------
# Scenario: SRE role is registered and retrievable
# ---------------------------------------------------------------------------
def test_sre_role_registered():
    role = _get_role("sre")
    if role is None:
        pytest.skip("zsiga.roles or get_role not yet implemented")
    assert getattr(role, "name", None) == "sre"
    assert getattr(role, "max_turns", None) == 15
    assert getattr(role, "read_only", None) is False


# ---------------------------------------------------------------------------
# Scenario: SRE role has correct allowed tools
# ---------------------------------------------------------------------------
def test_sre_role_allowed_tools():
    role = _get_role("sre")
    if role is None:
        pytest.skip("zsiga.roles or get_role not yet implemented")
    tools = getattr(role, "allowed_tools", None)
    assert tools is not None, "SRE role must have allowed_tools"
    expected = sorted(["bash", "read_file", "search", "list_files"])
    assert sorted(tools) == expected, f"Expected {expected}, got {sorted(tools)}"


# ---------------------------------------------------------------------------
# Scenario: SRE system prompt mentions idempotency
# ---------------------------------------------------------------------------
def test_sre_system_prompt_idempotency():
    role = _get_role("sre")
    if role is None:
        pytest.skip("zsiga.roles or get_role not yet implemented")
    prompt = getattr(role, "system_prompt", "")
    assert prompt, "SRE role must have a system_prompt"
    lower = prompt.lower()
    assert "幂等" in prompt or "idempotent" in lower, \
        "SRE system_prompt must mention idempotency (幂等 or idempotent)"


# ---------------------------------------------------------------------------
# Scenario: SRE system prompt mentions rollback
# ---------------------------------------------------------------------------
def test_sre_system_prompt_rollback():
    role = _get_role("sre")
    if role is None:
        pytest.skip("zsiga.roles or get_role not yet implemented")
    prompt = getattr(role, "system_prompt", "")
    lower = prompt.lower()
    assert "回滚" in prompt or "rollback" in lower, \
        "SRE system_prompt must mention rollback (回滚 or rollback)"


# ---------------------------------------------------------------------------
# Scenario: SRE system prompt mentions whitelist constraint
# ---------------------------------------------------------------------------
def test_sre_system_prompt_whitelist():
    role = _get_role("sre")
    if role is None:
        pytest.skip("zsiga.roles or get_role not yet implemented")
    prompt = getattr(role, "system_prompt", "")
    lower = prompt.lower()
    assert "白名单" in prompt or "whitelist" in lower, \
        "SRE system_prompt must mention whitelist (白名单 or whitelist)"


# ---------------------------------------------------------------------------
# Scenario: SRE system prompt prohibits git commits
# ---------------------------------------------------------------------------
def test_sre_system_prompt_no_git_commit():
    role = _get_role("sre")
    if role is None:
        pytest.skip("zsiga.roles or get_role not yet implemented")
    prompt = getattr(role, "system_prompt", "")
    lower = prompt.lower()
    has_git_commit = "git commit" in lower
    has_prohibition = any(w in prompt for w in ["禁止", "不得", "不能"]) or \
        any(w in lower for w in ["must not", "no git", "shall not", "do not"])
    assert has_git_commit and has_prohibition, \
        "SRE system_prompt must prohibit git commit (mention 'git commit' + prohibition language)"
