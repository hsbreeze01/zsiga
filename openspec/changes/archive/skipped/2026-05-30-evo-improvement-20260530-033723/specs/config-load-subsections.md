# config-load-subsections

Incremental test coverage for `load_config()` parsing of subsections
that are **not** covered by existing tests (`test_config_validation.py`,
`test_spec_evo_*_config_load_robustness.py`).

Targeted subsections: CompactionConfig, IntakeConfig (api_poll mode),
SafetyConfig, LoggingConfig, GithubConfig, PipelineConfig gates
(proposal_gate, design_gate, evolution, explore_pool), and budget_profiles.

## ADDED Requirements

### Requirement: CompactionConfig parsing

When the YAML `pipeline.compaction` section is present, `load_config()`
SHALL parse its fields into a `CompactionConfig` object with matching
attribute values.

#### Scenario: Custom compaction values are parsed correctly

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid `zsiga.yaml` with `pipeline.compaction` set to
  `enabled: false`, `threshold_chars: 50000`, `keep_recent: 5`,
  `use_llm_summary: false`, `total_budget: 400000`, `per_turn_limit: 4096`,
  `compaction_ratio: 0.6`
- **When** `load_config()` is called with that file path
- **Then** `config.pipeline.compaction.enabled` SHALL be `False`,
  `config.pipeline.compaction.threshold_chars` SHALL be `50000`,
  `config.pipeline.compaction.keep_recent` SHALL be `5`,
  `config.pipeline.compaction.use_llm_summary` SHALL be `False`,
  `config.pipeline.compaction.total_budget` SHALL be `400000`,
  `config.pipeline.compaction.per_turn_limit` SHALL be `4096`,
  `config.pipeline.compaction.compaction_ratio` SHALL be `0.6`

### Requirement: IntakeConfig api_poll mode

When the YAML `intake` section specifies `mode: api_poll` with nested
`api_poll` parameters, `load_config()` SHALL parse them into an
`IntakeConfig` with matching attributes.

#### Scenario: api_poll mode with custom URL and interval

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid `zsiga.yaml` with `intake.mode: api_poll`,
  `intake.api_poll.url: https://api.example.com/issues`,
  `intake.api_poll.poll_interval_seconds: 120`,
  `intake.api_poll.headers: {Authorization: "Bearer token123"}`
- **When** `load_config()` is called with that file path
- **Then** `config.intake.mode` SHALL be `"api_poll"`,
  `config.intake.api_url` SHALL be `"https://api.example.com/issues"`,
  `config.intake.poll_interval_seconds` SHALL be `120`,
  `config.intake.api_headers` SHALL be `{"Authorization": "Bearer token123"}`

### Requirement: LoggingConfig parsing

When the YAML `logging` section is present, `load_config()` SHALL parse
its fields into a `LoggingConfig` object.  The `level` field SHALL be
normalized to uppercase.

#### Scenario: Custom logging level is uppercased

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid `zsiga.yaml` with `logging.level: debug`,
  `logging.format: json`, `logging.file: /tmp/zsiga.log`
- **When** `load_config()` is called with that file path
- **Then** `config.logging_config.level` SHALL be `"DEBUG"`,
  `config.logging_config.fmt` SHALL be `"json"`,
  `config.logging_config.file` SHALL be `"/tmp/zsiga.log"`

### Requirement: GithubConfig parsing

When the YAML `github` section is present, `load_config()` SHALL parse
its fields into a `GithubConfig` object.

#### Scenario: Full github config is parsed

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid `zsiga.yaml` with `github.token: ghp_xxx`,
  `github.owner: myorg`, `github.issue_integration: true`
- **When** `load_config()` is called with that file path
- **Then** `config.github.token` SHALL be `"ghp_xxx"`,
  `config.github.owner` SHALL be `"myorg"`,
  `config.github.issue_integration` SHALL be `True`

### Requirement: PipelineConfig proposal_gate parsing

When the YAML `pipeline.proposal_gate` section is present, `load_config()`
SHALL parse its fields into the corresponding `PipelineConfig` attributes.

#### Scenario: proposal_gate enabled with custom steward settings

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid `zsiga.yaml` with `pipeline.proposal_gate.enabled: true`,
  `pipeline.proposal_gate.max_retries: 3`,
  `pipeline.proposal_gate.steward_max_turns: 5`,
  `pipeline.proposal_gate.steward_timeout: 120`,
  `pipeline.proposal_gate.score_accept: 8`,
  `pipeline.proposal_gate.score_pushback: 4`,
  `pipeline.proposal_gate.learning_weight_days: 30`
- **When** `load_config()` is called with that file path
- **Then** `config.pipeline.proposal_gate_enabled` SHALL be `True`,
  `config.pipeline.proposal_gate_max_retries` SHALL be `3`,
  `config.pipeline.proposal_gate_steward_max_turns` SHALL be `5`,
  `config.pipeline.proposal_gate_steward_timeout` SHALL be `120`,
  `config.pipeline.proposal_gate_score_accept` SHALL be `8`,
  `config.pipeline.proposal_gate_score_pushback` SHALL be `4`,
  `config.pipeline.proposal_gate_learning_weight_days` SHALL be `30`

### Requirement: PipelineConfig design_gate parsing

When the YAML `pipeline.design_gate` section is present, `load_config()`
SHALL parse its fields into the corresponding `PipelineConfig` attributes.

#### Scenario: design_gate enabled with custom settings

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid `zsiga.yaml` with `pipeline.design_gate.enabled: true`,
  `pipeline.design_gate.max_retries: 4`,
  `pipeline.design_gate.max_turns: 6`,
  `pipeline.design_gate.timeout: 200`
- **When** `load_config()` is called with that file path
- **Then** `config.pipeline.design_gate_enabled` SHALL be `True`,
  `config.pipeline.design_gate_max_retries` SHALL be `4`,
  `config.pipeline.design_gate_max_turns` SHALL be `6`,
  `config.pipeline.design_gate_timeout` SHALL be `200`

### Requirement: PipelineConfig evolution parsing

When the YAML `pipeline.evolution` section is present, `load_config()`
SHALL parse its fields into the corresponding `PipelineConfig` attributes.

#### Scenario: evolution disabled with custom window

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid `zsiga.yaml` with `pipeline.evolution.enabled: false`,
  `pipeline.evolution.window_start_hour: 23`,
  `pipeline.evolution.window_end_hour: 7`,
  `pipeline.evolution.max_proposals_per_window: 5`,
  `pipeline.evolution.min_cycle_gap_minutes: 30`
- **When** `load_config()` is called with that file path
- **Then** `config.pipeline.evolution_enabled` SHALL be `False`,
  `config.pipeline.evolution_window_start_hour` SHALL be `23`,
  `config.pipeline.evolution_window_end_hour` SHALL be `7`,
  `config.pipeline.evolution_max_proposals` SHALL be `5`,
  `config.pipeline.evolution_min_gap_minutes` SHALL be `30`

### Requirement: PipelineConfig explore_pool parsing

When the YAML `pipeline.explore_pool` section is present, `load_config()`
SHALL parse its nested fields into the corresponding `PipelineConfig`
attributes.

#### Scenario: explore_pool with custom concurrency and turns

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid `zsiga.yaml` with `pipeline.explore_pool.max_concurrency: 5`,
  `pipeline.explore_pool.max_turns_per_task: 8`,
  `pipeline.explore_pool.timeout_per_task: 200`
- **When** `load_config()` is called with that file path
- **Then** `config.pipeline.explore_pool_max_concurrency` SHALL be `5`,
  `config.pipeline.explore_pool_max_turns` SHALL be `8`,
  `config.pipeline.explore_pool_timeout` SHALL be `200`

### Requirement: PipelineConfig budget_profiles override

When the YAML `pipeline.budget_profiles` section is present, `load_config()`
SHALL merge the provided profiles into `DEFAULT_BUDGET_PROFILES`, overriding
matching keys and adding new ones.

#### Scenario: custom budget_profiles override defaults

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid `zsiga.yaml` with `pipeline.budget_profiles: {fix: 500000, custom: 100000}`
- **When** `load_config()` is called with that file path
- **Then** `config.pipeline.budget_profiles["fix"]` SHALL be `500000`,
  `config.pipeline.budget_profiles["custom"]` SHALL be `100000`,
  and the default `"implementation"` key SHALL still be present with value `600000`

### Requirement: SafetyConfig parsing

When the YAML `safety` section is present, `load_config()` SHALL parse
its fields into a `SafetyConfig` object.

#### Scenario: custom safety config with protected paths

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a valid `zsiga.yaml` with `safety.require_approval: false`,
  `safety.protected_paths: ["/etc/passwd", "/etc/shadow"]`,
  `safety.max_files_per_task: 5`, `safety.dry_run: true`
- **When** `load_config()` is called with that file path
- **Then** `config.safety.require_approval` SHALL be `False`,
  `config.safety.protected_paths` SHALL be `["/etc/passwd", "/etc/shadow"]`,
  `config.safety.max_files_per_task` SHALL be `5`,
  `config.safety.dry_run` SHALL be `True`
