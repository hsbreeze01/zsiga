# config-edge-cases

## ADDED Requirements

### Requirement: _find_config falls back to home directory

When `zsiga.yaml` is not found in the current working directory, the system
SHALL search `~/.zsiga/zsiga.yaml` as a fallback.

#### Scenario: config only in home directory

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** the current working directory has no `zsiga.yaml`
- **And** `~/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** the returned path SHALL point to `~/.zsiga/zsiga.yaml`

---

### Requirement: _resolve_env_vars only resolves exact placeholder

The system SHALL only resolve strings that are **exactly** `${VAR_NAME}` —
a dollar-brace at the start and closing brace at the end. Strings with
additional surrounding characters SHALL pass through unchanged.

#### Scenario: partial placeholder not resolved

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_VAR` is set to `"hello"`
- **When** `_resolve_env_vars("prefix${MY_VAR}")` is called
- **Then** the return value SHALL be `"prefix${MY_VAR}"` (unchanged)

#### Scenario: embedded placeholder not resolved

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_VAR` is set to `"hello"`
- **When** `_resolve_env_vars("${MY_VAR}suffix")` is called
- **Then** the return value SHALL be `"${MY_VAR}suffix"` (unchanged)

---

### Requirement: validate_config warns on unrecognized domain

When a target has a `domain` value other than `""`, `"self"`, or `"external"`,
the system SHALL emit a warning.

#### Scenario: domain value is unrecognized

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` with a target whose `domain` is `"unknown"`
- **When** `validate_config(config)` is called
- **Then** the result SHALL be valid (no errors)
- **And** `result.warnings` SHALL contain a string mentioning `"domain"`

---

### Requirement: validate_config warns on fix_attempts above recommended range

When `pipeline.fix_attempts` exceeds 20, the system SHALL emit a warning.

#### Scenario: fix_attempts exceeds upper bound

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` with `pipeline.fix_attempts=50`
- **When** `validate_config(config)` is called
- **Then** the result SHALL be valid (no errors)
- **And** `result.warnings` SHALL contain a string mentioning `"fix_attempts"`
