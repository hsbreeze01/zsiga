# config-test-coverage

Delta spec for adding **incremental** unit test coverage of `zsiga/config.py`
private functions (`_find_config`, `_resolve_env_vars`) and one uncovered
`validate_config` branch (domain warning).

**Overlap note**: `tests/test_config_validation.py` already provides ~39 tests
for `validate_config`, `ValidationResult`, `ConfigValidationError`, `load_config`
integration, and all 13 dataclasses.  This spec ONLY covers gaps not exercised
by the existing file.

---

## ADDED Requirements

### Requirement: _find_config Function Behavior

`_find_config()` SHALL search a list of candidate paths (`zsiga.yaml` in the
current directory, then `~/.zsiga/zsiga.yaml`) and return the first existing
one as a `Path`.  If no candidate exists it SHALL raise `FileNotFoundError`.

#### Scenario: find_config_returns_first_existing_candidate

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** a `zsiga.yaml` file exists in the current working directory
- **When** `_find_config()` is called
- **Then** it SHALL return a `Path` pointing to that file

#### Scenario: find_config_falls_back_to_home_dir

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in the current directory but a file exists under
  `~/.zsiga/zsiga.yaml`
- **When** `_find_config()` is called
- **Then** it SHALL return a `Path` equal to `Path.home() / ".zsiga" / "zsiga.yaml"`

#### Scenario: find_config_raises_file_not_found

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** no candidate config file exists in any searchable location
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError`

---

### Requirement: _resolve_env_vars Function Behavior

`_resolve_env_vars()` SHALL expand `${VAR}` patterns using environment
variables, recurse into dicts and lists, and pass through non-matching strings
and non-string values unchanged.

#### Scenario: resolve_env_vars_expands_dollar_brace_pattern

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ZSIGA_TEST_VAR` is set to `"resolved_value"`
- **When** `_resolve_env_vars("${ZSIGA_TEST_VAR}")` is called
- **Then** it SHALL return `"resolved_value"`

#### Scenario: resolve_env_vars_returns_empty_for_missing_var

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ZSIGA_NONEXISTENT_VAR` is not set
- **When** `_resolve_env_vars("${ZSIGA_NONEXISTENT_VAR}")` is called
- **Then** it SHALL return `""`

#### Scenario: resolve_env_vars_passthrough_plain_string

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a plain string `"hello"` that does not match `${...}` pattern
- **When** `_resolve_env_vars("hello")` is called
- **Then** it SHALL return `"hello"` unchanged

#### Scenario: resolve_env_vars_passthrough_non_string

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a non-string value such as `42`
- **When** `_resolve_env_vars(42)` is called
- **Then** it SHALL return `42` unchanged

#### Scenario: resolve_env_vars_recurses_into_dict

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ZSIGA_HOST` is set to `"example.com"`
- **When** `_resolve_env_vars({"key": "${ZSIGA_HOST}"})` is called
- **Then** it SHALL return `{"key": "example.com"}`

#### Scenario: resolve_env_vars_recurses_into_list

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ZSIGA_ITEM` is set to `"value"`
- **When** `_resolve_env_vars(["${ZSIGA_ITEM}", 123])` is called
- **Then** it SHALL return `["value", 123]`

---

### Requirement: validate_config Domain Warning Branch

`validate_config()` SHALL emit a warning when a target's `domain` field is
neither `""`, `"self"`, nor `"external"`.  This branch is NOT covered by the
existing `tests/test_config_validation.py`.

#### Scenario: validate_config_warns_on_unrecognized_domain

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"unknown"`
- **When** `validate_config(config)` is called
- **Then** the returned `ValidationResult` SHALL have `valid == True` and at
  least one warning containing `"domain"`

#### Scenario: validate_config_no_domain_warning_for_self

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"self"`
- **When** `validate_config(config)` is called
- **Then** no warning containing `"domain"` SHALL appear in `result.warnings`

---

### Requirement: Test File and Pass Condition

#### Scenario: all_config_tests_pass

- **testable**: true
- **target**: tests/test_config.py
- **Given** `tests/test_config.py` exists with all required test functions
- **When** `python -m pytest tests/test_config.py` is executed
- **Then** the process SHALL exit with code 0
