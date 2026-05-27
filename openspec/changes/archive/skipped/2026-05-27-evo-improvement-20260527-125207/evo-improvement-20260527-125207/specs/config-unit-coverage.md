# config-unit-coverage

Describes test-coverage requirements for two currently-untested private
functions in `zsiga/config.py`: `_resolve_env_vars` and `_find_config`.
Both functions have **existing, correct behavior** — they simply lack
unit tests.  This spec documents their contracts as testable scenarios.

---

## ADDED Requirements

### Requirement: _resolve_env_vars resolves environment variable placeholders

`_resolve_env_vars` SHALL resolve `${VAR_NAME}` string patterns to the
corresponding environment variable value, returning `""` for unset
variables.  Non-string values SHALL pass through unchanged.  Dict and
list values SHALL be resolved recursively.

#### Scenario: Resolves dollar-brace VAR to environment value

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ZSIGA_TEST_HOST` is set to `"example.com"`
- **When** `_resolve_env_vars("${ZSIGA_TEST_HOST}")` is called
- **Then** it SHALL return `"example.com"`

#### Scenario: Missing env var resolves to empty string

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ZSIGA_NONEXISTENT_9999` is not set
- **When** `_resolve_env_vars("${ZSIGA_NONEXISTENT_9999}")` is called
- **Then** it SHALL return `""`

#### Scenario: Non-string values pass through unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** an integer value `42`
- **When** `_resolve_env_vars(42)` is called
- **Then** it SHALL return `42`

#### Scenario: Nested dict values are resolved recursively

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ZSIGA_TEST_HOST` is set to `"myhost"`
- **When** `_resolve_env_vars({"server": {"host": "${ZSIGA_TEST_HOST}", "port": 8080}})` is called
- **Then** it SHALL return `{"server": {"host": "myhost", "port": 8080}}`

#### Scenario: List values are resolved recursively

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ZSIGA_TEST_ITEM` is set to `"resolved"`
- **When** `_resolve_env_vars(["${ZSIGA_TEST_ITEM}", "static", 123])` is called
- **Then** it SHALL return `["resolved", "static", 123]`

#### Scenario: Plain string without placeholder passes through unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a plain string `"hello world"`
- **When** `_resolve_env_vars("hello world")` is called
- **Then** it SHALL return `"hello world"`

---

### Requirement: _find_config discovers configuration files

`_find_config` SHALL search a list of candidate paths and return the
first existing one as a `Path`.  When no candidate exists it SHALL raise
`FileNotFoundError` with a message containing `"zsiga.yaml"`.

#### Scenario: Finds config in current directory

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** the current working directory contains a file named `zsiga.yaml`
- **When** `_find_config()` is called
- **Then** it SHALL return a `Path` object whose name is `"zsiga.yaml"`

#### Scenario: Raises FileNotFoundError when no config exists

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` exists in the current directory or in `~/.zsiga/`
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError` with a message containing `"zsiga.yaml"`
