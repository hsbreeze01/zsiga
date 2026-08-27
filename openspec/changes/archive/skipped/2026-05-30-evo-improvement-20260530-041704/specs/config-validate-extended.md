# Spec: config-validate-extended

Extended validation paths for `validate_config(config)` not covered by
`test_config_validation.py`: domain warnings, fix_attempts boundary,
and combined error paths.

## ADDED Requirements

### Requirement: validate_config warns on unexpected target domain

When a target's `domain` is not `""`, `"self"`, or `"external"`,
`validate_config` SHALL add a warning.

#### Scenario: domain with unexpected value produces warning

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a valid config where a target has `domain="production"`
- **When** `validate_config(config)` is called
- **Then** `result.valid` SHALL be `True` and `result.warnings` SHALL contain a string including `"domain"`

#### Scenario: domain self produces no warning

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a valid config where a target has `domain="self"`
- **When** `validate_config(config)` is called
- **Then** `result.warnings` SHALL NOT contain any string with `"domain"`

#### Scenario: domain external produces no warning

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a valid config where a target has `domain="external"`
- **When** `validate_config(config)` is called
- **Then** `result.warnings` SHALL NOT contain any string with `"domain"`

---

### Requirement: validate_config warns on fix_attempts outside recommended range

When `pipeline.fix_attempts` is outside `[1, 20]`, `validate_config` SHALL
add a warning.

#### Scenario: fix_attempts too high

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a valid config with `pipeline.fix_attempts=25`
- **When** `validate_config(config)` is called
- **Then** `result.warnings` SHALL contain a string including `"fix_attempts"`

---

### Requirement: validate_config collects multiple errors simultaneously

`validate_config` SHALL accumulate all errors rather than stopping at the
first one.

#### Scenario: multiple LLM errors collected

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a config with empty `provider`, `model`, and `api_key`
- **When** `validate_config(config)` is called
- **Then** `result.errors` SHALL contain at least 3 error strings (one for each missing field)

