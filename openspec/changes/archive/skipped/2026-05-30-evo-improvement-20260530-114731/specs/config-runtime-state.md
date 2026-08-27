# config-runtime-state

> Delta spec for change `evo-improvement-20260530-114731`
> Covers runtime state functions in `zsiga/config.py` that currently have **zero direct test coverage**.

## ADDED Requirements

### Requirement: Runtime state path resolution

The function `_runtime_state_path()` SHALL resolve the path to the runtime state
file (`data/runtime_state.yaml`) based on the `ZSIGA_HOME` environment variable:

- When `ZSIGA_HOME` is set, the state file SHALL be located at
  `$ZSIGA_HOME/data/runtime_state.yaml`.
- When `ZSIGA_HOME` is not set, the state file SHALL be located adjacent to
  the resolved config file, i.e. `<config_dir>/data/runtime_state.yaml`.

#### Scenario: State path uses ZSIGA_HOME when set

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/zsiga_home`
- **When** `_runtime_state_path()` is called
- **Then** the returned path SHALL be `Path("/tmp/zsiga_home/data/runtime_state.yaml")`

#### Scenario: State path falls back to config directory when ZSIGA_HOME unset

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is not set
- **And** a `zsiga.yaml` exists in the current working directory
- **When** `_runtime_state_path()` is called
- **Then** the returned path SHALL end with `data/runtime_state.yaml`
- **And** its parent directory SHALL be the same as `zsiga.yaml`'s parent directory

---

### Requirement: Load runtime state from disk

The function `load_runtime_state()` SHALL read the YAML state file and return a
dictionary. It SHALL gracefully handle missing files and corrupt YAML.

#### Scenario: Returns empty dict when state file does not exist

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file does not exist on disk
- **When** `load_runtime_state()` is called
- **Then** it SHALL return an empty dict `{}`

#### Scenario: Returns empty dict when state file contains corrupt YAML

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file exists but contains invalid YAML content
- **When** `load_runtime_state()` is called
- **Then** it SHALL return an empty dict `{}` without raising an exception

#### Scenario: Returns parsed dict for valid state file

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file exists and contains valid YAML
- **When** `load_runtime_state()` is called
- **Then** it SHALL return the parsed dictionary with all key-value pairs intact

---

### Requirement: Save runtime state to disk

The function `save_runtime_state(state)` SHALL write a dictionary as YAML to the
runtime state file, creating parent directories as needed.

#### Scenario: Creates parent directories and writes YAML

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** the runtime state directory does not exist
- **When** `save_runtime_state({"active_target": "myproject"})` is called
- **Then** the parent directories SHALL be created
- **And** the file SHALL exist on disk containing valid YAML with key `active_target`

#### Scenario: Round-trips data through save then load

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** a fresh writable directory
- **When** `save_runtime_state({"active_target": "proj1", "last_cycle": "2026-01-01"})` is called
- **And** `load_runtime_state()` is called
- **Then** the loaded dict SHALL equal `{"active_target": "proj1", "last_cycle": "2026-01-01"}`
