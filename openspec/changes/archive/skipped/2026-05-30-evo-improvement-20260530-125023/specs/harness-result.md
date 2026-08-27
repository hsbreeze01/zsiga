# harness-result

## ADDED Requirements

### Requirement: HarnessResult Default and Custom Construction

The test file `tests/test_runner.py` SHALL contain unit tests verifying that
`HarnessResult` initializes with zero counts and an empty events list, and that
custom values are stored correctly.

#### Scenario: Default HarnessResult has zero counts and empty events

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessResult

- **Given** the module `zsiga.harness.runner` is importable
- **When** `HarnessResult()` is constructed with no arguments
- **Then** `.total == 0`, `.passed == 0`, `.failed == 0`, `.errors == 0`, and `.events == []`

#### Scenario: HarnessResult stores custom values

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessResult

- **Given** the module `zsiga.harness.runner` is importable
- **When** `HarnessResult(total=3, passed=2, failed=1, errors=0)` is constructed
- **Then** `.total == 3`, `.passed == 2`, `.failed == 1`, `.errors == 0`

#### Scenario: HarnessResult events list is independent per instance

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessResult

- **Given** two instances `r1 = HarnessResult()` and `r2 = HarnessResult()`
- **When** an event is appended to `r1.events`
- **Then** `r2.events` remains `[]` (no shared mutable default)
