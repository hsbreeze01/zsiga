"""Tests for SRE pipeline spec — sre-pipeline.md"""
import importlib
import pytest
from unittest.mock import MagicMock


def _get_sre_pipeline_module():
    try:
        return importlib.import_module("zsiga.pipeline.sre_pipeline")
    except ModuleNotFoundError:
        return None


def _get_sre_pipeline_class():
    mod = _get_sre_pipeline_module()
    if mod is None:
        return None
    return getattr(mod, "SREPipeline", None)


def _make_mock_transport(responses=None):
    """Create a mock transport that returns predefined responses."""
    transport = MagicMock()
    responses = responses or []
    transport.call.side_effect = responses or [MagicMock(exit_code=0, stdout="ok")]
    return transport


# ---------------------------------------------------------------------------
# Scenario: Pipeline defines all five phases in order
# ---------------------------------------------------------------------------
def test_pipeline_five_phases_in_order():
    SREPipeline = _get_sre_pipeline_class()
    if SREPipeline is None:
        pytest.skip("zsiga.pipeline.sre_pipeline not yet implemented")

    # Check PHASES class attribute or similar
    phases = getattr(SREPipeline, "PHASES", None) or getattr(SREPipeline, "phases", None)
    if phases is None:
        # Try to get from instance
        instance = SREPipeline.__new__(SREPipeline)
        phases = getattr(instance, "PHASES", None) or getattr(instance, "phases", None)

    assert phases is not None, "SREPipeline must define PHASES attribute"
    expected = ["DIAGNOSE", "PLAN", "EXECUTE", "VERIFY", "REPORT"]
    assert list(phases) == expected, f"Expected {expected}, got {list(phases)}"


# ---------------------------------------------------------------------------
# Scenario: Pipeline run produces phase completion record for each phase
# ---------------------------------------------------------------------------
def test_pipeline_run_produces_all_phase_records():
    SREPipeline = _get_sre_pipeline_class()
    if SREPipeline is None:
        pytest.skip("zsiga.pipeline.sre_pipeline not yet implemented")

    mock_transport = _make_mock_transport([
        MagicMock(exit_code=0, stdout="active"),
        MagicMock(exit_code=0, stdout="planned"),
        MagicMock(exit_code=0, stdout="executed"),
        MagicMock(exit_code=0, stdout="verified"),
    ])

    pipeline = SREPipeline(transport=mock_transport)
    result = pipeline.run("检查磁盘使用情况")

    assert isinstance(result, dict), "Pipeline run must return a dict"
    # Check that all 5 phases have records
    phases_in_result = result.get("phases", [])
    assert len(phases_in_result) == 5, \
        f"Expected 5 phase records, got {len(phases_in_result)}"
    for record in phases_in_result:
        assert "phase" in record, f"Phase record missing 'phase' key: {record}"
        assert "status" in record, f"Phase record missing 'status' key: {record}"


# ---------------------------------------------------------------------------
# Scenario: DIAGNOSE phase collects read-only information
# ---------------------------------------------------------------------------
def test_diagnose_uses_read_only_commands():
    SREPipeline = _get_sre_pipeline_class()
    if SREPipeline is None:
        pytest.skip("zsiga.pipeline.sre_pipeline not yet implemented")

    commands_issued = []

    def capture_call(command, **kwargs):
        commands_issued.append(command)
        return MagicMock(exit_code=0, stdout="ok")

    mock_transport = MagicMock()
    mock_transport.call.side_effect = capture_call

    pipeline = SREPipeline(transport=mock_transport)
    pipeline._diagnose("检查 nginx 服务状态")

    mutating_patterns = ["start", "stop", "restart", "kill", "rm "]
    for cmd in commands_issued:
        cmd_lower = cmd.lower()
        for pattern in mutating_patterns:
            assert pattern not in cmd_lower, \
                f"DIAGNOSE issued mutating command: {cmd} (matched {pattern})"


# ---------------------------------------------------------------------------
# Scenario: PLAN phase only generates whitelisted commands
# ---------------------------------------------------------------------------
def test_plan_generates_whitelisted_commands():
    mod = _get_sre_pipeline_module()
    if mod is None:
        pytest.skip("zsiga.pipeline.sre_pipeline not yet implemented")

    validate_fn = getattr(mod, "validate_command", None)
    if validate_fn is None:
        pytest.skip("validate_command not yet implemented")

    SREPipeline = _get_sre_pipeline_class()
    mock_transport = _make_mock_transport([MagicMock(exit_code=0, stdout="disk: 50%")])
    pipeline = SREPipeline(transport=mock_transport)
    diagnose_result = {"status": "success", "data": {"disk": "50%"}}
    plan = pipeline._plan(diagnose_result)

    # plan should contain commands
    commands = plan.get("commands", []) if isinstance(plan, dict) else []
    for cmd in commands:
        assert validate_fn(cmd), f"Plan contains non-whitelisted command: {cmd}"


# ---------------------------------------------------------------------------
# Scenario: EXECUTE stops on first failure
# ---------------------------------------------------------------------------
def test_execute_stops_on_first_failure():
    SREPipeline = _get_sre_pipeline_class()
    if SREPipeline is None:
        pytest.skip("zsiga.pipeline.sre_pipeline not yet implemented")

    call_count = 0

    def mock_call(command, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            return MagicMock(exit_code=1, stdout="error")
        return MagicMock(exit_code=0, stdout="ok")

    mock_transport = MagicMock()
    mock_transport.call.side_effect = mock_call

    pipeline = SREPipeline(transport=mock_transport)
    plan = {
        "commands": [
            {"cmd": "systemctl status nginx", "rollback": "echo noop"},
            {"cmd": "systemctl restart nginx", "rollback": "systemctl stop nginx"},
            {"cmd": "systemctl status nginx", "rollback": "echo noop"},
        ]
    }
    result = pipeline._execute(plan)
    assert result.get("status") == "failed", "Execute should report failed when a step fails"
    assert call_count <= 2, f"Should stop after failure, but made {call_count} calls"


# ---------------------------------------------------------------------------
# Scenario: EXECUTE succeeds when all commands pass
# ---------------------------------------------------------------------------
def test_execute_succeeds_all_pass():
    SREPipeline = _get_sre_pipeline_class()
    if SREPipeline is None:
        pytest.skip("zsiga.pipeline.sre_pipeline not yet implemented")

    mock_transport = _make_mock_transport([
        MagicMock(exit_code=0, stdout="ok"),
        MagicMock(exit_code=0, stdout="ok"),
    ])

    pipeline = SREPipeline(transport=mock_transport)
    plan = {
        "commands": [
            {"cmd": "systemctl status nginx", "rollback": "echo noop"},
            {"cmd": "df -h", "rollback": "echo noop"},
        ]
    }
    result = pipeline._execute(plan)
    assert result.get("status") == "success", "Execute should report success when all pass"


# ---------------------------------------------------------------------------
# Scenario: VERIFY returns success when target state matches
# ---------------------------------------------------------------------------
def test_verify_success():
    SREPipeline = _get_sre_pipeline_class()
    if SREPipeline is None:
        pytest.skip("zsiga.pipeline.sre_pipeline not yet implemented")

    mock_transport = _make_mock_transport([MagicMock(exit_code=0, stdout="active (running)")])
    pipeline = SREPipeline(transport=mock_transport)
    execute_result = {"status": "success", "commands_executed": []}
    result = pipeline._verify(execute_result)
    assert result.get("status") == "success", "Verify should report success"


# ---------------------------------------------------------------------------
# Scenario: VERIFY returns failure when target state not achieved
# ---------------------------------------------------------------------------
def test_verify_failure():
    SREPipeline = _get_sre_pipeline_class()
    if SREPipeline is None:
        pytest.skip("zsiga.pipeline.sre_pipeline not yet implemented")

    mock_transport = _make_mock_transport([MagicMock(exit_code=0, stdout="inactive (dead)")])
    pipeline = SREPipeline(transport=mock_transport)
    execute_result = {"status": "success", "commands_executed": []}
    result = pipeline._verify(execute_result)
    assert result.get("status") == "failed", "Verify should report failure when target not met"


# ---------------------------------------------------------------------------
# Scenario: Pipeline does not invoke git commit
# ---------------------------------------------------------------------------
def test_pipeline_no_git_commit():
    SREPipeline = _get_sre_pipeline_class()
    if SREPipeline is None:
        pytest.skip("zsiga.pipeline.sre_pipeline not yet implemented")

    commands_issued = []

    def capture(command, **kwargs):
        commands_issued.append(command)
        return MagicMock(exit_code=0, stdout="ok")

    mock_transport = MagicMock()
    mock_transport.call.side_effect = capture
    pipeline = SREPipeline(transport=mock_transport)
    pipeline.run("检查磁盘使用情况")

    for cmd in commands_issued:
        assert "git commit" not in cmd.lower(), f"Pipeline issued git commit: {cmd}"
        assert "git add" not in cmd.lower(), f"Pipeline issued git add: {cmd}"


# ---------------------------------------------------------------------------
# Scenario: REPORT phase produces execution report data
# ---------------------------------------------------------------------------
def test_report_produces_execution_report_data():
    SREPipeline = _get_sre_pipeline_class()
    if SREPipeline is None:
        pytest.skip("zsiga.pipeline.sre_pipeline not yet implemented")

    mock_transport = _make_mock_transport()
    pipeline = SREPipeline(transport=mock_transport)
    phase_results = {
        "DIAGNOSE": {"status": "success"},
        "PLAN": {"status": "success"},
        "EXECUTE": {"status": "success"},
        "VERIFY": {"status": "success"},
    }
    report = pipeline._report(phase_results)
    assert isinstance(report, dict), "Report must be a dict"
    assert "status" in report, "Report must contain 'status' key"
    assert "phases" in report, "Report must contain 'phases' key"
