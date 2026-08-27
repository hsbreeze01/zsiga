# config-runtime-state

## ADDED Requirements

### Requirement: Runtime state path resolution

The `_runtime_state_path` function SHALL determine the location of the runtime state file
based on the `ZSIGA_HOME` environment variable. When `ZSIGA_HOME` is set, the state file
SHALL be at `$ZSIGA_HOME/data/runtime_state.yaml`. When not set, it SHALL fall back to
the directory containing the config file (as determined by `_find_config`).

#### Scenario: Path with ZSIGA_HOME set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to "/opt/zsiga"
- **When** `_runtime_state_path()` is called
- **Then** the result is `Path("/opt/zsiga/data/runtime_state.yaml")`

#### Scenario: Path without ZSIGA_HOME falls back to config dir

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** `ZSIGA_HOME` is not set and `_find_config` returns a path like `/project/zsiga.yaml`
- **When** `_runtime_state_path()` is called
- **Then** the result is `/project/data/runtime_state.yaml`

### Requirement: Load runtime state

The `load_runtime_state` function SHALL read and parse the runtime state YAML file.
If the file does not exist or is corrupt, it SHALL return an empty dict without raising.

#### Scenario: Load from non-existent file returns empty dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file does not exist
- **When** `load_runtime_state()` is called
- **Then** the result is `{}`

#### Scenario: Load from valid file returns parsed dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file contains `active_target: "my-project"`
- **When** `load_runtime_state()` is called
- **Then** the result is `{"active_target": "my-project"}`

#### Scenario: Load from corrupt file returns empty dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file contains invalid YAML like `: {broken`
- **When** `load_runtime_state()` is called
- **Then** the result is `{}` and no exception is raised

### Requirement: Save runtime state

The `save_runtime_state` function SHALL write the state dict as YAML to the runtime state
file path, creating parent directories as needed.

#### Scenario: Save creates parent directories

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** a state dict `{"active_target": "proj-a"}` and a non-existent parent directory
- **When** `save_runtime_state()` is called
- **Then** the parent directory is created and the file exists containing valid YAML
  with `active_target: proj-a`

#### Scenario: Save and load round-trip

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** a state dict `{"active_target": "round-trip", "count": 42}`
- **When** `save_runtime_state()` is called and then `load_runtime_state()` is called
- **Then** the loaded dict equals the original dict

