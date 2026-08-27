# Spec: config-dataclasses

## ADDED Requirements

### Requirement: Dataclass construction and field defaults

The system SHALL provide configuration dataclasses whose constructors accept parameters with documented default values. Tests SHALL verify that default construction produces expected field values and that explicit parameters override defaults.

#### Scenario: ssh_config_defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SSHConfig
- **Given** an `SSHConfig` is constructed with only `host="example.com"`
- **When** the instance fields are accessed
- **Then** `user` SHALL be `None`, `port` SHALL be `22`, `key_path` SHALL be `None`

#### Scenario: target_config_defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::TargetConfig
- **Given** a `TargetConfig` is constructed with only `name="t1"` and `path="/tmp"`
- **When** the instance fields are accessed
- **Then** `test_cmd` SHALL be `"pytest -x --tb=short"`, `lint_cmd` SHALL be `"ruff check ."`, `transport` SHALL be `"local"`, `ssh` SHALL be `None`, `deploy_branch` SHALL be `"main"`, `merge_to_branches` SHALL be `[]`, `domain` SHALL be `""`

#### Scenario: llm_config_explicit_fields

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LLMConfig
- **Given** an `LLMConfig` is constructed with `provider="p", model="m", api_key="k"`
- **When** the instance fields are accessed
- **Then** `base_url` SHALL be `None`, `proxy` SHALL be `None`, `max_tokens` SHALL be `4096`, `temperature` SHALL be `0.3`

#### Scenario: compaction_config_defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::CompactionConfig
- **Given** a `CompactionConfig` is constructed with no arguments
- **When** the instance fields are accessed
- **Then** `enabled` SHALL be `True`, `threshold_chars` SHALL be `30000`, `keep_recent` SHALL be `3`, `use_llm_summary` SHALL be `True`, `total_budget` SHALL be `200000`, `per_turn_limit` SHALL be `8192`, `compaction_ratio` SHALL be `0.8`

#### Scenario: pipeline_config_default_budget_profiles

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::PipelineConfig
- **Given** a `PipelineConfig` is constructed with no arguments
- **When** `budget_profiles` is accessed
- **Then** it SHALL contain keys `"fix"`, `"implementation"`, `"cross_project"`, `"self_modify"` with the default values from `DEFAULT_BUDGET_PROFILES`

#### Scenario: pipeline_config_custom_budget_profiles_merge

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::PipelineConfig
- **Given** a `PipelineConfig` is constructed with `budget_profiles={"fix": 999999}`
- **When** `budget_profiles` is accessed
- **Then** `"fix"` SHALL be `999999` AND other default keys SHALL still be present

#### Scenario: intake_config_defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::IntakeConfig
- **Given** an `IntakeConfig` is constructed with no arguments
- **When** the instance fields are accessed
- **Then** `mode` SHALL be `"dir_scan"`, `scan_interval_seconds` SHALL be `60`, `api_url` SHALL be `None`, `poll_interval_seconds` SHALL be `300`, `api_headers` SHALL be `{}`

#### Scenario: safety_config_defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SafetyConfig
- **Given** a `SafetyConfig` is constructed with no arguments
- **When** the instance fields are accessed
- **Then** `require_approval` SHALL be `True`, `protected_paths` SHALL be `[]`, `max_files_per_task` SHALL be `3`, `dry_run` SHALL be `False`

#### Scenario: github_config_defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::GithubConfig
- **Given** a `GithubConfig` is constructed with no arguments
- **When** the instance fields are accessed
- **Then** `token` SHALL be `""`, `owner` SHALL be `""`, `issue_integration` SHALL be `False`

#### Scenario: logging_config_level_uppercased

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LoggingConfig
- **Given** a `LoggingConfig` is constructed with `level="info"`
- **When** `level` is accessed
- **Then** it SHALL be `"INFO"` (uppercased)

#### Scenario: logging_config_defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LoggingConfig
- **Given** a `LoggingConfig` is constructed with no arguments
- **When** the instance fields are accessed
- **Then** `level` SHALL be `"INFO"`, `fmt` SHALL be `"text"`, `file` SHALL be `None`

