# Proposal: P1 Value-Based Budget — Statistics + Stale Detection

## Summary

Replace hard token-count budget cutoff with value-based budgeting: track budget usage per turn per phase, detect stale turns, only stop when consecutive stale turns exceed threshold.

## Motivation

Current budget: total_budget=600K, hard stop when exceeded. BUDGET_EXCEEDED generates 0 lessons. Cross-project tasks waste budget (11 attempts, ~10% success). User principle: "If value output is above threshold, it's not waste."

## Implementation

### 1. Budget Usage DB Table
```sql
CREATE TABLE IF NOT EXISTS budget_usage (
    id INTEGER PRIMARY KEY, change_name TEXT, phase TEXT,
    turn_number INTEGER, prompt_tokens INTEGER, completion_tokens INTEGER,
    cumulative_used INTEGER, budget_limit INTEGER, value_signal TEXT, created_at TEXT
);
```

### 2. Value Signal Detection
- Track stale turns: consecutive turns with no file_edited/test_passed/lint_clean/task_checked
- stale_limit=5 (configurable)

### 3. Soft Budget Cut
- Stale exceeded → stop immediately
- Token budget exceeded but producing value → extend up to 1.5x
- Record all usage to DB for analytics

### 4. Budget Analytics
- compute_budget_stats(): per-change efficiency, phase token distribution, stale ratio

## Constraints
- Scope: project=zsiga
- Keep total_budget as safety valve
