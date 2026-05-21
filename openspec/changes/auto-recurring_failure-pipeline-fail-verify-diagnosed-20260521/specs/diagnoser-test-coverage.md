# Spec: Diagnoser and Pre-Check Test Coverage

## ADDED Requirements

### Requirement: New Root-Cause Paths SHALL Have Unit Tests

Every new root-cause classification path in the diagnoser MUST be covered by at least one unit test in `tests/test_diagnoser.py`. Tests SHALL verify both the `root_cause` and `fix_description` fields of the returned `FixPlan`, ensuring neither contains the generic "Unconfirmed hypothesis" pattern for known error types.

#### Scenario: ImportError root cause has dedicated test

- **Given** the diagnoser receives a failure with `ImportError: No module named 'xyz'`
- **When** `targeted_fix()` is called (with or without probe confirmation)
- **Then** a test SHALL assert that `FixPlan.fix_description` does not contain "Unconfirmed hypothesis"
- **And** the test SHALL assert that `FixPlan.fix_description` contains the module name `xyz`

#### Scenario: Lint error root cause has dedicated test

- **Given** the diagnoser receives a failure with `E701 Multiple statements on one line` including a file path
- **When** `targeted_fix()` is called
- **Then** a test SHALL assert that `FixPlan.root_cause` references a lint/code-style issue
- **And** `FixPlan.affected_files` SHALL contain the reported file path

#### Scenario: AssertionError root cause has dedicated test

- **Given** the diagnoser receives a failure with `AssertionError` and a test function name
- **When** `targeted_fix()` is called
- **Then** a test SHALL assert that `FixPlan.root_cause` references test expectation or assertion mismatch
- **And** `FixPlan.fix_description` SHALL NOT contain "Unconfirmed hypothesis"

### Requirement: Pre-Check Logic SHALL Have Unit Tests

The verify pre-check function MUST have unit tests in `tests/test_diagnoser.py` (or a new test file) covering import detection, lint detection, and the pass-through case.

#### Scenario: Pre-check detects import error in changed file

- **Given** a temporary Python file with a broken import (`import nonexistent_xyz`)
- **When** the pre-check function is called on that file
- **Then** it SHALL return a failure result with `error_type="import_error"` and the file path

#### Scenario: Pre-check detects lint error in changed file

- **Given** a temporary Python file with an `E701` violation
- **When** the pre-check function is called on that file
- **Then** it SHALL return a failure result with `error_type="lint_error"` and the file path

#### Scenario: Pre-check passes on clean file

- **Given** a temporary Python file with no import or lint errors
- **When** the pre-check function is called on that file
- **Then** it SHALL return a pass result

### Requirement: Existing Tests MUST Continue to Pass

All existing tests in the project SHALL pass without modification. New code SHALL be additive — no existing public interface of `Diagnoser` (methods `hypothesize`, `instrument`, `targeted_fix`, `diagnose`) SHALL be removed or have its signature changed in a breaking way.

#### Scenario: Existing test suite passes after changes

- **Given** the new diagnoser and pre-check code is in place
- **When** `pytest tests/` is run
- **Then** all tests SHALL pass
- **And** `ruff check` SHALL report no errors
