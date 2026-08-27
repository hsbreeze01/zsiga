# config-data-class-defaults

> Delta spec for change `evo-improvement-20260528-014707`
> Covers data class construction and default values for config classes that have
> zero direct test coverage in `test_config_validation.py`.

---

## ADDED Requirements

### Requirement: CompactionConfig default values

`CompactionConfig` SHALL be constructable with no arguments. All attributes SHALL
default to documented values: `enabled=True`, `threshold_chars=30000`,
`keep_recent=3`, `use_llm_summary=True`, `total_budget=200000`,
`per_turn_limit=8192`, `compaction_ratio=0.8`.

#### Scenario: CompactionConfig constructed with no arguments yields documented defaults

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig.__init__
- **Given** a `CompactionConfig` constructed with no arguments
- **When** all attributes are inspected
- **Then** `enabled` SHALL be `True`, `threshold_chars` SHALL be `30000`, `keep_recent` SHALL be `3`, `use_llm_summary` SHALL be `True`, `total_budget` SHALL be `200000`, `per_turn_limit` SHALL be `8192`, `compaction_ratio` SHALL be `0.8`

---

### Requirement: LoggingConfig level normalization

`LoggingConfig` SHALL normalize the `level` parameter to uppercase regardless of
the input casing. Other attributes (`fmt`, `file`) SHALL pass through unchanged.

#### Scenario: LoggingConfig lowercased level is normalized to uppercase

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig.__init__
- **Given** a `LoggingConfig` constructed with `level="debug"`
- **When** the `level` attribute is read
- **Then** it SHALL be `"DEBUG"`

#### Scenario: LoggingConfig defaults without arguments

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig.__init__
- **Given** a `LoggingConfig` constructed with no arguments
- **When** attributes are inspected
- **Then** `level` SHALL be `"INFO"`, `fmt` SHALL be `"text"`, `file` SHALL be `None`

---

### Requirement: SafetyConfig default values

`SafetyConfig` SHALL be constructable with no arguments and provide documented
defaults for all attributes.

#### Scenario: SafetyConfig constructed with no arguments yields documented defaults

- **testable**: true
- **target**: zsiga/config.py::SafetyConfig.__init__
- **Given** a `SafetyConfig` constructed with no arguments
- **When** all attributes are inspected
- **Then** `require_approval` SHALL be `True`, `protected_paths` SHALL be `[]`, `max_files_per_task` SHALL be `3`, `dry_run` SHALL be `False`

---

### Requirement: GithubConfig default values

`GithubConfig` SHALL be constructable with no arguments and provide documented
defaults.

#### Scenario: GithubConfig constructed with no arguments yields documented defaults

- **testable**: true
- **target**: zsiga/config.py::GithubConfig.__init__
- **Given** a `GithubConfig` constructed with no arguments
- **When** all attributes are inspected
- **Then** `token` SHALL be `""`, `owner` SHALL be `""`, `issue_integration` SHALL be `False`

---

### Requirement: IntakeConfig default values

`IntakeConfig` SHALL be constructable with no arguments and provide documented
defaults.

#### Scenario: IntakeConfig constructed with no arguments yields documented defaults

- **testable**: true
- **target**: zsiga/config.py::IntakeConfig.__init__
- **Given** an `IntakeConfig` constructed with no arguments
- **When** all attributes are inspected
- **Then** `mode` SHALL be `"dir_scan"`, `scan_interval_seconds` SHALL be `60`, `api_url` SHALL be `None`, `poll_interval_seconds` SHALL be `300`, `api_headers` SHALL be `{}`

---

### Requirement: TargetConfig default values

`TargetConfig` SHALL provide documented defaults for optional parameters when
only `name` and `path` are specified.

#### Scenario: TargetConfig with only name and path uses documented defaults

- **testable**: true
- **target**: zsiga/config.py::TargetConfig.__init__
- **Given** a `TargetConfig` constructed with `name="t"` and `path="/tmp/t"`
- **When** optional attributes are inspected
- **Then** `test_cmd` SHALL be `"pytest -x --tb=short"`, `lint_cmd` SHALL be `"ruff check ."`, `transport` SHALL be `"local"`, `ssh` SHALL be `None`, `deploy_branch` SHALL be `"main"`, `merge_to_branches` SHALL be `[]`, `domain` SHALL be `""`, `tech_stack` SHALL be `[]`, `key_dirs` SHALL be `[]`, `conventions` SHALL be `""`

---

### Requirement: PipelineConfig default values

`PipelineConfig` SHALL be constructable with no arguments and provide a default
`operator_blocked_commands` list containing dangerous shell commands, and a
`compaction` sub-config with `CompactionConfig` defaults. `budget_profiles`
SHALL merge caller-provided profiles over the built-in defaults.

#### Scenario: PipelineConfig default operator_blocked_commands contains dangerous commands

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** a `PipelineConfig` constructed with no arguments
- **When** `operator_blocked_commands` is inspected
- **Then** it SHALL contain `"rm -rf /"` and `"shutdown"` and `"reboot"`

#### Scenario: PipelineConfig default compaction is CompactionConfig with defaults

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** a `PipelineConfig` constructed with no arguments
- **When** `compaction` attribute is inspected
- **Then** it SHALL be a `CompactionConfig` instance with `enabled=True` and `threshold_chars=30000`

#### Scenario: PipelineConfig budget_profiles merges over defaults

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** a `PipelineConfig` constructed with `budget_profiles={"fix": 999999}`
- **When** `budget_profiles` is inspected
- **Then** `budget_profiles["fix"]` SHALL be `999999` AND `budget_profiles` SHALL also contain the default key `"implementation"` with value `600000`
