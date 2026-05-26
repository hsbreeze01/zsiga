# add-phase-token-cap

## Summary
Add per-phase token budget caps to prevent any single phase from consuming excessive tokens. Currently, each phase has an independent 1.2M token budget with no phase-specific limits, leading to implement phases consuming up to 1.8M tokens and enrich phases up to 1.16M.

## Problem
Token consumption is unevenly distributed:
- implement: avg 678K prompt tokens (59.9% of total), peaks at 1.85M
- enrich: avg 333K prompt tokens (29.3%), peaks at 1.16M
- verify: avg 57K (10%), peaks at 145K
- review: avg 5K (0.2%)

There is no mechanism to say "enrich should not exceed 400K tokens" or "implement should not exceed 800K tokens". A single runaway phase can waste 1.8M tokens before hitting the session budget.

## Technical Design

### File: `zsiga/agent/token_budget.py`

Add a `phase_cap` parameter to `TokenBudget`:

```python
class TokenBudget:
    def __init__(self, ..., phase_cap: int = 0):
        self.phase_cap = phase_cap  # 0 = no cap
    
    def record(self, ...):
        ...
        cap_exceeded = self.phase_cap > 0 and self._used > self.phase_cap
        result["cap_exceeded"] = cap_exceeded
        ...
```

### File: `zsiga/config.py`

Add phase token caps to `PipelineConfig`:

```python
PHASE_TOKEN_CAPS: dict[str, int] = {
    "clarify": 200000,
    "enrich": 400000,
    "implement": 800000,
    "review": 100000,
    "verify": 150000,
    "optimize": 200000,
    "reflect": 50000,
    "deliver": 50000,
}
```

### File: `zsiga/pipeline/orchestrator.py`

Before each phase, set `self.agent.budget.phase_cap = PHASE_TOKEN_CAPS[phase_name]`.

When `cap_exceeded` is detected in `loop.py`, return a result with content `"CAP_EXCEEDED"` (similar to `"BUDGET_EXCEEDED"` but softer — don't treat as a hard failure).

In `orchestrator.py`, handle `CAP_EXCEEDED` by logging a warning and proceeding to the next phase (don't revert or retry).

## Acceptance Criteria
1. `TokenBudget` has a `phase_cap` attribute with default 0 (no cap)
2. `PipelineConfig` has `phase_token_caps` dict with per-phase caps
3. Each phase sets its cap before starting via `budget.phase_cap = ...`
4. When `phase_cap` is exceeded, the phase terminates gracefully with a warning log
5. `CAP_EXCEEDED` does NOT trigger revert — next phase proceeds normally
6. Existing `total_budget` and `session_exceeded` behavior unchanged
7. `ruff check` passes on all modified files

## Scope
- In scope: `token_budget.py`, `config.py`, `loop.py`, `orchestrator.py`
- Out of scope: Timeout-based budgets, compaction changes, Langfuse changes

## Risk
- Impact: Low — adds guardrails without changing existing behavior (cap=0 is default)
- Reversibility: Single config change to disable
