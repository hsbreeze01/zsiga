# Spec: Verify Failure Root Cause Telemetry

## ADDED Requirements

### Requirement: Verify failures are categorized by root cause

When the verify phase fails, the failure SHALL be categorized into one of the following root-cause buckets: `lint`, `test`, `checkout_conflict`, `review_rejection`, or `other`. This categorization SHALL be recorded in `metrics/changes.jsonl` alongside the existing failure record.

#### Scenario: Lint failure categorized correctly

- **Given** the verify phase runs `ruff check` and finds violations
- **When** the failure is recorded
- **Then** the record SHALL include a field `verify_failure_category` with value `"lint"`
- **And** the record SHALL include the specific violation codes (e.g., `["E701", "F841"]`)

#### Scenario: Test failure categorized correctly

- **Given** the verify phase runs `pytest` and one or more tests fail
- **When** the failure is recorded
- **Then** the record SHALL include `verify_failure_category` with value `"test"`
- **And** the record SHALL include the list of failed test names

#### Scenario: Review rejection categorized correctly

- **Given** the review phase produces a critical rejection
- **When** the failure is recorded
- **Then** the record SHALL include `verify_failure_category` with value `"review_rejection"`
- **And** the record SHALL include the review finding summary

#### Scenario: Checkout conflict categorized correctly

- **Given** the daemon encounters a git checkout conflict (before auto-recovery)
- **When** the event is recorded
- **Then** the record SHALL include `verify_failure_category` with value `"checkout_conflict"`
- **And** the record SHALL include the list of conflicting file paths

### Requirement: Pass rate metric computation is accurate

The `verify_pass_rate` metric SHALL be computed as `verify_pass_count / total_verify_attempts` where only genuine code-quality failures (lint, test, review) count as failures. Operational issues (checkout conflicts) that are auto-recovered SHALL be excluded from the denominator.

#### Scenario: Auto-recovered checkout conflict excluded from pass rate

- **Given** a daemon cycle encountered a checkout conflict
- **And** the auto-stash mechanism resolved it successfully
- **And** the verify phase subsequently passed
- **When** `verify_pass_rate` is computed
- **Then** this cycle SHALL be counted as a pass (not a failure)
- **And** it SHALL be included in the total_verify_attempts count

#### Scenario: Pre-verify lint-fix prevents failure from counting

- **Given** the implement phase produced a lint violation
- **And** the pre-verify auto-fix step corrected it
- **And** the verify phase subsequently passed
- **When** `verify_pass_rate` is computed
- **Then** this cycle SHALL be counted as a pass
- **And** the auto-fix event SHALL be tracked separately for trend analysis
