# config-load-sections

Behavioural spec for `load_config()` subsection parsing that is not covered
by existing tests (`test_config_validation.py`, `test_spec_*_config_load_robustness.py`).

Existing tests cover: basic LLM parsing, LLMFastConfig, validation error propagation,
empty/malformed YAML, missing agent/llm keys.

This spec covers: SSH target parsing, SafetyConfig, LoggingConfig, GithubConfig,
CompactionConfig, active_target, and env var resolution during load.

## ADDED Requirements

### Requirement: load-ssh-target

`load_config()` SHALL parse the `ssh` subsection under a target and construct
an `SSHConfig` with the correct fields.

#### Scenario: SSH target with full config parsed correctly

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with a target that has `transport: ssh` and an `ssh`
  subsection containing `host`, `user`, `port`, and `key_path`
- **When** `load_config(path)` is called
- **Then** the returned target's `ssh` SHALL be non-None,
  `ssh.host` SHALL equal the YAML value,
  `ssh.user` SHALL equal the YAML value,
  `ssh.port` SHALL equal the YAML value,
  and `ssh.key_path` SHALL equal the YAML value

### Requirement: load-safety-config

`load_config()` SHALL parse the `safety` subsection into a `SafetyConfig`.

#### Scenario: SafetyConfig with custom values

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `safety.require_approval: false`,
  `safety.max_files_per_task: 5`, and `safety.dry_run: true`
- **When** `load_config(path)` is called
- **Then** `config.safety.require_approval` SHALL be `False`,
  `config.safety.max_files_per_task` SHALL be `5`,
  and `config.safety.dry_run` SHALL be `True`

### Requirement: load-logging-config

`load_config()` SHALL parse the `logging` subsection into a `LoggingConfig`.

#### Scenario: LoggingConfig with custom values

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `logging.level: debug` and `logging.format: json`
- **When** `load_config(path)` is called
- **Then** `config.logging_config.level` SHALL be `"DEBUG"` (uppercased)
  and `config.logging_config.fmt` SHALL be `"json"`

### Requirement: load-github-config

`load_config()` SHALL parse the `github` subsection into a `GithubConfig`.

#### Scenario: GithubConfig parsed from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `github.token: ghu_abc123`,
  `github.owner: myorg`, and `github.issue_integration: true`
- **When** `load_config(path)` is called
- **Then** `config.github` SHALL be non-None,
  `config.github.token` SHALL be `"ghu_abc123"`,
  `config.github.owner` SHALL be `"myorg"`,
  and `config.github.issue_integration` SHALL be `True`

### Requirement: load-compaction-config

`load_config()` SHALL parse the `pipeline.compaction` subsection into a
`CompactionConfig` with custom values.

#### Scenario: CompactionConfig with custom values

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `pipeline.compaction.enabled: false`,
  `pipeline.compaction.threshold_chars: 50000`, and
  `pipeline.compaction.keep_recent: 5`
- **When** `load_config(path)` is called
- **Then** `config.pipeline.compaction.enabled` SHALL be `False`,
  `config.pipeline.compaction.threshold_chars` SHALL be `50000`,
  and `config.pipeline.compaction.keep_recent` SHALL be `5`

### Requirement: load-active-target

`load_config()` SHALL read the top-level `active_target` key.

#### Scenario: Active target read from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `active_target: myproject`
- **When** `load_config(path)` is called
- **Then** `config.active_target` SHALL be `"myproject"`

### Requirement: load-env-var-resolution

`load_config()` SHALL resolve `${VAR}` environment variable placeholders
in YAML values via `_resolve_env_vars`.

#### Scenario: Env var in api_key resolved during load

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** environment variable `ZSIGA_TEST_API_KEY` is set to `"sk-resolved-key"`,
  AND a YAML config with `agent.llm.api_key: "${ZSIGA_TEST_API_KEY}"`
- **When** `load_config(path)` is called
- **Then** `config.llm.api_key` SHALL be `"sk-resolved-key"`
