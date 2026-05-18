# Design: L4 Orchestrator Integration

## Overview

This change integrates three existing but disconnected modules into the orchestrator pipeline:

1. **Intent Router** (`zsiga/agent/intent_router.py`) → classified at the top of `_process_change()`
2. **Task Decomposer** (`zsiga/agent/task_decomposer.py`) → used in `run_cycle()` for cross-project proposals
3. **Escalation Manager** (`zsiga/agent/escalation.py`) → wraps the fix loops in `_run_phases()`

All three modules already exist with full data models and unit tests. This change only adds the **glue code** in `orchestrator.py` to call them at the right lifecycle points.

## Architecture Decisions

### AD-1: Intent classification as Phase 0 (before ENRICH)

- Call `intent_router.classify(proposal_text)` at the top of `_process_change()`
- Route to the appropriate path based on `route(intent)` result
- Only `IMPLEMENTATION` and `AMBIGUOUS` proceed to the standard pipeline
- `EXPLORATION` and `TRIVIAL` log the classification and skip (return `False`)
- **Rationale**: Keeps classification cheap (regex-only, no LLM) and early. Matches the L4 milestone's `intent_router` deliverable.

### AD-2: Task decomposition in `run_cycle()`, not `_process_change()`

- Add a new method `_process_cross_project()` in the orchestrator
- Called from `run_cycle()` when a proposal's content matches multiple target projects via `task_decomposer.decompose()`
- Each subtask in the decomposition maps to a synthetic proposal dict processed by `_process_change()`
- Results aggregated via `task_decomposer.aggregate_results()`
- **Rationale**: `run_cycle()` already iterates over proposals — decomposition is a layer above individual change processing. Single-project proposals bypass decomposition entirely.

### AD-3: Escalation manager wrapping both fix loops

- Create `EscalationManager` at the top of `_run_phases()`, passing `change_dir` as `persist_dir`
- Record failures from both `_fix_loop()` and `_eval_fix_loop()` to the same manager
- When `should_escalate()` is `True`, modify fix prompts to include "try a different approach" instructions
- When `should_abort()` is `True`, generate diagnosis report, revert, record lesson, and return `False`
- **Rationale**: Both fix loops already have `max_attempts` caps. Escalation adds strategy awareness on top — if the same approach fails 3 times, try differently. This matches the L4 milestone's `escalation_protocol` deliverable.

### AD-4: Escalation-aware fix prompt variation

- When `next_strategy == Strategy.DIFFERENT_APPROACH`: add "Try a fundamentally different approach. Your previous strategy failed multiple times." to the fix system prompt
- When `next_strategy == Strategy.SIMPLIFY`: add "Simplify the fix. Remove complexity rather than adding more code."
- When `next_strategy == Strategy.SKIP`: equivalent to abort (handled by `should_abort()`)

## Data Flow

```
run_cycle()
  │
  ├─ scan proposals (existing)
  │
  ├─ for each proposal:
  │   ├─ intent = classify(proposal_text)        ← NEW (REQ-IR-01)
  │   ├─ route(intent) == "pipeline"?            ← NEW (REQ-IR-01)
  │   │   └─ NO → log + skip
  │   │
  │   ├─ decompose(proposal_text, projects)       ← NEW (REQ-TD-01, only if multi-project)
  │   │   └─ for each subtask: _process_change()
  │   │   └─ aggregate_results()                  ← NEW (REQ-TD-03)
  │   │
  │   └─ _process_change(prop) → _run_phases(...)
  │       │
  │       ├─ escalation = EscalationManager(...)   ← NEW (REQ-ES-01)
  │       │
  │       ├─ Phase 1: ENRICH (existing)
  │       ├─ Phase 2: IMPLEMENT + _fix_loop
  │       │   └─ escalation.record_failure()       ← NEW (REQ-ES-02)
  │       │   └─ if should_escalate: altered prompt ← NEW (REQ-ES-03)
  │       │   └─ if should_abort: diagnosis + revert ← NEW (REQ-ES-04)
  │       │
  │       ├─ Phase 3: VERIFY + _eval_fix_loop
  │       │   └─ escalation.record_failure()       ← NEW (REQ-ES-05)
  │       │   └─ if should_abort: diagnosis + revert ← NEW (REQ-ES-04)
  │       │
  │       └─ Phase 4: DELIVER (existing)
  │
  └─ _update_memory() (existing)
```

## Files to Modify

| File | Change Type | Description |
|------|------------|-------------|
| `zsiga/pipeline/orchestrator.py` | MODIFIED | Add intent classification, task decomposition dispatch, escalation integration |

## Files NOT Modified

| File | Reason |
|------|--------|
| `zsiga/agent/intent_router.py` | Already complete, just needs to be called |
| `zsiga/agent/task_decomposer.py` | Already complete, just needs to be called |
| `zsiga/agent/escalation.py` | Already complete, just needs to be called |
| `zsiga/__main__.py` | No new commands needed — integration is internal |
| `zsiga/config.py` | No new config fields needed |
| `tests/test_l4_capabilities.py` | Existing tests cover module units; new integration tests will be added |

## New Test File

| File | Description |
|------|-------------|
| `tests/test_l4_integration.py` | Integration tests for orchestrator calling intent_router, task_decomposer, and escalation |
