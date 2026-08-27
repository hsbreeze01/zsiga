# Spec: config-load-parsing-gaps

## ADDED Requirements

### Requirement: load_config SHALL parse SSH target from YAML

When the YAML contains a target with an `ssh` sub-dict, `load_config` SHALL
construct a `TargetConfig` with a populated `SSHConfig` and set
`transport="ssh"` automatically.

#### Scenario: SSH target parsed from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with a target that has `ssh: {host: "deploy.example.com", port: 2222}`
- **When** `load_config(path)` is called
- **Then** the resulting target SHALL have `.transport == "ssh"`, `.ssh.host == "deploy.example.com"`, `.ssh.port == 2222`

### Requirement: load_config SHALL parse logging section from YAML

When the YAML contains a `logging` section, `load_config` SHALL populate the
`logging_config` attribute. When absent, defaults SHALL apply.

#### Scenario: Logging config parsed from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `logging: {level: debug, format: json}`
- **When** `load_config(path)` is called
- **Then** `config.logging_config.level` SHALL be `"DEBUG"`, `.fmt` SHALL be `"json"`

#### Scenario: Logging config defaults when absent

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file without a `logging` section
- **When** `load_config(path)` is called
- **Then** `config.logging_config.level` SHALL be `"INFO"`, `.fmt` SHALL be `"text"`

### Requirement: load_config SHALL parse github section from YAML

When the YAML contains a `github` section, `load_config` SHALL populate the
`github` attribute. When absent, defaults SHALL apply.

#### Scenario: Github config parsed from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `github: {token: "ghp_abc", owner: "myorg", issue_integration: true}`
- **When** `load_config(path)` is called
- **Then** `config.github.token` SHALL be `"ghp_abc"`, `.owner` SHALL be `"myorg"`, `.issue_integration is True`

#### Scenario: Github config defaults when absent

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file without a `github` section
- **When** `load_config(path)` is called
- **Then** `config.github` SHALL be non-None with `.token == ""`, `.issue_integration is False`

### Requirement: load_config SHALL parse pipeline sub-sections

`load_config` SHALL correctly parse `pipeline.compaction`, `pipeline.proposal_gate`,
`pipeline.design_gate`, `pipeline.evolution`, and `pipeline.budget_profiles` from YAML.

#### Scenario: Compaction section override

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `pipeline: {compaction: {enabled: false, threshold_chars: 5000}}`
- **When** `load_config(path)` is called
- **Then** `config.pipeline.compaction.enabled` SHALL be `False`, `.threshold_chars` SHALL be `5000`

#### Scenario: Proposal gate section

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `pipeline: {proposal_gate: {enabled: true, score_accept: 12}}`
- **When** `load_config(path)` is called
- **Then** `config.pipeline.proposal_gate_enabled` SHALL be `True`, `.proposal_gate_score_accept` SHALL be `12`

#### Scenario: Design gate section

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `pipeline: {design_gate: {enabled: true, max_retries: 3}}`
- **When** `load_config(path)` is called
- **Then** `config.pipeline.design_gate_enabled` SHALL be `True`, `.design_gate_max_retries` SHALL be `3`

#### Scenario: Evolution section

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `pipeline: {evolution: {enabled: false, max_proposals_per_window: 5}}`
- **When** `load_config(path)` is called
- **Then** `config.pipeline.evolution_enabled` SHALL be `False`, `.evolution_max_proposals` SHALL be `5`

#### Scenario: Custom budget profile merged with defaults

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `pipeline: {budget_profiles: {custom: 999999}}`
- **When** `load_config(path)` is called
- **Then** `config.pipeline.budget_profiles` SHALL contain `"custom": 999999` **and** all default keys

### Requirement: load_config SHALL parse safety section overrides

When the YAML contains a `safety` section with non-default values,
`load_config` SHALL reflect those in the resulting `SafetyConfig`.

#### Scenario: Safety overrides parsed from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `safety: {require_approval: false, max_files_per_task: 10}`
- **When** `load_config(path)` is called
- **Then** `config.safety.require_approval` SHALL be `False`, `.max_files_per_task` SHALL be `10`

### Requirement: load_config SHALL resolve environment variable placeholders

`load_config` SHALL resolve `${VAR}` placeholders in YAML values via
`_resolve_env_vars` before constructing config objects.

#### Scenario: Env var resolved in api_key

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `api_key: "${ZSIGA_TEST_API_KEY}"` and env var `ZSIGA_TEST_API_KEY="resolved-key"`
- **When** `load_config(path)` is called
- **Then** `config.llm.api_key` SHALL be `"resolved-key"`
