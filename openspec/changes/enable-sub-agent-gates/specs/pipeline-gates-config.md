# Pipeline Gates Configuration

## ADDED Requirements

### Requirement: Proposal Gate Configuration Block

zsiga.yaml 的 pipeline 节 SHALL 包含 `proposal_gate` 配置块，且 `enabled` 值为 `true`。

proposal_gate MUST 包含以下全部 7 个字段：
- `enabled`: true
- `max_retries`: 1
- `steward_max_turns`: 3
- `steward_timeout`: 90
- `score_accept`: 6
- `score_pushback`: 3
- `learning_weight_days`: 90

#### Scenario: proposal_gate block exists with all required fields

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded as YAML
- **When** the `pipeline` key is accessed
- **Then** `pipeline.proposal_gate` is a dict containing exactly the keys `enabled`, `max_retries`, `steward_max_turns`, `steward_timeout`, `score_accept`, `score_pushback`, `learning_weight_days` with the specified values

#### Scenario: proposal_gate is enabled

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded as YAML
- **When** the `pipeline.proposal_gate.enabled` key is accessed
- **Then** the value is `true` (boolean)

---

### Requirement: Design Gate Configuration Block

zsiga.yaml 的 pipeline 节 SHALL 包含 `design_gate` 配置块，且 `enabled` 值为 `true`。

design_gate MUST 包含以下全部 4 个字段：
- `enabled`: true
- `max_retries`: 2
- `max_turns`: 4
- `timeout`: 120

#### Scenario: design_gate block exists with all required fields

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded as YAML
- **When** the `pipeline` key is accessed
- **Then** `pipeline.design_gate` is a dict containing exactly the keys `enabled`, `max_retries`, `max_turns`, `timeout` with the specified values

#### Scenario: design_gate is enabled

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded as YAML
- **When** the `pipeline.design_gate.enabled` key is accessed
- **Then** the value is `true` (boolean)

---

### Requirement: Existing Pipeline Config Preservation

添加 proposal_gate 和 design_gate 后，pipeline 节中所有现有配置项 MUST 保持不变。

#### Scenario: existing pipeline fields unchanged after gate addition

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded as YAML
- **When** the `pipeline` key is accessed
- **Then** the following existing keys still exist with their original values: `max_changes_per_cycle` (10), `enrich_max_turns` (50), `enrich_timeout` (2400), `impl_max_turns` (60), `impl_timeout_minutes` (40), `fix_attempts` (10), `optimize_enabled` (true), `eval_fix_attempts` (3), `cycle_interval_hours` (8), `compaction.enabled` (false)

---

### Requirement: YAML Syntax Validity

修改后的 zsiga.yaml MUST 是合法的 YAML 文件，可被 Python `yaml.safe_load` 正常解析，不引发异常。

#### Scenario: zsiga.yaml is valid YAML

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml file exists at project root
- **When** the file is parsed with `yaml.safe_load`
- **Then** no exception is raised and the result is a dict with top-level key `pipeline`

---

### Requirement: Rollback Capability

将 `proposal_gate.enabled` 或 `design_gate.enabled` 改回 `false` SHALL 立即禁用对应的 gate，无需修改任何 Python 代码。

#### Scenario: setting proposal_gate.enabled to false disables proposal gate

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded as YAML
- **When** `pipeline.proposal_gate.enabled` is set to `false` and the config is re-loaded
- **Then** the value of `pipeline.proposal_gate.enabled` is `false`

#### Scenario: setting design_gate.enabled to false disables design gate

- **testable**: true
- **target**: zsiga.yaml
- **Given** zsiga.yaml is loaded as YAML
- **When** `pipeline.design_gate.enabled` is set to `false` and the config is re-loaded
- **Then** the value of `pipeline.design_gate.enabled` is `false`
