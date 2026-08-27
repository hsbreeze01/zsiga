# config-env-resolution

## ADDED Requirements

### Requirement: resolve-env-var-basic-substitution

`_resolve_env_vars` SHALL replace a string value of the form `${VAR_NAME}` with the value of the environment variable `VAR_NAME`.

#### Scenario: env-var-present

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** the environment variable `MY_TEST_KEY` is set to `"secret123"`
- **When** `_resolve_env_vars("${MY_TEST_KEY}")` is called
- **Then** the result SHALL be `"secret123"`

---

### Requirement: resolve-env-var-missing

`_resolve_env_vars` SHALL return an empty string when the referenced environment variable is not set.

#### Scenario: env-var-absent

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** the environment variable `NONEXISTENT_VAR_XYZ` is NOT set
- **When** `_resolve_env_vars("${NONEXISTENT_VAR_XYZ}")` is called
- **Then** the result SHALL be `""`

---

### Requirement: resolve-env-var-non-string-passthrough

`_resolve_env_vars` SHALL return non-string values unchanged.

#### Scenario: integer-passthrough

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** an integer value `42`
- **When** `_resolve_env_vars(42)` is called
- **Then** the result SHALL be `42`

#### Scenario: none-passthrough

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a `None` value
- **When** `_resolve_env_vars(None)` is called
- **Then** the result SHALL be `None`

---

### Requirement: resolve-env-var-dict-recursive

`_resolve_env_vars` SHALL recursively resolve `${VAR}` placeholders in all string values within a dictionary.

#### Scenario: dict-with-env-vars

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** the environment variable `HOST` is set to `"example.com"`
- **And** a dictionary `{"host": "${HOST}", "timeout": 30}`
- **When** `_resolve_env_vars` is called with that dictionary
- **Then** the result SHALL be `{"host": "example.com", "timeout": 30}`

---

### Requirement: resolve-env-var-list-recursive

`_resolve_env_vars` SHALL recursively resolve `${VAR}` placeholders in all string elements within a list.

#### Scenario: list-with-env-vars

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** the environment variable `MY_ITEM` is set to `"resolved"`
- **And** a list `["${MY_ITEM}", 42, "plain"]`
- **When** `_resolve_env_vars` is called with that list
- **Then** the result SHALL be `["resolved", 42, "plain"]`
