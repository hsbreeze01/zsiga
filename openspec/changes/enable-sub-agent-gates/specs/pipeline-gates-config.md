# Pipeline Gates Configuration

Describes the configuration delta for enabling Proposal Gate and Design Gate
in `zsiga.yaml`. All scenarios are mechanically testable via YAML parsing
and config module loading.

> **Note**: The gate config blocks are consumed by `zsiga/config.py` which
> reads the nested YAML mapping and exposes flat attributes on the
> `PipelineConfig` dataclass. Runtime gate enforcement (orchestrator
> branching) is specified separately in `gate-runtime-behavior.md`.

## ADDED Requirements

### Requirement: Proposal Gate Configuration Block

The `pipeline` section of `zsiga.yaml` SHALL contain a `proposal_gate` mapping
with exactly 7 keys, all with deterministic scalar values.

| Key                  | Type    | Value |
|----------------------|---------|-------|
| `enabled`            | bool    | true  |
| `max_retries`        | int     | 1     |
| `steward_max_turns`  | int     | 3     |
| `steward_timeout`    | int     | 90    |
| `score_accept`       | int     | 6     |
| `score_pushback`     | int     | 3     |
| `learning_weight_days`| int    | 90    |

#### Scenario: proposal-gate-block-structure

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded via `yaml.safe_load()`
- **When** the `pipeline.proposal_gate` mapping is accessed
- **Then** it is a `dict` containing exactly the keys `enabled`, `max_retries`,
  `steward_max_turns`, `steward_timeout`, `score_accept`, `score_pushback`,
  `learning_weight_days` with the values specified in the table above

#### Scenario: proposal-gate-enabled-true

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded via `yaml.safe_load()`
- **When** `pipeline.proposal_gate.enabled` is accessed
- **Then** the value equals `True` (Python `bool`)

#### Scenario: proposal-gate-value-types

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded via `yaml.safe_load()`
- **When** each value in `pipeline.proposal_gate` is inspected
- **Then** `enabled` is `bool`; all other values are `int` (not `float`, not `str`)

---

### Requirement: Design Gate Configuration Block

The `pipeline` section of `zsiga.yaml` SHALL contain a `design_gate` mapping
with exactly 4 keys.

| Key           | Type    | Value |
|---------------|---------|-------|
| `enabled`     | bool    | true  |
| `max_retries` | int     | 2     |
| `max_turns`   | int     | 4     |
| `timeout`     | int     | 120   |

#### Scenario: design-gate-block-structure

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded via `yaml.safe_load()`
- **When** the `pipeline.design_gate` mapping is accessed
- **Then** it is a `dict` containing exactly the keys `enabled`, `max_retries`,
  `max_turns`, `timeout` with the values specified in the table above

#### Scenario: design-gate-enabled-true

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded via `yaml.safe_load()`
- **When** `pipeline.design_gate.enabled` is accessed
- **Then** the value equals `True` (Python `bool`)

#### Scenario: design-gate-value-types

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded via `yaml.safe_load()`
- **When** each value in `pipeline.design_gate` is inspected
- **Then** `enabled` is `bool`; all other values are `int` (not `float`, not `str`)

---

### Requirement: Config Parsing Integration

The `zsiga/config.py` module SHALL correctly parse the gate configuration
values from `zsiga.yaml` into the corresponding `PipelineConfig` attributes.

#### Scenario: config-parses-proposal-gate

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** `zsiga.yaml` contains `pipeline.proposal_gate` with `enabled: true`
  and the values specified in the Proposal Gate Configuration Block table
- **When** `load_config()` is called with the path to this `zsiga.yaml`
- **Then** the returned `ZsigaConfig.pipeline` SHALL have:
  `proposal_gate_enabled == True`,
  `proposal_gate_max_retries == 1`,
  `proposal_gate_steward_max_turns == 3`,
  `proposal_gate_steward_timeout == 90`,
  `proposal_gate_score_accept == 6`,
  `proposal_gate_score_pushback == 3`,
  `proposal_gate_learning_weight_days == 90`

#### Scenario: config-parses-design-gate

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** `zsiga.yaml` contains `pipeline.design_gate` with `enabled: true`
  and the values specified in the Design Gate Configuration Block table
- **When** `load_config()` is called with the path to this `zsiga.yaml`
- **Then** the returned `ZsigaConfig.pipeline` SHALL have:
  `design_gate_enabled == True`,
  `design_gate_max_retries == 2`,
  `design_gate_max_turns == 4`,
  `design_gate_timeout == 120`

---

### Requirement: Existing Pipeline Config Preservation

Adding `proposal_gate` and `design_gate` MUST NOT alter any pre-existing
pipeline configuration keys.

#### Scenario: existing-pipeline-scalars-unchanged

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded via `yaml.safe_load()`
- **When** the `pipeline` mapping is accessed
- **Then** the following keys retain their original values:
  `max_changes_per_cycle` → 10, `enrich_max_turns` → 50,
  `enrich_timeout` → 2400, `impl_max_turns` → 60,
  `impl_timeout_minutes` → 40, `fix_attempts` → 10,
  `optimize_enabled` → true, `eval_fix_attempts` → 3,
  `cycle_interval_hours` → 8

#### Scenario: compaction-subtree-unchanged

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded via `yaml.safe_load()`
- **When** `pipeline.compaction` is accessed
- **Then** it equals `{"enabled": False, "threshold_chars": 60000,
  "keep_recent": 3, "use_llm_summary": True}`

---

### Requirement: YAML Syntax Validity

The modified `zsiga.yaml` MUST be well-formed YAML with no duplicate keys,
parseable by Python `yaml.safe_load` without warnings or exceptions.

#### Scenario: yaml-safe-load-succeeds

- **testable**: true
- **target**: zsiga.yaml
- **Given** the file `zsiga.yaml` exists at project root
- **When** it is parsed with `yaml.safe_load()`
- **Then** no exception is raised and the result is a `dict` with a
  top-level `pipeline` key

#### Scenario: yaml-roundtrip-preserves-gates

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded via `yaml.safe_load()`
- **When** the loaded dict is dumped with `yaml.dump()` and re-loaded
  with `yaml.safe_load()`
- **Then** `pipeline.proposal_gate.enabled` is `True` and
  `pipeline.design_gate.enabled` is `True`

#### Scenario: no-duplicate-yaml-keys

- **testable**: true
- **target**: zsiga.yaml
- **Given** the raw text of `zsiga.yaml`
- **When** each mapping block is scanned for duplicate keys
- **Then** no mapping block contains the same key name more than once

---

### Requirement: Rollback Capability

Each gate's `enabled` flag SHALL be independently toggleable to `false`
without affecting other configuration.

#### Scenario: proposal-gate-can-be-disabled

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded via `yaml.safe_load()`
- **When** `pipeline.proposal_gate.enabled` is set to `False` in a deep copy
- **Then** `pipeline.proposal_gate.enabled` in the copy is `False` and all
  other gate fields remain unchanged

#### Scenario: design-gate-can-be-disabled

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded via `yaml.safe_load()`
- **When** `pipeline.design_gate.enabled` is set to `False` in a deep copy
- **Then** `pipeline.design_gate.enabled` in the copy is `False` and all
  other gate fields remain unchanged
