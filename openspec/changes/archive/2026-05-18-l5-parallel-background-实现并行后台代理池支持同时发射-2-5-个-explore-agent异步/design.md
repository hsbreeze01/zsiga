# Design: L5 Parallel Background Explore Agent Pool

## Architecture Decision

### Approach: Extend existing `run_parallel` with a `PoolHandle` abstraction

The project already has `run_parallel()` in `zsiga/agent/sub_agent.py` that uses `asyncio.Semaphore` + `asyncio.gather`. Rather than replacing it, we wrap it with a `PoolHandle` / `dispatch_many` / `collect_all` API that provides:

1. **Non-blocking dispatch** — `dispatch_many` fires off tasks and returns a handle immediately
2. **Ordered result collection** — `collect_all` awaits all results and returns them in original task order
3. **Task derivation** — a pure function that converts proposal text into focused explore instructions

### Why not threads?

All existing sub-agent infrastructure (`AgentLoop.run`, `run_sub_agent`) is `async`. Using `asyncio` keeps the pool compatible with the event loop already running in `ZsigaOrchestrator.run_cycle`.

### Why PoolHandle pattern?

Separating dispatch from collection allows the orchestrator to do other work (e.g., prefetch mechanical data) while explore agents run. Even though the current ENRICH flow awaits immediately, the API is ready for future pipelining.

## Data Flow

```
proposal.md
    │
    ▼
derive_explore_tasks(proposal_text, project_name) → list[str]  (2-5 instructions)
    │
    ▼
dispatch_many(tasks, config, transport) → PoolHandle
    │  (creates N explore-role agents, runs via asyncio.gather)
    │
    ▼
collect_all(handle) → list[SubAgentResult]
    │
    ▼
Concatenate successful results → supplementary_context string
    │
    ▼
ENRICH agent receives: project_context + supplementary_context
```

## Files to Modify

| File | Change |
|------|--------|
| `zsiga/agent/sub_agent.py` | Add `PoolHandle` dataclass, `dispatch_many()`, `collect_all()` functions |
| `zsiga/config.py` | Add `enrich_parallel_explore`, `explore_pool_max_concurrency`, `explore_pool_max_turns`, `explore_pool_timeout` to `PipelineConfig` |
| `zsiga/pipeline/enricher.py` | Add `derive_explore_tasks()` function; modify `enrich()` to optionally run parallel explore before main agent |
| `zsiga/pipeline/orchestrator.py` | Pass pool config through to enrich phase |
| `tests/test_sub_agent.py` | Add tests for `PoolHandle`, `dispatch_many`, `collect_all` |
| `tests/test_l5_parallel.py` | New test file for pool-specific scenarios (task derivation, error handling) |

## Key Design Details

### PoolHandle

```python
@dataclass
class PoolHandle:
    tasks: list[str]
    pending: asyncio.Task  # the asyncio.gather handle
    max_concurrency: int
```

### dispatch_many

- Creates individual explore-role agents via `create_with_role("explore", ...)`
- Uses `asyncio.Semaphore(max_concurrency)` to bound concurrency (same pattern as existing `run_parallel`)
- Wraps each agent run in `_bounded_explore()` that catches exceptions and returns `SubAgentResult`
- Returns `PoolHandle` immediately

### collect_all

- Awaits the `pending` task from the handle
- Unpacks indexed results into ordered list
- Returns `list[SubAgentResult]`
- Logs per-agent and aggregate metrics

### derive_explore_tasks

Pure function that inspects proposal text and generates 2–5 focused exploration instructions:
1. "搜索项目中与 {proposal_keywords} 相关的现有代码和模块"
2. "查找项目的目录结构、入口文件、配置文件模式"
3. "搜索项目中与 {proposal_keywords} 相关的测试文件和测试模式"
4. "查找项目的依赖管理和技术栈（requirements.txt, pyproject.toml, package.json 等）"
5. "搜索项目中与 {proposal_keywords} 相关的数据库模型和数据结构"

Always returns at least 2 tasks, at most 5.

### Config additions to PipelineConfig

```yaml
pipeline:
  enrich_parallel_explore: false   # opt-in
  explore_pool:
    max_concurrency: 3
    max_turns_per_task: 5
    timeout_per_task: 120
```

Mapped to flat attributes on `PipelineConfig` for consistency with existing pattern.

## Backward Compatibility

- **Default off**: `enrich_parallel_explore` defaults to `false`. Existing behavior is unchanged unless explicitly enabled.
- **No API breakage**: Existing `run_parallel()` function remains untouched. New `dispatch_many`/`collect_all` are additive.
- **No new dependencies**: Uses only `asyncio` (already imported in `sub_agent.py`).
