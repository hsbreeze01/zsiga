# Delta Spec: agent/reviewer.py — Post-Implementation Code Review Loop

## ADDED Requirements

### REQ-RV-01: Review Sub-Agent Dispatch

The system SHALL dispatch a review-role sub-agent after the IMPLEMENT phase completes successfully and before the VERIFY phase begins. The review agent SHALL use read-only tools to inspect the code diff and compare it against the specs.

#### Scenario: Successful implementation triggers automatic review

- **Given** the IMPLEMENT phase has completed without mechanical verification errors
- **When** the orchestrator proceeds to the next pipeline stage
- **Then** a review-role sub-agent SHALL be dispatched with the specs, design, tasks, and git diff as input
- **And** the review agent SHALL produce a structured `review.md` artifact in the change directory

### REQ-RV-02: Structured Review Output

The review agent SHALL produce a `review.md` file containing a structured verdict with the following fields: `Verdict` (CLEAN / ISSUES_FOUND), `Issues` (categorized as CRITICAL or SUGGESTION), and `Evidence` (code references for each issue).

#### Scenario: Review finds no issues

- **Given** the implementation diff matches all spec requirements
- **When** the review agent completes its analysis
- **Then** `review.md` SHALL contain `Verdict: CLEAN` with no issues listed

#### Scenario: Review finds issues requiring fix

- **Given** the implementation diff contains a spec violation or a code quality problem
- **When** the review agent completes its analysis
- **Then** `review.md` SHALL contain `Verdict: ISSUES_FOUND` with one or more categorized issues
- **And** each issue SHALL have a severity (CRITICAL or SUGGESTION) and evidence text

### REQ-RV-03: Auto-Fix Loop on CRITICAL Issues

When the review verdict is `ISSUES_FOUND` and at least one CRITICAL issue exists, the system SHALL attempt an auto-fix loop: dispatch the main agent to fix the issues, then re-dispatch the review agent for re-review. This loop SHALL run at most `review_max_rounds` times (default: 2).

#### Scenario: Auto-fix succeeds on first round

- **Given** review finds a CRITICAL issue (e.g., missing spec requirement)
- **When** the auto-fix loop runs
- **Then** the main agent SHALL be instructed to fix only the CRITICAL issues listed in `review.md`
- **And** mechanical verification (lint + test) SHALL be run after the fix
- **And** a second review SHALL be dispatched
- **And** if the second review verdict is `CLEAN`, the pipeline SHALL proceed to VERIFY

#### Scenario: Auto-fix fails after max rounds

- **Given** review finds CRITICAL issues
- **When** the auto-fix loop has exhausted `review_max_rounds` attempts without achieving `CLEAN`
- **Then** the pipeline SHALL proceed to VERIFY with the issues noted in metrics
- **And** the review findings SHALL be recorded as a lesson via `record_lesson`

### REQ-RV-04: Suggestion-Only Reviews Continue Pipeline

When the review verdict is `ISSUES_FOUND` but ALL issues are severity `SUGGESTION`, the system SHALL NOT trigger the auto-fix loop. The pipeline SHALL proceed directly to VERIFY, and the suggestions SHALL be logged in the review phase metrics.

#### Scenario: Only suggestions found

- **Given** review produces `Verdict: ISSUES_FOUND` with only SUGGESTION-severity items
- **When** the orchestrator evaluates the review result
- **Then** the auto-fix loop SHALL NOT be triggered
- **And** the pipeline SHALL proceed to VERIFY
- **And** the suggestions count SHALL be recorded in the PhaseRecord detail

### REQ-RV-05: Review Phase Metrics

The orchestrator SHALL record a `PhaseRecord` with `phase=REVIEW` for each review round, capturing outcome, seconds_used, llm_calls, tool_calls, and the review verdict in the detail field.

#### Scenario: Review metrics recorded on success

- **Given** the review phase completes with `Verdict: CLEAN`
- **When** the orchestrator records phase metrics
- **Then** a `PhaseRecord(phase=REVIEW, outcome=SUCCESS)` SHALL be appended to the ChangeRecord
- **And** the detail field SHALL contain the review verdict text

#### Scenario: Review metrics recorded after failed auto-fix

- **Given** the review auto-fix loop exhausts max rounds
- **When** the orchestrator records phase metrics
- **Then** a `PhaseRecord(phase=REVIEW, outcome=FAIL)` SHALL be appended with the issue count in detail

### REQ-RV-06: PipelineConfig Extension

The `PipelineConfig` class SHALL accept the following new fields with defaults: `review_max_turns` (default: 10), `review_timeout` (default: 180), `review_max_rounds` (default: 2), `review_fix_max_turns` (default: 6). These fields control the review sub-agent's turn budget, timeout, and the auto-fix loop parameters.

#### Scenario: Default config values used

- **Given** a `PipelineConfig` is instantiated without explicit review parameters
- **When** the config is used to configure the review phase
- **Then** `review_max_turns` SHALL be 10, `review_timeout` SHALL be 180, `review_max_rounds` SHALL be 2, `review_fix_max_turns` SHALL be 6

### REQ-RV-07: Phase Enum Extension

The `Phase` enum in `metrics/types.py` SHALL include a `REVIEW = "review"` member, positioned between IMPLEMENT and VERIFY.

#### Scenario: Phase enum includes REVIEW

- **Given** the Phase enum
- **Then** `Phase.REVIEW` SHALL exist with value `"review"`
- **And** `Phase.REVIEW` SHALL be usable in PhaseRecord serialization

### REQ-RV-08: Review Skipped on Mechanical Failure

The review phase SHALL be skipped entirely when mechanical verification (lint/test) fails in the IMPLEMENT phase. In this case, the existing `_fix_loop` handles the errors. Review only runs after the IMPLEMENT phase produces mechanically clean code.

#### Scenario: Mechanical failure skips review

- **Given** the IMPLEMENT phase fails mechanical verification (lint or test errors)
- **When** the fix loop is invoked
- **Then** the review phase SHALL NOT be dispatched
- **And** the pipeline SHALL follow the existing fix/revert path

## MODIFIED Requirements

### REQ-ORCH-01: Pipeline Phase Order (Modified)

The orchestrator `_run_phases` method SHALL execute phases in order: ENRICH → IMPLEMENT → REVIEW → VERIFY → DELIVER. The REVIEW phase is inserted between IMPLEMENT and VERIFY, but only when mechanical verification passes after IMPLEMENT.

#### Scenario: Full pipeline with review

- **Given** a change with IMPLEMENTATION intent
- **When** the orchestrator runs the pipeline
- **Then** the phases SHALL execute in order: ENRICH → IMPLEMENT → (mechanical verify) → REVIEW → VERIFY → DELIVER

#### Scenario: Pipeline without review on implement failure

- **Given** a change where IMPLEMENT fails mechanical verification and cannot be fixed
- **When** the orchestrator processes the result
- **Then** REVIEW SHALL NOT execute
- **And** the change SHALL be reverted as before
