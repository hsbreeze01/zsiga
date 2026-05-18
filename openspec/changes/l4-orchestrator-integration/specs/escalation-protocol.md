# Delta Spec: Escalation Protocol in Orchestrator

## ADDED Requirements

### REQ-ES-01: Escalation Manager per Change

The orchestrator SHALL create an `EscalationManager` for each change being processed, tracking all fix failures across the implement and verify phases.

#### Scenario: Escalation manager initialized at change start

- **Given** the orchestrator begins processing a change
- **When** entering the `_run_phases()` method
- **Then** an `EscalationManager` SHALL be created with the change name

### REQ-ES-02: Failure Recording with Strategy Rotation

The orchestrator SHALL record each fix failure to the escalation manager and retrieve the next strategy for subsequent fix attempts.

#### Scenario: First fix failure triggers normal strategy

- **Given** the implement phase fix loop fails on the first attempt
- **When** the orchestrator records the failure via `escalation.record_failure()`
- **Then** the returned level SHALL be `NORMAL`
- **And** the next strategy SHALL be `SAME`

#### Scenario: Third fix failure triggers escalation

- **Given** the fix loop has failed 3 times
- **When** the orchestrator records the third failure
- **Then** the returned level SHALL be `RETRY_DIFFERENT`
- **And** `should_escalate()` SHALL return `True`
- **And** the next strategy SHALL be `DIFFERENT_APPROACH`

### REQ-ES-03: Escalation Alters Fix Behavior

When the escalation level reaches `RETRY_DIFFERENT`, the orchestrator SHALL modify the fix prompt to instruct the agent to try a fundamentally different approach.

#### Scenario: Escalated fix uses different approach prompt

- **Given** the escalation manager has recorded 3 failures
- **When** the fix loop continues with the next attempt
- **Then** the system prompt for the fix agent SHALL include instructions to use a different strategy
- **And** the prompt SHALL reference the escalation diagnosis

### REQ-ES-04: Auto-abort after Max Failures

The orchestrator SHALL abort the change after the escalation manager reaches the `NEEDS_HUMAN` level.

#### Scenario: Five failures trigger auto-abort

- **Given** the fix loop has failed 5 times across phases
- **When** `should_abort()` returns `True`
- **Then** the orchestrator SHALL generate a `DiagnosisReport` via `escalation.generate_diagnosis()`
- **And** the report SHALL be saved to the change directory
- **And** the change SHALL be reverted
- **And** a lesson SHALL be recorded with pattern key `"pipeline.fail.escalation"`

### REQ-ES-05: Escalation Integration in Verify Phase

The orchestrator SHALL also record eval-fix failures from the verify phase to the same escalation manager.

#### Scenario: Verify phase failure feeds escalation

- **Given** the verify phase eval-fix loop fails
- **When** the orchestrator records the failure
- **Then** the failure SHALL include `phase="verify"` in the escalation record
- **And** the failure count SHALL accumulate across implement and verify phases
