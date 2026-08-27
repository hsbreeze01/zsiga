# config-dataclasses

## ADDED Requirements

### Requirement: LoggingConfig construction

`LoggingConfig` SHALL accept `level`, `fmt`, and `file` parameters.  The
`level` parameter SHALL be stored uppercased regardless of input casing.
Defaults SHALL be `level="INFO"`, `fmt="text"`, `file=None`.

#### Scenario: Default values

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig

- **Given** a `LoggingConfig` is constructed with no arguments
- **When** its attributes are inspected
- **Then** `level` equals `"INFO"`, `fmt` equals `"text"`, `file` is `None`

#### Scenario: Level is uppercased

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig

- **Given** a `LoggingConfig` is constructed with `level="debug"`
- **When** `level` attribute is inspected
- **Then** it equals `"DEBUG"`

---

### Requirement: GithubConfig construction

`GithubConfig` SHALL accept `token`, `owner`, and `issue_integration`
parameters.  Defaults SHALL be `token=""`, `owner=""`,
`issue_integration=False`.

#### Scenario: Default values

- **testable**: true
- **target**: zsiga/config.py::GithubConfig

- **Given** a `GithubConfig` is constructed with no arguments
- **When** its attributes are inspected
- **Then** `token` equals `""`, `owner` equals `""`,
  `issue_integration` is `False`

#### Scenario: Custom values preserved

- **testable**: true
- **target**: zsiga/config.py::GithubConfig

- **Given** a `GithubConfig` is constructed with
  `token="ghp_abc"`, `owner="acme"`, `issue_integration=True`
- **When** its attributes are inspected
- **Then** `token` equals `"ghp_abc"`, `owner` equals `"acme"`,
  `issue_integration` is `True`

---

### Requirement: CompactionConfig construction

`CompactionConfig` SHALL accept `enabled`, `threshold_chars`, `keep_recent`,
`use_llm_summary`, `total_budget`, `per_turn_limit`, and `compaction_ratio`
parameters.  Defaults SHALL match the values documented in the class
definition.

#### Scenario: Default values

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig

- **Given** a `CompactionConfig` is constructed with no arguments
- **When** its attributes are inspected
- **Then** `enabled` is `True`, `threshold_chars` is `30000`,
  `keep_recent` is `3`, `use_llm_summary` is `True`,
  `total_budget` is `200000`, `per_turn_limit` is `8192`,
  `compaction_ratio` is `0.8`

#### Scenario: Custom values override defaults

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig

- **Given** a `CompactionConfig` is constructed with
  `enabled=False`, `threshold_chars=50000`, `compaction_ratio=0.5`
- **When** its attributes are inspected
- **Then** `enabled` is `False`, `threshold_chars` is `50000`,
  `compaction_ratio` is `0.5`
  - **And** other attributes retain their defaults
