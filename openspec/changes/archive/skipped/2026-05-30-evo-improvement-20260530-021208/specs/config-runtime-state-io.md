# config-runtime-state-io

## ADDED Requirements

### Requirement: load_runtime_state reads persisted state dict

`load_runtime_state()` SHALL read the YAML file at `_runtime_state_path()`.
If the file exists and contains valid YAML, it SHALL return the parsed dict.
If the file does not exist or is unreadable, it SHALL return an empty dict `{}`.

#### Scenario: load existing state file

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** a valid YAML file at the runtime state path containing `active_target: myproject`
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{"active_target": "myproject"}`

#### Scenario: load when state file does not exist

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** no file at the runtime state path
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

#### Scenario: load when state file contains only whitespace or empty YAML

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** a file at the runtime state path containing only whitespace
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

### Requirement: save_runtime_state writes state dict to YAML

`save_runtime_state(state)` SHALL serialize the given dict as YAML and write
it to `_runtime_state_path()`, creating parent directories as needed.

#### Scenario: save and reload round-trip

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** a writable directory for the runtime state path
- **When** `save_runtime_state({"active_target": "proj_a", "count": 5})` is called, followed by `load_runtime_state()`
- **Then** the reloaded dict SHALL equal `{"active_target": "proj_a", "count": 5}`

#### Scenario: save creates parent directories

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** the parent directory of the runtime state path does not exist
- **When** `save_runtime_state({"key": "val"})` is called
- **Then** the parent directory SHALL be created and the file SHALL exist
