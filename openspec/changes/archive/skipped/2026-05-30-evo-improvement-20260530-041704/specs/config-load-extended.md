# Spec: config-load-extended

Extended coverage for `load_config(path)` — YAML parsing paths not
covered by `test_config_validation.py`, including SSH targets, github
section, logging section, env var resolution, and runtime state
integration.

## ADDED Requirements

### Requirement: load_config parses SSH target from YAML

When a target entry contains an `ssh` sub-dict, `load_config` SHALL
construct an `SSHConfig` and attach it to the `TargetConfig`.

#### Scenario: target with ssh config is parsed correctly

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with a target containing `ssh: {host: myserver, user: deploy, port: 2222}`
- **When** `load_config(path)` is called
- **Then** the target's `ssh` attribute SHALL be an `SSHConfig` with `host="myserver"`, `user="deploy"`, `port=2222`

---

### Requirement: load_config resolves environment variables in YAML

`load_config` SHALL apply `_resolve_env_vars` to the raw parsed YAML
before constructing config objects.

#### Scenario: api_key resolved from environment variable

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `api_key: "${TEST_API_KEY_VAR}"` and env var `TEST_API_KEY_VAR` set to `"resolved-key"`
- **When** `load_config(path)` is called
- **Then** `config.llm.api_key` SHALL be `"resolved-key"`

---

### Requirement: load_config parses github section

When the YAML contains a `github` section, `load_config` SHALL construct
a `GithubConfig`.

#### Scenario: github section parsed with all fields

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `github: {token: ghp_abc, owner: myorg, issue_integration: true}`
- **When** `load_config(path)` is called
- **Then** `config.github` SHALL be a `GithubConfig` with `token="ghp_abc"`, `owner="myorg"`, `issue_integration=True`

#### Scenario: missing github section yields GithubConfig with defaults

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config without a `github` section
- **When** `load_config(path)` is called
- **Then** `config.github` SHALL be a `GithubConfig` with `token=""`, `owner=""`, `issue_integration=False`

---

### Requirement: load_config parses logging section

When the YAML contains a `logging` section, `load_config` SHALL construct
a `LoggingConfig`.

#### Scenario: logging section parsed

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `logging: {level: debug, format: json, file: /tmp/zsiga.log}`
- **When** `load_config(path)` is called
- **Then** `config.logging_config.level` SHALL be `"DEBUG"`, `config.logging_config.fmt` SHALL be `"json"`, `config.logging_config.file` SHALL be `"/tmp/zsiga.log"`

---

### Requirement: load_config reads active_target from runtime state

`load_config` SHALL call `load_runtime_state()` to obtain `active_target`.

#### Scenario: active_target taken from runtime state

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config and a runtime state file containing `active_target: my-target`
- **When** `load_config(path)` is called
- **Then** `config.active_target` SHALL be `"my-target"`

#### Scenario: active_target defaults to zsiga when runtime state is empty

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a valid YAML config and no runtime state file
- **When** `load_config(path)` is called
- **Then** `config.active_target` SHALL be `"zsiga"`

---

### Requirement: load_config raises ConfigValidationError on invalid config

When the parsed config fails validation, `load_config` SHALL raise
`ConfigValidationError`.

#### Scenario: raises on empty targets

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `targets: {}`
- **When** `load_config(path)` is called
- **Then** it SHALL raise `ConfigValidationError`

---

### Requirement: load_config parses pipeline sub-sections

`load_config` SHALL correctly parse nested pipeline sub-sections:
`compaction`, `proposal_gate`, `design_gate`, `evolution`, `explore_pool`.

#### Scenario: pipeline compaction overrides

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `pipeline.compaction: {enabled: false, threshold_chars: 5000}`
- **When** `load_config(path)` is called
- **Then** `config.pipeline.compaction.enabled` SHALL be `False` and `config.pipeline.compaction.threshold_chars` SHALL be `5000`

#### Scenario: proposal_gate sub-section parsed

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `pipeline.proposal_gate: {enabled: true, score_accept: 8}`
- **When** `load_config(path)` is called
- **Then** `config.pipeline.proposal_gate_enabled` SHALL be `True` and `config.pipeline.proposal_gate_score_accept` SHALL be `8`

#### Scenario: evolution sub-section parsed

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_config
- **Given** a YAML config with `pipeline.evolution: {enabled: false, max_proposals_per_window: 5}`
- **When** `load_config(path)` is called
- **Then** `config.pipeline.evolution_enabled` SHALL be `False` and `config.pipeline.evolution_max_proposals` SHALL be `5`

