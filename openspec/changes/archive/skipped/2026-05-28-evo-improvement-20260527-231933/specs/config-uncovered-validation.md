# config-uncovered-validation

## MODIFIED Requirements

### REQ-VAL-01: validate_config SHALL emit domain warning for invalid domain values

The `validate_config` function in `zsiga/config.py` SHALL emit a warning when a target's
`domain` field is set to a value other than `""`, `"self"`, or `"external"`.

#### Scenario: validate_config warns on unsupported domain value

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"production"`
- **When** `validate_config(config)` is called
- **Then** the returned `ValidationResult.warnings` SHALL contain at least one entry
  that includes the substring `"domain"` and the returned `ValidationResult.errors` SHALL be empty

#### Scenario: validate_config does not warn on valid domain value "self"

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"self"`
- **When** `validate_config(config)` is called
- **Then** the returned `ValidationResult.warnings` SHALL NOT contain any entry including
  the substring `"domain"`

#### Scenario: validate_config does not warn on empty domain value

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `""` (empty string)
- **When** `validate_config(config)` is called
- **Then** the returned `ValidationResult.warnings` SHALL NOT contain any entry including
  the substring `"domain"`

### REQ-VAL-02: validate_config SHALL warn when fix_attempts exceeds upper bound

The `validate_config` function SHALL emit a warning when `pipeline.fix_attempts` is greater
than 20, mirroring the existing lower-bound check (values below 1 already emit a warning).

#### Scenario: validate_config warns when fix_attempts is 21

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.fix_attempts = 21`
- **When** `validate_config(config)` is called
- **Then** the returned `ValidationResult.warnings` SHALL contain at least one entry
  that includes the substring `"fix_attempts"`

#### Scenario: validate_config does not warn when fix_attempts is 10

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` with `pipeline.fix_attempts = 10`
- **When** `validate_config(config)` is called
- **Then** the returned `ValidationResult.warnings` SHALL NOT contain any entry including
  the substring `"fix_attempts"`
