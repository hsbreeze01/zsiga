# event-dataclasses

## ADDED Requirements

### Requirement: Event Dataclass Construction and Inheritance

The test file `tests/test_runner.py` SHALL contain unit tests that verify every
event dataclass exported by `zsiga.harness.runner` can be constructed with
required fields, produces correct default values for optional fields, and
participates in the expected inheritance hierarchy (`TestStarted`, `TestPassed`,
`TestFailed`, `TestError` are all subclasses of `TestEvent`).

#### Scenario: Construct TestStarted with required fields

- **testable**: true
- **target**: zsiga/harness/runner.py::TestStarted

- **Given** the module `zsiga.harness.runner` is importable
- **When** `TestStarted(test_name="alpha", timestamp=1.0)` is called
- **Then** the resulting object has `.test_name == "alpha"` and `.timestamp == 1.0`

#### Scenario: TestPassed has default duration_ms of zero

- **testable**: true
- **target**: zsiga/harness/runner.py::TestPassed

- **Given** the module `zsiga.harness.runner` is importable
- **When** `TestPassed(test_name="t", timestamp=0.0)` is constructed without `duration_ms`
- **Then** `.duration_ms` equals `0.0`

#### Scenario: TestFailed has default duration_ms and error_message

- **testable**: true
- **target**: zsiga/harness/runner.py::TestFailed

- **Given** the module `zsiga.harness.runner` is importable
- **When** `TestFailed(test_name="t", timestamp=0.0)` is constructed without optional args
- **Then** `.duration_ms == 0.0` and `.error_message == ""`

#### Scenario: TestError has default error_message

- **testable**: true
- **target**: zsiga/harness/runner.py::TestError

- **Given** the module `zsiga.harness.runner` is importable
- **When** `TestError(test_name="t", timestamp=0.0)` is constructed without `error_message`
- **Then** `.error_message == ""`

#### Scenario: All event subclasses are instances of TestEvent

- **testable**: true
- **target**: zsiga/harness/runner.py::TestEvent

- **Given** instances of `TestStarted`, `TestPassed`, `TestFailed`, and `TestError`
- **When** each instance is checked with `isinstance(obj, TestEvent)`
- **Then** all checks return `True`

#### Scenario: TestEvent has __test__ set to False

- **testable**: true
- **target**: zsiga/harness/runner.py::TestEvent.__test__

- **Given** the class `TestEvent` from `zsiga.harness.runner`
- **When** `TestEvent.__test__` is accessed
- **Then** its value is `False`
