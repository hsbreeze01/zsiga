# Tasks: L5 Parallel Background Explore Agent Pool

## Group 1: Core Pool Infrastructure (sub_agent.py)

- [ ] 1.1 Add `PoolHandle` dataclass and implement `dispatch_many()` / `collect_all()` in `zsiga/agent/sub_agent.py`
  - `PoolHandle` holds tasks list, the asyncio gather future, and max_concurrency
  - `dispatch_many(tasks, api_key, model, base_url, proxy, target_path, transport, max_concurrency, max_turns_per_task, timeout_per_task)` creates explore-role agents and returns `PoolHandle`
  - `collect_all(handle)` awaits completion, returns ordered `list[SubAgentResult]`
  - Reuses `create_with_role("explore", ...)` and `run_sub_agent` internally
  - Logs dispatch/completion events per REQ-PP-07

## Group 2: Configuration (config.py)

- [ ] 2.1 Add parallel explore pool config fields to `PipelineConfig` and `load_config`
  - Add `enrich_parallel_explore: bool = False`
  - Add `explore_pool_max_concurrency: int = 3`
  - Add `explore_pool_max_turns: int = 5`
  - Add `explore_pool_timeout: int = 120`
  - Parse from `pipeline.explore_pool.*` and `pipeline.enrich_parallel_explore` in `load_config`

## Group 3: Task Derivation (enricher.py)

- [ ] 3.1 Implement `derive_explore_tasks(proposal_text: str) -> list[str]` in `zsiga/pipeline/enricher.py`
  - Extracts keywords from proposal title/first line
  - Generates 2–5 focused explore instructions covering: existing code search, directory structure, test patterns, dependency/tech stack, data models
  - Pure function, no LLM calls, deterministic output

## Group 4: ENRICH Phase Integration (enricher.py + orchestrator.py)

- [ ] 4.1 Modify `enrich()` to optionally run parallel explore pool before main agent
  - When `enrich_parallel_explore` is enabled: call `derive_explore_tasks`, `dispatch_many`, `collect_all`
  - Concatenate successful explore results into `supplementary_context` string
  - Inject `supplementary_context` into the user prompt for the main enrich agent
  - When disabled: existing flow unchanged (zero behavioral change)

## Group 5: Tests

- [ ] 5.1 Add unit tests for pool infrastructure (`tests/test_sub_agent.py` or new `tests/test_l5_parallel.py`)
  - Test `dispatch_many` with empty list returns handle with no pending
  - Test `collect_all` returns results in original order
  - Test `collect_all` handles timeout (SubAgentResult with success=False)
  - Test `collect_all` handles exception (SubAgentResult with SUB_AGENT_ERROR)
  - Test concurrency limit is respected (at most N running simultaneously)

- [ ] 5.2 Add unit tests for `derive_explore_tasks` in `tests/test_l5_parallel.py`
  - Test returns 2–5 tasks for a non-empty proposal
  - Test returns at least 2 tasks for a minimal proposal
  - Test tasks mention relevant keywords from proposal

- [ ] 5.3 Add config parsing test in `tests/test_l5_parallel.py`
  - Test default values when `explore_pool` section absent
  - Test custom values parsed correctly from YAML
