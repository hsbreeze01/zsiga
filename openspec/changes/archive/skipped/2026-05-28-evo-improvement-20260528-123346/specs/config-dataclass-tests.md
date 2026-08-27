# config-dataclass-tests

ADDED requirements for test coverage of configuration data classes in `zsiga/config.py`.

## ADDED Requirements

### Requirement: config data class construction

The test suite SHALL verify that configuration data classes (`LLMConfig`, `TargetConfig`, `SSHConfig`, `LoggingConfig`, `PipelineConfig`) correctly store constructor arguments and apply default values.

#### Scenario: LLMConfig stores all fields

- **testable**: true
- **target**: zsiga/config.py::LLMConfig
- **Given** an `LLMConfig(provider="openai", model="gpt-4", api_key="sk-test")`
- **When** its attributes are inspected
- **Then** `provider` SHALL be `"openai"`, `model` SHALL be `"gpt-4"`, `api_key` SHALL be `"sk-test"`, `max_tokens` SHALL be `4096` (default), `temperature` SHALL be `0.3` (default)

#### Scenario: TargetConfig stores required fields and defaults

- **testable**: true
- **target**: zsiga/config.py::TargetConfig
- **Given** a `TargetConfig(name="proj", path="/home/proj")`
- **When** its attributes are inspected
- **Then** `name` SHALL be `"proj"`, `path` SHALL be `"/home/proj"`, `transport` SHALL be `"local"` (default), `deploy_branch` SHALL be `"main"` (default), `merge_to_branches` SHALL be `[]` (default)

#### Scenario: SSHConfig stores fields with port default

- **testable**: true
- **target**: zsiga/config.py::SSHConfig
- **Given** an `SSHConfig(host="server.example.com")`
- **When** its attributes are inspected
- **Then** `host` SHALL be `"server.example.com"`, `port` SHALL be `22` (default), `user` SHALL be `None` (default)

#### Scenario: LoggingConfig uppercases level

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig
- **Given** a `LoggingConfig(level="debug")`
- **When** its `level` attribute is inspected
- **Then** it SHALL be `"DEBUG"`

#### Scenario: PipelineConfig default budget profiles

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** a `PipelineConfig()` (all defaults)
- **When** `budget_profiles` is inspected
- **Then** it SHALL contain keys `"fix"`, `"implementation"`, `"cross_project"`, `"self_modify"` with positive integer values

#### Scenario: PipelineConfig custom budget profiles merge with defaults

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** a `PipelineConfig(budget_profiles={"fix": 500000})`
- **When** `budget_profiles` is inspected
- **Then** `"fix"` SHALL be `500000` (overridden) and `"implementation"` SHALL still be `600000` (default preserved)
