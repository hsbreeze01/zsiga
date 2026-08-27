# daemon-path-state.md

## ADDED Requirements

### Requirement: Path helpers resolve against ZSIGA_HOME

`_lock_path()` and `_daemon_state_path()` SHALL resolve their return values
relative to the `ZSIGA_HOME` environment variable when it is set, or relative
to the parent of the daemon module's directory when it is not.

#### Scenario: lock path with ZSIGA_HOME set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path

- **Given** the environment variable `ZSIGA_HOME` is set to a known directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` equals `<ZSIGA_HOME>/data/lock.pid`

#### Scenario: daemon state path with ZSIGA_HOME set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_daemon_state_path

- **Given** the environment variable `ZSIGA_HOME` is set to a known directory
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` equals `<ZSIGA_HOME>/data/daemon_state.json`

#### Scenario: lock path without ZSIGA_HOME falls back to module parent

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path

- **Given** the environment variable `ZSIGA_HOME` is **not** set
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` and its parent directory is the project root

### Requirement: _read_daemon_state handles missing and corrupt files gracefully

`_read_daemon_state()` SHALL return an empty dict when the state file does not
exist or contains invalid JSON, and SHALL return the parsed dict when the file
is valid.

#### Scenario: state file missing returns empty dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state

- **Given** the daemon state file does not exist on disk
- **When** `_read_daemon_state()` is called
- **Then** the result is `{}`

#### Scenario: corrupt JSON returns empty dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state

- **Given** the daemon state file exists but contains `"{bad json"`
- **When** `_read_daemon_state()` is called
- **Then** the result is `{}`

#### Scenario: valid JSON returns parsed dict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state

- **Given** the daemon state file exists and contains `{"pid": 123, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** the result is `{"pid": 123, "state": "running"}`

