# L5 Parallel Background Explore Agent Pool

## ADDED Requirements

### REQ-PP-01: Agent Pool Lifecycle

The system SHALL maintain a configurable pool of explore-role sub-agents that can be dispatched in parallel (2–5 agents concurrently) during the ENRICH phase.

#### Scenario: Pool dispatches multiple explore agents in parallel
- Given a change proposal with multiple exploration tasks
- When the ENRICH phase begins
- Then the system SHALL create up to `max_concurrency` explore-role agents (configurable, default 3, range 2–5)
- And each agent SHALL receive a distinct task instruction derived from the proposal
- And all agents SHALL execute concurrently via asyncio

#### Scenario: Pool respects concurrency limit
- Given `max_concurrency` is set to 3
- And 5 exploration tasks are queued
- When dispatch_many is called
- Then at most 3 agents SHALL run simultaneously
- And the remaining 2 SHALL start as earlier agents complete

### REQ-PP-02: dispatch_many Interface

The system SHALL expose a `dispatch_many(tasks: list[str])` function that accepts a list of exploration task instructions and returns a handle for collecting results.

#### Scenario: Dispatch with valid task list
- Given a list of 3 task instructions
- When `dispatch_many(tasks)` is called
- Then the system SHALL return a `PoolHandle` object immediately (non-blocking)
- And the handle SHALL track the dispatch status of all tasks

#### Scenario: Dispatch with empty task list
- Given an empty task list
- When `dispatch_many([])` is called
- Then the system SHALL return a `PoolHandle` with zero pending tasks
- And `collect_all()` on this handle SHALL return an empty list immediately

### REQ-PP-03: collect_all Result Aggregation

The system SHALL expose a `collect_all(handle: PoolHandle) -> list[SubAgentResult]` async function that waits for all dispatched agents to complete and returns results in original task order.

#### Scenario: All agents succeed
- Given 3 tasks were dispatched
- When `collect_all(handle)` is called
- Then the system SHALL await completion of all 3 agents (up to per-task timeout)
- And return a `list[SubAgentResult]` of length 3, ordered by original task index

#### Scenario: One agent times out
- Given 3 tasks were dispatched
- And task #2 exceeds its timeout
- When `collect_all(handle)` is called
- Then the system SHALL return 3 results
- And result #2 SHALL have `success=False` and content containing "TIMEOUT"
- And results #1 and #3 SHALL reflect their actual outcomes

#### Scenario: One agent raises an exception
- Given 3 tasks were dispatched
- And task #1 raises an unexpected exception
- When `collect_all(handle)` is called
- Then the system SHALL return 3 results
- And result #1 SHALL have `success=False` and content containing "SUB_AGENT_ERROR"
- And results #2 and #3 SHALL reflect their actual outcomes

### REQ-PP-04: Orchestrator ENRICH Phase Integration

The ENRICH phase of the pipeline SHALL be enhanced to optionally use the parallel explore pool for project context enrichment before the main enrich agent run.

#### Scenario: ENRICH phase uses parallel exploration
- Given a change proposal in the ENRICH phase
- And `pipeline.enrich_parallel_explore` is enabled in config (default: false)
- When the ENRICH phase starts
- Then the system SHALL derive 2–5 exploration tasks from the proposal and project context
- And dispatch them via `dispatch_many`
- And collect results via `collect_all`
- And concatenate the exploration results into a supplementary context block
- And provide this block to the main enrich agent as additional project context

#### Scenario: ENRICH phase falls back to single-agent when disabled
- Given `pipeline.enrich_parallel_explore` is disabled
- When the ENRICH phase starts
- Then the system SHALL use the existing single-agent enrich flow unchanged

### REQ-PP-05: Configurable Pool Parameters

The parallel explore pool parameters SHALL be configurable via `zsiga.yaml`.

#### Scenario: Custom pool configuration
- Given `zsiga.yaml` contains:
  ```yaml
  pipeline:
    enrich_parallel_explore: true
    explore_pool:
      max_concurrency: 3
      max_turns_per_task: 5
      timeout_per_task: 120
  ```
- When the config is loaded
- Then `PipelineConfig` SHALL expose `enrich_parallel_explore=True`
- And `explore_pool_max_concurrency=3`
- And `explore_pool_max_turns=5`
- And `explore_pool_timeout=120`

#### Scenario: Default pool configuration
- Given `zsiga.yaml` does not contain `explore_pool` section
- When the config is loaded
- Then defaults SHALL be: `max_concurrency=3`, `max_turns_per_task=5`, `timeout_per_task=120`

### REQ-PP-06: Explore Task Derivation

The system SHALL derive focused exploration tasks from the proposal text to feed into the parallel pool.

#### Scenario: Derive tasks from a feature proposal
- Given a proposal titled "添加用户认证模块"
- When exploration tasks are derived
- Then the system SHALL produce 2–5 task instructions covering different aspects (e.g., "查找现有的认证相关代码", "搜索项目中间件和路由模式", "查找测试框架和测试工具配置")
- And each task instruction SHALL be specific enough for an explore-role agent to execute in ≤5 turns

### REQ-PP-07: Pool Metrics and Logging

The parallel explore pool SHALL log dispatch, completion, and error events for observability.

#### Scenario: Pool logs dispatch and results
- Given 3 tasks are dispatched
- When `dispatch_many` is called
- Then the system SHALL print "  🔍 Dispatching 3 explore agents (concurrency=3)..."
- When each agent completes
- Then the system SHALL print "  🔍 explore-agent #N done (X.Xs, success=True/False)"
- When `collect_all` finishes
- Then the system SHALL print "  🔍 Explore pool complete: 3/3 succeeded (total X.Xs)"
