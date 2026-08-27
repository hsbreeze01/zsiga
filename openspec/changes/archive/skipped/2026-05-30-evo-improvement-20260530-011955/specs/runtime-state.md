# runtime-state — Runtime State Persistence

## ADDED Requirements

### Requirement: Runtime state path resolution

`_runtime_state_path()` SHALL determine the filesystem path for the runtime state file based on the `ZSIGA_HOME` environment variable or the config file location.

#### Scenario: Uses ZSIGA_HOME when set

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/opt/zsiga`
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `Path("/opt/zsiga") / "data/runtime_state.yaml"`

#### Scenario: Falls back to config parent directory

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** `ZSIGA_HOME` is not set AND `_find_config()` returns `/project/zsiga.yaml`
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `Path("/project") / "data/runtime_state.yaml"`

### Requirement: Load runtime state

`load_runtime_state()` SHALL read and parse the runtime state YAML file if it exists, returning its contents as a dict. It SHALL return an empty dict if the file does not exist or cannot be parsed.

#### Scenario: Returns parsed dict when state file exists

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** a valid YAML file at `_runtime_state_path()` containing `active_target: myproject`
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{"active_target": "myproject"}`

#### Scenario: Returns empty dict when state file missing

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** no file exists at `_runtime_state_path()`
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

#### Scenario: Returns empty dict on corrupt YAML

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** a file at `_runtime_state_path()` containing invalid YAML content
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

### Requirement: Save runtime state

`save_runtime_state()` SHALL write the given dict as YAML to the runtime state file, creating parent directories as needed.

#### Scenario: Writes state to file and reads back identically

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** a writable directory and a state dict `{"active_target": "test-project"}`
- **When** `save_runtime_state({"active_target": "test-project"})` is called AND `load_runtime_state()` is called
- **Then** the loaded state SHALL equal `{"active_target": "test-project"}`

#### Scenario: Creates parent directories automatically

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** the runtime state path points to a non-existent parent directory
- **When** `save_runtime_state({"key": "val"})` is called
- **Then** the parent directory SHALL exist AND the state file SHALL exist
