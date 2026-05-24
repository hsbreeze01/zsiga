"""Tests for SRE pipeline spec."""
import os
import tempfile

from zsiga.transport import LocalTransport


# ---------------------------------------------------------------------------
# Scenario: Command Validation — whitelisted command passes
# ---------------------------------------------------------------------------
def test_validate_command_whitelisted():
    from zsiga.pipeline.sre_pipeline import validate_command

    whitelist = ["systemctl restart", "systemctl status", "df"]
    blacklist = ["rm -rf", "eval"]
    assert validate_command("systemctl restart nginx", whitelist, blacklist) is True


# ---------------------------------------------------------------------------
# Scenario: Command Validation — non-whitelisted command fails
# ---------------------------------------------------------------------------
def test_validate_command_not_whitelisted():
    from zsiga.pipeline.sre_pipeline import validate_command

    whitelist = ["systemctl", "df", "free"]
    blacklist = []
    assert validate_command("apt-get install something", whitelist, blacklist) is False


# ---------------------------------------------------------------------------
# Scenario: Command Validation — blacklisted command fails
# ---------------------------------------------------------------------------
def test_validate_command_blacklisted():
    from zsiga.pipeline.sre_pipeline import validate_command

    whitelist = ["systemctl"]
    blacklist = ["eval"]
    assert validate_command("systemctl eval malicious", whitelist, blacklist) is False


# ---------------------------------------------------------------------------
# Scenario: Command Validation — empty command fails
# ---------------------------------------------------------------------------
def test_validate_command_empty():
    from zsiga.pipeline.sre_pipeline import validate_command

    whitelist = ["systemctl"]
    blacklist = ["rm -rf"]
    assert validate_command("", whitelist, blacklist) is False


# ---------------------------------------------------------------------------
# Scenario: DIAGNOSE phase collects system state
# ---------------------------------------------------------------------------
def test_diagnose_collects_system_state():
    from zsiga.pipeline.sre_pipeline import diagnose

    transport = LocalTransport()
    result = diagnose(transport)
    assert isinstance(result, dict)
    assert "services" in result
    assert "disk" in result
    assert "memory" in result
    assert "processes" in result


# ---------------------------------------------------------------------------
# Scenario: PLAN rejects blacklisted commands
# ---------------------------------------------------------------------------
def test_plan_rejects_blacklisted_commands():
    from zsiga.pipeline.sre_pipeline import plan

    result = plan(
        intent_description="delete all logs",
        proposed_commands=["rm -rf /var/log", "df -h"],
        whitelist=["systemctl", "df"],
        blacklist=["rm -rf"],
    )
    assert result["success"] is False


# ---------------------------------------------------------------------------
# Scenario: PLAN accepts whitelisted commands
# ---------------------------------------------------------------------------
def test_plan_accepts_whitelisted_commands():
    from zsiga.pipeline.sre_pipeline import plan

    result = plan(
        intent_description="check disk and restart nginx",
        proposed_commands=["systemctl restart nginx", "df -h"],
        whitelist=["systemctl restart", "df"],
        blacklist=["rm -rf"],
    )
    assert result["success"] is True


# ---------------------------------------------------------------------------
# Scenario: EXECUTE records each command result
# ---------------------------------------------------------------------------
def test_execute_records_command_results():
    from zsiga.pipeline.sre_pipeline import execute

    transport = LocalTransport()
    commands = ["echo hello", "echo world", "echo done"]
    result = execute(commands, transport)
    assert result["success"] is True
    assert len(result["commands"]) == 3
    for cmd_record in result["commands"]:
        assert "command" in cmd_record
        assert "exit_code" in cmd_record
        assert "stdout" in cmd_record


# ---------------------------------------------------------------------------
# Scenario: EXECUTE stops on command failure
# ---------------------------------------------------------------------------
def test_execute_stops_on_failure():
    from zsiga.pipeline.sre_pipeline import execute

    transport = LocalTransport()
    commands = ["echo ok", "false", "echo should_not_run"]
    result = execute(commands, transport)
    assert result["success"] is False
    # Only 2 commands should have been recorded (1st success + 2nd failure)
    assert len(result["commands"]) == 2


# ---------------------------------------------------------------------------
# Scenario: VERIFY compares pre and post state
# ---------------------------------------------------------------------------
def test_verify_compares_state():
    from zsiga.pipeline.sre_pipeline import verify

    pre = {"services": "nginx (running)", "disk": "50%", "memory": "2GB"}
    post = {"services": "nginx (running)", "disk": "45%", "memory": "2GB"}
    result = verify(pre, post, "free up disk space")
    assert "passed" in result
    assert "differences" in result


# ---------------------------------------------------------------------------
# Scenario: REPORT generates execution_report.md
# ---------------------------------------------------------------------------
def test_report_generates_execution_report():
    from zsiga.pipeline.sre_pipeline import report

    with tempfile.TemporaryDirectory() as tmpdir:
        transport = LocalTransport()
        results = {
            "intent": "restart nginx",
            "phases": [
                {"name": "DIAGNOSE", "status": "ok", "duration": "1.2s"},
                {"name": "PLAN", "status": "ok", "duration": "0.1s"},
                {"name": "EXECUTE", "status": "ok", "duration": "2.0s"},
                {"name": "VERIFY", "status": "ok", "duration": "0.5s"},
            ],
            "commands": [
                {"command": "systemctl restart nginx", "exit_code": 0, "stdout": ""},
            ],
            "verification": {"passed": True, "differences": []},
        }
        report(results, tmpdir, transport)
        report_path = os.path.join(tmpdir, "execution_report.md")
        assert os.path.exists(report_path)
        content = open(report_path).read()
        assert "## Intent" in content
        assert "## Timeline" in content or "## Phases" in content
        assert "## Commands" in content
        assert "## Verification" in content


# ---------------------------------------------------------------------------
# Scenario: Report contains all required sections
# ---------------------------------------------------------------------------
def test_generate_report_content_has_required_sections():
    from zsiga.pipeline.sre_pipeline import generate_report_content

    results = {
        "intent": "restart nginx",
        "phases": [
            {"name": "DIAGNOSE", "status": "ok", "duration": "1.2s"},
        ],
        "commands": [
            {"command": "systemctl restart nginx", "exit_code": 0, "stdout": ""},
        ],
        "verification": {"passed": True, "differences": []},
    }
    content = generate_report_content(results)
    assert "# SRE Execution Report" in content
    assert "## Intent" in content
    assert "## Timeline" in content
    assert "## Commands" in content
    assert "## Verification" in content
    assert "## Summary" in content


# ---------------------------------------------------------------------------
# Scenario: Report commands table includes all executed commands
# ---------------------------------------------------------------------------
def test_report_includes_all_commands():
    from zsiga.pipeline.sre_pipeline import generate_report_content

    results = {
        "intent": "check health",
        "phases": [],
        "commands": [
            {"command": "systemctl status nginx", "exit_code": 0, "stdout": "active"},
            {"command": "df -h", "exit_code": 0, "stdout": "50%"},
        ],
        "verification": {"passed": True, "differences": []},
    }
    content = generate_report_content(results)
    assert "systemctl status nginx" in content
    assert "df -h" in content
