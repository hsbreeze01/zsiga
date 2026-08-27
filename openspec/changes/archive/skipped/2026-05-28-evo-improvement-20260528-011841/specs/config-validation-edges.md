# config-validation-edges

Behavioural spec for uncovered branches of `validate_config()`.

Existing tests in `test_config_validation.py` cover: missing LLM fields,
temperature/max_tokens warnings, no-targets, empty target path, invalid transport,
SSH without config, SSH with empty host, pipeline max_changes_per_cycle/fix_attempts
boundary, and enrich/impl max_turns warnings.

This spec covers the **remaining untested branches**.

## ADDED Requirements

### Requirement: validate-domain-warning

`validate_config()` SHALL emit a warning when a target's `domain` field
is not one of `""`, `"self"`, or `"external"`.

#### Scenario: Non-standard domain produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` with a target whose `domain` is `"production"`
- **When** `validate_config(config)` is called
- **Then** `result.valid` SHALL be `True` and `result.warnings` SHALL contain
  a string mentioning `"domain"` and `"production"`

#### Scenario: Standard domain self produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` with a target whose `domain` is `"self"`
- **When** `validate_config(config)` is called
- **Then** no warning containing `"domain"` SHALL appear in `result.warnings`

### Requirement: validate-multiple-errors

`validate_config()` SHALL accumulate all errors from different sections
(LLM, targets, pipeline) into a single `ValidationResult`.

#### Scenario: Multiple errors accumulated across sections

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with empty LLM `provider`, empty `model`, and empty
  `api_key` (3 LLM errors), AND `targets` is an empty dict (1 target error)
- **When** `validate_config(config)` is called
- **Then** `result.errors` SHALL contain at least 4 entries, and `result.valid`
  SHALL be `False`

### Requirement: validate-fix-attempts-boundary

`validate_config()` SHALL warn when `pipeline.fix_attempts` is outside the
range [1, 20].

#### Scenario: fix_attempts at upper boundary produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` with `pipeline.fix_attempts` set to `20`
- **When** `validate_config(config)` is called
- **Then** no warning containing `"fix_attempts"` SHALL appear in `result.warnings`

#### Scenario: fix_attempts above upper boundary produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` with `pipeline.fix_attempts` set to `21`
- **When** `validate_config(config)` is called
- **Then** `result.warnings` SHALL contain a string mentioning `"fix_attempts"` and `"21"`
