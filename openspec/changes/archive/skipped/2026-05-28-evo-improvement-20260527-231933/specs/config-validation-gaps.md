# Spec: config-validation-gaps

## ADDED Requirements

### Requirement: validate_config SHALL warn on non-standard target domain values

When a target's `domain` field is set to a value that is not one of `""`,
`"self"`, or `"external"`, `validate_config` SHALL emit a warning.

#### Scenario: Non-standard domain produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain="production"`
- **When** `validate_config(config)` is called
- **Then** the result SHALL be valid (`result.valid is True`) but `result.warnings` SHALL contain an entry mentioning "domain"

#### Scenario: Standard domain values produce no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with targets whose domains are `""`, `"self"`, and `"external"` respectively
- **When** `validate_config(config)` is called
- **Then** `result.warnings` SHALL NOT contain any entry mentioning "domain"

### Requirement: validate_config SHALL warn when fix_attempts exceeds upper bound

When `pipeline.fix_attempts` is greater than `20`, `validate_config` SHALL emit
a warning mentioning `fix_attempts`.

#### Scenario: fix_attempts above upper bound produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline=PipelineConfig(fix_attempts=25)`
- **When** `validate_config(config)` is called
- **Then** the result SHALL be valid but `result.warnings` SHALL contain an entry mentioning "fix_attempts"

### Requirement: validate_config SHALL accumulate multiple independent errors

When a configuration has more than one independent validation error,
`validate_config` SHALL return all of them in `result.errors`.

#### Scenario: Multiple LLM errors accumulated

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `llm` having empty `provider`, empty `model`, and empty `api_key`
- **When** `validate_config(config)` is called
- **Then** `result.errors` SHALL have at least 3 entries

### Requirement: _find_config SHALL fall back to home directory

When `zsiga.yaml` does not exist in the current working directory but does
exist under `~/.zsiga/zsiga.yaml`, `_find_config` SHALL return that path.

#### Scenario: Home directory fallback when cwd has no config

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** the current working directory has no `zsiga.yaml` but `Path.home()/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** it SHALL return a `Path` ending in `zsiga.yaml` that exists
