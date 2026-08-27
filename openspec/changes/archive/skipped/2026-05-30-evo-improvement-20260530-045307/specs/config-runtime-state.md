# config-runtime-state

## ADDED Requirements

### Requirement: runtime state path resolution

`_runtime_state_path` SHALL resolve the path to the runtime state file based on
the `ZSIGA_HOME` environment variable or the config file location.

#### Scenario: path uses ZSIGA_HOME when set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/opt/zsiga`
- **When** `_runtime_state_path()` is called
- **Then** the result SHALL be `Path("/opt/zsiga/data/runtime_state.yaml")`

#### Scenario: path falls back to config file parent when ZSIGA_HOME is not set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is not set and a `zsiga.yaml` exists in the current directory
- **When** `_runtime_state_path()` is called
- **Then** the result SHALL end with `data/runtime_state.yaml` and its parent
  SHALL correspond to the config file's parent directory

### Requirement: load_runtime_state returns dict from YAML

`load_runtime_state` SHALL read the runtime state YAML file and return a dict.
If the file does not exist or cannot be parsed, it SHALL return an empty dict.

#### Scenario: load from existing file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** a valid YAML file at `_runtime_state_path()` containing `active_target: myproject`
- **When** `load_runtime_state()` is called
- **Then** the result SHALL be `{"active_target": "myproject"}`

#### Scenario: load returns empty dict when file missing

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** no runtime state file exists
- **When** `load_runtime_state()` is called
- **Then** the result SHALL be `{}`

#### Scenario: load returns empty dict on corrupt YAML

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** a file at `_runtime_state_path()` containing invalid YAML `: [broken`
- **When** `load_runtime_state()` is called
- **Then** the result SHALL be `{}`

### Requirement: save_runtime_state writes YAML

`save_runtime_state` SHALL serialize the given dict as YAML to the runtime
state file, creating parent directories as needed.

#### Scenario: save and reload roundtrip

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** a writable directory for the runtime state file
- **When** `save_runtime_state({"active_target": "newproj", "counter": 42})` is called
  and then `load_runtime_state()` is called
- **Then** the loaded dict SHALL contain `{"active_target": "newproj", "counter": 42}`

