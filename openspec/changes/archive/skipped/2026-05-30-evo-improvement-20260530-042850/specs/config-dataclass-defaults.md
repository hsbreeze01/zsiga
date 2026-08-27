# config-dataclass-defaults.md

## ADDED Requirements

### Requirement: Data class constructors SHALL provide documented default values

Each configuration data class in `zsiga/config.py` SHALL initialize with the default
parameter values documented in its `__init__` signature. These defaults guarantee that
a no-argument (or minimal-argument) construction produces a valid object.

#### Scenario: SSHConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SSHConfig
- **Given** an `SSHConfig` constructed with only `host="myhost"`
- **Then** `user` SHALL be `None`, `port` SHALL be `22`, `key_path` SHALL be `None`

#### Scenario: TargetConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::TargetConfig
- **Given** a `TargetConfig` constructed with only `name="t"` and `path="/tmp"`
- **Then** `test_cmd` SHALL be `"pytest -x --tb=short"`, `lint_cmd` SHALL be `"ruff check ."`, `transport` SHALL be `"local"`, `deploy_branch` SHALL be `"main"`, `merge_to_branches` SHALL be `[]`, `domain` SHALL be `""`, `tech_stack` SHALL be `[]`, `key_dirs` SHALL be `[]`, `conventions` SHALL be `""`

#### Scenario: LLMConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LLMConfig
- **Given** an `LLMConfig` constructed with only `provider="p"`, `model="m"`, `api_key="k"`
- **Then** `base_url` SHALL be `None`, `proxy` SHALL be `None`, `max_tokens` SHALL be `4096`, `temperature` SHALL be `0.3`

#### Scenario: CompactionConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::CompactionConfig
- **Given** a `CompactionConfig` constructed with no arguments
- **Then** `enabled` SHALL be `True`, `threshold_chars` SHALL be `30000`, `keep_recent` SHALL be `3`, `use_llm_summary` SHALL be `True`, `total_budget` SHALL be `200000`, `per_turn_limit` SHALL be `8192`, `compaction_ratio` SHALL be `0.8`

#### Scenario: PipelineConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::PipelineConfig
- **Given** a `PipelineConfig` constructed with no arguments
- **Then** `max_changes_per_cycle` SHALL be `3`, `impl_timeout_minutes` SHALL be `20`, `fix_attempts` SHALL be `10`, `cycle_interval_hours` SHALL be `8`, `proposal_gate_enabled` SHALL be `False`, `evolution_enabled` SHALL be `True`, `budget_profiles` SHALL equal `DEFAULT_BUDGET_PROFILES`

#### Scenario: IntakeConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::IntakeConfig
- **Given** an `IntakeConfig` constructed with no arguments
- **Then** `mode` SHALL be `"dir_scan"`, `scan_interval_seconds` SHALL be `60`, `api_headers` SHALL be `{}`

#### Scenario: SafetyConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SafetyConfig
- **Given** a `SafetyConfig` constructed with no arguments
- **Then** `require_approval` SHALL be `True`, `protected_paths` SHALL be `[]`, `max_files_per_task` SHALL be `3`, `dry_run` SHALL be `False`

#### Scenario: GithubConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::GithubConfig
- **Given** a `GithubConfig` constructed with no arguments
- **Then** `token` SHALL be `""`, `owner` SHALL be `""`, `issue_integration` SHALL be `False`

#### Scenario: LoggingConfig defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LoggingConfig
- **Given** a `LoggingConfig` constructed with no arguments
- **Then** `level` SHALL be `"INFO"`, `fmt` SHALL be `"text"`, `file` SHALL be `None`

#### Scenario: LoggingConfig uppercases level

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LoggingConfig
- **Given** a `LoggingConfig` constructed with `level="debug"`
- **Then** `level` SHALL be `"DEBUG"`

