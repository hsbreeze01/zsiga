# config-discovery

## ADDED Requirements

### Requirement: config-discovery-test-file-exists

A test file `tests/test_config.py` SHALL exist in the project test directory.

#### Scenario: test file present on disk

- **testable**: true
- **target**: tests/test_config.py
- **Given** the project repository root
- **When** checking for the existence of `tests/test_config.py`
- **Then** the file SHALL exist

---

### Requirement: config-discovery-minimum-test-functions

The test file `tests/test_config.py` SHALL contain at least 3 top-level test functions.

#### Scenario: minimum test function count

- **testable**: true
- **target**: tests/test_config.py
- **Given** the file `tests/test_config.py` exists
- **When** counting the number of `def test_` function definitions in the file
- **Then** the count SHALL be greater than or equal to 3

---

### Requirement: config-discovery-named-test-functions

The test file `tests/test_config.py` SHALL contain the specific test functions `test__find_config`, `test__resolve_env_vars`, and `test_validate_config`.

#### Scenario: required test function names present

- **testable**: true
- **target**: tests/test_config.py
- **Given** the file `tests/test_config.py` exists
- **When** checking for function definitions named `test__find_config`, `test__resolve_env_vars`, and `test_validate_config`
- **Then** all three function names SHALL be present

---

### Requirement: config-discovery-pytest-passes

All tests in `tests/test_config.py` SHALL pass when executed by pytest.

#### Scenario: pytest exit code zero

- **testable**: true
- **target**: tests/test_config.py
- **Given** the project with `zsiga/config.py` available and `tests/test_config.py` exists
- **When** running `python -m pytest tests/test_config.py -x --tb=short`
- **Then** the exit code SHALL be 0
