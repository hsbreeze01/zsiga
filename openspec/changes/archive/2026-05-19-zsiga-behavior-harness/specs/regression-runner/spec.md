## ADDED Requirements

### Requirement: Automated regression execution
The system SHALL automatically run the full harness suite (capability + behavioral tests) after every change completion in the orchestrator pipeline.

#### Scenario: Post-change regression trigger
- **WHEN** a change completes (success or failure) in `_run_phases`
- **THEN** `run_regression()` SHALL be called in the finally block

#### Scenario: Regression completion within time budget
- **WHEN** regression suite runs
- **THEN** it SHALL complete within 30 seconds on standard hardware

### Requirement: Structured regression event output
The system SHALL emit structured JSON events for each regression run result, written to `harness-results.jsonl`.

#### Scenario: All tests pass
- **WHEN** regression runs and all test cases pass
- **THEN** an event with `event: "regression.passed"`, total/pass/fail counts, and duration SHALL be emitted

#### Scenario: One or more tests fail
- **WHEN** regression runs and any test case fails
- **THEN** an event with `event: "regression.failed"` SHALL include the list of failed test names and error summaries

### Requirement: Regression result persistence
The system SHALL persist regression results in the metrics database for historical analysis.

#### Scenario: Result stored in harness_results table
- **WHEN** a regression run completes
- **THEN** a row SHALL be inserted into `harness_results` table with timestamp, change_name, pass_count, fail_count, and failed_tests JSON

### Requirement: CLI integration
The system SHALL provide `zsiga harness run` and `zsiga harness regression` CLI commands.

#### Scenario: Manual harness run
- **WHEN** user runs `zsiga harness run`
- **THEN** all capability + behavioral tests SHALL execute and print results to stdout

#### Scenario: Manual regression with report
- **WHEN** user runs `zsiga harness regression`
- **THEN** regression SHALL execute, write results to JSONL, and print summary to stdout
