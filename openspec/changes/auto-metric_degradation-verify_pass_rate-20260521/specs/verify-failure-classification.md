# Spec: Verify Failure Classification

## ADDED Requirements

### Requirement: Verify failure record extraction

The system SHALL provide a function that reads `metrics/changes.jsonl` and extracts all records where the verify phase has a non-success outcome.

#### Scenario: Extract verify failures from change history

- **Given** `metrics/changes.jsonl` contains change records with phase data
- **When** the classification function is invoked
- **Then** it SHALL return a list of failure entries, each containing `change_name`, `project`, `detail` (the PhaseRecord detail field), and `outcome`

#### Scenario: Empty metrics file

- **Given** `metrics/changes.jsonl` does not exist or is empty
- **When** the classification function is invoked
- **Then** it SHALL return an empty list without raising an exception

### Requirement: Failure category classification

The system SHALL classify each verify failure into one or more predefined categories based on pattern matching against the `detail` field and the phase records.

Categories MUST include at minimum:
- `lint_error` — detail contains lint error codes (E701, E702, E401, F401, etc.)
- `test_failure` — detail contains test failure output
- `no_impl_changes` — detail indicates no implementation diff was found
- `daemon_cycle_error` — the change record is associated with a `daemon.cycle_error` lesson
- `review_critical` — a preceding review phase had critical findings
- `unknown` — detail does not match any known category

#### Scenario: Classify a lint failure

- **Given** a verify failure with `detail` containing `"lint:\nE701 Multiple statements"`
- **When** the classification function processes this entry
- **Then** it SHALL assign category `lint_error`

#### Scenario: Classify a test failure

- **Given** a verify failure with `detail` containing `"tests:\nFAILED test_foo.py"`
- **When** the classification function processes this entry
- **Then** it SHALL assign category `test_failure`

#### Scenario: Classify an unknown failure

- **Given** a verify failure with empty `detail`
- **When** the classification function processes this entry
- **Then** it SHALL assign category `unknown`

### Requirement: Failure classification report output

The system SHALL produce a classification report as a dictionary containing:
- `total_failures` — total number of verify failures
- `by_category` — a dict mapping category name to `{count, percentage}`
- `top_categories` — ordered list of categories by count (descending)

#### Scenario: Generate report from mixed failures

- **Given** 5 verify failure records: 2 lint, 2 test, 1 unknown
- **When** the report function is invoked
- **Then** the report SHALL contain `total_failures: 5`, `by_category.lint_error.count: 2`, `by_category.test_failure.count: 2`, `by_category.unknown.count: 1`
- **And** `top_categories` SHALL be `["lint_error", "test_failure", "unknown"]` (descending by count)

### Requirement: Classification function unit-testable

The classification function SHALL accept an optional list of change records as input, allowing unit tests to pass pre-constructed data without depending on the actual `metrics/changes.jsonl` file.

#### Scenario: Unit test with synthetic data

- **Given** a list of 3 synthetic change records passed as argument
- **When** the classification function is invoked with that list
- **Then** it SHALL return classification results based only on the provided records
- **And** it SHALL NOT read from the filesystem
