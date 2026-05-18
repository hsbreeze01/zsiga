# Tasks: Token Budget Manager

## 1. Core TokenBudget class

- [x] **1.1** Create `zsiga/agent/token_budget.py` with `TokenBudget` class (constructor, `record`, `should_compact`, `snapshot` methods) — REQ-BUDGET-001, REQ-BUDGET-002, REQ-BUDGET-003, REQ-BUDGET-004, REQ-BUDGET-006

## 2. Configuration integration

- [x] **2.1** Extend `CompactionConfig` in `zsiga/config.py` with `total_budget`, `per_turn_limit`, `compaction_ratio` fields and update `load_config()` to parse them — REQ-BUDGET-005

## 3. AgentLoop integration

- [x] **3.1** Modify `zsiga/agent/loop.py` to instantiate `TokenBudget`, replace fixed-interval compaction with `should_compact`, and add budget enforcement checks after each LLM response — REQ-BUDGET-M001, REQ-BUDGET-M002

## 4. Tests

- [x] **4.1** Create `tests/test_token_budget.py` with unit tests for TokenBudget (recording, per-turn limit, session limit, should_compact ratio boundary, snapshot) and add CompactionConfig new-field tests to `tests/test_compaction.py` — all REQs
