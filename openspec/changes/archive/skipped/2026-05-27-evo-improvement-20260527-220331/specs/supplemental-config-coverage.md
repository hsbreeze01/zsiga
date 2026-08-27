# supplemental-config-coverage

Supplementary test coverage for `zsiga/config.py`, adding non-duplicate tests
that exercise paths not covered by the existing 52 tests across
`test_config_validation.py`,
`test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`, and
`test_spec_evo_improvement_20260527_125207__config_load_robustness.py`.

## ADDED Requirements

### Requirement: _find_config home-directory fallback

`_find_config()` SHALL return the `~/.zsiga/zsiga.yaml` path when no
`zsiga.yaml` exists in the current working directory but one exists in the
user's home `.zsiga/` directory.

#### Scenario: falls back to home directory when cwd has no config

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** the current working directory does not contain `zsiga.yaml`
  AND `~/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** the returned `Path` points to `~/.zsiga/zsiga.yaml`

### Requirement: _resolve_env_vars partial placeholder passthrough

`_resolve_env_vars()` SHALL return a string unchanged when it starts with `${`
but does not end with `}`, because it does not match the full `${...}` pattern.

#### Scenario: partial placeholder without closing brace passes through

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a string value `${INCOMPLETE`
- **When** `_resolve_env_vars("${INCOMPLETE")` is called
- **Then** the return value equals `"${INCOMPLETE"` unchanged

### Requirement: validate_config boundary temperature values produce no warnings

`validate_config()` SHALL NOT produce temperature warnings when
`llm.temperature` is exactly `0.0` or exactly `2.0`, because these are the
inclusive boundaries of the valid range `[0.0, 2.0]`.

#### Scenario: temperature exactly 0.0 produces no temperature warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `llm.temperature = 0.0` and otherwise valid fields
- **When** `validate_config(config)` is called
- **Then** `result.warnings` contains no element with the substring `"temperature"`
  AND `result.valid` is `True`

#### Scenario: temperature exactly 2.0 produces no temperature warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `llm.temperature = 2.0` and otherwise valid fields
- **When** `validate_config(config)` is called
- **Then** `result.warnings` contains no element with the substring `"temperature"`
  AND `result.valid` is `True`

### Requirement: validate_config fix_attempts upper bound warning

`validate_config()` SHALL produce a warning when `pipeline.fix_attempts` exceeds
20, because it is outside the recommended range `[1, 20]`.

#### Scenario: fix_attempts above 20 produces warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `pipeline.fix_attempts = 25` and otherwise valid fields
- **When** `validate_config(config)` is called
- **Then** `result.warnings` contains an element with the substring `"fix_attempts"`
  AND `result.valid` is `True`

### Requirement: load_config parses github section

`load_config()` SHALL populate the `github` attribute of the returned
`ZsigaConfig` from the `github` section of the YAML file.

#### Scenario: github section is parsed into GithubConfig

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config file containing a `github` section with
  `token`, `owner`, and `issue_integration` fields
- **When** `load_config(path)` is called with that file path
- **Then** the returned config's `github.token` equals the YAML value
  AND `github.owner` equals the YAML value
  AND `github.issue_integration` is `True`

### Requirement: load_config parses logging section

`load_config()` SHALL populate the `logging_config` attribute of the returned
`ZsigaConfig` from the `logging` section of the YAML file.

#### Scenario: logging section is parsed into LoggingConfig

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config file containing a `logging` section with
  `level` set to `"DEBUG"` and `format` set to `"json"`
- **When** `load_config(path)` is called with that file path
- **Then** `config.logging_config.level` equals `"DEBUG"`
  AND `config.logging_config.fmt` equals `"json"`

### Requirement: load_config parses ssh target from YAML

`load_config()` SHALL construct an `SSHConfig` and attach it to the
corresponding `TargetConfig` when the target's YAML contains an `ssh` sub-dict.

#### Scenario: ssh target with host user and port parsed correctly

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config file with a target containing
  `transport: ssh` and an `ssh` sub-dict with `host`, `user`, and `port`
- **When** `load_config(path)` is called with that file path
- **Then** the target's `ssh.host` equals the YAML value
  AND `ssh.user` equals the YAML value
  AND `ssh.port` equals the YAML value

### Requirement: load_config parses compaction sub-config

`load_config()` SHALL construct a `CompactionConfig` from the
`pipeline.compaction` sub-dict with custom values overriding defaults.

#### Scenario: custom compaction settings override defaults

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config file with `pipeline.compaction.enabled` set to
  `false` and `pipeline.compaction.threshold_chars` set to `50000`
- **When** `load_config(path)` is called with that file path
- **Then** `config.pipeline.compaction.enabled` is `False`
  AND `config.pipeline.compaction.threshold_chars` is `50000`
