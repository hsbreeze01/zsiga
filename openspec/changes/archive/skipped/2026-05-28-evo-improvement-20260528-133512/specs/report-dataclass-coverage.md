# Report Dataclass Test Coverage

## ADDED Requirements

### Requirement: TestReport dataclass

`TestReport` SHALL be a dataclass with four positional fields:
`name` (str), `status` (str, one of `"passed"`|`"failed"`|`"error"`),
`duration_s` (float), `message` (str).

`TestReport` SHALL set `__test__ = False` to prevent pytest collection.

#### Scenario: Construct TestReport with all fields

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport

- **Given** the `TestReport` dataclass
- **When** constructed with `name="t1"`, `status="passed"`, `duration_s=0.5`, `message=""`
- **Then** all four fields SHALL equal the constructor arguments

#### Scenario: TestReport is not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::TestReport

- **Given** the `TestReport` class
- **When** its `__test__` attribute is inspected
- **Then** it SHALL be `False`

---

### Requirement: QualificationReport dataclass

`QualificationReport` SHALL be a dataclass with three fields:
`capability_results` (list[TestReport]), `regression_results` (list[TestReport]),
`passed` (bool). The caller computes `passed`; the dataclass does not derive it.

`QualificationReport` SHALL set `__test__ = False`.

#### Scenario: QualificationReport all-passing

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** two `TestReport` instances with `status="passed"`
- **When** a `QualificationReport` is constructed with both lists and `passed=True`
- **Then** `passed` SHALL be `True` and both lists SHALL be non-empty

#### Scenario: QualificationReport with mixed results

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** one `TestReport` with `status="passed"` and one with `status="failed"`
- **When** a `QualificationReport` is constructed with `passed=False`
- **Then** `passed` SHALL be `False`

#### Scenario: QualificationReport is not collected by pytest

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** the `QualificationReport` class
- **When** its `__test__` attribute is inspected
- **Then** it SHALL be `False`

#### Scenario: QualificationReport with empty lists

- **testable**: true
- **target**: zsiga/harness/runner.py::QualificationReport

- **Given** empty `capability_results` and `regression_results` lists
- **When** a `QualificationReport` is constructed with `passed=True`
- **Then** both lists SHALL be empty and `passed` SHALL be `True`
