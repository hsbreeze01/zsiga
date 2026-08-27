# Spec: config-helpers

## ADDED Requirements

### Requirement: Config file discovery

The system SHALL provide a `_find_config()` function that locates the configuration file by searching a prioritized list of candidate paths.

#### Scenario: find_config_returns_current_dir_yaml_when_exists

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** a file named `zsiga.yaml` exists in the current working directory
- **When** `_find_config()` is called
- **Then** it SHALL return `Path("zsiga.yaml")`

#### Scenario: find_config_falls_back_to_home_dir

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** `zsiga.yaml` does NOT exist in the current working directory AND `~/.zsiga/zsiga.yaml` DOES exist
- **When** `_find_config()` is called
- **Then** it SHALL return `Path.home() / ".zsiga" / "zsiga.yaml"`

#### Scenario: find_config_raises_file_not_found

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** neither `zsiga.yaml` nor `~/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError` with a message containing "zsiga.yaml"

---

### Requirement: Environment variable resolution

The system SHALL provide a `_resolve_env_vars(value)` function that recursively substitutes `${VAR}` references with their environment variable values.

#### Scenario: resolve_env_vars_string_substitution

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_KEY` is set to `"secret_value"`
- **When** `_resolve_env_vars("${MY_KEY}")` is called
- **Then** the result SHALL be `"secret_value"`

#### Scenario: resolve_env_vars_missing_var_returns_empty

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `NONEXISTENT_VAR_XYZ` is NOT set
- **When** `_resolve_env_vars("${NONEXISTENT_VAR_XYZ}")` is called
- **Then** the result SHALL be `""`

#### Scenario: resolve_env_vars_plain_string_passthrough

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a plain string `"hello"` that does NOT start with `${` and end with `}`
- **When** `_resolve_env_vars("hello")` is called
- **Then** the result SHALL be `"hello"` (unchanged)

#### Scenario: resolve_env_vars_dict_recursive

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `API_KEY` is set to `"abc123"` AND a dict `{"key": "${API_KEY}", "port": 8080}`
- **When** `_resolve_env_vars` is called with that dict
- **Then** the result SHALL be `{"key": "abc123", "port": 8080}`

#### Scenario: resolve_env_vars_list_recursive

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `HOST` is set to `"myhost"` AND a list `["${HOST}", "static"]`
- **When** `_resolve_env_vars` is called with that list
- **Then** the result SHALL be `["myhost", "static"]`

#### Scenario: resolve_env_vars_non_string_passthrough

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** an integer value `42`
- **When** `_resolve_env_vars(42)` is called
- **Then** the result SHALL be `42` (unchanged)

