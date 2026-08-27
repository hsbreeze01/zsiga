# config-gap-coverage

Consolidated spec covering test gaps in `zsiga/config.py` identified by auditing
`test_config_validation.py` (39 tests), `config_unit_coverage.py` (8 tests), and
`config_load_robustness.py` (5 tests). Existing tests cover: `_find_config`,
`_resolve_env_vars`, `validate_config` core paths, `load_config` error paths,
`ValidationResult`, `ConfigValidationError`, `LLMFastConfig`.

This spec covers the **uncovered** surface: dataclass constructors (CompactionConfig,
LoggingConfig, IntakeConfig, SafetyConfig, GithubConfig, SSHConfig, TargetConfig,
PipelineConfig), validate_config boundary branches, and load_config YAML→object
assembly for sections not exercised by existing tests.

## ADDED Requirements

### Requirement: CompactionConfig constructor defaults and custom values

`CompactionConfig` SHALL store all 7 fields with sensible defaults when constructed
without arguments and SHALL accept custom values for any field.

#### Scenario: CompactionConfig default construction

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig.__init__

- **Given** a `CompactionConfig()` constructed with no arguments
- **When** all attributes are inspected
- **Then** `enabled` is `True`, `threshold_chars` is `30000`, `keep_recent` is `3`,
  `use_llm_summary` is `True`, `total_budget` is `200000`, `per_turn_limit` is `8192`,
  `compaction_ratio` is `0.8`

#### Scenario: CompactionConfig custom construction

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig.__init__

- **Given** a `CompactionConfig(enabled=False, threshold_chars=5000, keep_recent=1)`
- **When** the overridden and default attributes are inspected
- **Then** `enabled` is `False`, `threshold_chars` is `5000`, `keep_recent` is `1`,
  and `use_llm_summary` is `True` (default preserved)

---

### Requirement: LoggingConfig level normalization and defaults

`LoggingConfig` SHALL normalize the `level` field to uppercase on construction and
SHALL default to `level="INFO"`, `fmt="text"`, `file=None`.

#### Scenario: LoggingConfig lower-case level uppercased

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig.__init__

- **Given** a `LoggingConfig(level="debug")`
- **When** the `level` attribute is inspected
- **Then** `level` equals `"DEBUG"`

#### Scenario: LoggingConfig default values

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig.__init__

- **Given** a `LoggingConfig()` constructed with no arguments
- **When** all attributes are inspected
- **Then** `level` is `"INFO"`, `fmt` is `"text"`, `file` is `None`

---

### Requirement: IntakeConfig constructor defaults

`IntakeConfig` SHALL default to `mode="dir_scan"` with reasonable polling intervals
and an empty `api_headers` dict.

#### Scenario: IntakeConfig default construction

- **testable**: true
- **target**: zsiga/config.py::IntakeConfig.__init__

- **Given** an `IntakeConfig()` constructed with no arguments
- **When** all attributes are inspected
- **Then** `mode` is `"dir_scan"`, `scan_interval_seconds` is `60`,
  `api_url` is `None`, `poll_interval_seconds` is `300`,
  `api_headers` equals `{}`

---

### Requirement: SafetyConfig constructor defaults

`SafetyConfig` SHALL default to requiring approval with conservative safety limits.

#### Scenario: SafetyConfig default construction

- **testable**: true
- **target**: zsiga/config.py::SafetyConfig.__init__

- **Given** a `SafetyConfig()` constructed with no arguments
- **When** all attributes are inspected
- **Then** `require_approval` is `True`, `protected_paths` is `[]`,
  `max_files_per_task` is `3`, `dry_run` is `False`

---

### Requirement: GithubConfig constructor defaults and custom values

`GithubConfig` SHALL default to empty strings and disabled integration, and SHALL
accept custom values.

#### Scenario: GithubConfig default construction

- **testable**: true
- **target**: zsiga/config.py::GithubConfig.__init__

- **Given** a `GithubConfig()` constructed with no arguments
- **When** all attributes are inspected
- **Then** `token` is `""`, `owner` is `""`, `issue_integration` is `False`

#### Scenario: GithubConfig custom construction

- **testable**: true
- **target**: zsiga/config.py::GithubConfig.__init__

- **Given** a `GithubConfig(token="ghp_abc", owner="acme", issue_integration=True)`
- **When** all attributes are inspected
- **Then** `token` is `"ghp_abc"`, `owner` is `"acme"`, `issue_integration` is `True`

---

### Requirement: SSHConfig constructor defaults and field assignment

`SSHConfig` SHALL default `port` to `22` and optional fields to `None`.

#### Scenario: SSHConfig minimal construction

- **testable**: true
- **target**: zsiga/config.py::SSHConfig.__init__

- **Given** an `SSHConfig(host="example.com")`
- **When** all attributes are inspected
- **Then** `host` is `"example.com"`, `user` is `None`, `port` is `22`,
  `key_path` is `None`

#### Scenario: SSHConfig all fields specified

- **testable**: true
- **target**: zsiga/config.py::SSHConfig.__init__

- **Given** an `SSHConfig(host="srv.com", user="admin", port=2222, key_path="/tmp/key")`
- **When** all attributes are inspected
- **Then** `host` is `"srv.com"`, `user` is `"admin"`, `port` is `2222`,
  `key_path` is `"/tmp/key"`

---

### Requirement: TargetConfig list field defaults

`TargetConfig` SHALL default `merge_to_branches`, `tech_stack`, and `key_dirs` to
empty lists and string fields to empty strings.

#### Scenario: TargetConfig list field defaults

- **testable**: true
- **target**: zsiga/config.py::TargetConfig.__init__

- **Given** a `TargetConfig(name="t", path="/tmp")`
- **When** list and string fields are inspected
- **Then** `merge_to_branches` is `[]`, `tech_stack` is `[]`, `key_dirs` is `[]`,
  `domain` is `""`, `description` is `""`, `conventions` is `""`

---

### Requirement: PipelineConfig budget_profiles merging

`PipelineConfig` SHALL merge user-provided `budget_profiles` on top of
`DEFAULT_BUDGET_PROFILES`, preserving keys not overridden.

#### Scenario: PipelineConfig default budget profiles

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig.__init__

- **Given** a `PipelineConfig()` constructed with no arguments
- **When** `budget_profiles` is inspected
- **Then** it equals `{"fix": 300000, "implementation": 600000,
  "cross_project": 200000, "self_modify": 800000}`

#### Scenario: PipelineConfig custom budget profiles merge

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig.__init__

- **Given** a `PipelineConfig(budget_profiles={"fix": 999999})`
- **When** `budget_profiles` is inspected
- **Then** `"fix"` is `999999` and `"implementation"` is `600000` (default preserved)

---

### Requirement: PipelineConfig SRE safety defaults

`PipelineConfig` SHALL provide non-empty default blocklists for SRE operator safety.

#### Scenario: PipelineConfig default blocked commands

- **testable**: true
- **target**: zsiga/config.py::PipelineConfig.__init__

- **Given** a `PipelineConfig()` constructed with no arguments
- **When** `operator_blocked_commands` is inspected
- **Then** the list contains `"rm -rf /"` and `"shutdown"`

---

### Requirement: validate_config domain warning for unexpected values

`validate_config` SHALL emit a warning when a target's `domain` is not one of
`""`, `"self"`, or `"external"`. Valid domain values SHALL produce no domain warning.

#### Scenario: Target with unexpected domain produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config

- **Given** a valid `ZsigaConfig` with a target whose `domain` is `"production"`
- **When** `validate_config` is called
- **Then** the result is valid (`errors` is empty) and `warnings` contains a
  string mentioning `"domain"`

#### Scenario: Target with domain self produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config

- **Given** a valid `ZsigaConfig` with a target whose `domain` is `"self"`
- **When** `validate_config` is called
- **Then** no warning containing `"domain"` is present

---

### Requirement: validate_config fix_attempts boundary values

`validate_config` SHALL NOT warn when `fix_attempts` is exactly 1 or 20 (boundary
values). It SHALL warn when `fix_attempts` exceeds 20.

#### Scenario: fix_attempts at upper boundary 20 produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config

- **Given** a valid `ZsigaConfig` with `pipeline.fix_attempts=20`
- **When** `validate_config` is called
- **Then** no warning containing `"fix_attempts"` is present

#### Scenario: fix_attempts at 21 produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config

- **Given** a valid `ZsigaConfig` with `pipeline.fix_attempts=21`
- **When** `validate_config` is called
- **Then** a warning containing `"fix_attempts"` is present

#### Scenario: fix_attempts at lower boundary 1 produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config

- **Given** a valid `ZsigaConfig` with `pipeline.fix_attempts=1`
- **When** `validate_config` is called
- **Then** no warning containing `"fix_attempts"` is present

---

### Requirement: validate_config max_changes_per_cycle upper boundary

`validate_config` SHALL NOT warn when `max_changes_per_cycle` is exactly 10.

#### Scenario: max_changes_per_cycle at boundary 10 produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config

- **Given** a valid `ZsigaConfig` with `pipeline.max_changes_per_cycle=10`
- **When** `validate_config` is called
- **Then** no warning containing `"max_changes_per_cycle"` is present

---

### Requirement: load_config SSH target integration

`load_config` SHALL construct an `SSHConfig` and set `transport="ssh"` when a
target section includes an `ssh` sub-dictionary. Targets without `ssh` SHALL
default `transport` to `"local"`.

#### Scenario: SSH target parsed from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config

- **Given** a YAML config file with a target containing
  `ssh: {host: "srv.example.com", user: "deploy", port: 2222}`
- **When** `load_config` is called with that file's path
- **Then** the returned config has a target with `transport == "ssh"`,
  `ssh.host == "srv.example.com"`, `ssh.user == "deploy"`, `ssh.port == 2222`

#### Scenario: Target without SSH defaults transport to local

- **testable**: true
- **target**: zsiga/config.py::load_config

- **Given** a YAML config file with a target that has no `ssh` key
- **When** `load_config` is called
- **Then** the returned target's `transport` is `"local"` and `ssh` is `None`

---

### Requirement: load_config LoggingConfig integration

`load_config` SHALL parse the `logging` section and construct a `LoggingConfig`
with level normalization.

#### Scenario: Logging section parsed from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config

- **Given** a YAML config file with
  `logging: {level: "debug", format: "json", file: "/tmp/zsiga.log"}`
- **When** `load_config` is called
- **Then** `config.logging_config.level == "DEBUG"`,
  `config.logging_config.fmt == "json"`,
  `config.logging_config.file == "/tmp/zsiga.log"`

---

### Requirement: load_config GithubConfig integration

`load_config` SHALL parse the `github` section and construct a `GithubConfig`.

#### Scenario: Github section parsed from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config

- **Given** a YAML config file with
  `github: {token: "ghp_123", owner: "acme", issue_integration: true}`
- **When** `load_config` is called
- **Then** `config.github.token == "ghp_123"`,
  `config.github.owner == "acme"`,
  `config.github.issue_integration is True`

---

### Requirement: load_config active_target override

`load_config` SHALL read `active_target` from the YAML root, defaulting to `"zsiga"`.

#### Scenario: active_target parsed from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config

- **Given** a YAML config file with `active_target: "my-project"`
- **When** `load_config` is called
- **Then** `config.active_target == "my-project"`

#### Scenario: active_target defaults to zsiga when absent

- **testable**: true
- **target**: zsiga/config.py::load_config

- **Given** a valid YAML config file without an `active_target` key
- **When** `load_config` is called
- **Then** `config.active_target == "zsiga"`

---

### Requirement: load_config CompactionConfig integration

`load_config` SHALL parse the `pipeline.compaction` subsection and construct a
`CompactionConfig` with custom values when provided.

#### Scenario: Compaction subsection parsed from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config

- **Given** a YAML config file with
  `pipeline: {compaction: {enabled: false, threshold_chars: 9999}}`
- **When** `load_config` is called
- **Then** `config.pipeline.compaction.enabled is False`,
  `config.pipeline.compaction.threshold_chars == 9999`

---

### Requirement: load_config SafetyConfig integration

`load_config` SHALL parse the `safety` section and construct a `SafetyConfig`.

#### Scenario: Safety section parsed from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config

- **Given** a YAML config file with
  `safety: {require_approval: false, max_files_per_task: 10}`
- **When** `load_config` is called
- **Then** `config.safety.require_approval is False`,
  `config.safety.max_files_per_task == 10`

---

### Requirement: load_config env var resolution in context

`load_config` SHALL apply `_resolve_env_vars` to the raw YAML content before
constructing config objects.

#### Scenario: Env var resolved in api_key field

- **testable**: true
- **target**: zsiga/config.py::load_config

- **Given** environment variable `ZSIGA_TEST_API_KEY` is set to `"resolved-key"`
- **And** a YAML config file with `agent.llm.api_key="${ZSIGA_TEST_API_KEY}"`
- **When** `load_config` is called
- **Then** `config.llm.api_key == "resolved-key"`
