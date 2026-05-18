# Tasks: Implement agent/recovery.py — Failure Recovery Module

## 1. Core Recovery Module

- [x] **1.1** Create `zsiga/agent/recovery.py` — `RecoveryAction` and `RecoveryReport` dataclasses, plus `RecoveryManager` class skeleton with `__init__(change_name, target_path=None, pre_sha=None, transport=None, persist_dir=None, max_failures=3)` composing internal `EscalationManager` and `Diagnoser`. Include all imports (`EscalationManager`, `Strategy`, `FailureRecord` from `escalation`; `Diagnoser`, `DiagnosisReport` from `pipeline.diagnoser`; `git_ops`; `record_lesson`; `Transport`).

- [x] **1.2** Implement `RecoveryManager.record_failure(error, phase) -> RecoveryAction` — Delegates to internal `EscalationManager.record_failure()`, runs `Diagnoser.diagnose()` when `target_path` and `transport` are available, computes `should_rollback = (self._escalation.attempts >= self.max_failures)`, and returns a `RecoveryAction` with strategy from `_escalation.next_strategy`, hint from `get_strategy_hint()`, and the RCA report.

- [x] **1.3** Implement `RecoveryManager.execute_rollback() -> bool` and `RecoveryManager.generate_diagnostic_report() -> RecoveryReport` — Rollback calls `git_ops.reset_hard(target_path, pre_sha, transport)` + `record_lesson(pattern_key="pipeline.fail.rollback")`. Report aggregates all failures from `_escalation.failures`, determines root cause from best RCA report, lists strategies tried, generates markdown via `RecoveryReport.to_markdown()`, saves via `RecoveryReport.save(change_dir, transport)` using heredoc pattern, and records `record_lesson(pattern_key="pipeline.fail.recovery")`.

## 2. Orchestrator Integration

- [ ] **2.1** Refactor `zsiga/pipeline/orchestrator.py` — Import `RecoveryManager` from `zsiga.agent.recovery`. In `_run_phases()`, create `RecoveryManager` alongside existing `EscalationManager` (passing `change_name, target_path, pre_sha, transport, persist_dir=change_dir`). Pass `recovery=recovery` kwarg to `_fix_loop()` and `_eval_fix_loop()`. In both loop methods, when `recovery` is provided, use `recovery.record_failure()` instead of `escalation.record_failure()`, read `RecoveryAction.strategy_hint` for prompt injection, and check `RecoveryAction.should_rollback`. In `_handle_escalation_abort()`, call `recovery.generate_diagnostic_report()` + `recovery.execute_rollback()` when recovery is present, otherwise fall back to existing EscalationManager logic.

## 3. Tests

- [ ] **3.1** Create `tests/test_recovery.py` — Test `RecoveryAction` fields on `record_failure()` (1st/2nd/3rd failure), `should_rollback` threshold (False at 2, True at 3), strategy rotation (SAME → DIFFERENT_APPROACH → SIMPLIFY → caps at SIMPLIFY), strategy hint content for each strategy, `RecoveryReport.to_markdown()` contains required sections, `execute_rollback()` calls `git_ops.reset_hard` + `record_lesson`, `generate_diagnostic_report()` saves file + records lesson. Mock `EscalationManager`, `Diagnoser`, `git_ops`, `record_lesson`, and `Transport`.
