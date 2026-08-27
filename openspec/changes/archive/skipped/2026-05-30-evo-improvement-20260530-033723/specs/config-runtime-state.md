# config-runtime-state

Incremental test coverage for `zsiga/config.py` runtime state functions:
`_runtime_state_path()`, `load_runtime_state()`, `save_runtime_state(state)`.

These functions currently have **zero** direct test coverage.

## ADDED Requirements

### Requirement: Runtime state path resolution

The system SHALL resolve the runtime state file path based on the
`ZSIGA_HOME` environment variable.  When `ZSIGA_HOME` is set to a
non-empty string, the state file SHALL be located at
`<ZSIGA_HOME>/data/runtime_state.yaml`.  When `ZSIGA_HOME` is not set
or is empty, the state file SHALL be located at the directory that
contains the resolved config file (i.e. the parent of the path returned
by `_find_config()`).

#### Scenario: ZSIGA_HOME env var overrides default path

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/custom_home`
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `Path("/tmp/custom_home") / "data/runtime_state.yaml"`

#### Scenario: Fallback to config directory when ZSIGA_HOME is unset

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is not set and a valid
  `zsiga.yaml` exists in the current working directory at path `<cwd>/zsiga.yaml`
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `<cwd> / "data/runtime_state.yaml"`

### Requirement: Load runtime state

`load_runtime_state()` SHALL read the runtime state YAML file and return
its parsed content as a dict.  When the file does not exist or cannot be
parsed, it SHALL return an empty dict without raising.

#### Scenario: Returns empty dict when state file does not exist

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** `ZSIGA_HOME` points to an empty temporary directory
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

#### Scenario: Returns parsed dict when state file exists

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** `ZSIGA_HOME` points to a directory that contains a valid
  `data/runtime_state.yaml` with content `active_target: myproject`
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{"active_target": "myproject"}`

#### Scenario: Returns empty dict when state file contains invalid YAML

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** `ZSIGA_HOME` points to a directory that contains a
  `data/runtime_state.yaml` with malformed content `: :: bad yaml {{{`
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}` without raising an exception

### Requirement: Save runtime state

`save_runtime_state(state)` SHALL serialize the given dict to YAML and
write it to the runtime state file path, creating parent directories as
needed.

#### Scenario: Writes valid YAML and creates parent directories

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** `ZSIGA_HOME` points to a temporary directory (no `data/` subdirectory yet)
- **When** `save_runtime_state({"active_target": "newproj", "cycle": 5})` is called
- **Then** a file at `<ZSIGA_HOME>/data/runtime_state.yaml` SHALL exist and
  its parsed content SHALL equal `{"active_target": "newproj", "cycle": 5}`

#### Scenario: Round-trip: save then load preserves data

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** `ZSIGA_HOME` points to a temporary directory
- **When** `save_runtime_state({"active_target": "rtt"})` is called followed by
  `load_runtime_state()`
- **Then** the loaded dict SHALL equal `{"active_target": "rtt"}`

