# Tasks: Config Validation

## 1. Core Validation Layer

- [x] Add `ValidationResult` dataclass, `ConfigValidationError` exception, and `validate_config()` function to `zsiga/config.py` — includes all LLM/target/SSH/pipeline checks as specified in design.md
- [x] Integrate `validate_config()` into `load_config()`: call after construction, log warnings to stderr, raise `ConfigValidationError` on errors

## 2. Tests

- [x] Add `tests/test_config_validation.py` covering: valid config, missing LLM fields, temperature warning, max_tokens warning, no targets error, empty target path, invalid transport, SSH target without config, pipeline range warnings, ValidationResult.valid property, ConfigValidationError message format, load_config integration (error raises, warning logs)
