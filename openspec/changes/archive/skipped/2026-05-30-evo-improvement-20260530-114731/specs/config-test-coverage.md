# config-test-coverage

> Delta spec for change `evo-improvement-20260530-114731`
> Covers data class construction defaults and validation edge cases in `zsiga/config.py`
> that lack direct unit test coverage in existing test files.

## ADDED Requirements

### Requirement: LoggingConfig normalizes level to uppercase

The `LoggingConfig` class SHALL convert the `level` parameter to uppercase
regardless of the input casing.

#### Scenario: Level is normalized to uppercase

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig
- **Given** a LoggingConfig is constructed with `level="debug"`
- **When** the instance is inspected
- **Then** `config.level` SHALL equal `"DEBUG"`

#### Scenario: Level already uppercase stays unchanged

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig
- **Given** a LoggingConfig is constructed with `level="INFO"`
- **When** the instance is inspected
- **Then** `config.level` SHALL equal `"INFO"`

---

### Requirement: CompactionConfig defaults

The `CompactionConfig` class SHALL provide sensible defaults for all fields
when constructed without arguments.

#### Scenario: Default values are correct

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig
- **Given** a CompactionConfig is constructed with no arguments
- **When** the instance is inspected
- **Then** `enabled` SHALL be `True`, `threshold_chars` SHALL be `30000`,
  `keep_recent` SHALL be `3`, `use_llm_summary` SHALL be `True`,
  `total_budget` SHALL be `200000`, `per_turn_limit` SHALL be `8192`,
  `compaction_ratio` SHALL be `0.8`

---

### Requirement: SafetyConfig defaults

The `SafetyConfig` class SHALL provide sensible defaults when constructed
without arguments.

#### Scenario: Default values are correct

- **testable**: true
- **target**: zsiga/config.py::SafetyConfig
- **Given** a SafetyConfig is constructed with no arguments
- **When** the instance is inspected
- **Then** `require_approval` SHALL be `True`, `protected_paths` SHALL be `[]`,
  `max_files_per_task` SHALL be `3`, `dry_run` SHALL be `False`

---

### Requirement: GithubConfig defaults

The `GithubConfig` class SHALL provide empty-string defaults for token and
owner, and `False` for issue_integration.

#### Scenario: Default values are correct

- **testable**: true
- **target**: zsiga/config.py::GithubConfig
- **Given** a GithubConfig is constructed with no arguments
- **When** the instance is inspected
- **Then** `token` SHALL be `""`, `owner` SHALL be `""`,
  `issue_integration` SHALL be `False`

---

### Requirement: IntakeConfig defaults

The `IntakeConfig` class SHALL default to `dir_scan` mode with a 60-second
scan interval.

#### Scenario: Default values are correct

- **testable**: true
- **target**: zsiga/config.py::IntakeConfig
- **Given** an IntakeConfig is constructed with no arguments
- **When** the instance is inspected
- **Then** `mode` SHALL be `"dir_scan"`, `scan_interval_seconds` SHALL be `60`,
  `api_url` SHALL be `None`, `poll_interval_seconds` SHALL be `300`,
  `api_headers` SHALL be `{}`

---

### Requirement: validate_config warns on non-standard domain value

When a target's `domain` field is set to a value that is not `""`, `"self"`, or
`"external"`, `validate_config()` SHALL produce a warning.

#### Scenario: Non-standard domain produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a ZsigaConfig with a target whose `domain` is `"production"`
- **When** `validate_config(config)` is called
- **Then** the result SHALL be valid (no errors)
- **And** the result's warnings SHALL contain a message mentioning `"domain"` and `"production"`

#### Scenario: Standard domain values produce no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a ZsigaConfig with targets having `domain=""` and `domain="self"`
- **When** `validate_config(config)` is called
- **Then** the result's warnings SHALL NOT contain any message mentioning `"domain"`

---

### Requirement: SSHConfig construction preserves all fields

The `SSHConfig` class SHALL store all provided fields and use port 22 as
default when not specified.

#### Scenario: Default port is 22

- **testable**: true
- **target**: zsiga/config.py::SSHConfig
- **Given** an SSHConfig is constructed with only `host="myserver.com"`
- **When** the instance is inspected
- **Then** `host` SHALL be `"myserver.com"`, `port` SHALL be `22`,
  `user` SHALL be `None`, `key_path` SHALL be `None`

#### Scenario: All fields are stored

- **testable**: true
- **target**: zsiga/config.py::SSHConfig
- **Given** an SSHConfig is constructed with `host="myserver.com"`,
  `user="admin"`, `port=2222`, `key_path="/home/.ssh/id_rsa"`
- **When** the instance is inspected
- **Then** all four fields SHALL match their construction values
