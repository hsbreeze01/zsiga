# runtime-state-persistence

## ADDED Requirements

### Requirement: Runtime state file read/write round-trip

`save_runtime_state` SHALL persist a dict to YAML on disk such that a
subsequent call to `load_runtime_state` returns an equivalent dict.

#### Scenario: save then load round-trip

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** a clean temporary directory used as the config root (no pre-existing runtime state file)
- **When** `save_runtime_state({"active_target": "proj-a", "last_cycle": 12345})` is called, followed by `load_runtime_state()`
- **Then** the returned dict equals `{"active_target": "proj-a", "last_cycle": 12345}`

### Requirement: load_runtime_state graceful fallback on missing file

`load_runtime_state` SHALL return an empty dict when the runtime state file
does not exist, without raising any exception.

#### Scenario: load when state file absent

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** a temporary directory with no `data/runtime_state.yaml`
- **When** `load_runtime_state()` is called (with `_runtime_state_path` pointing to that directory)
- **Then** the returned dict is `{}`

### Requirement: load_runtime_state graceful fallback on corrupt YAML

`load_runtime_state` SHALL return an empty dict when the runtime state file
exists but contains unparseable content, without raising any exception.

#### Scenario: load when state file contains invalid YAML

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** a temporary directory where `data/runtime_state.yaml` exists and contains the string `": [unbalanced`
- **When** `load_runtime_state()` is called (with `_runtime_state_path` pointing to that file)
- **Then** the returned dict is `{}`

### Requirement: load_runtime_state returns empty dict for empty file

`load_runtime_state` SHALL return an empty dict when the runtime state file
exists but is empty (or parses to `None`).

#### Scenario: load when state file is empty

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** a temporary directory where `data/runtime_state.yaml` exists and is empty (0 bytes)
- **When** `load_runtime_state()` is called
- **Then** the returned dict is `{}`

### Requirement: save_runtime_state creates parent directories

`save_runtime_state` SHALL create any missing parent directories for the
state file path before writing.

#### Scenario: save creates missing parent dirs

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** a temporary directory where the `data/` subdirectory does NOT exist
- **When** `save_runtime_state({"k": "v"})` is called (with `_runtime_state_path` pointing to `<tmp>/data/runtime_state.yaml`)
- **Then** the directory `<tmp>/data/` exists and the file contains valid YAML with `{"k": "v"}`
