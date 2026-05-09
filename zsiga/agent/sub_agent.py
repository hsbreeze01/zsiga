import asyncio
import json
import time
from dataclasses import dataclass, field

from .loop import AgentLoop, RunResult
from .tools import register_tools
from ..transport import Transport


@dataclass
class SubAgentResult:
    content: str
    llm_calls: int = 0
    tool_calls: int = 0
    success: bool = True
    prompt_tokens: int = 0
    completion_tokens: int = 0
    elapsed_seconds: float = 0.0


def create_sub_agent(
    api_key: str,
    model: str,
    base_url: str = None,
    proxy: str = None,
) -> AgentLoop:
    agent = AgentLoop(
        api_key=api_key,
        model=model,
        base_url=base_url,
        proxy=proxy,
        compaction_enabled=False,
        compaction_threshold=999999,
        compaction_keep_recent=999,
    )
    return agent


async def run_sub_agent(
    agent: AgentLoop,
    target_path: str,
    transport: Transport,
    task_instruction: str,
    max_turns: int = 15,
    timeout_seconds: int = 600,
) -> SubAgentResult:
    register_tools(agent, target_path, transport=transport)
    agent.set_phase("sub-agent")

    start = time.monotonic()
    result = await agent.run(
        system_prompt="你是 zsiga 的子 agent。精确执行分配给你的任务，完成后简洁报告结果。",
        user_prompt=task_instruction,
        max_turns=max_turns,
        timeout_seconds=timeout_seconds,
    )
    elapsed = time.monotonic() - start

    success = result.content not in ("TIMEOUT", "MAX_TURNS_REACHED")

    return SubAgentResult(
        content=result.content,
        llm_calls=result.llm_calls,
        tool_calls=result.tool_calls,
        success=success,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        elapsed_seconds=elapsed,
    )


async def run_parallel(
    api_key: str,
    model: str,
    base_url: str,
    proxy: str,
    target_path: str,
    transport: Transport,
    tasks: list[str],
    max_concurrency: int = 2,
    max_turns_per_task: int = 15,
    timeout_per_task: int = 600,
) -> list[SubAgentResult]:
    sem = asyncio.Semaphore(max_concurrency)

    async def _bounded_run(idx: int, instruction: str) -> tuple[int, SubAgentResult]:
        async with sem:
            agent = create_sub_agent(api_key, model, base_url, proxy)
            result = await run_sub_agent(
                agent, target_path, transport, instruction,
                max_turns=max_turns_per_task,
                timeout_seconds=timeout_per_task,
            )
            return idx, result

    coros = [_bounded_run(i, task) for i, task in enumerate(tasks)]
    indexed_results = await asyncio.gather(*coros, return_exceptions=True)

    results: list[SubAgentResult] = [None] * len(tasks)
    for item in indexed_results:
        if isinstance(item, Exception):
            idx = indexed_results.index(item)
            results[idx] = SubAgentResult(
                content=f"SUB_AGENT_ERROR: {item}",
                success=False,
            )
        else:
            idx, result = item
            results[idx] = result

    return results
