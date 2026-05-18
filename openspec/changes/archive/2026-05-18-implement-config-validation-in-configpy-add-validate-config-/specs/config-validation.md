# Delta Spec: Config Validation

## ADDED Requirements

### Requirement: validate_config function

The system SHALL provide a `validate_config(config: ZsigaConfig)` function in `zsiga/config.py` that inspects a loaded configuration and returns a `ValidationResult` containing a list of errors and warnings.

#### Scenario: All required fields present and valid

- Given a `ZsigaConfig` with valid `llm` (provider, model, api_key), at least one target, and sane pipeline/intake/safety sections
- When `validate_config(config)` is called
- Then it SHALL return a `ValidationResult` with `valid=True`, zero errors, and zero or more informational warnings

#### Scenario: Missing LLM required fields

- Given a `ZsigaConfig` where `llm.provider` is empty or `None`, or `llm.model` is empty or `None`, or `llm.api_key` is empty or `None`
- When `validate_config(config)` is called
- Then it SHALL return a `ValidationResult` with `valid=False` and at least one error describing the missing field

### Requirement: LLM field validation

The system SHALL validate the following LLM fields:

- `provider` MUST be a non-empty string
- `model` MUST be a non-empty string
- `api_key` MUST be a non-empty string
- `temperature` SHOULD be between 0.0 and 2.0 (warning if outside range)
- `max_tokens` SHOULD be a positive integer (warning if ≤ 0)

#### Scenario: Temperature out of recommended range

- Given a `ZsigaConfig` where `llm.temperature` is 5.0
- When `validate_config(config)` is called
- Then the result SHALL contain a warning about temperature being outside the recommended range
- And `valid` SHALL remain `True` (warning, not error)

### Requirement: Target validation

The system SHALL validate that:

- At least one target is defined (error if zero targets)
- Each target's `path` MUST be a non-empty string
- Each target's `transport` MUST be either `"local"` or `"ssh"` (error for other values)
- When `transport` is `"ssh"`, the target MUST have an `ssh` config with a non-empty `host` (error if missing)

#### Scenario: SSH target without SSH config

- Given a `ZsigaConfig` with a target where `transport` is `"ssh"` but `ssh` is `None`
- When `validate_config(config)` is called
- Then the result SHALL contain an error indicating the target requires SSH configuration

#### Scenario: No targets defined

- Given a `ZsigaConfig` where `targets` is an empty dict
- When `validate_config(config)` is called
- Then the result SHALL contain an error indicating at least one target is required

### Requirement: Pipeline parameter range validation

The system SHALL emit warnings for pipeline parameters outside recommended ranges:

- `max_changes_per_cycle` SHOULD be between 1 and 10
- `fix_attempts` SHOULD be between 1 and 20
- `enrich_max_turns` SHOULD be positive
- `impl_max_turns` SHOULD be positive

#### Scenario: Pipeline parameter out of range

- Given a `ZsigaConfig` where `pipeline.max_changes_per_cycle` is 0
- When `validate_config(config)` is called
- Then the result SHALL contain a warning about the out-of-range value

### Requirement: Validation result structure

The system SHALL define a `ValidationResult` dataclass with:

- `errors: list[str]` — fatal problems that prevent safe operation
- `warnings: list[str]` — non-fatal issues that may cause suboptimal behavior
- `valid: bool` — `True` if and only if `errors` is empty

#### Scenario: Accessing valid field

- Given a `ValidationResult` with 2 errors and 1 warning
- When `valid` is accessed
- Then it SHALL return `False`

### Requirement: Integration with load_config

The system SHALL call `validate_config` inside `load_config` after construction. When errors are found, `load_config` MUST log all errors and raise a `ConfigValidationError` exception. Warnings SHALL be logged but MUST NOT prevent config loading.

#### Scenario: Load config with validation errors

- Given a `zsiga.yaml` that is missing `agent.llm.api_key`
- When `load_config()` is called
- Then a `ConfigValidationError` SHALL be raised containing all error messages

#### Scenario: Load config with only warnings

- Given a `zsiga.yaml` where `pipeline.max_changes_per_cycle` is 0
- When `load_config()` is called
- Then the config SHALL be returned successfully
- And warnings SHALL be logged to stderr
