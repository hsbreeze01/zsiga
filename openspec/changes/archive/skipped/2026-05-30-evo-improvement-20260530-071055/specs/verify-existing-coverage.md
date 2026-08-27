# verify-existing-coverage

## ADDED Requirements

### Requirement: Existing test file covers harness runner public API

The module `zsiga/harness/runner.py` SHALL be considered fully tested by
`tests/test_harness_runner.py`. No additional test file (`tests/test_runner.py`)
SHALL be created for this module.

The existing test file MUST contain test functions covering all 10 public
classes defined in `zsiga/harness/runner.py`: TestEvent, TestStarted,
TestPassed, TestFailed, TestError, HarnessResult, TestReport,
QualificationReport, HarnessRunner, and _HarnessCollectorPlugin.

#### Scenario: Existing test file has sufficient test count

- **testable**: true
- **target**: tests/test_harness_runner.py
- **Given** `tests/test_harness_runner.py` exists in the project
- **When** counting all `def test_` function definitions in the file
- **Then** the count SHALL be at least 18

#### Scenario: Redundant test file must not exist

- **testable**: true
- **target**: tests/test_runner.py
- **Given** the project has `tests/test_harness_runner.py` covering `zsiga/harness/runner.py`
- **When** checking whether `tests/test_runner.py` exists
- **Then** `tests/test_runner.py` SHALL NOT exist (path.exists() returns False)

#### Scenario: Existing tests pass

- **testable**: true
- **target**: tests/test_harness_runner.py
- **Given** `tests/test_harness_runner.py` exists
- **When** running `python -m pytest tests/test_harness_runner.py`
- **Then** the exit code SHALL be 0

#### Scenario: Existing test file covers all runner public classes

- **testable**: true
- **target**: tests/test_harness_runner.py
- **Given** `zsiga/harness/runner.py` defines classes TestEvent, TestStarted, TestPassed, TestFailed, TestError, HarnessResult, HarnessRunner, QualificationReport, TestReport
- **When** `tests/test_harness_runner.py` is analyzed for test class/group names
- **Then** it SHALL contain at minimum: TestEventDataclasses, TestHarnessResult, TestHarnessRunnerDiscover, TestHarnessRunnerRun, TestHarnessRunnerPytestFailClosed

### Requirement: Proposal loop terminated

This change (`evo-improvement-20260530-071055`) SHALL be resolved as a
verification-only action. No source code files SHALL be created or modified
in the `zsiga/` or `tests/` directories as a result of this change.

#### Scenario: No source files created by this change

- **testable**: false
- **Given** this change is processed
- **When** inspecting the git diff on the deploy branch
- **Then** no files under `zsiga/` or `tests/` SHALL appear in the diff
  (only openspec metadata files may change)
