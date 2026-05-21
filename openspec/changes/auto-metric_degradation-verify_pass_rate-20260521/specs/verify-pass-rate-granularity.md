# Spec: Verify Pass Rate Metric Granularity

## ADDED Requirements

### Requirement: Failure-type breakdown in verify metrics

The metrics module SHALL extend `verify_pass_rate` computation to include a breakdown of failures by category. Each verify result record SHALL carry a `fail_category` field with one of: `lint`, `test`, `regression`, `dependency`, `other`.

#### Scenario: Recording a lint failure in metrics

- **Given** the verify phase fails due to a ruff violation
- **When** the result is recorded in `metrics/changes.jsonl`
- **Then** the record SHALL include `fail_category: "lint"`

#### Scenario: Recording a test failure in metrics

- **Given** the verify phase fails due to a pytest assertion error
- **When** the result is recorded in `metrics/changes.jsonl`
- **Then** the record SHALL include `fail_category: "test"`

#### Scenario: Recording a regression failure in metrics

- **Given** the verify phase fails because a previously passing test now fails
- **When** the result is recorded in `metrics/changes.jsonl`
- **Then** the record SHALL include `fail_category: "regression"`

### Requirement: Per-category pass rate computation

The metrics module SHALL provide a function that computes pass rate per failure category from `metrics/changes.jsonl`. The function SHALL return a mapping of category to pass-rate percentage.

#### Scenario: Computing per-category rates from mixed records

- **Given** `metrics/changes.jsonl` contains 20 verify records: 8 pass, 4 fail_lint, 5 fail_test, 2 fail_regression, 1 fail_dependency
- **When** the per-category pass rate is computed
- **Then** the result SHALL include:
  - `lint`: pass rate calculated from lint-related entries only
  - `test`: pass rate calculated from test-related entries only
  - `regression`: pass rate calculated from regression-related entries only
  - `dependency`: pass rate calculated from dependency-related entries only

#### Scenario: Empty category produces zero rate

- **Given** no verify records have `fail_category: "dependency"`
- **When** the per-category pass rate is computed
- **Then** the `dependency` entry SHALL have a pass rate of N/A or be omitted from the result

### Requirement: Backward-compatible overall verify_pass_rate

The existing `verify_pass_rate` metric (overall percentage) SHALL remain computable and unchanged in semantics. The new per-category breakdown is additive and SHALL NOT alter the existing overall calculation.

#### Scenario: Overall rate unchanged after adding categories

- **Given** 10 verify records exist: 6 pass, 4 fail (of various categories)
- **When** `verify_pass_rate` is computed
- **Then** the overall rate SHALL be 60%
- **And** the per-category breakdown SHALL be available as a separate query

## MODIFIED Requirements

### Requirement: Verify result record schema

Each verify result record written to `metrics/changes.jsonl` SHALL include an additional field `fail_category`. Existing records without this field SHALL be treated as `fail_category: null` (unknown) for backward compatibility.

#### Scenario: Reading legacy records without fail_category

- **Given** an existing record in `metrics/changes.jsonl` that does not contain `fail_category`
- **When** the metrics module reads and processes this record
- **Then** the record SHALL be treated as having `fail_category: null`
- **And** it SHALL be excluded from per-category breakdowns but included in the overall `verify_pass_rate`
