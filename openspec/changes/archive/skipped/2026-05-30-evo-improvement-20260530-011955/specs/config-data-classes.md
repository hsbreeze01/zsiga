# config-data-classes — Configuration Data Class Construction and Defaults

## ADDED Requirements

### Requirement: SSHConfig construction and defaults

`SSHConfig` SHALL accept `host` as a required parameter and provide default values for `user` (None), `port` (22), and `key_path` (None).

#### Scenario: Constructs with defaults

- **testable**: true
- **target**: zsiga/config.py::SSHConfig
- **Given** no optional arguments
- **When** `SSHConfig(host="myserver.com")` is constructed
- **Then** `host` SHALL be `"myserver.com"` AND `user` SHALL be `None` AND `port` SHALL be `22` AND `key_path` SHALL be `None`

### Requirement: TargetConfig construction and defaults

`TargetConfig` SHALL accept `name` and `path` as required parameters and provide sensible defaults for all other fields including `test_cmd`, `lint_cmd`, `transport`, `deploy_branch`, and empty lists for collection fields.

#### Scenario: Constructs with required fields only

- **testable**: true
- **target**: zsiga/config.py::TargetConfig
- **Given** no optional arguments
- **When** `TargetConfig(name="proj", path="/proj")` is constructed
- **Then** `test_cmd` SHALL be `"pytest -x --tb=short"` AND `lint_cmd` SHALL be `"ruff check ."` AND `transport` SHALL be `"local"` AND `deploy_branch` SHALL be `"main"` AND `merge_to_branches` SHALL be `[]`

### Requirement: CompactionConfig defaults

`CompactionConfig` SHALL provide default values for all parameters including `enabled` (True), `threshold_chars` (30000), `keep_recent` (3), `use_llm_summary` (True), `total_budget` (200000), `per_turn_limit` (8192), `compaction_ratio` (0.8).

#### Scenario: Constructs with all defaults

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig
- **Given** no arguments
- **When** `CompactionConfig()` is constructed
- **Then** `enabled` SHALL be `True` AND `threshold_chars` SHALL be `30000` AND `compaction_ratio` SHALL be `0.8`

### Requirement: LoggingConfig normalizes level to uppercase

`LoggingConfig` SHALL convert the `level` parameter to uppercase regardless of input casing.

#### Scenario: Lowercase level is normalized

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig
- **Given** a lowercase level string `"debug"`
- **When** `LoggingConfig(level="debug")` is constructed
- **Then** `level` SHALL be `"DEBUG"`

#### Scenario: Mixed case level is normalized

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig
- **Given** a mixed-case level string `"Info"`
- **When** `LoggingConfig(level="Info")` is constructed
- **Then** `level` SHALL be `"INFO"`

### Requirement: PipelineConfig default budget profiles

`PipelineConfig` SHALL initialize `budget_profiles` with the default profiles (`fix`, `implementation`, `cross_project`, `self_modify`) and merge any user-provided overrides on top.

#### Scenario: Default budget profiles when no override

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** no `budget_profiles` argument
- **When** `PipelineConfig()` is constructed
- **Then** `budget_profiles` SHALL contain keys `"fix"`, `"implementation"`, `"cross_project"`, `"self_modify"`

#### Scenario: User override merges onto defaults

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** `budget_profiles={"fix": 500000}`
- **When** `PipelineConfig(budget_profiles={"fix": 500000})` is constructed
- **Then** `budget_profiles["fix"]` SHALL be `500000` AND `budget_profiles["implementation"]` SHALL be the default `600000`

### Requirement: PipelineConfig default blocked commands

`PipelineConfig` SHALL provide a non-empty default list of `operator_blocked_commands` when none are specified.

#### Scenario: Default blocked commands present

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig
- **Given** no `operator_blocked_commands` argument
- **When** `PipelineConfig()` is constructed
- **Then** `operator_blocked_commands` SHALL be a non-empty list containing `"rm -rf /"`

### Requirement: SafetyConfig defaults

`SafetyConfig` SHALL provide defaults of `require_approval=True`, `protected_paths=[]`, `max_files_per_task=3`, `dry_run=False`.

#### Scenario: Constructs with all defaults

- **testable**: true
- **target**: zsiga/config.py::SafetyConfig
- **Given** no arguments
- **When** `SafetyConfig()` is constructed
- **Then** `require_approval` SHALL be `True` AND `protected_paths` SHALL be `[]` AND `max_files_per_task` SHALL be `3` AND `dry_run` SHALL be `False`
