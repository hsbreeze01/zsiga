# runner-unit-tests

> **Status**: Delta spec for `zsiga/harness/runner.py` test coverage.
> **Note**: `tests/test_harness_runner.py` already exists with 277 lines / 20 tests covering
> all 10 public symbols. This spec defines the additional `tests/test_runner.py` file required
> by the proposal's BAC items. The resulting file will be structurally redundant with the
> existing test file.

## ADDED Requirements

### Requirement: Runner test file presence

The project SHALL contain a file `tests/test_runner.py` that provides unit-level
test coverage for the public symbols exported by `zsiga.harness.runner`.

#### Scenario: test_runner_py_file_exists

- **testable**: true
- **target**: tests/test_runner.py

- **Given** the project root directory
- **When** checking for the existence of `tests/test_runner.py`
- **Then** the file SHALL exist and be a valid Python source file

---

### Requirement: Module import and smoke tests

The file `tests/test_runner.py` SHALL contain at minimum two functions named
`test_module_import` and `test_module_smoke` that verify the `zsiga.harness.runner`
module can be imported and its primary public symbols are accessible.

#### Scenario: test_module_import_function_present

- **testable**: true
- **target**: tests/test_runner.py::test_module_import

- **Given** the file `tests/test_runner.py` exists
- **When** parsing the file's AST for top-level function definitions
- **Then** a function named `test_module_import` SHALL be present

#### Scenario: test_module_smoke_function_present

- **testable**: true
- **target**: tests/test_runner.py::test_module_smoke

- **Given** the file `tests/test_runner.py` exists
- **When** parsing the file's AST for top-level function definitions
- **Then** a function named `test_module_smoke` SHALL be present

---

### Requirement: Minimum test function count

The file `tests/test_runner.py` SHALL contain at least one `def test_*` function.

#### Scenario: at_least_one_test_function

- **testable**: true
- **target**: tests/test_runner.py

- **Given** the file `tests/test_runner.py` exists
- **When** counting all top-level and class-method functions whose names start with `test_`
- **Then** the count SHALL be >= 1

---

### Requirement: All tests pass under pytest

Every test function in `tests/test_runner.py` SHALL pass when executed via
`python -m pytest tests/test_runner.py`.

#### Scenario: pytest_exits_zero

- **testable**: true
- **target**: tests/test_runner.py

- **Given** the file `tests/test_runner.py` exists in the project
- **When** running `python -m pytest tests/test_runner.py`
- **Then** the pytest process SHALL exit with code 0

---

### Requirement: Event dataclass field structure

Tests in `tests/test_runner.py` SHALL verify that each event dataclass
(`TestStarted`, `TestPassed`, `TestFailed`, `TestError`) inherits from
`TestEvent` and exposes its documented fields.

#### Scenario: event_inheritance_and_fields

- **testable**: true
- **target**: zsiga/harness/runner.py::TestStarted

- **Given** the module `zsiga.harness.runner` is imported
- **When** instantiating each event dataclass with valid field values
- **Then** the instance SHALL be an instance of `TestEvent` and all assigned fields SHALL
  be retrievable via attribute access

---

### Requirement: HarnessRunner discover behaviour

Tests in `tests/test_runner.py` SHALL verify that `HarnessRunner.discover()` returns
`test_*.py` files from a given directory and raises `FileNotFoundError` for
non-existent directories.

#### Scenario: discover_finds_test_files

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.discover

- **Given** a temporary directory containing files `test_a.py`, `test_b.py`, and `helper.py`
- **When** calling `HarnessRunner().discover(temp_dir)`
- **Then** the returned list SHALL contain `test_a.py` and `test_b.py` but NOT `helper.py`

#### Scenario: discover_raises_on_missing_directory

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.discover

- **Given** a path that does not exist on the filesystem
- **When** calling `HarnessRunner().discover(nonexistent_path)`
- **Then** a `FileNotFoundError` SHALL be raised

---

### Requirement: HarnessRunner run behaviour

Tests in `tests/test_runner.py` SHALL verify that `HarnessRunner.run()` correctly
counts passed, failed, and error outcomes and emits the corresponding event types.

#### Scenario: run_counts_passing_tests

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a temporary directory with one test file containing a single passing test function
- **When** calling `HarnessRunner().discover(dir)` then `.run()`
- **Then** the returned `HarnessResult` SHALL have `passed == 1`, `failed == 0`, `errors == 0`

#### Scenario: run_counts_failing_tests

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a temporary directory with one test file containing `assert False`
- **When** calling `HarnessRunner().discover(dir)` then `.run()`
- **Then** the returned `HarnessResult` SHALL have `failed == 1`, `passed == 0`
