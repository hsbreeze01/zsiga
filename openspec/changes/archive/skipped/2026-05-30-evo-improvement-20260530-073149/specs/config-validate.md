# spec: config-validate

## ADDED Requirements

### Requirement: Domain validation warning

`validate_config` SHALL emit a warning when a target's `domain` field is neither
`""`, `"self"`, nor `"external"`.

#### Scenario: Domain with unrecognized value produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"custom"`
- **When** `validate_config` is called
- **Then** the result SHALL be valid (`errors` empty) AND `warnings` SHALL contain
  a string mentioning `"domain"` and `"custom"`

#### Scenario: Domain self produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"self"`
- **When** `validate_config` is called
- **Then** `warnings` SHALL NOT contain any string mentioning `"domain"`

#### Scenario: Domain empty produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `""`
- **When** `validate_config` is called
- **Then** `warnings` SHALL NOT contain any string mentioning `"domain"`

### Requirement: Pipeline fix_attempts boundary

`validate_config` SHALL emit a warning when `fix_attempts` is outside `[1, 20]`.

#### Scenario: fix_attempts at upper boundary produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.fix_attempts` set to `20`
- **When** `validate_config` is called
- **Then** `warnings` SHALL NOT contain any string mentioning `"fix_attempts"`

#### Scenario: fix_attempts above boundary produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.fix_attempts` set to `21`
- **When** `validate_config` is called
- **Then** `warnings` SHALL contain a string mentioning `"fix_attempts"`

### Requirement: Multiple validation errors accumulated

`validate_config` SHALL collect all applicable errors rather than stopping at the first.

#### Scenario: Multiple LLM errors accumulated

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `llm.provider=""`, `llm.model=""`, and `llm.api_key=""`
- **When** `validate_config` is called
- **Then** `result.errors` SHALL contain at least 3 entries
