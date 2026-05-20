# Design: P1 Value-Based Budget

## Architecture Decision

Replace the hard `session_exceeded` cutoff in `AgentLoop.run()` with a two-layer decision:

1. **Stale detection** (primary stop): Stop when consecutive unproductive turns ≥ `stale_limit`
2. **Soft budget** (secondary stop): Extend budget to 1.5× when producing value; hard-stop at 1.5× regardless

This preserves `total_budget` as a safety valve while allowing productive sessions to continue past the nominal limit.

## Data Flow

```
LLM response → record() → classify turn (productive/stale)
                                ↓
                    ┌─ stale_count >= stale_limit? → return STALE_LIMIT
                    ├─ session_exceeded AND productive? → extend, continue
                    └─ session_exceeded AND stale? → return BUDGET_EXCEEDED
                                ↓
                    insert row into budget_usage table
```

## Changes by File

### New file: `zsiga/agent/value_signal.py`
- `ValueTracker` class: tracks consecutive stale count, classifies turns
- `classify_turn(tool_calls, tool_results) → "productive" | "stale"`
- `ValueTracker.record_turn(classification) → {stale_count, value_signal}`

### Modified: `zsiga/agent/token_budget.py`
- Add `stale_limit: int = 5` and `budget_extend_factor: float = 1.5` to constructor
- Add `_consecutive_stale: int` and `_extended: bool` internal state
- Extend `record()` to accept `value_signal` and return `stale_count`, `should_stop`, `extended_budget`
- Add `effective_budget` property that returns `total_budget * 1.5` when extended

### Modified: `zsiga/agent/loop.py`
- Import `ValueTracker` from `value_signal.py`
- After each tool-call batch, call `value_tracker.record_turn()` with tool names and results
- Replace hard `BUDGET_EXCEEDED` check with value-based logic (REQ-VBB-003, REQ-VBB-004)
- Return `STALE_LIMIT` when stale limit hit
- In `set_phase()`, reset `value_tracker` alongside `budget._used`

### Modified: `zsiga/metrics/db.py`
- Add `budget_usage` table to `_SCHEMA`
- Add `record_budget_usage(row: dict, db_path=None)` function
- Add `load_budget_usage(change_name=None, db_path=None) -> list[dict]` function

### Modified: `zsiga/metrics/collector.py`
- Add `compute_budget_stats()` function (per-change efficiency, phase distribution, stale ratio)

### Modified: `zsiga/config.py`
- Add `stale_limit: int = 5` and `budget_extend_factor: float = 1.5` to `CompactionConfig`
- Pass these through to `AgentLoop` in orchestrator

### Modified: `zsiga/pipeline/orchestrator.py`
- Pass `stale_limit` and `budget_extend_factor` from config to `AgentLoop`

### New file: `tests/test_value_budget.py`
- Test `ValueTracker` classification logic
- Test soft budget extension in `TokenBudget`
- Test `compute_budget_stats()`
- Test stale-limit stop in agent loop mock

## Key Design Decisions

1. **ValueTracker is separate from TokenBudget** — separation of concerns: TokenBudget tracks tokens, ValueTracker tracks productivity. They compose in the loop.

2. **Tool-call-based classification** — no LLM call needed to detect stale. We inspect tool names and results that already exist in the loop's message history.

3. **budget_usage table in existing DB** — reuses the same `data/zsiga.db` SQLite file. Schema migration is additive (CREATE TABLE IF NOT EXISTS).

4. **1.5× hard cap** — prevents runaway budget consumption. Even if the agent keeps being "productive" in a degenerate loop, it stops at 1.5×.

5. **stale_limit default 5** — empirical: cross-project patterns show 3-4 stale turns is noise, 5+ indicates stuck.

## Config Changes

```yaml
pipeline:
  compaction:
    stale_limit: 5              # new, default 5
    budget_extend_factor: 1.5   # new, default 1.5
```

No breaking changes to existing config — both new fields have defaults.
