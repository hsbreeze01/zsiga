# runner-events.md

## ADDED Requirements

### Requirement: Event dataclass construction and inheritance

The test file `tests/test_runner.py` SHALL verify that every event dataclass
in `zsiga.harness.runner` can be constructed with required fields, inherits from
`TestEvent`, and provides correct default values for optional fields.

#### Scenario: TestStarted inherits TestEvent and carries required fields

- **testable**: true
- **target**: zsiga/harness/runner.py::TestStarted

- **Given** the module `zsiga.harness.runner` is importable
- **When** `TestStarted(test_name="alpha", timestamp=1.0)` is constructed
- **Then** the instance `test_name` equals `"alpha"`, `timestamp` equals `1.0`,
  and `isinstance(instance, TestEvent)` is `True`

#### Scenario: TestPassed provides default duration_ms of zero

- **testable**: true
- **target**: zsiga/harness/runner.py::TestPassed

- **Given** the module `zsiga.harness.runner` is importable
- **When** `TestPassed(test_name="p", timestamp=2.0)` is constructed without
  specifying `duration_ms`
- **Then** `duration_ms` equals `0.0`

#### Scenario: TestFailed carries duration_ms and error_message

- **testable**: true
- **target**: zsiga/harness/runner.py::TestFailed

- **Given** the module `zsiga.harness.runner` is importable
- **When** `TestFailed(test_name="f", timestamp=3.0, duration_ms=50.0, error_message="boom")`
  is constructed
- **Then** `duration_ms` equals `50.0` and `error_message` equals `"boom"`

#### Scenario: TestError carries error_message with default empty string

- **testable**: true
- **target**: zsiga/harness/runner.py::TestError

- **Given** the module `zsiga.harness.runner` is importable
- **When** `TestError(test_name="e", timestamp=4.0)` is constructed without
  `error_message`
- **Then** `error_message` equals `""`

#### Scenario: TestEvent base class sets __test__ to False

- **testable**: true
- **target**: zsiga/harness/runner.py::TestEvent

- **Given** the module `zsiga.harness.runner` is importable
- **When** `TestEvent` class attribute `__test__` is inspected
- **Then** it SHALL equal `False` to prevent pytest collection

#### Scenario: All concrete event classes are subclasses of TestEvent

- **testable**: true
- **target**: zsiga/harness/runner.py::TestEvent

- **Given** the classes `TestStarted`, `TestPassed`, `TestFailed`, `TestError`
  from `zsiga.harness.runner`
- **When** each class is checked with `issubclass(cls, TestEvent)`
- **Then** every check SHALL return `True`
