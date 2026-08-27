# Spec: config-validate

## ADDED Requirements

### Requirement: validate_config domain warning for invalid domain value

`validate_config` SHALL emit a warning when a target's `domain` is not one of `""`, `"self"`, or `"external"`.

#### Scenario: Warning for unrecognized domain value

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a valid config where a target has `domain="production"`
- **When** `validate_config(config)` is called
- **Then** the result is valid (no errors) but contains a warning mentioning `domain` and the target name

### Requirement: validate_config fix_attempts upper bound warning

`validate_config` SHALL warn when `pipeline.fix_attempts` exceeds 20.

#### Scenario: Warning for fix_attempts above range

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a valid config with `pipeline.fix_attempts=25`
- **When** `validate_config(config)` is called
- **Then** the result is valid and contains a warning mentioning `fix_attempts`

### Requirement: validate_config multiple errors accumulated

`validate_config` SHALL accumulate all errors into a single `ValidationResult` rather than failing on the first error.

#### Scenario: Multiple LLM field errors reported together

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a config with empty `provider`, empty `model`, and empty `api_key`
- **When** `validate_config(config)` is called
- **Then** the result contains at least 3 errors, one for each missing field

### Requirement: validate_config boundary values for max_changes_per_cycle

`validate_config` SHALL NOT warn when `max_changes_per_cycle` is exactly 1 or exactly 10 (boundary values of the recommended range).

#### Scenario: Boundary value 1 produces no warning

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a valid config with `pipeline.max_changes_per_cycle=1`
- **When** `validate_config(config)` is called
- **Then** no warning about `max_changes_per_cycle` appears in the result

#### Scenario: Boundary value 10 produces no warning

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a valid config with `pipeline.max_changes_per_cycle=10`
- **When** `validate_config(config)` is called
- **Then** no warning about `max_changes_per_cycle` appears in the result

### Requirement: validate_config temperature boundary values

`validate_config` SHALL NOT warn when `temperature` is exactly 0.0 or exactly 2.0.

#### Scenario: Temperature at lower boundary 0.0

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a valid config with `llm.temperature=0.0`
- **When** `validate_config(config)` is called
- **Then** no temperature warning appears

#### Scenario: Temperature at upper boundary 2.0

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::validate_config
- **Given** a valid config with `llm.temperature=2.0`
- **When** `validate_config(config)` is called
- **Then** no temperature warning appears

