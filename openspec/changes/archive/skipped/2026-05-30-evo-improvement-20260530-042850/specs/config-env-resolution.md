# config-env-resolution

## ADDED Requirements

### Requirement: Environment variable resolution in config values

The `_resolve_env_vars` function SHALL recursively walk config structures (dicts, lists, strings)
and replace any string matching the pattern `${VAR_NAME}` with the value of the environment variable
`VAR_NAME`. If the variable is not set, the empty string SHALL be used. Non-matching strings and
non-string types SHALL pass through unchanged.

#### Scenario: Resolve existing env var

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `TEST_RESOLVE_VAR` is set to "resolved_value"
- **When** `_resolve_env_vars("${TEST_RESOLVE_VAR}")` is called
- **Then** the result is "resolved_value"

#### Scenario: Resolve missing env var

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `NONEXISTENT_ZSIGA_VAR_XYZ` is not set
- **When** `_resolve_env_vars("${NONEXISTENT_ZSIGA_VAR_XYZ}")` is called
- **Then** the result is ""

#### Scenario: Resolve dict values recursively

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `DICT_TEST_VAR` is set to "from_env"
- **When** `_resolve_env_vars({"key": "${DICT_TEST_VAR}", "other": "plain"})` is called
- **Then** the result is {"key": "from_env", "other": "plain"}

#### Scenario: Resolve list values recursively

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `LIST_TEST_VAR` is set to "list_val"
- **When** `_resolve_env_vars(["${LIST_TEST_VAR}", "static", 42])` is called
- **Then** the result is ["list_val", "static", 42]

#### Scenario: Plain string passthrough

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a plain string without `${...}` pattern
- **When** `_resolve_env_vars("just_a_string")` is called
- **Then** the result is "just_a_string"

#### Scenario: Non-string passthrough

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a non-string value (int, bool, None)
- **When** `_resolve_env_vars` is called with that value
- **Then** the value is returned unchanged (int remains int, bool remains bool, None remains None)

#### Scenario: Nested structure resolution

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `NESTED_VAR` is set to "deep_value"
- **When** `_resolve_env_vars({"outer": [{"inner": "${NESTED_VAR}"}]})` is called
- **Then** the result is {"outer": [{"inner": "deep_value"}]}

