# config-dataclass-defaults

## ADDED Requirements

### Requirement: SSHConfig stores connection parameters

`SSHConfig` SHALL accept `host`, `user`, `port`, and `key_path` parameters.
Default values: `user=None`, `port=22`, `key_path=None`.

#### Scenario: construct with defaults

- **testable**: true
- **target**: zsiga/config.py::SSHConfig
- **Given** no special preconditions
- **When** `SSHConfig(host="myhost")` is constructed
- **Then** `instance.host` SHALL equal `"myhost"`, `instance.port` SHALL equal `22`, `instance.user` SHALL be `None`, `instance.key_path` SHALL be `None`

### Requirement: TargetConfig stores target specification with defaults

`TargetConfig` SHALL accept `name`, `path`, and optional parameters with sensible
defaults: `test_cmd="pytest -x --tb=short"`, `lint_cmd="ruff check ."`,
`transport="local"`, `deploy_branch="main"`, and empty lists for
`merge_to_branches`, `tech_stack`, `key_dirs`.

#### Scenario: construct with required fields only

- **testable**: true
- **target**: zsiga/config.py::TargetConfig
- **Given** no special preconditions
- **When** `TargetConfig(name="t1", path="/tmp/proj")` is constructed
- **Then** `instance.test_cmd` SHALL equal `"pytest -x --tb=short"`, `instance.lint_cmd` SHALL equal `"ruff check ."`, `instance.transport` SHALL equal `"local"`, `instance.deploy_branch` SHALL equal `"main"`, `instance.merge_to_branches` SHALL equal `[]`

### Requirement: LLMConfig stores provider settings with defaults

`LLMConfig` SHALL accept `provider`, `model`, `api_key`, and optional
`base_url`, `proxy`, `max_tokens` (default `4096`), `temperature` (default `0.3`).

#### Scenario: construct with required fields and verify defaults

- **testable**: true
- **target**: zsiga/config.py::LLMConfig
- **Given** no special preconditions
- **When** `LLMConfig(provider="openai", model="gpt-4", api_key="k1")` is constructed
- **Then** `instance.max_tokens` SHALL equal `4096`, `instance.temperature` SHALL equal `0.3`, `instance.base_url` SHALL be `None`, `instance.proxy` SHALL be `None`

### Requirement: CompactionConfig has compaction tuning defaults

`CompactionConfig` SHALL default `enabled=True`, `threshold_chars=30000`,
`keep_recent=3`, `use_llm_summary=True`, `total_budget=200000`,
`per_turn_limit=8192`, `compaction_ratio=0.8`.

#### Scenario: construct with all defaults

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig
- **Given** no special preconditions
- **When** `CompactionConfig()` is constructed
- **Then** `instance.enabled` SHALL be `True`, `instance.threshold_chars` SHALL equal `30000`, `instance.keep_recent` SHALL equal `3`, `instance.total_budget` SHALL equal `200000`, `instance.compaction_ratio` SHALL equal `0.8`

### Requirement: PipelineConfig provides extensive pipeline tuning defaults

`PipelineConfig` SHALL provide defaults for all pipeline parameters including
`max_changes_per_cycle=3`, `fix_attempts=10`, `enrich_max_turns=25`,
`compaction` as a default `CompactionConfig()`, and role-specific timeouts.
It SHALL also include `budget_profiles` initialized from
`DEFAULT_BUDGET_PROFILES` and overridden by any user-provided profiles.

#### Scenario: default construction has expected values

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** no special preconditions
- **When** `PipelineConfig()` is constructed
- **Then** `instance.max_changes_per_cycle` SHALL equal `3`, `instance.fix_attempts` SHALL equal `10`, `instance.enrich_max_turns` SHALL equal `25`, `instance.compaction` SHALL be a `CompactionConfig` instance, `instance.idle_poll_minutes` SHALL equal `5`

#### Scenario: custom budget_profiles override defaults

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** no special preconditions
- **When** `PipelineConfig(budget_profiles={"fix": 999999})` is constructed
- **Then** `instance.budget_profiles["fix"]` SHALL equal `999999`, and `instance.budget_profiles["implementation"]` SHALL equal `600000` (preserved from default)

### Requirement: IntakeConfig defaults to dir_scan mode

`IntakeConfig` SHALL default `mode="dir_scan"`, `scan_interval_seconds=60`,
and empty `api_headers` dict.

#### Scenario: default construction

- **testable**: true
- **target**: zsiga/config.py::IntakeConfig
- **Given** no special preconditions
- **When** `IntakeConfig()` is constructed
- **Then** `instance.mode` SHALL equal `"dir_scan"`, `instance.scan_interval_seconds` SHALL equal `60`, `instance.api_headers` SHALL equal `{}`

### Requirement: SafetyConfig defaults to safe settings

`SafetyConfig` SHALL default `require_approval=True`, empty `protected_paths`,
`max_files_per_task=3`, `dry_run=False`.

#### Scenario: default construction

- **testable**: true
- **target**: zsiga/config.py::SafetyConfig
- **Given** no special preconditions
- **When** `SafetyConfig()` is constructed
- **Then** `instance.require_approval` SHALL be `True`, `instance.protected_paths` SHALL equal `[]`, `instance.max_files_per_task` SHALL equal `3`, `instance.dry_run` SHALL be `False`

### Requirement: GithubConfig defaults to empty strings

`GithubConfig` SHALL default `token=""`, `owner=""`, `issue_integration=False`.

#### Scenario: default construction

- **testable**: true
- **target**: zsiga/config.py::GithubConfig
- **Given** no special preconditions
- **When** `GithubConfig()` is constructed
- **Then** `instance.token` SHALL equal `""`, `instance.owner` SHALL equal `""`, `instance.issue_integration` SHALL be `False`

### Requirement: LoggingConfig uppercases level and has defaults

`LoggingConfig` SHALL convert `level` to uppercase, and default `fmt="text"`,
`file=None`.

#### Scenario: default level uppercased

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig
- **Given** no special preconditions
- **When** `LoggingConfig(level="debug")` is constructed
- **Then** `instance.level` SHALL equal `"DEBUG"`, `instance.fmt` SHALL equal `"text"`, `instance.file` SHALL be `None`

### Requirement: ValidationResult reports valid when no errors

`ValidationResult` SHALL have `valid` property that returns `True` when
`errors` list is empty and `False` otherwise.

#### Scenario: empty errors means valid

- **testable**: true
- **target**: zsiga/config.py::ValidationResult.valid
- **Given** no special preconditions
- **When** `ValidationResult()` is constructed
- **Then** `instance.valid` SHALL be `True`

#### Scenario: non-empty errors means invalid

- **testable**: true
- **target**: zsiga/config.py::ValidationResult.valid
- **Given** no special preconditions
- **When** `ValidationResult(errors=["bad"])` is constructed
- **Then** `instance.valid` SHALL be `False`

### Requirement: ConfigValidationError carries ValidationResult

`ConfigValidationError` SHALL store the `ValidationResult` in `self.result`
and format error messages in the exception text.

#### Scenario: error message contains validation errors

- **testable**: true
- **target**: zsiga/config.py::ConfigValidationError
- **Given** no special preconditions
- **When** `ConfigValidationError(ValidationResult(errors=["err1", "err2"]))` is constructed
- **Then** `str(instance)` SHALL contain `"err1"` and `"err2"`, and `instance.result.errors` SHALL equal `["err1", "err2"]`
