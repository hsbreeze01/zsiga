# Design: Config Validation

## Architecture Decision

Add a `validate_config()` function and supporting types to the existing `zsiga/config.py` module. No new files needed — the module already owns all config classes and `load_config()`.

## Data Flow

```
zsiga.yaml
  → load_config()
      → yaml.safe_load + _resolve_env_vars  (existing)
      → construct ZsigaConfig objects         (existing)
      → validate_config(config)               (NEW)
          → check LLM required fields
          → check targets existence + transport
          → check SSH config for ssh targets
          → check pipeline parameter ranges
          → return ValidationResult
      → if errors: raise ConfigValidationError (NEW)
      → if warnings: log to stderr             (NEW)
      → return ZsigaConfig
```

## New Types

1. **`ValidationResult`** — dataclass with `errors: list[str]`, `warnings: list[str]`, computed property `valid: bool`
2. **`ConfigValidationError(Exception)`** — raised by `load_config` when validation fails, holds the `ValidationResult`

## Validation Logic (inside `validate_config`)

| Section | Check | Severity |
|---------|-------|----------|
| LLM | provider non-empty | error |
| LLM | model non-empty | error |
| LLM | api_key non-empty | error |
| LLM | temperature in [0, 2] | warning |
| LLM | max_tokens > 0 | warning |
| Targets | at least 1 target | error |
| Target | path non-empty | error |
| Target | transport in {local, ssh} | error |
| Target | ssh transport requires ssh.host | error |
| Pipeline | max_changes_per_cycle in [1, 10] | warning |
| Pipeline | fix_attempts in [1, 20] | warning |
| Pipeline | enrich_max_turns > 0 | warning |
| Pipeline | impl_max_turns > 0 | warning |

## Files Modified

| File | Change |
|------|--------|
| `zsiga/config.py` | Add `ValidationResult`, `ConfigValidationError`, `validate_config()`, integrate into `load_config()` |
| `tests/test_config_validation.py` | New test file covering all validation scenarios |

## Implementation Notes

- `validate_config` takes a `ZsigaConfig` instance and returns `ValidationResult` — pure function, no side effects
- `load_config` calls `validate_config` and handles the result: log warnings, raise on errors
- Use `sys.stderr` for warning output (no logging framework dependency)
- `ConfigValidationError` string representation includes all error messages joined by newlines
- No changes to existing config classes — validation is separate from construction
