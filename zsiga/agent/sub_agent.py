import asyncio
import time
from dataclasses import dataclass

from .loop import AgentLoop
from .roles import Role, get_role_config
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
    provider: str = "zhipuai",
) -> AgentLoop:
    agent = AgentLoop(
        api_key=api_key,
        model=model,
        base_url=base_url,
        proxy=proxy,
        compaction_enabled=False,
        compaction_threshold=999999,
        compaction_keep_recent=999,
        provider=provider,
    )
    return agent


def create_with_role(
    role: str,
    api_key: str,
    model: str,
    base_url: str = None,
    proxy: str = None,
    provider: str = "zhipuai",
) -> AgentLoop:
    r = Role(role)
    config = get_role_config(r)
    agent = create_sub_agent(api_key, model, base_url, proxy, provider=provider)
    agent._role_config = config
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
    role_config = getattr(agent, "_role_config", None)

    if role_config:
        _filter_tools_by_role(agent, role_config.allowed_tools)
        effective_max_turns = min(max_turns, role_config.max_turns)
        system_prompt = role_config.system_prompt
        agent.set_phase(f"sub-agent:{role_config.name}")
    else:
        effective_max_turns = max_turns
        system_prompt = "你是 zsiga 的子 agent。精确执行分配给你的任务，完成后简洁报告结果。"
        agent.set_phase("sub-agent")

    start = time.monotonic()
    result = await agent.run(
        system_prompt=system_prompt,
        user_prompt=task_instruction,
        max_turns=effective_max_turns,
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


def _filter_tools_by_role(agent: AgentLoop, allowed: list[str]):
    agent.tools = [t for t in agent.tools if t.get("name") in allowed]
    agent.tool_funcs = {k: v for k, v in agent.tool_funcs.items() if k in allowed}


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


# ---------------------------------------------------------------------------
# L5: Parallel Explore Agent Pool (PoolHandle / dispatch_many / collect_all)
# ---------------------------------------------------------------------------

@dataclass
class PoolHandle:
    """Opaque handle returned by dispatch_many; passed to collect_all."""

    tasks: list[str]
    pending: asyncio.Task | None
    max_concurrency: int


def dispatch_many(
    tasks: list[str],
    api_key: str,
    model: str,
    base_url: str = None,
    proxy: str = None,
    target_path: str = "/tmp",
    transport: Transport | None = None,
    max_concurrency: int = 3,
    max_turns_per_task: int = 5,
    timeout_per_task: int = 120,
) -> PoolHandle:
    """Create explore-role agents for *tasks* and return a PoolHandle immediately.

    The agents are scheduled on the running event loop via ``asyncio.ensure_future``.
    Callers later call ``await collect_all(handle)`` to retrieve ordered results.
    """
    from ..transport import LocalTransport

    if transport is None:
        transport = LocalTransport()

    if not tasks:
        return PoolHandle(tasks=tasks, pending=None, max_concurrency=max_concurrency)

    sem = asyncio.Semaphore(max_concurrency)

    async def _bounded_explore(
        idx: int, instruction: str
    ) -> tuple[int, SubAgentResult]:
        async with sem:
            agent = create_with_role("explore", api_key, model, base_url, proxy)
            result = await run_sub_agent(
                agent,
                target_path,
                transport,
                instruction,
                max_turns=max_turns_per_task,
                timeout_seconds=timeout_per_task,
            )
            return idx, result

    coros = [_bounded_explore(i, task) for i, task in enumerate(tasks)]

    print(
        f"  🔍 Dispatching {len(tasks)} explore agents "
        f"(concurrency={max_concurrency})..."
    )

    pending = asyncio.ensure_future(asyncio.gather(*coros, return_exceptions=True))

    return PoolHandle(tasks=tasks, pending=pending, max_concurrency=max_concurrency)


async def collect_all(handle: PoolHandle) -> list[SubAgentResult]:
    """Await all dispatched agents and return results in original task order."""
    if handle.pending is None:
        return []

    indexed_results = await handle.pending
    n = len(handle.tasks)
    results: list[SubAgentResult] = [None] * n
    succeeded = 0

    for item in indexed_results:
        if isinstance(item, Exception):
            idx = indexed_results.index(item)
            results[idx] = SubAgentResult(
                content=f"SUB_AGENT_ERROR: {item}",
                success=False,
            )
            print(
                f"  🔍 explore-agent #{idx + 1} done "
                f"(error, SUB_AGENT_ERROR)"
            )
        else:
            idx, result = item
            results[idx] = result
            elapsed = result.elapsed_seconds
            print(
                f"  🔍 explore-agent #{idx + 1} done "
                f"({elapsed:.1f}s, success={result.success})"
            )
            if result.success:
                succeeded += 1

    total_elapsed = sum(r.elapsed_seconds for r in results if r is not None)
    print(
        f"  🔍 Explore pool complete: "
        f"{succeeded}/{n} succeeded (total {total_elapsed:.1f}s)"
    )

    return results

# ---------------------------------------------------------------------------
# Multi-role parallel dispatch (supports different roles per task)
# ---------------------------------------------------------------------------

@dataclass
class MultiRoleHandle:
    """Opaque handle for multi-role dispatch; pass to collect_multi_role."""
    tasks: list[dict]          # Each: {"role": "scout", "instruction": "..."}
    pending: asyncio.Task | None
    max_concurrency: int


def dispatch_multi_role(
    tasks: list[dict],
    api_key: str,
    model: str,
    base_url: str = None,
    proxy: str = None,
    target_path: str = "/tmp",
    transport: Transport | None = None,
    max_concurrency: int = 3,
    max_turns_per_task: int = 5,
    timeout_per_task: int = 120,
) -> MultiRoleHandle:
    """Create agents with different roles for *tasks* and return a MultiRoleHandle.

    Each task dict must have:
      - "role": str — one of the Role enum values (e.g. "scout", "analyst", "steward")
      - "instruction": str — the task instruction for the agent

    Optional per-task overrides:
      - "max_turns": int — override max_turns_per_task for this specific task
      - "timeout": int — override timeout_per_task for this specific task
    """
    from ..transport import LocalTransport

    if transport is None:
        transport = LocalTransport()

    if not tasks:
        return MultiRoleHandle(tasks=tasks, pending=None, max_concurrency=max_concurrency)

    sem = asyncio.Semaphore(max_concurrency)

    async def _bounded_multi_role(
        idx: int, task_spec: dict
    ) -> tuple[int, SubAgentResult]:
        async with sem:
            role_name = task_spec["role"]
            instruction = task_spec["instruction"]
            task_max_turns = task_spec.get("max_turns", max_turns_per_task)
            task_timeout = task_spec.get("timeout", timeout_per_task)

            agent = create_with_role(role_name, api_key, model, base_url, proxy)
            result = await run_sub_agent(
                agent,
                target_path,
                transport,
                instruction,
                max_turns=task_max_turns,
                timeout_seconds=task_timeout,
            )
            return idx, result

    coros = [_bounded_multi_role(i, task) for i, task in enumerate(tasks)]

    role_names = [t.get("role", "?") for t in tasks]
    print(
        f"  🚀 Dispatching {len(tasks)} multi-role agents "
        f"(roles: {', '.join(role_names)}, concurrency={max_concurrency})..."
    )

    pending = asyncio.ensure_future(asyncio.gather(*coros, return_exceptions=True))

    return MultiRoleHandle(tasks=tasks, pending=pending, max_concurrency=max_concurrency)


async def collect_multi_role(handle: MultiRoleHandle) -> list[SubAgentResult]:
    """Await all dispatched multi-role agents and return results in original task order."""
    if handle.pending is None:
        return []

    indexed_results = await handle.pending
    n = len(handle.tasks)
    results: list[SubAgentResult] = [None] * n
    succeeded = 0

    for item in indexed_results:
        if isinstance(item, Exception):
            idx = indexed_results.index(item)
            results[idx] = SubAgentResult(
                content=f"SUB_AGENT_ERROR: {item}",
                success=False,
            )
            print(
                f"  🚀 multi-role-agent #{idx + 1} ({handle.tasks[idx].get('role', '?')}) done "
                f"(error)"
            )
        else:
            idx, result = item
            results[idx] = result
            elapsed = result.elapsed_seconds
            role = handle.tasks[idx].get("role", "?")
            print(
                f"  🚀 multi-role-agent #{idx + 1} ({role}) done "
                f"({elapsed:.1f}s, success={result.success})"
            )
            if result.success:
                succeeded += 1

    total_elapsed = sum(r.elapsed_seconds for r in results if r is not None)
    print(
        f"  🚀 Multi-role pool complete: "
        f"{succeeded}/{n} succeeded (total {total_elapsed:.1f}s)"
    )

    return results
