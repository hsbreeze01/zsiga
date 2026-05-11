"""Tests for agent/roles.py"""

from zsiga.agent.roles import (
    Role, get_role_config, get_role_system_prompt, get_all_roles,
)


def test_role_enum_values():
    assert Role.EXPLORE.value == "explore"
    assert Role.IMPLEMENT.value == "implement"
    assert Role.REVIEW.value == "review"


def test_explore_role_config():
    config = get_role_config(Role.EXPLORE)
    assert config.name == "explore"
    assert config.max_turns == 5
    assert config.read_only is True
    assert "write_file" not in config.allowed_tools
    assert "edit_file" not in config.allowed_tools
    assert "ast_replace" not in config.allowed_tools
    assert "read_file" in config.allowed_tools
    assert "search" in config.allowed_tools


def test_implement_role_has_all_tools():
    config = get_role_config(Role.IMPLEMENT)
    assert config.read_only is False
    assert "write_file" in config.allowed_tools
    assert "edit_file" in config.allowed_tools
    assert "ast_replace" in config.allowed_tools
    assert len(config.allowed_tools) == 8


def test_review_role_read_only():
    config = get_role_config(Role.REVIEW)
    assert config.max_turns == 8
    assert config.read_only is True
    assert "write_file" not in config.allowed_tools


def test_system_prompts_are_chinese():
    for role in Role:
        prompt = get_role_system_prompt(role)
        assert len(prompt) > 50
        assert "zsiga" in prompt.lower() or "子代理" in prompt or "子 agent" in prompt


def test_get_all_roles_returns_three():
    all_roles = get_all_roles()
    assert len(all_roles) == 3
    assert set(all_roles.keys()) == {Role.EXPLORE, Role.IMPLEMENT, Role.REVIEW}


def test_role_from_string():
    assert Role("explore") == Role.EXPLORE
    assert Role("implement") == Role.IMPLEMENT
    assert Role("review") == Role.REVIEW
