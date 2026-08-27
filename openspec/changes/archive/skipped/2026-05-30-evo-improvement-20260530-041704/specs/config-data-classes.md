# Spec: config-data-classes

Coverage for the 13 data/configuration classes in `zsiga/config.py`:
constructors, default values, and attribute access. These classes are
currently only tested indirectly through `validate_config` in
`test_config_validation.py`.

## ADDED Requirements

### Requirement: SSHConfig stores connection parameters

`SSHConfig.__init__` SHALL accept `host`, `user`, `port`, `key_path`
and store them as attributes. Default values: `user=None`, `port=22`,
`key_path=None`.

#### Scenario: stores host with defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SSHConfig.__init__
- **Given** an `SSHConfig` constructed with `host="example.com"`
- **When** attributes are inspected
- **Then** `host` SHALL be `"example.com"`, `user` SHALL be `None`, `port` SHALL be `22`, `key_path` SHALL be `None`

#### Scenario: stores all parameters

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::SSHConfig.__init__
- **Given** an `SSHConfig` constructed with `host="srv", user="alice", port=2222, key_path="/id_rsa"`
- **When** attributes are inspected
- **Then** all four values SHALL match the constructor arguments

---

### Requirement: TargetConfig stores target definition with defaults

`TargetConfig` SHALL accept ~15 parameters and store them as attributes.
List defaults SHALL be empty lists, not `None`.

#### Scenario: stores name and path with all defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::TargetConfig.__init__
- **Given** a `TargetConfig` constructed with `name="myproj", path="/repo"`
- **When** attributes are inspected
- **Then** `test_cmd` SHALL be `"pytest -x --tb=short"`, `lint_cmd` SHALL be `"ruff check ."`, `transport` SHALL be `"local"`, `deploy_branch` SHALL be `"main"`, `merge_to_branches` SHALL be `[]`, `tech_stack` SHALL be `[]`, `key_dirs` SHALL be `[]`

#### Scenario: stores all parameters including SSH

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::TargetConfig.__init__
- **Given** a `TargetConfig` with `ssh=SSHConfig(host="srv")` and `merge_to_branches=["dev"]`
- **When** attributes are inspected
- **Then** `ssh` SHALL be the provided `SSHConfig` instance, `merge_to_branches` SHALL be `["dev"]`

---

### Requirement: LLMConfig stores provider settings

`LLMConfig` SHALL store `provider`, `model`, `api_key`, `base_url`,
`proxy`, `max_tokens`, `temperature` with defaults for the latter four.

#### Scenario: stores required fields with defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LLMConfig.__init__
- **Given** an `LLMConfig` constructed with `provider="openai", model="gpt-4", api_key="sk-1"`
- **When** attributes are inspected
- **Then** `base_url` SHALL be `None`, `proxy` SHALL be `None`, `max_tokens` SHALL be `4096`, `temperature` SHALL be `0.3`

---

### Requirement: CompactionConfig stores compaction policy

`CompactionConfig` SHALL store 7 parameters with defaults.

#### Scenario: stores default values

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::CompactionConfig.__init__
- **Given** a `CompactionConfig` constructed with no arguments
- **When** attributes are inspected
- **Then** `enabled` SHALL be `True`, `threshold_chars` SHALL be `30000`, `keep_recent` SHALL be `3`, `use_llm_summary` SHALL be `True`, `total_budget` SHALL be `200000`, `per_turn_limit` SHALL be `8192`, `compaction_ratio` SHALL be `0.8`

---

### Requirement: PipelineConfig stores pipeline tuning parameters

`PipelineConfig` SHALL store ~50 parameters. The `budget_profiles` attribute
SHALL default to a copy of `DEFAULT_BUDGET_PROFILES`. The `compaction`
attribute SHALL default to a new `CompactionConfig()`.

#### Scenario: default budget_profiles is a copy of DEFAULT_BUDGET_PROFILES

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** a `PipelineConfig` constructed with no arguments
- **When** `budget_profiles` is inspected
- **Then** it SHALL equal `{"fix": 300000, "implementation": 600000, "cross_project": 200000, "self_modify": 800000}`

#### Scenario: custom budget_profiles merges with defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** a `PipelineConfig` constructed with `budget_profiles={"fix": 999}`
- **When** `budget_profiles` is inspected
- **Then** `"fix"` SHALL be `999` and `"implementation"` SHALL remain `600000`

#### Scenario: default operator_blocked_commands list is non-empty

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::PipelineConfig.__init__
- **Given** a `PipelineConfig` constructed with no arguments
- **When** `operator_blocked_commands` is inspected
- **Then** it SHALL contain `"rm -rf /"` and `"shutdown"`

---

### Requirement: LoggingConfig normalises level to uppercase

`LoggingConfig.__init__` SHALL convert the `level` parameter to uppercase.

#### Scenario: lower-case level is normalised

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::LoggingConfig.__init__
- **Given** a `LoggingConfig` constructed with `level="debug"`
- **When** `level` attribute is inspected
- **Then** it SHALL be `"DEBUG"`

---

### Requirement: ZsigaConfig stores all top-level config sections

`ZsigaConfig` SHALL store `llm`, `targets`, `pipeline`, `intake`, `safety`,
`logging_config`, `llm_fast`, `github`, `active_target`.

#### Scenario: stores all sections with defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::ZsigaConfig.__init__
- **Given** a `ZsigaConfig` with minimal required args (`llm`, `targets`, `pipeline`, `intake`, `safety`)
- **When** attributes are inspected
- **Then** `logging_config` SHALL be `None`, `llm_fast` SHALL be `None`, `github` SHALL be `None`, `active_target` SHALL be `"zsiga"`

