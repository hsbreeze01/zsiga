# daemon-path-utils

Delta spec for daemon path utility functions: `_lock_path`, `_daemon_state_path`, `_read_daemon_state`.

## ADDED Requirements

### Requirement: lock-path-resolution

`_lock_path()` SHALL resolve the PID lock file location using the `ZSIGA_HOME` environment variable when set, falling back to the repository root (parent of `zsiga/` package directory) when unset. The lock file SHALL be located at `<home>/data/lock.pid`. The `data/` directory SHALL be created automatically if it does not exist.

#### Scenario: lock-path-with-zsiga-home-env

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** the `ZSIGA_HOME` environment variable is set to `/tmp/daemon-test-home`
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` under that home directory

#### Scenario: lock-path-without-zsiga-home-env

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** the `ZSIGA_HOME` environment variable is not set
- **When** `_lock_path()` is called
- **Then** the returned `Path` is `<repo_root>/data/lock.pid`

#### Scenario: lock-path-creates-data-dir

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_lock_path
- **Given** the `ZSIGA_HOME` environment variable points to a directory without a `data/` subdirectory
- **When** `_lock_path()` is called
- **Then** the `data/` directory exists at `<ZSIGA_HOME>/data/`

### Requirement: daemon-state-path-resolution

`_daemon_state_path()` SHALL resolve the daemon state JSON file location using the `ZSIGA_HOME` environment variable when set, falling back to the repository root. The state file SHALL be at `<home>/data/daemon_state.json`.

#### Scenario: state-path-with-zsiga-home-env

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the `ZSIGA_HOME` environment variable is set to `/tmp/daemon-test-home`
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` is `/tmp/daemon-test-home/data/daemon_state.json`

#### Scenario: state-path-without-zsiga-home-env

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the `ZSIGA_HOME` environment variable is not set
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` ends with `data/daemon_state.json` under the repo root

### Requirement: read-daemon-state-fallback

`_read_daemon_state()` SHALL return the parsed contents of `daemon_state.json` as a dict when the file exists and contains valid JSON. It SHALL return an empty dict `{}` when the file does not exist, contains invalid JSON, or cannot be read.

#### Scenario: read-state-valid-json

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` exists and contains `{"pid": 1234, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** the returned dict equals `{"pid": 1234, "state": "running"}`

#### Scenario: read-state-file-not-found

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` does not exist
- **When** `_read_daemon_state()` is called
- **Then** the returned dict equals `{}`

#### Scenario: read-state-invalid-json

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` exists but contains `not valid json`
- **When** `_read_daemon_state()` is called
- **Then** the returned dict equals `{}`

