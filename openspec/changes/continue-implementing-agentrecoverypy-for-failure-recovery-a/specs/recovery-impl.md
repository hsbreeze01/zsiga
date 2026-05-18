# Delta Spec: Implement agent/recovery.py — Failure Recovery Module

## ADDED Requirements

### REQ-RI-01: RecoveryManager Dataclasses

The system SHALL define `RecoveryAction` and `RecoveryReport` dataclasses in `zsiga/agent/recovery.py`. `RecoveryAction` SHALL carry `strategy`, `strategy_hint`, `should_rollback`, `attempt`, and `rca_report` fields. `RecoveryReport` SHALL carry `change_name`, `total_attempts`, `failures`, `root_cause`, `root_cause_confirmed`, `strategies_tried`, and `recommended_action` fields, and SHALL expose `to_markdown() -> str` and `save(change_dir, transport)` methods.

#### Scenario: RecoveryAction carries all orchestrator decision data
- **Given** a failure has been recorded
- **When** `RecoveryManager.record_failure()` returns a `RecoveryAction`
- **Then** the action SHALL contain `strategy` (a `Strategy` enum value), `strategy_hint` (a string prompt modifier), `should_rollback` (a bool), `attempt` (an int), and `rca_report` (a `DiagnosisReport` or None)

#### Scenario: RecoveryReport renders to markdown
- **Given** a `RecoveryReport` with 3 failures and root cause `"import error"`
- **When** `to_markdown()` is called
- **Then** the output SHALL contain sections: `# Recovery Report`, `## Failure History`, `## Root Cause Analysis`, `## Strategies Tried`, `## Recommended Action`
- **And** each failure in the history SHALL list its phase, error snippet, and strategy used

---

### REQ-RI-02: RecoveryManager Failure Tracking and Rollback

The `RecoveryManager` SHALL compose `EscalationManager` and `Diagnoser` internally. Its `record_failure(error, phase)` method SHALL delegate to `EscalationManager.record_failure()`, run `Diagnoser.diagnose()` when `target_path` and `transport` are available, and return a `RecoveryAction` with the rollback decision. `should_rollback()` SHALL return `True` when attempts >= `max_failures`. `execute_rollback()` SHALL invoke `git_ops.reset_hard()` and `record_lesson()`.

#### Scenario: record_failure delegates and returns RecoveryAction
- **Given** a `RecoveryManager` initialized with `change_name="feat-x"`, `target_path="/proj"`, `pre_sha="abc123"`, `transport`, `max_failures=3`
- **When** `record_failure(error="E701 at line 5", phase="implement")` is called
- **Then** `EscalationManager.record_failure()` SHALL be called internally
- **And** the returned `RecoveryAction.attempt` SHALL be 1
- **And** `RecoveryAction.should_rollback` SHALL be `False`

#### Scenario: should_rollback triggers at threshold
- **Given** a `RecoveryManager` with `max_failures=3` and 2 failures already recorded
- **When** `record_failure(...)` is called (3rd failure)
- **Then** the returned `RecoveryAction.should_rollback` SHALL be `True`

#### Scenario: execute_rollback resets git and records lesson
- **Given** a `RecoveryManager` where `should_rollback()` is `True`
- **When** `execute_rollback()` is called
- **Then** `git_ops.reset_hard(target_path, pre_sha, transport)` SHALL be invoked
- **And** `record_lesson(pattern_key="pipeline.fail.rollback")` SHALL be called

---

### REQ-RI-03: Strategy Rotation via EscalationManager

`RecoveryManager.get_strategy()` SHALL return the value from `EscalationManager.next_strategy`. `RecoveryManager.get_strategy_hint()` SHALL return an empty string for `Strategy.SAME`, a different-approach prompt for `Strategy.DIFFERENT_APPROACH`, and a simplify prompt for `Strategy.SIMPLIFY`.

#### Scenario: Strategy rotates SAME → DIFFERENT_APPROACH → SIMPLIFY
- **Given** a new `RecoveryManager`
- **When** the 1st failure is recorded
- **Then** `get_strategy()` SHALL return `Strategy.SAME`
- **When** the 2nd failure is recorded
- **Then** `get_strategy()` SHALL return `Strategy.DIFFERENT_APPROACH`
- **When** the 3rd failure is recorded
- **Then** `get_strategy()` SHALL return `Strategy.SIMPLIFY`

#### Scenario: Strategy caps at SIMPLIFY
- **Given** a `RecoveryManager` with 5 failures
- **When** `get_strategy()` is called
- **Then** it SHALL return `Strategy.SIMPLIFY`

---

### REQ-RI-04: Diagnostic Report Generation

When all recovery strategies are exhausted (attempts >= `max_failures`), `generate_diagnostic_report()` SHALL produce a `RecoveryReport`, save it as `recovery-report.md` in the change directory, and record a lesson with `pattern_key="pipeline.fail.recovery"`.

#### Scenario: Report generated on strategy exhaustion
- **Given** a `RecoveryManager` with 3 failures (at threshold)
- **When** `generate_diagnostic_report()` is called
- **Then** a file named `recovery-report.md` SHALL be written to the change directory via transport
- **And** the report SHALL list all 3 failures with phase, error, and strategy
- **And** `record_lesson(pattern_key="pipeline.fail.recovery")` SHALL be called

---

### REQ-RI-05: Orchestrator Integration

`ZsigaOrchestrator._run_phases()` SHALL create a `RecoveryManager` instead of using `EscalationManager` directly. `_fix_loop()` and `_eval_fix_loop()` SHALL call `recovery.record_failure()` and consume `RecoveryAction` for strategy hints and rollback decisions. `_handle_escalation_abort()` SHALL be replaced by `recovery.execute_rollback()` + `recovery.generate_diagnostic_report()`.

#### Scenario: Orchestrator uses RecoveryManager in fix loop
- **Given** an orchestrator processing a change that fails mechanical verification
- **When** the fix loop records a failure
- **Then** the orchestrator SHALL call `RecoveryManager.record_failure()` and use the returned `RecoveryAction.strategy_hint` for the next fix attempt

#### Scenario: Backward compatibility preserved
- **Given** the existing `EscalationManager` class
- **When** `recovery.py` is added
- **Then** `EscalationManager` SHALL remain importable from `zsiga.agent.escalation` unchanged

## MODIFIED Requirements

### REQ-RI-06: Orchestrator _handle_escalation_abort Replacement

The `_handle_escalation_abort` method SHALL be simplified to delegate to `RecoveryManager.generate_diagnostic_report()` instead of manually composing the diagnosis report. If a `RecoveryManager` is not available, it SHALL fall back to the existing `EscalationManager`-based logic.

#### Scenario: Delegation when RecoveryManager is present
- **Given** an orchestrator with a `RecoveryManager` instance
- **When** escalation abort is triggered
- **Then** `RecoveryManager.generate_diagnostic_report()` SHALL be called
- **And** `RecoveryManager.execute_rollback()` SHALL be called
- **And** no direct `EscalationManager.generate_diagnosis()` call SHALL occur
