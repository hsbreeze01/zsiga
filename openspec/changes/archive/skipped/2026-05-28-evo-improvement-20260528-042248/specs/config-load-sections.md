# config-load-sections

Coverage for `load_config` YAML parsing of subsections that have no dedicated test coverage:
`logging`, `github`, `safety`, and `active_target`.

Existing tests cover: `agent.llm` fields, `targets` basic parsing, `llm_fast`, validation
error paths, and robustness (empty/malformed YAML). No existing test verifies that
`logging`, `github`, `safety`, or `active_target` YAML keys are correctly parsed into
their corresponding data class instances.

## ADDED Requirements

### Requirement: load_config parses logging section

When `zsiga.yaml` contains a `logging` section, `load_config` SHALL populate
`ZsigaConfig.logging_config` with a `LoggingConfig` instance reflecting the YAML values,
including level uppercasing. When absent, SHALL use defaults.

#### Scenario: load_config with logging section

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file containing a `logging` section with
  `level: "debug"`, `format: "json"`, `file: "/tmp/zsiga.log"`
  and valid minimal `agent` and `targets` sections
- **When** `load_config` is called with that file path
- **Then** `config.logging_config.level` SHALL be `"DEBUG"` (uppercased),
  `config.logging_config.fmt` SHALL be `"json"`,
  `config.logging_config.file` SHALL be `"/tmp/zsiga.log"`

#### Scenario: load_config without logging section

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a minimal valid YAML config file with no `logging` key
- **When** `load_config` is called with that file path
- **Then** `config.logging_config` is not `None`,
  `config.logging_config.level` is `"INFO"`,
  `config.logging_config.fmt` is `"text"`

### Requirement: load_config parses github section

When `zsiga.yaml` contains a `github` section, `load_config` SHALL populate
`ZsigaConfig.github` with a `GithubConfig` instance. When absent, SHALL use defaults.

#### Scenario: load_config with github section

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file containing a `github` section with
  `token: "ghp_abc123"`, `owner: "myorg"`, `issue_integration: true`
  and valid minimal sections
- **When** `load_config` is called with that file path
- **Then** `config.github.token` SHALL be `"ghp_abc123"`,
  `config.github.owner` SHALL be `"myorg"`,
  `config.github.issue_integration` SHALL be `True`

#### Scenario: load_config without github section

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a minimal valid YAML config file with no `github` key
- **When** `load_config` is called with that file path
- **Then** `config.github` is not `None`,
  `config.github.token` is `""` (default applied)

### Requirement: load_config parses safety section

When `zsiga.yaml` contains a `safety` section, `load_config` SHALL populate
`ZsigaConfig.safety` with the specified values.

#### Scenario: load_config with safety section

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file containing a `safety` section with
  `require_approval: false`, `protected_paths: ["/etc"]`, `max_files_per_task: 5`,
  `dry_run: true` and valid minimal sections
- **When** `load_config` is called with that file path
- **Then** `config.safety.require_approval` SHALL be `False`,
  `config.safety.protected_paths` SHALL contain `"/etc"`,
  `config.safety.max_files_per_task` SHALL be `5`,
  `config.safety.dry_run` SHALL be `True`

### Requirement: load_config parses active_target field

`load_config` SHALL set `ZsigaConfig.active_target` from the `active_target` YAML key,
defaulting to `"zsiga"` when absent.

#### Scenario: load_config with custom active_target

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `active_target: "my-project"` and valid minimal sections
- **When** `load_config` is called with that file path
- **Then** `config.active_target` SHALL be `"my-project"`

#### Scenario: load_config active_target defaults to zsiga

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a minimal valid YAML config file with no `active_target` key
- **When** `load_config` is called with that file path
- **Then** `config.active_target` SHALL be `"zsiga"`
