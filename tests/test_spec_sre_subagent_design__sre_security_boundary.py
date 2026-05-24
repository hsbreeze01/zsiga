"""Tests for SRE security boundary spec."""
from zsiga.pipeline.sre_pipeline import (
    validate_command,
    is_dangerous_command,
    take_snapshot,
)
from zsiga.transport import LocalTransport


# ---------------------------------------------------------------------------
# Scenario: Whitelisted command passes validation (covered in pipeline test)
# ---------------------------------------------------------------------------
def test_validate_command_whitelisted_passes():
    whitelist = ["systemctl restart", "df"]
    blacklist = ["rm -rf"]
    assert validate_command("systemctl restart nginx", whitelist, blacklist) is True


# ---------------------------------------------------------------------------
# Scenario: Non-whitelisted command fails validation
# ---------------------------------------------------------------------------
def test_validate_command_non_whitelisted_fails():
    whitelist = ["systemctl"]
    blacklist = []
    assert validate_command("apt-get install something", whitelist, blacklist) is False


# ---------------------------------------------------------------------------
# Scenario: Blacklisted command fails even if whitelisted
# ---------------------------------------------------------------------------
def test_validate_command_blacklist_overrides_whitelist():
    whitelist = ["systemctl"]
    blacklist = ["eval"]
    assert validate_command("systemctl eval malicious", whitelist, blacklist) is False


# ---------------------------------------------------------------------------
# Scenario: Empty command fails validation
# ---------------------------------------------------------------------------
def test_validate_command_empty_fails():
    assert validate_command("", ["systemctl"], ["rm -rf"]) is False


# ---------------------------------------------------------------------------
# Scenario: Snapshot captures service and resource state
# ---------------------------------------------------------------------------
def test_snapshot_captures_state():
    transport = LocalTransport()
    snapshot = take_snapshot(transport)
    assert isinstance(snapshot, dict)
    assert "services" in snapshot
    assert "disk" in snapshot
    assert "memory" in snapshot


# ---------------------------------------------------------------------------
# Scenario: Snapshot contains non-empty string values
# ---------------------------------------------------------------------------
def test_snapshot_non_empty_values():
    transport = LocalTransport()
    snapshot = take_snapshot(transport)
    for key in ("services", "disk", "memory"):
        assert isinstance(snapshot[key], str)
        assert len(snapshot[key]) > 0


# ---------------------------------------------------------------------------
# Scenario: Service stop commands are flagged as dangerous
# ---------------------------------------------------------------------------
def test_service_stop_is_dangerous():
    assert is_dangerous_command("systemctl stop nginx") is True


# ---------------------------------------------------------------------------
# Scenario: Status query is not flagged as dangerous
# ---------------------------------------------------------------------------
def test_status_not_dangerous():
    assert is_dangerous_command("systemctl status nginx") is False


# ---------------------------------------------------------------------------
# Scenario: Disk usage query is not flagged as dangerous
# ---------------------------------------------------------------------------
def test_df_not_dangerous():
    assert is_dangerous_command("df -h") is False
