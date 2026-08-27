# config-consolidated-test

> Delta spec for change `evo-improvement-20260528-014707`
> Creates `tests/test_config.py` — a consolidated smoke-test file covering the
> three core config module functions (`_find_config`, `_resolve_env_vars`,
> `validate_config`). These scenarios are chosen to be non-overlapping with
> existing test files:
> - `test_config_validation.py` covers validate_config field-by-field errors
> - `test_spec_evo_..._config_unit_coverage.py` covers basic _find_config and
>   _resolve_env_vars paths
> - `test_spec_evo_..._config_boundary_coverage.py` covers boundary scenarios
> This file fills specific gaps: error message content, deeply nested env var
> resolution, multi-field error accumulation, and float passthrough.

---

## ADDED Requirements

### Requirement: _find_config error message content

When no config file exists in any candidate location, `_find_config()` SHALL
raise `FileNotFoundError` whose message mentions both search locations so that
operators can diagnose where the function looked.

#### Scenario: FileNotFoundError message references both search locations

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** current working directory has no `zsiga.yaml` AND `~/.zsiga/zsiga.yaml` does not exist
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError` whose string representation contains `"current dir"` and `".zsiga"`

---

### Requirement: _resolve_env_vars deeply nested mixed-type resolution

`_resolve_env_vars()` SHALL resolve `${VAR}` placeholders recursively in
mixed-type structures where a dict contains a list that contains `${VAR}`
strings, and SHALL pass through float values unchanged (the only numeric type
not yet exercised by existing tests, which only cover int passthrough).

#### Scenario: Mixed nested structure with env vars is fully resolved

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** env var `ZSIGA_NESTED_VAL` is set to `"resolved"` AND `_resolve_env_vars` is called with `{"a": ["${ZSIGA_NESTED_VAL}", 42], "b": "plain"}`
- **When** the result is inspected
- **Then** it SHALL equal `{"a": ["resolved", 42], "b": "plain"}`

#### Scenario: Float value passes through unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** `_resolve_env_vars` is called with `3.14`
- **When** the result is inspected
- **Then** it SHALL return `3.14` (float, not coerced to string or other type)

---

### Requirement: validate_config multi-field error accumulation

`validate_config()` SHALL report all missing LLM fields simultaneously rather
than short-circuiting on the first error. When provider, model, and api_key are
all empty, the result SHALL contain at least three distinct error messages.

#### Scenario: Multiple missing LLM fields produce distinct errors

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` whose `LLMConfig` has `provider=""`, `model=""`, and `api_key=""`
- **When** `validate_config()` is called
- **Then** the result SHALL be invalid (`valid` is `False`) AND `errors` SHALL contain at least 3 entries — one mentioning `"provider"`, one mentioning `"model"`, and one mentioning `"api_key"`

#### Scenario: Fully valid default config produces zero warnings

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` constructed with `LLMConfig(provider="openai", model="gpt-4", api_key="sk-test")`, a single `TargetConfig(name="t", path="/tmp", transport="local")`, and default `PipelineConfig()`
- **When** `validate_config()` is called
- **Then** the result SHALL be valid AND `warnings` SHALL be an empty list
