# validate-config-incremental

## ADDED Requirements

### Requirement: Target domain validation warning

When a target's `domain` field is set to a value other than `""`, `"self"`, or
`"external"`, `validate_config` SHALL emit a warning (not an error) indicating
the unexpected domain value. This is an incremental branch not covered by
existing `test_config_validation.py`.

#### Scenario: Non-standard target domain produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with one target whose `domain` is `"unknown"`
- **When** `validate_config(config)` is called
- **Then** `result.warnings` SHALL contain at least one entry mentioning `"domain"`

#### Scenario: Domain value self produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with one target whose `domain` is `"self"`
- **When** `validate_config(config)` is called
- **Then** `result.warnings` SHALL NOT contain any entry mentioning `"domain"`

#### Scenario: Domain value external produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with one target whose `domain` is `"external"`
- **When** `validate_config(config)` is called
- **Then** `result.warnings` SHALL NOT contain any entry mentioning `"domain"`

---

### Requirement: Fix attempts upper bound warning

When `pipeline.fix_attempts` exceeds 20, `validate_config` SHALL emit a
warning indicating the value is outside the recommended range `[1, 20]`.

#### Scenario: Fix attempts above 20 produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.fix_attempts = 25`
- **When** `validate_config(config)` is called
- **Then** `result.warnings` SHALL contain at least one entry mentioning `"fix_attempts"`

#### Scenario: Fix attempts at upper boundary 20 produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.fix_attempts = 20`
- **When** `validate_config(config)` is called
- **Then** `result.warnings` SHALL NOT contain any entry mentioning `"fix_attempts"`
