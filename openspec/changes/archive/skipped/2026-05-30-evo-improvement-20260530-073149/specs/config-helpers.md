# spec: config-helpers

## ADDED Requirements

### Requirement: Environment variable resolution

`_resolve_env_vars` SHALL recursively resolve `${VAR_NAME}` patterns in strings,
returning the environment variable value if set, or an empty string if unset.

#### Scenario: Resolve existing env var

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ZSIGA_TEST_VAR` is set to `"hello"`
- **When** `_resolve_env_vars("${ZSIGA_TEST_VAR}")` is called
- **Then** the return value SHALL be `"hello"`

#### Scenario: Resolve missing env var returns empty string

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ZSIGA_MISSING_VAR` is NOT set
- **When** `_resolve_env_vars("${ZSIGA_MISSING_VAR}")` is called
- **Then** the return value SHALL be `""`

#### Scenario: Recursive dict resolution

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_KEY` is set to `"resolved_val"`
- **When** `_resolve_env_vars({"key1": "${MY_KEY}", "key2": "plain"})` is called
- **Then** the return value SHALL be `{"key1": "resolved_val", "key2": "plain"}`

#### Scenario: Recursive list resolution

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ITEM` is set to `"resolved_item"`
- **When** `_resolve_env_vars(["${ITEM}", "static"])` is called
- **Then** the return value SHALL be `["resolved_item", "static"]`

#### Scenario: Non-string passthrough

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** an integer value `42`
- **When** `_resolve_env_vars(42)` is called
- **Then** the return value SHALL be `42`

#### Scenario: Plain string passthrough

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a plain string `"no-env-var-here"`
- **When** `_resolve_env_vars("no-env-var-here")` is called
- **Then** the return value SHALL be `"no-env-var-here"`

#### Scenario: Nested structure resolution

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `NESTED_VAR` is set to `"deep"`
- **When** `_resolve_env_vars({"outer": ["${NESTED_VAR}", 123]})` is called
- **Then** the return value SHALL be `{"outer": ["deep", 123]}`

### Requirement: Config file discovery

`_find_config` SHALL search for `zsiga.yaml` in the current directory first,
then `~/.zsiga/zsiga.yaml`, and raise `FileNotFoundError` if neither exists.

#### Scenario: Found in current directory

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** a file named `zsiga.yaml` exists in the current working directory
- **When** `_find_config()` is called
- **Then** it SHALL return a `Path` pointing to `zsiga.yaml` in the current directory

#### Scenario: Found in home directory

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** `zsiga.yaml` does NOT exist in the current directory
  AND `zsiga.yaml` exists at `~/.zsiga/zsiga.yaml`
- **When** `_find_config()` is called
- **Then** it SHALL return a `Path` pointing to `~/.zsiga/zsiga.yaml`

#### Scenario: Not found raises FileNotFoundError

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** `zsiga.yaml` exists in neither the current directory nor `~/.zsiga/`
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError` with message containing `"zsiga.yaml"`
