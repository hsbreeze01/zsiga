# Spec: config-runtime-state

## ADDED Requirements

### Requirement: Runtime state path resolution

The system SHALL provide a `_runtime_state_path()` function that determines the filesystem path for the runtime state file based on environment configuration.

#### Scenario: runtime_state_path_with_zsiga_home

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `"/custom/home"`
- **When** `_runtime_state_path()` is called
- **Then** the result SHALL be `Path("/custom/home") / "data/runtime_state.yaml"`

#### Scenario: runtime_state_path_without_zsiga_home

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is NOT set AND a config file exists at a known path
- **When** `_runtime_state_path()` is called
- **Then** the result SHALL be the config file's parent directory joined with `data/runtime_state.yaml`

---

### Requirement: Load runtime state

The system SHALL provide a `load_runtime_state()` function that reads the runtime state YAML file. When the file does not exist or is unreadable, it SHALL return an empty dict.

#### Scenario: load_runtime_state_file_not_exists

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file does NOT exist
- **When** `load_runtime_state()` is called
- **Then** the result SHALL be `{}`

#### Scenario: load_runtime_state_file_exists

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file exists and contains `active_target: myproject`
- **When** `load_runtime_state()` is called
- **Then** the result SHALL be `{"active_target": "myproject"}`

#### Scenario: load_runtime_state_corrupt_yaml

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file exists but contains invalid YAML content
- **When** `load_runtime_state()` is called
- **Then** the result SHALL be `{}` (graceful fallback)

---

### Requirement: Save runtime state

The system SHALL provide a `save_runtime_state(state)` function that atomically writes the runtime state dict to a YAML file, creating parent directories as needed.

#### Scenario: save_runtime_state_creates_file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** a writable directory and a state dict `{"active_target": "proj1"}`
- **When** `save_runtime_state(state)` is called
- **Then** a YAML file SHALL be created at the runtime state path containing the key `active_target` with value `proj1`, AND the parent directory SHALL be created if it does not exist

#### Scenario: save_and_load_roundtrip

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** a writable directory
- **When** `save_runtime_state({"active_target": "roundtrip_test"})` is called followed by `load_runtime_state()`
- **Then** the loaded state SHALL contain `{"active_target": "roundtrip_test"}`

