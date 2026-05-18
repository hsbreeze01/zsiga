# Tasks: agent/recovery.py — Failure Recovery Protocol

## 1. Core Recovery Module

- [ ] **1.1** Create `zsiga/agent/recovery.py` — `RecoveryManager` class with `__init__(change_name, target_path, pre_sha, transport, persist_dir, max_failures=3)`, composing `EscalationManager` and `Diagnoser` internally. Include `RecoveryAction` and `RecoveryReport` dataclasses.

- [ ] **1.2** Implement failure tracking + rollback logic — `record_failure(error, phase) -> RecoveryAction` that delegates to `EscalationManager.record_failure()`, runs `Diagnoser.diagnose()` for RCA, and computes `should_rollback`. Implement `should_rollback() -> bool` (returns `True` when `attempts >= max_failures`) and `execute_rollback() -> bool` that calls `git_ops.reset_hard()` + `record_lesson()`.

- [ ] **1.3** Implement strategy rotation + hint generation — `get_strategy() -> Strategy` and `get_strategy_hint() -> str` methods that read from `EscalationManager.next_strategy` and produce phase-appropriate prompt modifiers (SAME=empty, DIFFERENT_APPROACH=alternate approach, SIMPLIFY=reduce complexity).

- [ ] **1.4** Implement diagnostic report generation — `generate_diagnostic_report() -> RecoveryReport` that aggregates all failures, root cause, strategies tried, and recommended action. Implement `RecoveryReport.to_markdown()` and `RecoveryReport.save(change_dir, transport)` writing to `recovery-report.md`. Include `record_lesson(pattern_key="pipeline.fail.recovery")`.

## 2. Orchestrator Integration

- [ ] **2.1** Refactor `zsiga/pipeline/orchestrator.py` to use `RecoveryManager` — Replace `EscalationManager` construction in `_run_phases()` with `RecoveryManager`. Update `_fix_loop()` and `_eval_fix_loop()` to call `recovery.record_failure()` and read `RecoveryAction` (strategy, hint, should_rollback). Replace `_handle_escalation_abort()` with `recovery.execute_rollback()` + `recovery.generate_diagnostic_report()`. Keep `EscalationManager` import for backward compatibility.

## 3. Tests

- [ ] **3.1** Create `tests/test_recovery.py` — Test failure tracking (record 1/2/3 failures, verify register), rollback threshold (should_rollback returns False at 2, True at 3), strategy rotation (SAME→DIFFERENT_APPROACH→SIMPLIFY), strategy hint content, report markdown generation, and report save via mock transport. Use `unittest.mock` for `git_ops`, `Diagnoser`, and `Transport`.
