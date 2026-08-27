# config-func-tests

ADDED requirements for test coverage of utility functions `_find_config` and `_resolve_env_vars` in `zsiga/config.py`.

## ADDED Requirements

### Requirement: _find_config discovery

The test suite SHALL verify `_find_config()` returns the first existing candidate path and raises `FileNotFoundError` when no candidate exists.

#### Scenario: _find_config returns current-dir config when it exists

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** a temporary directory containing a file named `zsiga.yaml`
- **When** `_find_config()` is called with the working directory set to that temp dir
- **Then** it SHALL return a `Path` whose `name` equals `"zsiga.yaml"` and `exists()` is `True`

#### Scenario: _find_config raises FileNotFoundError when no config exists

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** a temporary directory with no `zsiga.yaml` and `~/.zsiga/zsiga.yaml` absent
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError`

#### Scenario: _find_config falls back to home-dir config

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** current directory has no `zsiga.yaml` and `~/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** it SHALL return a `Path` ending with `.zsiga/zsiga.yaml`

### Requirement: _resolve_env_vars substitution

The test suite SHALL verify `_resolve_env_vars()` resolves `${VAR}` patterns, recurses through dicts and lists, and passes non-matching values unchanged.

#### Scenario: plain string passed through unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** the value `"hello"` (no `${}` markers)
- **When** `_resolve_env_vars("hello")` is called
- **Then** it SHALL return `"hello"`

#### Scenario: single env var resolved

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_KEY` is set to `"secret123"`
- **When** `_resolve_env_vars("${MY_KEY}")` is called
- **Then** it SHALL return `"secret123"`

#### Scenario: undefined env var resolves to empty string

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `UNSET_XYZ` is not defined
- **When** `_resolve_env_vars("${UNSET_XYZ}")` is called
- **Then** it SHALL return `""`

#### Scenario: dict values resolved recursively

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `HOST` is set to `"localhost"`
- **When** `_resolve_env_vars({"url": "${HOST}", "port": 8080})` is called
- **Then** it SHALL return `{"url": "localhost", "port": 8080}`

#### Scenario: list values resolved recursively

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ITEM` is set to `"resolved"`
- **When** `_resolve_env_vars(["${ITEM}", "static"])` is called
- **Then** it SHALL return `["resolved", "static"]`

#### Scenario: non-string non-dict non-list passed through

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** the value `42` (an integer)
- **When** `_resolve_env_vars(42)` is called
- **Then** it SHALL return `42`
