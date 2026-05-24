"""Tests for SRE role definition spec."""
from zsiga.agent.roles import Role, get_role_config, get_role_system_prompt, get_all_roles


# ---------------------------------------------------------------------------
# Scenario: SRE role enum value exists
# ---------------------------------------------------------------------------
def test_sre_role_enum_value():
    assert Role("sre") is Role.SRE
    assert Role.SRE.value == "sre"


# ---------------------------------------------------------------------------
# Scenario: SRE role config has correct attributes
# ---------------------------------------------------------------------------
def test_sre_role_config_attributes():
    config = get_role_config(Role.SRE)
    assert config.name == "sre"
    assert config.max_turns == 15
    assert config.read_only is False
    assert set(config.allowed_tools) == {"bash", "read_file", "search", "list_files"}


# ---------------------------------------------------------------------------
# Scenario: SRE system prompt is non-empty
# ---------------------------------------------------------------------------
def test_sre_system_prompt_non_empty():
    prompt = get_role_system_prompt(Role.SRE)
    assert isinstance(prompt, str)
    assert len(prompt) > 50


# ---------------------------------------------------------------------------
# Scenario: SRE system prompt mentions idempotency
# ---------------------------------------------------------------------------
def test_sre_system_prompt_mentions_idempotency():
    prompt = get_role_system_prompt(Role.SRE)
    lower = prompt.lower()
    assert "幂等" in prompt or "idempotent" in lower


# ---------------------------------------------------------------------------
# Scenario: SRE system prompt mentions rollback
# ---------------------------------------------------------------------------
def test_sre_system_prompt_mentions_rollback():
    prompt = get_role_system_prompt(Role.SRE)
    lower = prompt.lower()
    assert "回滚" in prompt or "rollback" in lower or "revert" in lower


# ---------------------------------------------------------------------------
# Scenario: Existing roles remain unchanged
# ---------------------------------------------------------------------------
def test_existing_roles_unchanged():
    all_roles = get_all_roles()
    # All original roles still exist
    assert Role.EXPLORE in all_roles
    assert Role.IMPLEMENT in all_roles
    assert Role.REVIEW in all_roles
    assert Role.DIAGNOSER in all_roles

    # Check original attributes are preserved
    explore = all_roles[Role.EXPLORE]
    assert explore.name == "explore"
    assert explore.read_only is True

    impl = all_roles[Role.IMPLEMENT]
    assert impl.name == "implement"
    assert impl.max_turns == 15

    review = all_roles[Role.REVIEW]
    assert review.name == "review"

    diag = all_roles[Role.DIAGNOSER]
    assert diag.name == "diagnose"


# ---------------------------------------------------------------------------
# Scenario: Command whitelist contains systemctl variants
# ---------------------------------------------------------------------------
def test_command_whitelist_contains_systemctl():
    config = get_role_config(Role.SRE)
    wl = config.command_whitelist
    assert any("systemctl start" in e for e in wl), f"Missing 'systemctl start' in {wl}"
    assert any("systemctl stop" in e for e in wl), f"Missing 'systemctl stop' in {wl}"
    assert any("systemctl restart" in e for e in wl), f"Missing 'systemctl restart' in {wl}"
    assert any("systemctl status" in e for e in wl), f"Missing 'systemctl status' in {wl}"


# ---------------------------------------------------------------------------
# Scenario: Command whitelist contains diagnostic commands
# ---------------------------------------------------------------------------
def test_command_whitelist_contains_diagnostic():
    config = get_role_config(Role.SRE)
    wl = config.command_whitelist
    for cmd in ["df", "free", "du", "journalctl", "dmesg"]:
        assert cmd in wl, f"Missing '{cmd}' in whitelist"


# ---------------------------------------------------------------------------
# Scenario: Blacklist blocks rm -rf
# ---------------------------------------------------------------------------
def test_blacklist_blocks_rm_rf():
    config = get_role_config(Role.SRE)
    bl = config.command_blacklist
    assert "rm -rf" in bl, f"Missing 'rm -rf' in blacklist {bl}"


# ---------------------------------------------------------------------------
# Scenario: Blacklist blocks iptables and sysctl
# ---------------------------------------------------------------------------
def test_blacklist_blocks_iptables_sysctl():
    config = get_role_config(Role.SRE)
    bl = config.command_blacklist
    assert "iptables" in bl, f"Missing 'iptables' in blacklist {bl}"
    assert "sysctl" in bl, f"Missing 'sysctl' in blacklist {bl}"
