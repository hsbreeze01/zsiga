# Spec: Config Diff Viewer

## ADDED Requirements

### Requirement: compare two zsiga.yaml configs and return structured diff

The system SHALL provide a function `compare_configs(old_config: dict, new_config: dict) -> dict` that accepts two parsed YAML config dictionaries and returns a structured dictionary describing key differences.

#### Scenario: identical configs produce empty diff

- **Given** two config dictionaries with identical model, budget, and transport settings
- **When** `compare_configs` is called with both dictionaries
- **Then** the result SHALL be `{"changed": [], "details": {}}`

#### Scenario: model setting changed

- **Given** `old_config` with `model.name = "gpt-4"` and `new_config` with `model.name = "gpt-4o"`
- **When** `compare_configs` is called
- **Then** the result SHALL contain `"model.name"` in the `changed` list
- **And** `details["model.name"]` SHALL be `{"old": "gpt-4", "new": "gpt-4o"}`

#### Scenario: budget setting changed

- **Given** `old_config` with `budget.max_tokens = 8000` and `new_config` with `budget.max_tokens = 16000`
- **When** `compare_configs` is called
- **Then** the result SHALL contain `"budget.max_tokens"` in the `changed` list
- **And** `details["budget.max_tokens"]` SHALL be `{"old": 8000, "new": 16000}`

#### Scenario: transport setting changed

- **Given** `old_config` with `transport.type = "stdio"` and `new_config` with `transport.type = "http"`
- **When** `compare_configs` is called
- **Then** the result SHALL contain `"transport.type"` in the `changed` list
- **And** `details["transport.type"]` SHALL be `{"old": "stdio", "new": "http"}`

#### Scenario: key present in old but missing in new

- **Given** `old_config` with `model.temperature = 0.7` and `new_config` with no `model.temperature` key
- **When** `compare_configs` is called
- **Then** the result SHALL contain `"model.temperature"` in the `changed` list
- **And** `details["model.temperature"]` SHALL be `{"old": 0.7, "new": None}`

#### Scenario: key present in new but missing in old

- **Given** `old_config` with no `budget.max_cost` and `new_config` with `budget.max_cost = 5.0`
- **When** `compare_configs` is called
- **Then** the result SHALL contain `"budget.max_cost"` in the `changed` list
- **And** `details["budget.max_cost"]` SHALL be `{"old": None, "new": 5.0}`

### Requirement: diff only watches model, budget, and transport sections

The function SHALL only compare keys under the `model`, `budget`, and `transport` top-level sections. Keys under other sections (e.g. `logging`, `plugins`) SHALL be ignored.

#### Scenario: unrelated section changes are not reported

- **Given** `old_config` with `logging.level = "INFO"` and `new_config` with `logging.level = "DEBUG"`
- **When** `compare_configs` is called
- **Then** the `changed` list SHALL NOT contain `"logging.level"`

### Requirement: dot-notation flattened keys

The `changed` list and `details` dictionary SHALL use dot-notation flattened keys (e.g. `model.name`, `budget.max_tokens`) to identify nested config values.

#### Scenario: deeply nested key is flattened

- **Given** `old_config` with `transport.http.port = 8080` and `new_config` with `transport.http.port = 9090`
- **When** `compare_configs` is called
- **Then** the `changed` list SHALL contain `"transport.http.port"`

### Requirement: output structure

The returned dictionary SHALL have exactly two top-level keys:

- `changed`: a `list[str]` of dot-notation keys that differ, sorted alphabetically
- `details`: a `dict[str, dict]` mapping each changed key to `{"old": <value>, "new": <value>}`

#### Scenario: multiple changes are sorted alphabetically

- **Given** configs that differ in `budget.max_tokens` and `model.name`
- **When** `compare_configs` is called
- **Then** `changed` SHALL be `["budget.max_tokens", "model.name"]`
