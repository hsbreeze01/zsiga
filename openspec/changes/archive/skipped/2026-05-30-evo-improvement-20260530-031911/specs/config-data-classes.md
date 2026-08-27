# config-data-classes

## ADDED Requirements

### Requirement: CompactionConfig default values

`CompactionConfig` SHALL provide sensible defaults for all fields when
constructed without arguments: `enabled=True`, `threshold_chars=30000`,
`keep_recent=3`, `use_llm_summary=True`, `total_budget=200000`,
`per_turn_limit=8192`, `compaction_ratio=0.8`.

#### Scenario: Default CompactionConfig construction

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig
- **Given** no arguments
- **When** `CompactionConfig()` is constructed
- **Then** all fields SHALL equal their documented default values

---

### Requirement: SafetyConfig default values

`SafetyConfig` SHALL default to `require_approval=True`,
`protected_paths=[]`, `max_files_per_task=3`, `dry_run=False`.

#### Scenario: Default SafetyConfig construction

- **testable**: true
- **target**: zsiga/config.py::SafetyConfig
- **Given** no arguments
- **When** `SafetyConfig()` is constructed
- **Then** `require_approval` SHALL be `True`, `protected_paths` SHALL be `[]`,
  `max_files_per_task` SHALL be `3`, `dry_run` SHALL be `False`

---

### Requirement: LoggingConfig level normalization

`LoggingConfig` SHALL normalize the `level` argument to uppercase regardless
of the casing provided by the caller.

#### Scenario: Lowercase level is normalized to uppercase

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig
- **Given** level argument `"debug"`
- **When** `LoggingConfig(level="debug")` is constructed
- **Then** `logging_config.level` SHALL equal `"DEBUG"`

#### Scenario: Mixed-case level is normalized to uppercase

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig
- **Given** level argument `"Info"`
- **When** `LoggingConfig(level="Info")` is constructed
- **Then** `logging_config.level` SHALL equal `"INFO"`

---

### Requirement: PipelineConfig budget_profiles defaults

`PipelineConfig` SHALL initialize `budget_profiles` with a copy of
`DEFAULT_BUDGET_PROFILES` containing keys `"fix"`, `"implementation"`,
`"cross_project"`, `"self_modify"`. User-provided `budget_profiles` SHALL
merge on top of these defaults without removing unspecified keys.

#### Scenario: Default budget profiles include standard keys

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** no `budget_profiles` argument
- **When** `PipelineConfig()` is constructed
- **Then** `budget_profiles` SHALL contain keys `"fix"`, `"implementation"`,
  `"cross_project"`, `"self_modify"` with values from `DEFAULT_BUDGET_PROFILES`

#### Scenario: Custom budget profiles merge with defaults

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** `budget_profiles={"fix": 500000}`
- **When** `PipelineConfig(budget_profiles={"fix": 500000})` is constructed
- **Then** `budget_profiles["fix"]` SHALL be `500000` and all other default keys
  SHALL remain present with their default values

---

### Requirement: GithubConfig default values

`GithubConfig` SHALL default to empty token, empty owner, and
`issue_integration=False`.

#### Scenario: Default GithubConfig construction

- **testable**: true
- **target**: zsiga/config.py::GithubConfig
- **Given** no arguments
- **When** `GithubConfig()` is constructed
- **Then** `token` SHALL be `""`, `owner` SHALL be `""`,
  `issue_integration` SHALL be `False`

---

### Requirement: IntakeConfig default values

`IntakeConfig` SHALL default to `mode="dir_scan"`,
`scan_interval_seconds=60`, `api_url=None`,
`poll_interval_seconds=300`, `api_headers={}`.

#### Scenario: Default IntakeConfig construction

- **testable**: true
- **target**: zsiga/config.py::IntakeConfig
- **Given** no arguments
- **When** `IntakeConfig()` is constructed
- **Then** `mode` SHALL be `"dir_scan"`, `scan_interval_seconds` SHALL be `60`,
  `api_url` SHALL be `None`, `poll_interval_seconds` SHALL be `300`,
  `api_headers` SHALL be `{}`
