import tempfile
from pathlib import Path

import pytest

from zsiga.agent.sub_agent import (
    _filter_tools_by_role,
    create_sub_agent,
    run_parallel,
    SubAgentResult,
)
from zsiga.agent.tools import register_tools
from zsiga.transport import LocalTransport


def _make_project(tmpdir: str) -> str:
    app = Path(tmpdir) / "app.py"
    app.write_text("def hello():\n    return 'hello'\n")
    return tmpdir


@pytest.mark.asyncio
async def test_create_sub_agent():
    agent = create_sub_agent("fake-key", "glm-5.1")
    assert agent.compaction_enabled is False
    assert agent.compaction_threshold == 999999


@pytest.mark.asyncio
async def test_run_sub_agent_registers_tools():
    with tempfile.TemporaryDirectory() as tmpdir:
        _make_project(tmpdir)
        agent = create_sub_agent("fake-key", "glm-5.1")
        t = LocalTransport()
        register_tools(agent, tmpdir, transport=t)
        tool_names = [t["function"]["name"] for t in agent.tools]
        assert "bash" in tool_names
        assert "read_file" in tool_names
        assert "write_file" in tool_names


def test_filter_tools_by_role_uses_function_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = create_sub_agent("fake-key", "glm-5.1")
        register_tools(agent, tmpdir, transport=LocalTransport())
        _filter_tools_by_role(agent, ["read_file"])
        tool_names = [t["function"]["name"] for t in agent.tools]
        assert tool_names == ["read_file"]
        assert set(agent.tool_funcs) == {"read_file"}


@pytest.mark.asyncio
async def test_run_parallel_empty():
    results = await run_parallel(
        api_key="fake-key",
        model="glm-5.1",
        base_url=None,
        proxy=None,
        target_path="/tmp",
        transport=LocalTransport(),
        tasks=[],
    )
    assert results == []


@pytest.mark.asyncio
async def test_run_parallel_results_length():
    results = await run_parallel(
        api_key="fake-key",
        model="glm-5.1",
        base_url=None,
        proxy=None,
        target_path="/tmp",
        transport=LocalTransport(),
        tasks=["task 1", "task 2"],
        max_turns_per_task=1,
        timeout_per_task=5,
    )
    assert len(results) == 2
    for r in results:
        assert isinstance(r, SubAgentResult)


@pytest.mark.asyncio
async def test_sub_agent_result_fields():
    r = SubAgentResult(content="done", llm_calls=2, tool_calls=1, success=True)
    assert r.success is True
    assert r.llm_calls == 2
