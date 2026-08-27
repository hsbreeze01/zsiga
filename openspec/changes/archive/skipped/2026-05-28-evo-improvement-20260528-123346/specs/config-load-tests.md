# config-load-tests

ADDED requirements for test coverage of `load_config()` integration path in `zsiga/config.py`.

## ADDED Requirements

### Requirement: load_config parses valid YAML into ZsigaConfig

The system SHALL accept a path to a valid YAML file and return a fully constructed `ZsigaConfig` with all sub-objects populated from YAML data.

#### Scenario: load_config returns ZsigaConfig from valid YAML

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML file containing `agent.llm` with `provider`, `model`, `api_key` and at least one `targets` entry with a `path`
- **When** `load_config(path)` is called with that file path
- **Then** it SHALL return a `ZsigaConfig` instance where `config.llm.provider` equals the YAML value, `config.targets` contains the expected target name, and `config.pipeline` is a `PipelineConfig`

### Requirement: load_config resolves environment variables in YAML

The system SHALL apply `_resolve_env_vars` to the raw YAML before constructing config objects.

#### Scenario: load_config resolves env var in api_key

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** environment variable `TEST_LOAD_KEY` is set to `"resolved-key"` and a YAML file where `agent.llm.api_key` is `"${TEST_LOAD_KEY}"`
- **When** `load_config(path)` is called
- **Then** `config.llm.api_key` SHALL be `"resolved-key"`

### Requirement: load_config raises ConfigValidationError on invalid config

The system SHALL validate the constructed config and raise `ConfigValidationError` when validation fails.

#### Scenario: load_config with empty provider raises ConfigValidationError

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML file where `agent.llm.provider` is `""`
- **When** `load_config(path)` is called
- **Then** it SHALL raise `ConfigValidationError`
