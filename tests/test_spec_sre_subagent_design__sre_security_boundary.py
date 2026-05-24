"""Tests for SRE security boundary spec — sre-security-boundary.md"""
import importlib
import pytest


def _get_sre_module():
    try:
        return importlib.import_module("zsiga.pipeline.sre_pipeline")
    except ModuleNotFoundError:
        return None


def _get_validate_command():
    mod = _get_sre_module()
    if mod is None:
        return None
    return getattr(mod, "validate_command", None)


def _get_classify_command_risk():
    mod = _get_sre_module()
    if mod is None:
        return None
    return getattr(mod, "classify_command_risk", None)


def _skip_if_missing():
    if _get_sre_module() is None:
        pytest.skip("zsiga.pipeline.sre_pipeline not yet implemented")


# ---------------------------------------------------------------------------
# Scenario: Whitelisted command passes validation
# ---------------------------------------------------------------------------
def test_whitelisted_systemctl_status():
    validate = _get_validate_command()
    if validate is None:
        pytest.skip("validate_command not yet implemented")
    assert validate("systemctl status nginx") is True


# ---------------------------------------------------------------------------
# Scenario: Whitelisted command with sudo passes validation
# ---------------------------------------------------------------------------
def test_whitelisted_sudo_systemctl():
    validate = _get_validate_command()
    if validate is None:
        pytest.skip("validate_command not yet implemented")
    assert validate("sudo systemctl restart nginx") is True


# ---------------------------------------------------------------------------
# Scenario: Non-whitelisted command is rejected
# ---------------------------------------------------------------------------
def test_non_whitelisted_rejected():
    validate = _get_validate_command()
    if validate is None:
        pytest.skip("validate_command not yet implemented")
    assert validate("apt-get install something") is False


# ---------------------------------------------------------------------------
# Scenario: Blacklisted rm -rf is rejected
# ---------------------------------------------------------------------------
def test_blacklisted_rm_rf():
    validate = _get_validate_command()
    if validate is None:
        pytest.skip("validate_command not yet implemented")
    assert validate("rm -rf /var/log/old") is False


# ---------------------------------------------------------------------------
# Scenario: Blacklisted iptables is rejected
# ---------------------------------------------------------------------------
def test_blacklisted_iptables():
    validate = _get_validate_command()
    if validate is None:
        pytest.skip("validate_command not yet implemented")
    assert validate("iptables -A INPUT -j DROP") is False


# ---------------------------------------------------------------------------
# Scenario: Blacklisted reboot is rejected
# ---------------------------------------------------------------------------
def test_blacklisted_reboot():
    validate = _get_validate_command()
    if validate is None:
        pytest.skip("validate_command not yet implemented")
    assert validate("reboot") is False


# ---------------------------------------------------------------------------
# Scenario: Blacklisted command hidden behind sudo is still rejected
# ---------------------------------------------------------------------------
def test_blacklisted_sudo_reboot():
    validate = _get_validate_command()
    if validate is None:
        pytest.skip("validate_command not yet implemented")
    assert validate("sudo reboot") is False


# ---------------------------------------------------------------------------
# Scenario: Blacklisted sysctl is rejected
# ---------------------------------------------------------------------------
def test_blacklisted_sysctl():
    validate = _get_validate_command()
    if validate is None:
        pytest.skip("validate_command not yet implemented")
    assert validate("sysctl -w vm.swappiness=10") is False


# ---------------------------------------------------------------------------
# Scenario: Blacklist takes precedence (systemctl shutdown)
# ---------------------------------------------------------------------------
def test_blacklist_precedence_over_whitelist():
    validate = _get_validate_command()
    if validate is None:
        pytest.skip("validate_command not yet implemented")
    # 'shutdown' is blacklisted even though 'systemctl' is whitelisted
    assert validate("systemctl shutdown") is False


# ---------------------------------------------------------------------------
# Scenario: Dangerous command flagged in plan (systemctl stop)
# ---------------------------------------------------------------------------
def test_dangerous_command_flagged_stop():
    classify = _get_classify_command_risk()
    if classify is None:
        pytest.skip("classify_command_risk not yet implemented")
    result = classify("systemctl stop nginx")
    assert isinstance(result, dict), "classify_command_risk must return a dict"
    assert result.get("require_approval") is True, \
        "systemctl stop should have require_approval=True"


# ---------------------------------------------------------------------------
# Scenario: Safe command not flagged (systemctl status)
# ---------------------------------------------------------------------------
def test_safe_command_not_flagged():
    classify = _get_classify_command_risk()
    if classify is None:
        pytest.skip("classify_command_risk not yet implemented")
    result = classify("systemctl status nginx")
    assert isinstance(result, dict), "classify_command_risk must return a dict"
    assert result.get("require_approval") is False, \
        "systemctl status should have require_approval=False"


# ---------------------------------------------------------------------------
# Scenario: Execution failure triggers rollback attempt
# ---------------------------------------------------------------------------
def test_execute_failure_triggers_rollback():
    SREPipeline = getattr(_get_sre_module() or object, "SREPipeline", None)
    if SREPipeline is None:
        pytest.skip("SREPipeline not yet implemented")

    commands_issued = []

    def mock_call(command, **kwargs):
        commands_issued.append(command)
        if "restart" in command:
            return type("R", (), {"exit_code": 1, "stdout": "failed"})()
        return type("R", (), {"exit_code": 0, "stdout": "ok"})()

    from unittest.mock import MagicMock
    mock_transport = MagicMock()
    mock_transport.call.side_effect = mock_call

    pipeline = SREPipeline(transport=mock_transport)
    plan = {
        "commands": [
            {"cmd": "systemctl restart nginx", "rollback": "systemctl stop nginx"},
        ]
    }
    pipeline._execute(plan)

    # rollback command should have been issued
    assert any("stop" in c for c in commands_issued), \
        f"Rollback not triggered. Commands: {commands_issued}"
