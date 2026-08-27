# Spec: config-data-class-defaults

## ADDED Requirements

### Requirement: Data class constructors SHALL provide documented default values

Every data class in `zsiga/config.py` SHALL initialise optional parameters to
sensible defaults when no explicit value is supplied, so that a minimally
constructed instance is always valid.

#### Scenario: SSHConfig defaults

- **testable**: true
- **target**: zsiga/config.py::SSHConfig.__init__
- **Given** an `SSHConfig` constructed with only `host="example.com"`
- **When** the instance attributes are inspected
- **Then** `.user` SHALL be `None`, `.port` SHALL be `22`, `.key_path` SHALL be `None`

#### Scenario: TargetConfig defaults

- **testable**: true
- **target**: zsiga/config.py::TargetConfig.__init__
- **Given** a `TargetConfig` constructed with only `name="t"` and `path="/tmp"`
- **When** the instance attributes are inspected
- **Then** `.test_cmd` SHALL be `"pytest -x --tb=short"`, `.lint_cmd` SHALL be `"ruff check ."`, `.transport` SHALL be `"local"`, `.ssh` SHALL be `None`, `.venv_path` SHALL be `None`, `.deploy_branch` SHALL be `"main"`, `.merge_to_branches` SHALL be `[]`, `.domain` SHALL be `""`, `.tech_stack` SHALL be `[]`, `.key_dirs` SHALL be `[]`, `.conventions` SHALL be `""`

#### Scenario: LLMConfig defaults

- **testable**: true
- **target**: zsiga/config.py::LLMConfig.__init__
- **Given** an `LLMConfig` constructed with `provider="openai"`, `model="gpt-4"`, `api_key="sk-test"`
- **When** the instance attributes are inspected
- **Then** `.base_url` SHALL be `None`, `.proxy` SHALL be `None`, `.max_tokens` SHALL be `4096`, `.temperature` SHALL be `0.3`

#### Scenario: LoggingConfig level uppercasing

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig.__init__
- **Given** a `LoggingConfig` constructed with `level="debug"`
- **When** `.level` is inspected
- **Then** it SHALL be `"DEBUG"` (uppercased)

#### Scenario: LoggingConfig defaults

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig.__init__
- **Given** a `LoggingConfig` constructed with no arguments
- **When** the instance attributes are inspected
- **Then** `.level` SHALL be `"INFO"`, `.fmt` SHALL be `"text"`, `.file` SHALL be `None`

#### Scenario: CompactionConfig defaults

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig.__init__
- **Given** a `CompactionConfig` constructed with no arguments
- **When** the instance attributes are inspected
- **Then** `.enabled` SHALL be `True`, `.threshold_chars` SHALL be `30000`, `.keep_recent` SHALL be `3`, `.use_llm_summary` SHALL be `True`, `.total_budget` SHALL be `200000`, `.per_turn_limit` SHALL be `8192`, `.compaction_ratio` SHALL be `0.8`

#### Scenario: PipelineConfig budget_profiles merges with defaults

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** a `PipelineConfig` constructed with `budget_profiles={"custom": 500000}`
- **When** `.budget_profiles` is inspected
- **Then** it SHALL contain all keys from `DEFAULT_BUDGET_PROFILES` **plus** `"custom": 500000`

#### Scenario: PipelineConfig default operator safety

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** a `PipelineConfig` constructed with no arguments
- **When** `.operator_blocked_commands` is inspected
- **Then** it SHALL be a non-empty list containing `"rm -rf /"` and `"shutdown"`

#### Scenario: IntakeConfig defaults

- **testable**: true
- **target**: zsiga/config.py::IntakeConfig.__init__
- **Given** an `IntakeConfig` constructed with no arguments
- **When** the instance attributes are inspected
- **Then** `.mode` SHALL be `"dir_scan"`, `.scan_interval_seconds` SHALL be `60`, `.api_url` SHALL be `None`, `.poll_interval_seconds` SHALL be `300`, `.api_headers` SHALL be `{}`

#### Scenario: SafetyConfig defaults

- **testable**: true
- **target**: zsiga/config.py::SafetyConfig.__init__
- **Given** a `SafetyConfig` constructed with no arguments
- **When** the instance attributes are inspected
- **Then** `.require_approval` SHALL be `True`, `.protected_paths` SHALL be `[]`, `.max_files_per_task` SHALL be `3`, `.dry_run` SHALL be `False`

#### Scenario: GithubConfig defaults

- **testable**: true
- **target**: zsiga/config.py::GithubConfig.__init__
- **Given** a `GithubConfig` constructed with no arguments
- **When** the instance attributes are inspected
- **Then** `.token` SHALL be `""`, `.owner` SHALL be `""`, `.issue_integration` SHALL be `False`
