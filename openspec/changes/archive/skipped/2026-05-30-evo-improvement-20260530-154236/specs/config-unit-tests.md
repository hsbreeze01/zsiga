# config-unit-tests

> Tests for `zsiga/config.py` entry points that lack dedicated unit-test coverage
> in a file named `tests/test_config.py`.  Existing coverage lives in
> `test_config_validation.py` (39 tests), `test_active_target_filter.py`,
> and archived `test_spec_*` files.  This spec defines the incremental
> behaviours that `tests/test_config.py` SHALL verify.

## ADDED Requirements

### Requirement: test-file-structure

The file `tests/test_config.py` SHALL exist and contain at least three
`def test_` functions, including `test__find_config`,
`test__resolve_env_vars`, and `test_validate_config`.

#### Scenario: test-file-exists

- **testable**: true
- **target**: tests/test_config.py
- **Given** the project root directory
- **When** checking for the file `tests/test_config.py`
- **Then** the file SHALL exist

#### Scenario: test-file-contains-required-functions

- **testable**: true
- **target**: tests/test_config.py
- **Given** the file `tests/test_config.py`
- **When** extracting all top-level function names starting with `test_`
- **Then** the set SHALL include `test__find_config`, `test__resolve_env_vars`, and `test_validate_config`
- **And** the total count of `def test_` functions SHALL be at least 3

---

### Requirement: find-config-discovers-file

`_find_config()` SHALL return a `Path` to the first existing config file
among the search candidates, or raise `FileNotFoundError` when none exists.

#### Scenario: find-config-in-current-dir

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** a temporary directory containing `zsiga.yaml`
- **And** the current working directory is set to that directory
- **When** `_find_config()` is called
- **Then** it SHALL return `Path("zsiga.yaml")`

#### Scenario: find-config-in-home-dir

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in the current directory
- **And** `~/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** it SHALL return `Path.home() / ".zsiga" / "zsiga.yaml"`

#### Scenario: find-config-not-found

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in the current directory or `~/.zsiga/`
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError`

---

### Requirement: resolve-env-vars-substitution

`_resolve_env_vars(value)` SHALL substitute `${VAR}` patterns with the
corresponding environment variable value, returning `""` for unset vars,
and SHALL recurse into dicts and lists.

#### Scenario: resolve-existing-env-var

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_KEY` is set to `"hello"`
- **When** `_resolve_env_vars("${MY_KEY}")` is called
- **Then** it SHALL return `"hello"`

#### Scenario: resolve-missing-env-var

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `NONEXISTENT_ZSIGA_VAR` is not set
- **When** `_resolve_env_vars("${NONEXISTENT_ZSIGA_VAR}")` is called
- **Then** it SHALL return `""`

#### Scenario: resolve-plain-string-passthrough

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a plain string `"just-text"` without `${…}` syntax
- **When** `_resolve_env_vars("just-text")` is called
- **Then** it SHALL return `"just-text"` unchanged

#### Scenario: resolve-nested-dict

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `HOST` is set to `"myhost"`
- **And** a dict `{"url": "http://${HOST}/api"}`
- **When** `_resolve_env_vars` is called with that dict
- **Then** the result SHALL equal `{"url": "http://${HOST}/api"}` (only exact `${…}` strings are resolved, not embedded patterns)

#### Scenario: resolve-dict-with-full-env-pattern

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_API_KEY` is set to `"secret123"`
- **And** a dict `{"api_key": "${MY_API_KEY}"}`
- **When** `_resolve_env_vars` is called with that dict
- **Then** the result SHALL equal `{"api_key": "secret123"}`

#### Scenario: resolve-list

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ITEM` is set to `"resolved"`
- **And** a list `["${ITEM}", "plain"]`
- **When** `_resolve_env_vars` is called with that list
- **Then** the result SHALL equal `["resolved", "plain"]`

#### Scenario: resolve-non-string-passthrough

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** an integer `42`
- **When** `_resolve_env_vars(42)` is called
- **Then** it SHALL return `42` unchanged

---

### Requirement: validate-config-domain-warning

`validate_config(config)` SHALL emit a warning when a target's `domain`
field is neither `""`, `"self"`, nor `"external"`.

#### Scenario: validate-domain-invalid-value

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` with a target whose `domain` is `"unknown"`
- **When** `validate_config(config)` is called
- **Then** the result SHALL be valid (no errors)
- **And** `result.warnings` SHALL contain a string including `"domain"`
