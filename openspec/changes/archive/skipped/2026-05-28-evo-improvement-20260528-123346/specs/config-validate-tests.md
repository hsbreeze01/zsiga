# config-validate-tests

ADDED requirements for test coverage of `validate_config()`, `ValidationResult`, and `ConfigValidationError` in `zsiga/config.py`.

## ADDED Requirements

### Requirement: validate_config accepts valid ZsigaConfig

The system SHALL accept a minimally valid `ZsigaConfig` and return a `ValidationResult` with `valid == True`.

#### Scenario: valid config returns no errors

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `LLMConfig(provider="p", model="m", api_key="k")`, one `TargetConfig(name="t", path="/tmp", transport="local")`, and default `PipelineConfig`
- **When** `validate_config(config)` is called
- **Then** `result.valid` SHALL be `True` and `result.errors` SHALL be empty

### Requirement: validate_config rejects missing LLM fields

The system SHALL add an error when any of `provider`, `model`, or `api_key` is empty.

#### Scenario: missing provider produces error

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `LLMConfig(provider="", model="m", api_key="k")`
- **When** `validate_config(config)` is called
- **Then** `result.valid` SHALL be `False` and `result.errors` SHALL contain `"llm.provider is required and must be a non-empty string"`

#### Scenario: missing model produces error

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `LLMConfig(provider="p", model="", api_key="k")`
- **When** `validate_config(config)` is called
- **Then** `result.valid` SHALL be `False` and `result.errors` SHALL contain `"llm.model is required and must be a non-empty string"`

#### Scenario: missing api_key produces error

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `LLMConfig(provider="p", model="m", api_key="")`
- **When** `validate_config(config)` is called
- **Then** `result.valid` SHALL be `False` and `result.errors` SHALL contain `"llm.api_key is required and must be a non-empty string"`

### Requirement: validate_config rejects empty targets

The system SHALL add an error when no targets are defined.

#### Scenario: empty targets dict produces error

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with valid LLM but `targets={}`
- **When** `validate_config(config)` is called
- **Then** `result.valid` SHALL be `False` and `result.errors` SHALL contain `"at least one target is required"`

### Requirement: validate_config rejects invalid target transport

The system SHALL add an error when a target's transport is neither `"local"` nor `"ssh"`.

#### Scenario: invalid transport produces error

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `transport="ftp"`
- **When** `validate_config(config)` is called
- **Then** `result.valid` SHALL be `False` and `result.errors` SHALL contain a string matching `"transport must be 'local' or 'ssh'"`

### Requirement: validate_config warns on out-of-range temperature

The system SHALL add a warning when `temperature` is outside `[0.0, 2.0]`.

#### Scenario: temperature 3.0 produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `LLMConfig(..., temperature=3.0)`
- **When** `validate_config(config)` is called
- **Then** `result.valid` SHALL be `True` and `result.warnings` SHALL contain a string matching `"llm.temperature"`

### Requirement: validate_config rejects SSH target without host

The system SHALL add an error when a target uses SSH transport but has no SSH config or empty host.

#### Scenario: SSH transport without ssh config produces error

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `transport="ssh"` and `ssh=None`
- **When** `validate_config(config)` is called
- **Then** `result.valid` SHALL be `False` and `result.errors` SHALL contain a string matching `"SSH"`

#### Scenario: SSH transport with empty host produces error

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `transport="ssh"` and `ssh=SSHConfig(host="")`
- **When** `validate_config(config)` is called
- **Then** `result.valid` SHALL be `False` and `result.errors` SHALL contain a string matching `"SSH"`

### Requirement: ValidationResult valid property

The `valid` property SHALL return `True` when errors list is empty and `False` otherwise.

#### Scenario: ValidationResult with empty errors is valid

- **testable**: true
- **target**: zsiga/config.py::ValidationResult.valid
- **Given** a `ValidationResult(errors=[])`
- **When** `.valid` is accessed
- **Then** it SHALL return `True`

#### Scenario: ValidationResult with errors is invalid

- **testable**: true
- **target**: zsiga/config.py::ValidationResult.valid
- **Given** a `ValidationResult(errors=["something broke"])`
- **When** `.valid` is accessed
- **Then** it SHALL return `False`

### Requirement: ConfigValidationError wraps ValidationResult

`ConfigValidationError` SHALL carry the `ValidationResult` and format errors into the exception message.

#### Scenario: exception carries result and message

- **testable**: true
- **target**: zsiga/config.py::ConfigValidationError
- **Given** a `ValidationResult(errors=["err1", "err2"])`
- **When** `ConfigValidationError(result)` is constructed
- **Then** `exc.result` SHALL be the same `ValidationResult` and `str(exc)` SHALL contain both `"err1"` and `"err2"`
