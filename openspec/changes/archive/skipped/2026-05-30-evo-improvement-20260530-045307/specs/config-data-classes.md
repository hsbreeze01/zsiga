# Spec: config-data-classes

## ADDED Requirements

### Requirement: SSHConfig construction and defaults

`SSHConfig` SHALL accept `host` (required), `user`, `port`, `key_path` with defaults `user=None`, `port=22`, `key_path=None`.

#### Scenario: Full construction with all parameters

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SSHConfig
- **Given** all four parameters are provided
- **When** `SSHConfig(host="myhost", user="deploy", port=2222, key_path="/keys/id_rsa")` is constructed
- **Then** all attributes match the provided values

#### Scenario: Default values for optional parameters

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SSHConfig
- **Given** only `host` is provided
- **When** `SSHConfig(host="myhost")` is constructed
- **Then** `user` is `None`, `port` is `22`, `key_path` is `None`

### Requirement: TargetConfig construction and defaults

`TargetConfig` SHALL provide sensible defaults: `test_cmd="pytest -x --tb=short"`, `lint_cmd="ruff check ."`, `transport="local"`, `ssh=None`, `deploy_branch="main"`, and empty lists for `merge_to_branches`, `tech_stack`, `key_dirs`.

#### Scenario: Minimal construction uses all defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::TargetConfig
- **Given** only `name` and `path` are provided
- **When** `TargetConfig(name="t1", path="/tmp/proj")` is constructed
- **Then** all default values are set correctly

#### Scenario: Full construction overrides all defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::TargetConfig
- **Given** all parameters including `ssh`, `venv_path`, `merge_to_branches`, `domain`, `tech_stack`, `key_dirs`, `conventions`
- **When** `TargetConfig(...)` is constructed with all parameters
- **Then** all attributes match the provided values

### Requirement: LLMConfig defaults

`LLMConfig` SHALL default `base_url=None`, `proxy=None`, `max_tokens=4096`, `temperature=0.3`.

#### Scenario: Default values for optional parameters

- **testable**: true
- **target**: zsiga/config.py::LLMConfig
- **Given** only required parameters `provider`, `model`, `api_key`
- **When** `LLMConfig(provider="openai", model="gpt-4", api_key="sk-test")` is constructed
- **Then** `base_url` is `None`, `proxy` is `None`, `max_tokens` is `4096`, `temperature` is `0.3`

### Requirement: CompactionConfig defaults

`CompactionConfig` SHALL default `enabled=True`, `threshold_chars=30000`, `keep_recent=3`, `use_llm_summary=True`, `total_budget=200000`, `per_turn_limit=8192`, `compaction_ratio=0.8`.

#### Scenario: All defaults match specification

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::CompactionConfig
- **Given** no parameters provided
- **When** `CompactionConfig()` is constructed
- **Then** all seven attributes match the specified defaults

### Requirement: PipelineConfig defaults and budget_profiles merge

`PipelineConfig` SHALL provide default values for all fields and merge custom `budget_profiles` on top of `DEFAULT_BUDGET_PROFILES`.

#### Scenario: Default values for key fields

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::PipelineConfig
- **Given** no parameters
- **When** `PipelineConfig()` is constructed
- **Then** `max_changes_per_cycle` is `3`, `fix_attempts` is `10`, `compaction` is a `CompactionConfig` instance, `operator_blocked_commands` contains `"rm -rf /"`, and `budget_profiles` includes default entries

#### Scenario: Custom budget_profiles merge with defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::PipelineConfig
- **Given** custom `budget_profiles` overriding `"fix"` and adding `"custom"`
- **When** `PipelineConfig(budget_profiles={"fix": 500000, "custom": 100000})` is constructed
- **Then** `"fix"` is overridden to `500000`, `"custom"` is `100000`, and other default keys remain unchanged

### Requirement: IntakeConfig, SafetyConfig, GithubConfig, LoggingConfig defaults

Each config class SHALL provide documented defaults when constructed without arguments.

#### Scenario: IntakeConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::IntakeConfig
- **Given** no parameters
- **When** `IntakeConfig()` is constructed
- **Then** `mode` is `"dir_scan"`, `scan_interval_seconds` is `60`, `api_url` is `None`, `api_headers` is `{}`

#### Scenario: SafetyConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SafetyConfig
- **Given** no parameters
- **When** `SafetyConfig()` is constructed
- **Then** `require_approval` is `True`, `protected_paths` is `[]`, `max_files_per_task` is `3`, `dry_run` is `False`

#### Scenario: GithubConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::GithubConfig
- **Given** no parameters
- **When** `GithubConfig()` is constructed
- **Then** `token` is `""`, `owner` is `""`, `issue_integration` is `False`

#### Scenario: LoggingConfig level normalization

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LoggingConfig
- **Given** `level="debug"` (lowercase)
- **When** `LoggingConfig(level="debug")` is constructed
- **Then** `level` is `"DEBUG"` (uppercased)

### Requirement: ZsigaConfig construction with optional fields

`ZsigaConfig` SHALL accept `logging_config`, `llm_fast`, `github` as optional parameters defaulting to `None`, and `active_target` defaulting to `"zsiga"`.

#### Scenario: Minimal construction with None optionals

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::ZsigaConfig
- **Given** only required arguments
- **When** `ZsigaConfig(llm=..., targets=..., pipeline=..., intake=..., safety=...)` is constructed
- **Then** `logging_config` is `None`, `llm_fast` is `None`, `github` is `None`, `active_target` is `"zsiga"`

