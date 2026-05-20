# Tasks: P1 Value-Based Budget

## Group 1: Core Value-Signal Infrastructure

- [ ] 1.1 Add `zsiga/agent/value_signal.py` — `ValueTracker` class with `classify_turn(tool_names, tool_results) → "productive"|"stale"` and `record_turn(classification) → {stale_count, value_signal, reset}`. Classify productive if any of: `write_file`, `edit_file` in tool_names OR bash result with exit_code=0 matching test/lint patterns.

- [ ] 1.2 Extend `zsiga/agent/token_budget.py` — add `stale_limit`, `budget_extend_factor` to constructor; add `_consecutive_stale`, `_extended` state; extend `record()` to accept `value_signal` param and return `stale_count`, `should_stop`, `effective_budget` in status dict; add `effective_budget` property.

- [ ] 1.3 Integrate value-based budget into `zsiga/agent/loop.py` — import ValueTracker, instantiate in `__init__`, call `record_turn()` after each tool-call batch, replace hard `BUDGET_EXCEEDED` with stale-limit check (→ return `STALE_LIMIT`) and soft-budget logic (→ extend if productive, stop if stale), reset ValueTracker in `set_phase()`.

## Group 2: Persistence & Analytics

- [ ] 2.1 Add `budget_usage` table and CRUD to `zsiga/metrics/db.py` — add table schema (id, change_name, phase, turn_number, prompt_tokens, completion_tokens, cumulative_used, budget_limit, value_signal, created_at) to `_SCHEMA`; add `record_budget_usage(row, db_path)` and `load_budget_usage(change_name, db_path)` functions; record a row from `AgentLoop.run()` after each turn via a callback or direct call.

- [ ] 2.2 Add `compute_budget_stats()` to `zsiga/metrics/collector.py` — query `budget_usage` table, compute per-change efficiency (total_tokens, turns, stale_ratio, phases breakdown), phase_distribution (total_tokens, avg_per_turn, turn_count per phase), overall_stale_ratio.

## Group 3: Configuration & Wiring

- [ ] 3.1 Add `stale_limit` and `budget_extend_factor` to config pipeline — extend `CompactionConfig` in `zsiga/config.py` with `stale_limit: int = 5` and `budget_extend_factor: float = 1.5`; pass these from `ZsigaOrchestrator.__init__()` in `zsiga/pipeline/orchestrator.py` into `AgentLoop` constructor.

## Group 4: Tests

- [ ] 4.1 Add `tests/test_value_budget.py` — test ValueTracker classification (productive on write_file, productive on test pass, stale on read-only tools), test stale counter reset, test soft budget extension in TokenBudget (extend on productive, stop on stale), test stale-limit stop condition, test compute_budget_stats with mock DB data.
