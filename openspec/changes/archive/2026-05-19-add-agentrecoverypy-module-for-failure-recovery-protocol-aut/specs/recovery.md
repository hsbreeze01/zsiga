# Delta Spec: agent/recovery.py — Failure Recovery Protocol

## ADDED Requirements

### REQ-RC-01: Failure Tracking

The system SHALL maintain a per-change failure register that records each failure with its error text, originating phase (implement / verify / eval-fix), timestamp, strategy used, and attempt number.

#### Scenario: Record a single failure
- **Given** a `RecoveryManager` initialized for change `my-feature`
- **When** `record_failure(error="E701 at line 5", phase="implement")` is called
- **Then** the failure register SHALL contain exactly one entry
- **And** the entry SHALL have `attempt=1`, `phase="implement"`, and the error text preserved exactly

#### Scenario: Track multiple failures across phases
- **Given** a `RecoveryManager` with 2 failures already recorded (1 in implement, 1 in verify)
- **When** `record_failure(error="assertion failed", phase="verify")` is called
- **Then** the register SHALL contain exactly 3 entries
- **And** the new entry SHALL have `attempt=3`

---

### REQ-RC-02: Auto-Rollback on Consecutive Failures

When the number of consecutive failures reaches a configurable threshold (default 3), the system SHALL signal that an automatic git rollback MUST be performed to the pre-implementation commit SHA.

#### Scenario: Trigger rollback at threshold
- **Given** a `RecoveryManager` with `max_failures=3` and 2 failures already recorded
- **When** `record_failure(...)` is called (3rd consecutive failure)
- **Then** `should_rollback()` SHALL return `True`

#### Scenario: No rollback below threshold
- **Given** a `RecoveryManager` with `max_failures=3` and 1 failure recorded
- **When** `should_rollback()` is called
- **Then** it SHALL return `False`

#### Scenario: Execute rollback resets state
- **Given** a `RecoveryManager` with 3 failures and `should_rollback()` returning `True`
- **When** `execute_rollback()` is called with valid `target_path` and `pre_sha`
- **Then** `git_ops.reset_hard(target_path, pre_sha, transport)` SHALL be invoked
- **And** a lesson SHALL be recorded via `memory.learn.record_lesson` with `pattern_key="pipeline.fail.rollback"`

---

### REQ-RC-03: Root Cause Analysis

On each failure, the system SHALL run root cause analysis that classifies the error, generates ranked hypotheses, probes the codebase, and produces a `RCAReport` with a confirmed or best-guess root cause.

#### Scenario: RCA classifies import error
- **Given** a failure with error `"ModuleNotFoundError: No module named 'foo'"`
- **When** `run_root_cause_analysis(failure_info)` is called
- **Then** the returned `RCAReport` SHALL contain at least one hypothesis mentioning "import" or "dependency"
- **And** the root cause confidence SHALL be > 0

#### Scenario: RCA generates multiple hypotheses
- **Given** a failure with ambiguous error output
- **When** `run_root_cause_analysis(failure_info)` is called
- **Then** the report SHALL contain between 3 and 5 ranked hypotheses
- **And** hypotheses SHALL be sorted by confidence descending

---

### REQ-RC-04: Strategy Rotation

The system SHALL rotate through a fixed sequence of recovery strategies: `SAME` → `DIFFERENT_APPROACH` → `SIMPLIFY`. Each strategy SHALL produce a prompt modifier that guides the fix engine to adjust its approach.

#### Scenario: Strategy rotates on each failure
- **Given** a new `RecoveryManager` with 0 failures
- **When** the first failure is recorded
- **Then** `get_strategy()` SHALL return `Strategy.SAME`
- **When** the second failure is recorded
- **Then** `get_strategy()` SHALL return `Strategy.DIFFERENT_APPROACH`
- **When** the third failure is recorded
- **Then** `get_strategy()` SHALL return `Strategy.SIMPLIFY`

#### Scenario: Strategy caps at last option
- **Given** a `RecoveryManager` with 5 failures recorded
- **When** `get_strategy()` is called
- **Then** it SHALL return `Strategy.SIMPLIFY` (never exceeds the rotation list)

#### Scenario: DIFFERENT_APPROACH strategy produces prompt modifier
- **Given** `get_strategy()` returns `Strategy.DIFFERENT_APPROACH`
- **When** `get_strategy_hint()` is called
- **Then** the returned string SHALL contain language directing the agent to try a fundamentally different approach

---

### REQ-RC-05: Diagnostic Report Generation

When all recovery strategies are exhausted (i.e., the maximum number of retries across all strategies has been attempted without success), the system SHALL generate a comprehensive diagnostic report file and record a lesson.

#### Scenario: Generate report on strategy exhaustion
- **Given** a `RecoveryManager` with `max_failures=3` and 3 consecutive failures (all strategies tried)
- **When** `generate_diagnostic_report()` is called
- **Then** a markdown report SHALL be saved to the change directory as `recovery-report.md`
- **And** the report SHALL contain sections for: Failure History, Root Cause Analysis, Strategies Tried, and Recommended Action
- **And** `record_lesson()` SHALL be called with `pattern_key="pipeline.fail.recovery"`

#### Scenario: Report includes all failure records
- **Given** 3 failures across phases implement, implement, verify
- **When** the diagnostic report is generated
- **Then** the Failure History section SHALL list all 3 failures with their phase, error, and strategy used

---

### REQ-RC-06: Orchestrator Integration

The `ZsigaOrchestrator` SHALL use `RecoveryManager` in place of direct `EscalationManager` usage within `_run_phases`, `_fix_loop`, and `_eval_fix_loop`, delegating all failure tracking, rollback, and diagnosis to the recovery module.

#### Scenario: Orchestrator delegates to RecoveryManager
- **Given** an orchestrator processing a change that fails mechanical verification
- **When** the fix loop exhausts its attempts
- **Then** the orchestrator SHALL call `RecoveryManager.record_failure()` instead of `EscalationManager.record_failure()`
- **And** rollback decision SHALL come from `RecoveryManager.should_rollback()` instead of `EscalationManager.should_abort()`

#### Scenario: Backward compatibility
- **Given** existing `EscalationManager` class
- **When** the new module is added
- **Then** `EscalationManager` SHALL remain importable and unchanged (not removed)
- **And** `RecoveryManager` SHALL be the preferred interface going forward
