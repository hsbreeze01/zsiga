# daemon-path-utilities

Delta spec for path utility functions in `zsiga/daemon.py`.

## ADDED Requirements

### Requirement: _lock_path returns PID lock file path

The system SHALL provide `_lock_path()` that returns a `Path` pointing to
`data/lock.pid` under the resolved home directory (`ZSIGA_HOME` env var or
repo root). The function MUST create the `data/` directory if it does not
exist.

#### Scenario: _lock_path returns path containing lock.pid

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** ZSIGA_HOME is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` string ends with `data/lock.pid`
- **And** the `data/` directory exists

#### Scenario: _lock_path respects ZSIGA_HOME environment variable

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** ZSIGA_HOME is set to `/tmp/zsiga-test-home`
- **When** `_lock_path()` is called
- **Then** the returned `Path` starts with `/tmp/zsiga-test-home`

### Requirement: _daemon_state_path returns state file path

The system SHALL provide `_daemon_state_path()` that returns a `Path`
pointing to `data/daemon_state.json` under the resolved home directory.

#### Scenario: _daemon_state_path returns path containing daemon_state.json

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** ZSIGA_HOME is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` string ends with `data/daemon_state.json`

### Requirement: _read_daemon_state reads state or returns empty dict

The system SHALL provide `_read_daemon_state()` that reads the JSON state
file. When the file does not exist or contains invalid JSON, it MUST return
an empty dict.

#### Scenario: _read_daemon_state returns parsed dict from valid JSON file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `{"pid": 123, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{"pid": 123, "state": "running"}`

#### Scenario: _read_daemon_state returns empty dict when file missing

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

#### Scenario: _read_daemon_state returns empty dict on invalid JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `{invalid json`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`
