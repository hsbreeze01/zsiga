# config-dataclass-defaults

Coverage for 6 data classes in `zsiga/config.py` with zero direct test coverage:
`CompactionConfig`, `LoggingConfig`, `GithubConfig`, `IntakeConfig`, `SafetyConfig`, `SSHConfig`.

Also covers `PipelineConfig` default construction including `budget_profiles` merge behavior
and `operator_blocked_commands` defaults.

Existing test files (`test_config_validation.py`, `test_spec_evo_*__config_unit_coverage.py`,
`test_spec_evo_*__config_load_robustness.py`) do NOT instantiate or assert on any of these
classes in isolation.

## ADDED Requirements

### Requirement: CompactionConfig default and custom construction

`CompactionConfig` SHALL provide 7 sensible defaults when constructed with no arguments,
and SHALL allow selective overrides while preserving unoverridden defaults.

#### Scenario: CompactionConfig defaults

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig
- **Given** a `CompactionConfig` constructed with no arguments
- **When** all 7 fields are inspected
- **Then** `enabled` is `True`, `threshold_chars` is 30000, `keep_recent` is 3,
  `use_llm_summary` is `True`, `total_budget` is 200000, `per_turn_limit` is 8192,
  `compaction_ratio` is 0.8

#### Scenario: CompactionConfig custom overrides

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig
- **Given** a `CompactionConfig` constructed with `enabled=False, threshold_chars=1000, keep_recent=1`
- **When** the fields are inspected
- **Then** `enabled` is `False`, `threshold_chars` is 1000, `keep_recent` is 1,
  and `use_llm_summary` is `True`, `total_budget` is 200000` (defaults preserved)

### Requirement: LoggingConfig level normalization

`LoggingConfig` SHALL normalize the `level` field to uppercase and provide defaults
for `fmt` and `file`.

#### Scenario: LoggingConfig level uppercased

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig
- **Given** a `LoggingConfig` constructed with `level="debug"`
- **When** the `level` field is inspected
- **Then** it SHALL be `"DEBUG"` (uppercase)

#### Scenario: LoggingConfig defaults for fmt and file

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig
- **Given** a `LoggingConfig` constructed with only `level="info"`
- **When** `fmt` and `file` are inspected
- **Then** `level` is `"INFO"` (uppercased), `fmt` is `"text"`, `file` is `None`

### Requirement: GithubConfig defaults and custom values

`GithubConfig` SHALL expose `token`, `owner`, and `issue_integration` with
empty-string/False defaults and allow custom overrides.

#### Scenario: GithubConfig default construction

- **testable**: true
- **target**: zsiga/config.py::GithubConfig
- **Given** a `GithubConfig` constructed with no arguments
- **When** all fields are inspected
- **Then** `token` is `""`, `owner` is `""`, `issue_integration` is `False`

#### Scenario: GithubConfig custom values

- **testable**: true
- **target**: zsiga/config.py::GithubConfig
- **Given** a `GithubConfig` constructed with `token="ghp_abc"`, `owner="myorg"`, `issue_integration=True`
- **When** fields are inspected
- **Then** `token` is `"ghp_abc"`, `owner` is `"myorg"`, `issue_integration` is `True`

### Requirement: IntakeConfig defaults

`IntakeConfig` SHALL expose `mode`, `scan_interval_seconds`, `api_url`,
`poll_interval_seconds`, `api_headers` with sensible defaults.

#### Scenario: IntakeConfig default construction

- **testable**: true
- **target**: zsiga/config.py::IntakeConfig
- **Given** an `IntakeConfig` constructed with no arguments
- **When** all fields are inspected
- **Then** `mode` is `"dir_scan"`, `scan_interval_seconds` is 60,
  `api_url` is `None`, `poll_interval_seconds` is 300, `api_headers` is `{}`

### Requirement: SafetyConfig defaults and overrides

`SafetyConfig` SHALL expose `require_approval`, `protected_paths`,
`max_files_per_task`, `dry_run` with safe defaults and allow overrides.

#### Scenario: SafetyConfig default construction

- **testable**: true
- **target**: zsiga/config.py::SafetyConfig
- **Given** a `SafetyConfig` constructed with no arguments
- **When** all fields are inspected
- **Then** `require_approval` is `True`, `protected_paths` is `[]`,
  `max_files_per_task` is 3, `dry_run` is `False`

#### Scenario: SafetyConfig custom overrides

- **testable**: true
- **target**: zsiga/config.py::SafetyConfig
- **Given** a `SafetyConfig` constructed with `require_approval=False, max_files_per_task=10`
- **When** fields are inspected
- **Then** `require_approval` is `False`, `max_files_per_task` is 10,
  `protected_paths` is `[]` (default preserved)

### Requirement: SSHConfig field assignment

`SSHConfig` SHALL store `host`, `user`, `port`, `key_path` from constructor
arguments with defaults for optional fields.

#### Scenario: SSHConfig with defaults

- **testable**: true
- **target**: zsiga/config.py::SSHConfig
- **Given** an `SSHConfig` constructed with `host="example.com"`
- **When** all fields are inspected
- **Then** `host` is `"example.com"`, `user` is `None`, `port` is 22, `key_path` is `None`

### Requirement: PipelineConfig budget_profiles merge

`PipelineConfig` SHALL merge caller-provided `budget_profiles` into the
`DEFAULT_BUDGET_PROFILES` base, preserving unoverridden keys.

#### Scenario: PipelineConfig default budget_profiles

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** a `PipelineConfig` constructed with no arguments
- **When** `budget_profiles` is inspected
- **Then** it SHALL equal `DEFAULT_BUDGET_PROFILES`
  (`{"fix": 300000, "implementation": 600000, "cross_project": 200000, "self_modify": 800000}`)

#### Scenario: PipelineConfig merged budget_profiles

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** a `PipelineConfig` constructed with `budget_profiles={"fix": 500000, "custom": 999}`
- **When** `budget_profiles` is inspected
- **Then** `fix` is 500000 (overridden), `custom` is 999,
  `implementation` is 600000 (preserved), `cross_project` is 200000 (preserved)

### Requirement: PipelineConfig operator safety defaults

`PipelineConfig` SHALL default `operator_allowed_dirs` to `[]` and
`operator_blocked_commands` to a non-empty list of dangerous commands.

#### Scenario: PipelineConfig default safety lists

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** a `PipelineConfig` constructed with no arguments
- **When** `operator_allowed_dirs` and `operator_blocked_commands` are inspected
- **Then** `operator_allowed_dirs` is `[]` and `operator_blocked_commands`
  is a list containing `"rm -rf /"` and `"shutdown"`
