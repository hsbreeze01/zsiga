"""Tests for SRE orchestrator integration spec — sre-orchestrator-integration.md"""
import importlib
import pytest
from unittest.mock import MagicMock


def _get_orchestrator_module():
    try:
        return importlib.import_module("zsiga.orchestrator")
    except ModuleNotFoundError:
        return None


def _get_orchestrator_class():
    mod = _get_orchestrator_module()
    if mod is None:
        return None
    return getattr(mod, "Orchestrator", None)


def _make_mock_pipeline(name="mock_pipeline"):
    """Create a mock pipeline with a run method."""
    pipeline = MagicMock()
    pipeline.name = name
    pipeline.run = MagicMock(return_value={"status": "success", "pipeline": name})
    return pipeline


def _make_mock_intent_router(intent="code"):
    """Create a mock intent router returning fixed intent."""
    router = MagicMock()
    router.detect_intent = MagicMock(return_value=intent)
    return router


# ---------------------------------------------------------------------------
# Scenario: Orchestrator dispatches SRE intent to SRE pipeline
# ---------------------------------------------------------------------------
def test_dispatch_sre_intent_to_sre_pipeline():
    Orchestrator = _get_orchestrator_class()
    if Orchestrator is None:
        pytest.skip("zsiga.orchestrator not yet implemented")

    sre_pipeline = _make_mock_pipeline("sre")
    code_pipeline = _make_mock_pipeline("code")
    router = _make_mock_intent_router("sre")

    orch = Orchestrator(intent_router=router, pipelines={"sre": sre_pipeline, "code": code_pipeline})
    orch.dispatch("检查磁盘空间")

    sre_pipeline.run.assert_called_once()
    code_pipeline.run.assert_not_called()


# ---------------------------------------------------------------------------
# Scenario: Orchestrator dispatches code intent to code pipeline
# ---------------------------------------------------------------------------
def test_dispatch_code_intent_to_code_pipeline():
    Orchestrator = _get_orchestrator_class()
    if Orchestrator is None:
        pytest.skip("zsiga.orchestrator not yet implemented")

    sre_pipeline = _make_mock_pipeline("sre")
    code_pipeline = _make_mock_pipeline("code")
    router = _make_mock_intent_router("code")

    orch = Orchestrator(intent_router=router, pipelines={"sre": sre_pipeline, "code": code_pipeline})
    orch.dispatch("修复这个函数的bug")

    code_pipeline.run.assert_called_once()
    sre_pipeline.run.assert_not_called()


# ---------------------------------------------------------------------------
# Scenario: Single dispatch — never both pipelines for one task
# ---------------------------------------------------------------------------
def test_single_dispatch_mutual_exclusivity():
    Orchestrator = _get_orchestrator_class()
    if Orchestrator is None:
        pytest.skip("zsiga.orchestrator not yet implemented")

    for intent_type in ["sre", "code"]:
        sre_pipeline = _make_mock_pipeline("sre")
        code_pipeline = _make_mock_pipeline("code")
        router = _make_mock_intent_router(intent_type)

        orch = Orchestrator(intent_router=router, pipelines={"sre": sre_pipeline, "code": code_pipeline})
        orch.dispatch("test task")

        total_calls = sre_pipeline.run.call_count + code_pipeline.run.call_count
        assert total_calls == 1, \
            f"Expected exactly 1 pipeline call for intent={intent_type}, got {total_calls}"


# ---------------------------------------------------------------------------
# Scenario: Code pipeline execution path preserved
# ---------------------------------------------------------------------------
def test_code_pipeline_path_preserved():
    Orchestrator = _get_orchestrator_class()
    if Orchestrator is None:
        pytest.skip("zsiga.orchestrator not yet implemented")

    sre_pipeline = _make_mock_pipeline("sre")
    code_pipeline = _make_mock_pipeline("code")
    router = _make_mock_intent_router("code")

    orch = Orchestrator(intent_router=router, pipelines={"sre": sre_pipeline, "code": code_pipeline})
    result = orch.dispatch("修复这个函数的bug")

    assert isinstance(result, dict), "Dispatch result must be a dict"
    assert result.get("pipeline") == "code", \
        f"Code dispatch should return code pipeline result, got {result}"
    assert result.get("status") == "success"


# ---------------------------------------------------------------------------
# Scenario: Orchestrator initializes with both pipelines
# ---------------------------------------------------------------------------
def test_orchestrator_initializes_with_both_pipelines():
    Orchestrator = _get_orchestrator_class()
    if Orchestrator is None:
        pytest.skip("zsiga.orchestrator not yet implemented")

    sre_pipeline = _make_mock_pipeline("sre")
    code_pipeline = _make_mock_pipeline("code")
    router = _make_mock_intent_router("code")

    # Should not raise
    orch = Orchestrator(intent_router=router, pipelines={"sre": sre_pipeline, "code": code_pipeline})
    assert orch is not None, "Orchestrator must initialize successfully"
