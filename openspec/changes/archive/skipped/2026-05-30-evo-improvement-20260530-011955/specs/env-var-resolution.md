# env-var-resolution — Environment Variable Resolution in Config Values

## ADDED Requirements

### Requirement: String env var interpolation

`_resolve_env_vars()` SHALL resolve strings matching the pattern `${ENV_VAR}` by replacing them with the corresponding environment variable value, or an empty string if the variable is not set.

#### Scenario: Resolves a single env var reference

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_KEY` is set to `"secret123"`
- **When** `_resolve_env_vars("${MY_KEY}")` is called
- **Then** it SHALL return `"secret123"`

#### Scenario: Returns empty string for unset env var

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `UNSET_VAR_XYZ` is not set
- **When** `_resolve_env_vars("${UNSET_VAR_XYZ}")` is called
- **Then** it SHALL return `""`

#### Scenario: Passes through non-interpolated strings unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a plain string value `"hello"`
- **When** `_resolve_env_vars("hello")` is called
- **Then** it SHALL return `"hello"`

### Requirement: Recursive resolution in containers

`_resolve_env_vars()` SHALL recursively traverse dict and list values, resolving any env var references found at any nesting depth.

#### Scenario: Resolves env vars inside a dict

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_HOST` is set to `"example.com"`
- **When** `_resolve_env_vars({"host": "${MY_HOST}", "port": 22})` is called
- **Then** it SHALL return `{"host": "example.com", "port": 22}`

#### Scenario: Resolves env vars inside a list

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ITEM_A` is set to `"alpha"`
- **When** `_resolve_env_vars(["${ITEM_A}", "plain", 42])` is called
- **Then** it SHALL return `["alpha", "plain", 42]`

### Requirement: Non-string passthrough

`_resolve_env_vars()` SHALL return non-string, non-dict, non-list values unchanged.

#### Scenario: Passes through integer value unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** an integer value `42`
- **When** `_resolve_env_vars(42)` is called
- **Then** it SHALL return `42`
