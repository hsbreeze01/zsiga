# config-validate-edges

Edge-case coverage for `validate_config` branches not exercised by existing tests.
Existing tests cover: missing LLM fields, temperature/max_tokens warnings, missing targets,
empty target path, invalid transport, SSH without config, pipeline zero-value warnings.
Uncovered: `target.domain` non-standard warning, boundary values for `fix_attempts`
upper range and `max_changes_per_cycle` upper range.

## ADDED Requirements

### Requirement: validate_config warns on non-standard domain

When a target has a `domain` value that is not `""`, `"self"`, or `"external"`,
`validate_config` SHALL emit a warning. Valid domain values and empty string SHALL
produce no domain-related warning.

#### Scenario: target with unrecognized domain emits warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"production"`
- **When** `validate_config` is called
- **Then** `result.valid` SHALL be `True` (no errors) and `result.warnings`
  SHALL contain at least one entry mentioning `"domain"`

#### Scenario: target with domain "self" produces no domain warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"self"`
- **When** `validate_config` is called
- **Then** no warning mentioning `"domain"` SHALL appear in `result.warnings`

#### Scenario: target with domain "external" produces no domain warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"external"`
- **When** `validate_config` is called
- **Then** no warning mentioning `"domain"` SHALL appear in `result.warnings`

#### Scenario: target with empty domain produces no domain warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `""`
- **When** `validate_config` is called
- **Then** no warning mentioning `"domain"` SHALL appear in `result.warnings`

### Requirement: validate_config boundary values for pipeline settings

`validate_config` SHALL produce warnings when `fix_attempts` or `max_changes_per_cycle`
fall outside the recommended range, and SHALL NOT warn at exact boundaries.

#### Scenario: fix_attempts at upper boundary does not warn

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.fix_attempts=20`
- **When** `validate_config` is called
- **Then** `result.warnings` SHALL NOT contain any entry mentioning `"fix_attempts"`

#### Scenario: fix_attempts above upper boundary warns

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.fix_attempts=21`
- **When** `validate_config` is called
- **Then** `result.warnings` SHALL contain an entry mentioning `"fix_attempts"`

#### Scenario: max_changes_per_cycle at lower boundary does not warn

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.max_changes_per_cycle=1`
- **When** `validate_config` is called
- **Then** `result.warnings` SHALL NOT contain any entry mentioning `"max_changes_per_cycle"`

#### Scenario: max_changes_per_cycle above upper boundary warns

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.max_changes_per_cycle=11`
- **When** `validate_config` is called
- **Then** `result.warnings` SHALL contain an entry mentioning `"max_changes_per_cycle"`
