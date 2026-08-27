# runtime-state-functions

## ADDED Requirements

### Requirement: Runtime State Path Resolution

The system SHALL provide `_runtime_state_path()` that returns the absolute path
where runtime state is persisted.  When the `ZSIGA_HOME` environment variable is
set, the path SHALL be `ZSIGA_HOME/data/runtime_state.yaml`.  When unset, the
path SHALL be derived from `_find_config().parent / "data/runtime_state.yaml"`.

#### Scenario: Returns ZSIGA_HOME-derived path when env var set

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** the `ZSIGA_HOME` environment variable is set to `/tmp/zsiga_test_home`
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `Path("/tmp/zsiga_test_home/data/runtime_state.yaml")`

#### Scenario: Falls back to config parent when ZSIGA_HOME unset

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** the `ZSIGA_HOME` environment variable is unset
  and a `zsiga.yaml` exists in the current directory
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `<config_dir>/data/runtime_state.yaml` where
  `<config_dir>` is the parent of the found `zsiga.yaml`

---

### Requirement: Load Runtime State Graceful Degradation

The system SHALL provide `load_runtime_state()` to read persisted runtime state.
When the state file does not exist, it SHALL return an empty dict.  When the
file contains invalid YAML, it SHALL also return an empty dict without raising.

#### Scenario: Returns empty dict when state file missing

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the `ZSIGA_HOME` directory exists but `data/runtime_state.yaml` does
  not exist
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

#### Scenario: Returns empty dict on corrupt YAML

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file exists but contains invalid YAML content
  `": [broken`
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}` without raising an exception

---

### Requirement: Save Runtime State Persists to Disk

The system SHALL provide `save_runtime_state(state)` to persist the given
dictionary to disk as YAML.  It SHALL create parent directories if they do not
exist.

#### Scenario: Creates parent directory and writes YAML

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** the `ZSIGA_HOME` directory does not exist
- **When** `save_runtime_state({"active_target": "test_target"})` is called
- **Then** the directory `ZSIGA_HOME/data/` SHALL exist and the file
  `data/runtime_state.yaml` SHALL contain valid YAML with key
  `active_target` having value `test_target`
