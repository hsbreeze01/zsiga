# Spec: config-loading

## ADDED Requirements

### Requirement: load_config parses SSH target configuration

`load_config` SHALL correctly parse SSH target configurations from YAML, creating `SSHConfig` instances with host, user, port, and key_path.

#### Scenario: SSH target with full configuration

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config with an SSH target containing host, user, port, key_path
- **When** `load_config(path=...)` is called
- **Then** the returned config's target has `transport="ssh"` and an `SSHConfig` with all fields populated

### Requirement: load_config parses pipeline overrides

`load_config` SHALL override default pipeline values from the `pipeline` YAML section.

#### Scenario: Pipeline override for max_changes_per_cycle and enrich_max_turns

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config with `pipeline.max_changes_per_cycle: 5` and `pipeline.enrich_max_turns: 30`
- **When** `load_config(path=...)` is called
- **Then** `config.pipeline.max_changes_per_cycle` is `5` and `config.pipeline.enrich_max_turns` is `30`

### Requirement: load_config parses compaction overrides

`load_config` SHALL override compaction defaults from `pipeline.compaction` section.

#### Scenario: Compaction override for enabled and threshold_chars

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config with `pipeline.compaction.enabled: false` and `pipeline.compaction.threshold_chars: 50000`
- **When** `load_config(path=...)` is called
- **Then** `config.pipeline.compaction.enabled` is `False` and `config.pipeline.compaction.threshold_chars` is `50000`

### Requirement: load_config resolves environment variables in values

`load_config` SHALL resolve `${VAR_NAME}` patterns in YAML values using `_resolve_env_vars`.

#### Scenario: API key from environment variable

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** environment variable `MY_API_KEY` is set to `"sk-from-env"` and YAML has `api_key: "${MY_API_KEY}"`
- **When** `load_config(path=...)` is called
- **Then** `config.llm.api_key` is `"sk-from-env"`

### Requirement: load_config parses github section

`load_config` SHALL parse the `github` YAML section into a `GithubConfig` instance.

#### Scenario: Github section with token, owner, issue_integration

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config with `github.token`, `github.owner`, `github.issue_integration: true`
- **When** `load_config(path=...)` is called
- **Then** `config.github` is a `GithubConfig` with the parsed values

### Requirement: load_config parses logging section with level normalization

`load_config` SHALL parse the `logging` YAML section into a `LoggingConfig` with uppercased level.

#### Scenario: Logging section with lowercase level

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config with `logging.level: debug`, `logging.format: json`, `logging.file: /tmp/zsiga.log`
- **When** `load_config(path=...)` is called
- **Then** `config.logging_config.level` is `"DEBUG"`, `fmt` is `"json"`, `file` is `"/tmp/zsiga.log"`

### Requirement: load_config parses safety overrides

`load_config` SHALL parse the `safety` YAML section into a `SafetyConfig` instance.

#### Scenario: Safety overrides for require_approval and max_files_per_task

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config with `safety.require_approval: false` and `safety.max_files_per_task: 10`
- **When** `load_config(path=...)` is called
- **Then** `config.safety.require_approval` is `False` and `config.safety.max_files_per_task` is `10`

### Requirement: load_config parses intake api_poll section

`load_config` SHALL parse `intake.api_poll` subsection into `IntakeConfig.api_url` and `IntakeConfig.poll_interval_seconds`.

#### Scenario: Intake API poll configuration

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config with `intake.mode: api_poll`, `intake.api_poll.url`, `intake.api_poll.poll_interval_seconds: 60`
- **When** `load_config(path=...)` is called
- **Then** `config.intake.mode` is `"api_poll"` and `config.intake.api_url` matches the YAML value

### Requirement: _runtime_state_path uses ZSIGA_HOME environment variable

`_runtime_state_path` SHALL return `Path($ZSIGA_HOME)/data/runtime_state.yaml` when `ZSIGA_HOME` is set.

#### Scenario: Path with ZSIGA_HOME set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** `ZSIGA_HOME` environment variable is set to `"/opt/zsiga"`
- **When** `_runtime_state_path()` is called
- **Then** it returns `Path("/opt/zsiga/data/runtime_state.yaml")`

#### Scenario: Path falls back to config parent dir when ZSIGA_HOME unset

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** `ZSIGA_HOME` is not set and `_find_config()` returns `/project/zsiga.yaml`
- **When** `_runtime_state_path()` is called
- **Then** it returns `Path("/project/data/runtime_state.yaml")`

### Requirement: load_runtime_state handles missing and corrupt files

`load_runtime_state` SHALL return an empty dict when the state file does not exist or is corrupt YAML.

#### Scenario: Non-existent file returns empty dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** `ZSIGA_HOME` points to a directory without a `data/runtime_state.yaml` file
- **When** `load_runtime_state()` is called
- **Then** it returns `{}`

#### Scenario: Valid YAML file returns parsed dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** `ZSIGA_HOME` points to a directory with `data/runtime_state.yaml` containing `active_target: my-project`
- **When** `load_runtime_state()` is called
- **Then** it returns `{"active_target": "my-project"}`

#### Scenario: Corrupt YAML file returns empty dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** `ZSIGA_HOME` points to a directory with `data/runtime_state.yaml` containing invalid YAML
- **When** `load_runtime_state()` is called
- **Then** it returns `{}`

### Requirement: save_runtime_state creates directories and writes YAML

`save_runtime_state` SHALL create parent directories if they don't exist and write state as YAML.

#### Scenario: Save creates parent directories

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** `ZSIGA_HOME` points to a non-existent directory
- **When** `save_runtime_state({"active_target": "proj-a"})` is called
- **Then** the state file exists at `$ZSIGA_HOME/data/runtime_state.yaml` and contains `"proj-a"`

### Requirement: save and load round-trip preserves state

The combination of `save_runtime_state` and `load_runtime_state` SHALL preserve dict contents exactly.

#### Scenario: Round-trip preserves all keys and values

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** `ZSIGA_HOME` points to a writable directory
- **When** `save_runtime_state({"active_target": "round-trip", "count": 42})` is called followed by `load_runtime_state()`
- **Then** the loaded dict equals the original dict

