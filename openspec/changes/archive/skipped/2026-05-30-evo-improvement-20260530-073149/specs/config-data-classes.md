# spec: config-data-classes

## ADDED Requirements

### Requirement: Dataclass construction defaults

All configuration dataclasses in `zsiga/config.py` SHALL provide sensible default
values for optional parameters so that callers only need to supply required fields.

#### Scenario: SSHConfig defaults

- **testable**: true
- **target**: zsiga/config.py::SSHConfig.__init__
- **Given** a new `SSHConfig` constructed with only `host="myhost"`
- **When** the instance attributes are inspected
- **Then** `user` SHALL be `None`, `port` SHALL be `22`, `key_path` SHALL be `None`

#### Scenario: TargetConfig defaults

- **testable**: true
- **target**: zsiga/config.py::TargetConfig.__init__
- **Given** a new `TargetConfig` constructed with `name="proj"`, `path="/tmp/proj"`
- **When** the instance attributes are inspected
- **Then** `test_cmd` SHALL be `"pytest -x --tb=short"`, `lint_cmd` SHALL be `"ruff check ."`,
  `transport` SHALL be `"local"`, `ssh` SHALL be `None`, `venv_path` SHALL be `None`,
  `deploy_branch` SHALL be `"main"`, `merge_to_branches` SHALL be `[]`,
  `domain` SHALL be `""`, `tech_stack` SHALL be `[]`, `key_dirs` SHALL be `[]`

#### Scenario: TargetConfig mutable defaults are independent

- **testable**: true
- **target**: zsiga/config.py::TargetConfig.__init__
- **Given** two `TargetConfig` instances constructed without specifying `merge_to_branches`
- **When** `merge_to_branches` is appended on one instance
- **Then** the other instance's `merge_to_branches` SHALL remain `[]`

#### Scenario: LLMConfig defaults

- **testable**: true
- **target**: zsiga/config.py::LLMConfig.__init__
- **Given** a new `LLMConfig` constructed with `provider="openai"`, `model="gpt-4"`, `api_key="sk-test"`
- **When** the instance attributes are inspected
- **Then** `base_url` SHALL be `None`, `proxy` SHALL be `None`,
  `max_tokens` SHALL be `4096`, `temperature` SHALL be `0.3`

#### Scenario: CompactionConfig defaults

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig.__init__
- **Given** a new `CompactionConfig` constructed with no arguments
- **When** the instance attributes are inspected
- **Then** `enabled` SHALL be `True`, `threshold_chars` SHALL be `30000`,
  `keep_recent` SHALL be `3`, `use_llm_summary` SHALL be `True`,
  `total_budget` SHALL be `200000`, `per_turn_limit` SHALL be `8192`,
  `compaction_ratio` SHALL be `0.8`

#### Scenario: IntakeConfig defaults

- **testable**: true
- **target**: zsiga/config.py::IntakeConfig.__init__
- **Given** a new `IntakeConfig` constructed with no arguments
- **When** the instance attributes are inspected
- **Then** `mode` SHALL be `"dir_scan"`, `scan_interval_seconds` SHALL be `60`,
  `api_url` SHALL be `None`, `poll_interval_seconds` SHALL be `300`,
  `api_headers` SHALL be `{}`

#### Scenario: SafetyConfig defaults

- **testable**: true
- **target**: zsiga/config.py::SafetyConfig.__init__
- **Given** a new `SafetyConfig` constructed with no arguments
- **When** the instance attributes are inspected
- **Then** `require_approval` SHALL be `True`, `protected_paths` SHALL be `[]`,
  `max_files_per_task` SHALL be `3`, `dry_run` SHALL be `False`

#### Scenario: GithubConfig defaults

- **testable**: true
- **target**: zsiga/config.py::GithubConfig.__init__
- **Given** a new `GithubConfig` constructed with no arguments
- **When** the instance attributes are inspected
- **Then** `token` SHALL be `""`, `owner` SHALL be `""`, `issue_integration` SHALL be `False`

#### Scenario: LoggingConfig uppercases level

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig.__init__
- **Given** a new `LoggingConfig` constructed with `level="debug"`
- **When** the `level` attribute is inspected
- **Then** it SHALL be `"DEBUG"`

#### Scenario: LoggingConfig defaults

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig.__init__
- **Given** a new `LoggingConfig` constructed with no arguments
- **When** the instance attributes are inspected
- **Then** `level` SHALL be `"INFO"`, `fmt` SHALL be `"text"`, `file` SHALL be `None`

#### Scenario: PipelineConfig budget_profiles merges with defaults

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** a new `PipelineConfig` constructed with `budget_profiles={"fix": 999999}`
- **When** the `budget_profiles` attribute is inspected
- **Then** it SHALL contain `"fix": 999999` (overridden) AND `"implementation": 600000` (default preserved)

#### Scenario: PipelineConfig default blocked_commands

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** a new `PipelineConfig` constructed with no arguments
- **When** the `operator_blocked_commands` attribute is inspected
- **Then** it SHALL contain `"rm -rf /"` and `"shutdown"`
