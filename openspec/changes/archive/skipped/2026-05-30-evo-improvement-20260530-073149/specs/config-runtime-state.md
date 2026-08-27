# spec: config-runtime-state

## ADDED Requirements

### Requirement: Runtime state path resolution

`_runtime_state_path` SHALL resolve to `$ZSIGA_HOME/data/runtime_state.yaml`
when `ZSIGA_HOME` env var is set, and fall back to the config file's parent
directory when it is not.

#### Scenario: Path with ZSIGA_HOME env var

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/opt/zsiga`
- **When** `_runtime_state_path()` is called
- **Then** the returned `Path` SHALL be `/opt/zsiga/data/runtime_state.yaml`

#### Scenario: Path without ZSIGA_HOME falls back to config parent

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** `ZSIGA_HOME` is NOT set
  AND `_find_config()` returns `/home/user/zsiga.yaml`
- **When** `_runtime_state_path()` is called
- **Then** the returned `Path` SHALL be `/home/user/data/runtime_state.yaml`

### Requirement: Load runtime state

`load_runtime_state` SHALL return a dict parsed from the runtime state YAML file,
or an empty dict if the file does not exist or is unreadable.

#### Scenario: Load state when file exists

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file exists and contains `active_target: proj1`
- **When** `load_runtime_state()` is called
- **Then** the return value SHALL be `{"active_target": "proj1"}`

#### Scenario: Load state when file does not exist

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file does NOT exist
- **When** `load_runtime_state()` is called
- **Then** the return value SHALL be `{}`

#### Scenario: Load state when file is corrupted

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file exists but contains invalid YAML
- **When** `load_runtime_state()` is called
- **Then** the return value SHALL be `{}`

### Requirement: Save runtime state

`save_runtime_state` SHALL write the given dict as YAML to the runtime state file,
creating parent directories as needed.

#### Scenario: Save state creates file and dirs

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** the runtime state file does NOT exist and parent directories do NOT exist
- **When** `save_runtime_state({"active_target": "proj2"})` is called
- **Then** the runtime state file SHALL exist AND contain `active_target: proj2`

#### Scenario: Save state overwrites existing

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** the runtime state file exists with `active_target: old`
- **When** `save_runtime_state({"active_target": "new"})` is called
- **Then** reading the file back SHALL yield `active_target: new`
