# Design: Token Budget Manager

## Architecture Decision

Introduce a `TokenBudget` class as a stateful budget tracker that lives within the `AgentLoop.run()` scope. This replaces the current fixed-interval compaction trigger (`turn % 3 == 0`) with a budget-aware, proactive compaction mechanism.

**Why a dedicated class instead of inline logic?**
- Single Responsibility: budget tracking, limit enforcement, and compaction signaling are separate concerns from the main loop orchestration
- Testability: budget logic can be unit-tested independently of the LLM client and tool execution
- Configurability: all budget parameters flow from `CompactionConfig` through a single object

## Data Flow

```
zsiga.yaml
  └─ pipeline.compaction (total_budget, per_turn_limit, compaction_ratio)
       └─ CompactionConfig (extended with new fields)
            └─ AgentLoop.__init__()
                 └─ TokenBudget(total_budget, per_turn_limit, compaction_threshold, compaction_ratio)
                      │
                      └─ AgentLoop.run()
                           │
                           ├─ Before LLM call: budget.should_compact(messages, estimate_tokens)
                           │    └─ if True → compact_messages(...)
                           │
                           ├─ After LLM call: budget.record(prompt_tokens, completion_tokens)
                           │    ├─ checks per_turn exceeded
                           │    └─ checks session exceeded
                           │
                           └─ If exceeded → return RunResult("BUDGET_EXCEEDED", ...)
```

## New File

### `zsiga/agent/token_budget.py`

```python
class TokenBudget:
    """Tracks cumulative token usage and enforces budget limits."""

    def __init__(self, total_budget, per_turn_limit,
                 compaction_threshold, compaction_ratio=0.8):
        ...

    def record(self, prompt_tokens: int, completion_tokens: int) -> dict:
        """Record usage from one LLM call. Returns status dict with:
        - 'session_exceeded': bool
        - 'turn_exceeded': bool
        - 'used': int (cumulative)
        - 'remaining': int
        """
        ...

    def should_compact(self, messages, estimate_fn) -> bool:
        """Return True if estimated tokens >= threshold * ratio."""
        ...

    def snapshot(self) -> dict:
        """Return current budget state for logging."""
        ...
```

## Modified Files

### `zsiga/agent/loop.py`

Changes:
1. Import `TokenBudget` from `zsiga.agent.token_budget`
2. In `AgentLoop.__init__()`: create `TokenBudget` instance from config params
3. In `AgentLoop.run()`:
   - Replace `turn % 3 == 0` compaction trigger with `self.budget.should_compact(messages, estimate_tokens)`
   - After each LLM response, call `self.budget.record(prompt, completion)` and check result
   - If `session_exceeded` or `turn_exceeded`, return `RunResult("BUDGET_EXCEEDED", ...)`
   - Log budget state periodically

### `zsiga/config.py`

Changes:
1. Extend `CompactionConfig.__init__()` with three new optional params:
   - `total_budget: int = 200000`
   - `per_turn_limit: int = 8192`
   - `compaction_ratio: float = 0.8`
2. In `load_config()`: pass new fields from `compaction_raw` to `CompactionConfig`

### `tests/test_token_budget.py` (new)

Unit tests for TokenBudget class covering:
- Recording usage and tracking cumulative totals
- Per-turn limit enforcement
- Session budget enforcement
- should_compact trigger logic at ratio boundary
- Snapshot reporting
- Default values

### `tests/test_compaction.py` (modified)

Add tests for:
- CompactionConfig loading with new fields
- Default values when fields absent in yaml

## No Frontend Changes

All changes are backend Python. The dashboard (`site/dashboard.html`) already reads metrics from log output — budget state will appear in structured log fields automatically.
