# runtime-state-functions

## ADDED Requirements

### Requirement: Runtime state path resolution

The system SHALL resolve the runtime state file path based on the `ZSIGA_HOME`
environment variable. When `ZSIGA_HOME` is set to a non-empty string, the
state file MUST be located at `<ZSIGA_HOME>/data/runtime_state.yaml`. When
`ZSIGA_HOME` is unset or empty, the state file MUST be located at the parent
directory of the config file (as returned by `_find_config()`) joined with
`data/runtime_state.yaml`.

#### Scenario: ZSIGA_HOME env var overrides state file location

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to a directory path `/tmp/zsiga_home`
- **When** `_runtime_state_path()` is called
- **Then** the returned path SHALL equal `/tmp/zsiga_home/data/runtime_state.yaml`

#### Scenario: ZSIGA_HOME empty falls back to config directory

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is unset and a `zsiga.yaml` exists in the current working directory
- **When** `_runtime_state_path()` is called
- **Then** the returned path SHALL be `<parent of zsiga.yaml>/data/runtime_state.yaml`

---

### Requirement: Load runtime state

`load_runtime_state()` SHALL read and parse the YAML state file if it exists
and contains valid YAML. If the file does not exist or is malformed, it MUST
return an empty dict without raising.

#### Scenario: Returns parsed dict when state file exists and is valid

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file contains `active_target: myproject`
- **When** `load_runtime_state()` is called
- **Then** the result SHALL equal `{"active_target": "myproject"}`

#### Scenario: Returns empty dict when state file does not exist

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file path points to a non-existent file
- **When** `load_runtime_state()` is called
- **Then** the result SHALL equal `{}`

#### Scenario: Returns empty dict when state file contains invalid YAML

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file contains `: invalid: yaml: [`
- **When** `load_runtime_state()` is called
- **Then** the result SHALL equal `{}`

#### Scenario: Returns empty dict when state file is empty

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file exists but is empty
- **When** `load_runtime_state()` is called
- **Then** the result SHALL equal `{}`

---

### Requirement: Save runtime state

`save_runtime_state(state)` SHALL write the given dict as YAML to the runtime
state file path, creating parent directories if they do not exist. The file
MUST be overwrite-safe (subsequent reads return equivalent data).

#### Scenario: Creates parent directories and writes YAML

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** `ZSIGA_HOME` points to an empty temporary directory
- **When** `save_runtime_state({"active_target": "proj"})` is called
- **Then** a file at `<ZSIGA_HOME>/data/runtime_state.yaml` SHALL exist and contain valid YAML with key `active_target` equal to `"proj"`

#### Scenario: Round-trip write then read

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** `ZSIGA_HOME` points to a temporary directory
- **When** `save_runtime_state({"active_target": "proj", "last_run": "2025-01-01"})` is called and then `load_runtime_state()` is called
- **Then** the loaded result SHALL equal `{"active_target": "proj", "last_run": "2025-01-01"}`
