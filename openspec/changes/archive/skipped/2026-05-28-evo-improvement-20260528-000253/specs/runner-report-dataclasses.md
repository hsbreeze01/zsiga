# runner-report-dataclasses

## ADDED Requirements

### Requirement: TestEvent base class is not collected by pytest

`TestEvent` SHALL set `__test__ = False` as a class attribute so that pytest
does not attempt to collect it as a test class.

#### Scenario: TestEvent base class has __test__ = False

- **testable**: true
- **target**: zsiga/harness/runner.py::TestEvent
- **Given** the `TestEvent` class definition
- **When** `TestEvent.__test__` is accessed
- **Then** the value is `False`

### Requirement: TestStarted inherits TestEvent fields

`TestStarted` SHALL inherit `test_name` and `timestamp` from `TestEvent`
without adding additional required fields.

#### Scenario: TestStarted preserves inherited test_name and timestamp

- **testable**: true
- **target**: zsiga/harness/runner.py::TestStarted
- **Given** a `TestStarted` constructed with `test_name="t1"`, `timestamp=1.0`
- **When** `test_name` and `timestamp` fields are accessed
- **Then** `test_name == "t1"` and `timestamp == 1.0`

### Requirement: TestPassed defaults duration_ms to zero

`TestPassed` SHALL default `duration_ms` to `0.0` when not provided.

#### Scenario: TestPassed defaults duration_ms to 0.0

- **testable**: true
- **target**: zsiga/harness/runner.py::TestPassed
- **Given** a `TestPassed` constructed with only `test_name="x"`, `timestamp=1.0`
- **When** `duration_ms` field is accessed
- **Then** it equals `0.0`

### Requirement: TestFailed defaults optional fields

`TestFailed` SHALL default `duration_ms` to `0.0` and `error_message` to `""`
when not provided.

#### Scenario: TestFailed defaults duration_ms and error_message

- **testable**: true
- **target**: zsiga/harness/runner.py::TestFailed
- **Given** a `TestFailed` constructed with only `test_name="x"`, `timestamp=1.0`
- **When** `duration_ms` and `error_message` fields are accessed
- **Then** `duration_ms == 0.0` and `error_message == ""`

### Requirement: TestError defaults error_message to empty string

`TestError` SHALL default `error_message` to `""` when not provided.

#### Scenario: TestError defaults error_message to empty string

- **testable**: true
- **target**: zsiga/harness/runner.py::TestError
- **Given** a `TestError` constructed with only `test_name="x"`, `timestamp=1.0`
- **When** `error_message` field is accessed
- **Then** it equals `""`

### Requirement: HarnessResult defaults to zero counts and empty events

`HarnessResult` SHALL default `total`, `passed`, `failed`, `errors` to `0`
and `events` to an empty list when constructed without arguments.

#### Scenario: HarnessResult defaults to zeros and empty events

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessResult
- **Given** a `HarnessResult` constructed with no arguments
- **When** all fields are accessed
- **Then** `total == 0`, `passed == 0`, `failed == 0`, `errors == 0`, and `events == []`
