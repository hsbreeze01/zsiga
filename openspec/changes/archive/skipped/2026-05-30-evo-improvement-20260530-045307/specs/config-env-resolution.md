# Spec: config-env-resolution

## ADDED Requirements

### Requirement: _find_config locates config file

The `_find_config()` function SHALL search for `zsiga.yaml` in the current working directory first, then in `~/.zsiga/zsiga.yaml` as fallback. If neither exists, it MUST raise `FileNotFoundError`.

#### Scenario: Find config in current directory

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** a directory containing `zsiga.yaml`
- **When** `_find_config()` is called with that directory as cwd
- **Then** it returns `Path("zsiga.yaml")`

#### Scenario: Find config in home directory fallback

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** cwd has no `zsiga.yaml` and `~/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** it returns the path under the home directory

#### Scenario: Raise FileNotFoundError when no config exists

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** neither cwd nor `~/.zsiga/` contains `zsiga.yaml`
- **When** `_find_config()` is called
- **Then** it raises `FileNotFoundError` with message containing "zsiga.yaml not found"

### Requirement: _resolve_env_vars substitutes environment variables

The `_resolve_env_vars(value)` function SHALL resolve `${VAR_NAME}` patterns by reading from `os.environ`. Missing variables resolve to empty string. It MUST recurse into dicts and lists, and pass through non-matching values unchanged.

#### Scenario: Resolve existing environment variable

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `TEST_RESOLVE_VAR` is set to `"resolved_value"`
- **When** `_resolve_env_vars("${TEST_RESOLVE_VAR}")` is called
- **Then** it returns `"resolved_value"`

#### Scenario: Missing environment variable returns empty string

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `NONEXISTENT_ZSIGA_VAR_XYZ` is not set
- **When** `_resolve_env_vars("${NONEXISTENT_ZSIGA_VAR_XYZ}")` is called
- **Then** it returns `""`

#### Scenario: Resolve dict values recursively

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `DICT_TEST_VAR` is set to `"from_env"`
- **When** `_resolve_env_vars({"key": "${DICT_TEST_VAR}", "other": "plain"})` is called
- **Then** it returns `{"key": "from_env", "other": "plain"}`

#### Scenario: Resolve list values recursively

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `LIST_TEST_VAR` is set to `"list_val"`
- **When** `_resolve_env_vars(["${LIST_TEST_VAR}", "static", 42])` is called
- **Then** it returns `["list_val", "static", 42]`

#### Scenario: Plain string passthrough

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a plain string without `${...}` pattern
- **When** `_resolve_env_vars("just_a_string")` is called
- **Then** it returns `"just_a_string"` unchanged

#### Scenario: Non-string value passthrough

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** non-string values (int, bool, None, float)
- **When** `_resolve_env_vars()` is called with each value
- **Then** it returns the value unchanged

#### Scenario: Nested structure resolution

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `NESTED_VAR` is set to `"deep_value"`
- **When** `_resolve_env_vars({"outer": [{"inner": "${NESTED_VAR}"}]})` is called
- **Then** it returns `{"outer": [{"inner": "deep_value"}]}`

