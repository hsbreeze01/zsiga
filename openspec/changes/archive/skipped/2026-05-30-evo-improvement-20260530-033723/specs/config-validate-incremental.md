# config-validate-incremental

Incremental test coverage for `validate_config()` edge cases **not**
covered by existing `test_config_validation.py`.  Specifically: target
domain warnings and boundary-value checks for numeric ranges.

## ADDED Requirements

### Requirement: Target domain validation

`validate_config()` SHALL emit a warning when a target's `domain` field
is a non-empty string that is neither `"self"` nor `"external"`.  It
SHALL NOT emit a warning when `domain` is an empty string, `"self"`, or `"external"`.

#### Scenario: invalid domain produces a warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"weird"`
- **When** `validate_config(config)` is called
- **Then** the result SHALL be valid (no errors) and `result.warnings`
  SHALL contain at least one entry mentioning `"domain"`

#### Scenario: domain self produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"self"`
- **When** `validate_config(config)` is called
- **Then** no warning mentioning `"domain"` SHALL appear in `result.warnings`

#### Scenario: domain external produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"external"`
- **When** `validate_config(config)` is called
- **Then** no warning mentioning `"domain"` SHALL appear in `result.warnings`

### Requirement: Numeric boundary values for validate_config

`validate_config()` SHALL NOT emit warnings when numeric parameters are
exactly at the boundary of their valid ranges.

#### Scenario: temperature at lower boundary 0.0 produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `llm.temperature` set to `0.0`
- **When** `validate_config(config)` is called
- **Then** no warning mentioning `"temperature"` SHALL appear in
  `result.warnings`

#### Scenario: temperature at upper boundary 2.0 produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `llm.temperature` set to `2.0`
- **When** `validate_config(config)` is called
- **Then** no warning mentioning `"temperature"` SHALL appear in
  `result.warnings`

#### Scenario: max_changes_per_cycle at lower boundary 1 produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.max_changes_per_cycle` set to `1`
- **When** `validate_config(config)` is called
- **Then** no warning mentioning `"max_changes_per_cycle"` SHALL appear in
  `result.warnings`

#### Scenario: max_changes_per_cycle at upper boundary 10 produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.max_changes_per_cycle` set to `10`
- **When** `validate_config(config)` is called
- **Then** no warning mentioning `"max_changes_per_cycle"` SHALL appear in
  `result.warnings`

#### Scenario: fix_attempts at upper boundary 20 produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.fix_attempts` set to `20`
- **When** `validate_config(config)` is called
- **Then** no warning mentioning `"fix_attempts"` SHALL appear in
  `result.warnings`

#### Scenario: fix_attempts above boundary 21 produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.fix_attempts` set to `21`
- **When** `validate_config(config)` is called
- **Then** `result.warnings` SHALL contain at least one entry mentioning `"fix_attempts"`
