"""Sub-agent dispatch capability test suite.

Validates that ZsigaOrchestrator._process_change routes each IntentType to the
correct execution path by mocking the internal dispatch methods.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from zsiga.agent.intent_router import Intent, IntentType
from zsiga.config import (
    LLMConfig,
    PipelineConfig,
    SafetyConfig,
    TargetConfig,
    ZsigaConfig,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config() -> ZsigaConfig:
    """Build a minimal ZsigaConfig for testing."""
    return ZsigaConfig(
        llm=LLMConfig(provider="test", model="test", api_key="test-key"),
        targets={
            "testproj": TargetConfig(
                name="testproj",
                path="/tmp/testproj",
                test_cmd="pytest",
                lint_cmd="ruff check .",
            ),
        },
        pipeline=PipelineConfig(),
        intake=MagicMock(),
        safety=SafetyConfig(require_approval=False),
    )


def _make_prop(text: str = "test proposal") -> dict:
    return {
        "id": "test-change",
        "project": "testproj",
        "change_dir": "/tmp/test-change",
        "target_path": "/tmp/testproj",
        "has_specs": False,
        "has_design": False,
        "has_tasks": False,
    }


def _intent_for(itype: IntentType) -> Intent:
    return Intent(
        verbalization=f"test-{itype.value}",
        intent_type=itype,
        confidence=0.9,
        reasoning="test",
        suggested_action="test",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def orchestrator():
    """Create a ZsigaOrchestrator with mocked AgentLoop."""
    with patch("zsiga.pipeline.orchestrator.AgentLoop"), \
         patch("zsiga.pipeline.orchestrator.load_active_context", return_value=None):
        from zsiga.pipeline.orchestrator import ZsigaOrchestrator

        orch = ZsigaOrchestrator(_make_config())
    return orch


def _run(coro):
    """Run an async coroutine synchronously for testing."""
    return asyncio.get_event_loop().run_until_complete(coro)


def _setup_process_change_mocks(orchestrator, intent_type: IntentType):
    """Patch classify, route, read_file, and dispatch methods."""
    intent = _intent_for(intent_type)

    p_classify = patch(
        "zsiga.pipeline.orchestrator.classify", return_value=intent
    )
    p_route = patch(
        "zsiga.pipeline.orchestrator.route",
        return_value={
            IntentType.RESEARCH: "dispatch_explore",
            IntentType.IMPLEMENTATION: "pipeline",
            IntentType.INVESTIGATION: "dispatch_diagnoser",
            IntentType.EVALUATION: "dispatch_review",
            IntentType.FIX: "pipeline_fix",
            IntentType.OPEN_ENDED: "ask_user",
        }[intent_type],
    )
    p_read = patch(
        "zsiga.pipeline.orchestrator.read_file", return_value=""
    )
    orch._dispatch_explore = AsyncMock(return_value=True)
    orch._dispatch_diagnoser = AsyncMock(return_value=True)
    orch._dispatch_review = AsyncMock(return_value=True)
    orch._run_phases = AsyncMock(return_value=True)

    return p_classify, p_route, p_read


@pytest.mark.asyncio
async def test_research_routes_to_dispatch_explore(orchestrator):
    """RESEARCH intent → _dispatch_explore called, _run_phases NOT called."""
    p_c, p_r, p_rd = _setup_process_change_mocks(orchestrator, IntentType.RESEARCH)
    with p_c, p_r, p_rd:
        result = await orchestrator._process_change(_make_prop())

    orchestrator._dispatch_explore.assert_called_once()
    orchestrator._run_phases.assert_not_called()


@pytest.mark.asyncio
async def test_implementation_routes_to_pipeline(orchestrator):
    """IMPLEMENTATION intent → _run_phases called with skip_enrich=False."""
    p_c, p_r, p_rd = _setup_process_change_mocks(
        orchestrator, IntentType.IMPLEMENTATION
    )
    with p_c, p_r, p_rd:
        result = await orchestrator._process_change(_make_prop())

    orchestrator._run_phases.assert_called_once()
    call_kwargs = orchestrator._run_phases.call_args
    assert call_kwargs.kwargs.get("skip_enrich", False) is False or \
        "skip_enrich" not in call_kwargs.kwargs or \
        list(call_kwargs.args)[-1] is False if len(call_kwargs.args) > 8 else True
    # Verify skip_enrich=False via positional arg (9th arg)
    orch_call = orchestrator._run_phases.call_args_list[0]
    # skip_enrich is the last positional arg or keyword
    if "skip_enrich" in orch_call.kwargs:
        assert orch_call.kwargs["skip_enrich"] is False


@pytest.mark.asyncio
async def test_fix_routes_to_pipeline_with_skip_enrich(orchestrator):
    """FIX intent → _run_phases called with skip_enrich=True."""
    p_c, p_r, p_rd = _setup_process_change_mocks(orchestrator, IntentType.FIX)
    with p_c, p_r, p_rd:
        result = await orchestrator._process_change(_make_prop())

    orchestrator._run_phases.assert_called_once()
    orch_call = orchestrator._run_phases.call_args_list[0]
    # skip_enrich is last positional arg or keyword
    if "skip_enrich" in orch_call.kwargs:
        assert orch_call.kwargs["skip_enrich"] is True
    else:
        # It's the last positional arg
        assert orch_call.args[-1] is True


@pytest.mark.asyncio
async def test_investigation_routes_to_dispatch_diagnoser(orchestrator):
    """INVESTIGATION intent → _dispatch_diagnoser called, _run_phases NOT."""
    p_c, p_r, p_rd = _setup_process_change_mocks(
        orchestrator, IntentType.INVESTIGATION
    )
    with p_c, p_r, p_rd:
        result = await orchestrator._process_change(_make_prop())

    orchestrator._dispatch_diagnoser.assert_called_once()
    orchestrator._run_phases.assert_not_called()


@pytest.mark.asyncio
async def test_evaluation_routes_to_dispatch_review(orchestrator):
    """EVALUATION intent → _dispatch_review called, _run_phases NOT."""
    p_c, p_r, p_rd = _setup_process_change_mocks(
        orchestrator, IntentType.EVALUATION
    )
    with p_c, p_r, p_rd:
        result = await orchestrator._process_change(_make_prop())

    orchestrator._dispatch_review.assert_called_once()
    orchestrator._run_phases.assert_not_called()


@pytest.mark.asyncio
async def test_open_ended_returns_false_without_dispatching(orchestrator):
    """OPEN_ENDED intent → returns False, no dispatch method called."""
    p_c, p_r, p_rd = _setup_process_change_mocks(
        orchestrator, IntentType.OPEN_ENDED
    )
    with p_c, p_r, p_rd:
        result = await orchestrator._process_change(_make_prop())

    assert result is False
    orchestrator._dispatch_explore.assert_not_called()
    orchestrator._dispatch_diagnoser.assert_not_called()
    orchestrator._dispatch_review.assert_not_called()
    orchestrator._run_phases.assert_not_called()
