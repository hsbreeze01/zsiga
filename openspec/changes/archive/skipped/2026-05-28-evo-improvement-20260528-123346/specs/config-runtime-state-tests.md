# config-runtime-state-tests

ADDED requirements for test coverage of `_runtime_state_path()`, `load_runtime_state()`, and `save_runtime_state()` in `zsiga/config.py`.

## ADDED Requirements

### Requirement: _runtime_state_path uses ZSIGA_HOME when set

The system SHALL return `Path(ZSIGA_HOME) / "data/runtime_state.yaml"` when the `ZSIGA_HOME` environment variable is set.

#### Scenario: ZSIGA_HOME set returns path under it

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/zsiga-home`
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `Path("/tmp/zsiga-home/data/runtime_state.yaml")`

### Requirement: _runtime_state_path falls back to config parent

The system SHALL fall back to `_find_config().parent / "data/runtime_state.yaml"` when `ZSIGA_HOME` is not set.

#### Scenario: ZSIGA_HOME unset falls back to config parent

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is unset and `_find_config()` returns a known path
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `_find_config().parent / "data/runtime_state.yaml"`

### Requirement: load_runtime_state reads existing file

The system SHALL parse an existing YAML state file and return its contents as a dict.

#### Scenario: existing state file returns parsed dict

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** a YAML file at the runtime state path containing `active_target: my-project`
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{"active_target": "my-project"}`

### Requirement: load_runtime_state returns empty dict for missing file

The system SHALL return an empty dict when the state file does not exist.

#### Scenario: missing state file returns empty dict

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** no file exists at the runtime state path
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

### Requirement: load_runtime_state returns empty dict for corrupted file

The system SHALL return an empty dict when the state file cannot be parsed.

#### Scenario: corrupted YAML returns empty dict

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** a file at the runtime state path containing invalid YAML (e.g., `": bad: [yaml"`)
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

### Requirement: save_runtime_state writes YAML file

The system SHALL serialize the given dict to YAML and write it to the runtime state path, creating parent directories as needed.

#### Scenario: save creates file with correct content

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** a dict `{"active_target": "proj-a", "counter": 5}` and a writable runtime state path
- **When** `save_runtime_state(state)` is called
- **Then** the file at the runtime state path SHALL exist and `yaml.safe_load` of its content SHALL equal the original dict

#### Scenario: save creates parent directories

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** a runtime state path whose parent directory does not exist
- **When** `save_runtime_state({"key": "val"})` is called
- **Then** the parent directory SHALL exist and the state file SHALL be readable
