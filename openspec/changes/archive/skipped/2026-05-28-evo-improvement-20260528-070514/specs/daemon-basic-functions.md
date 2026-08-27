# daemon-basic-functions

## ADDED Requirements

### Requirement: lock-path-resolution
`_lock_path()` SHALL resolve the PID lock file location using the `ZSIGA_HOME`
environment variable when set, falling back to the repository root (parent of
the `zsiga` package directory) when the variable is absent.  The returned path
MUST end with `data/lock.pid` and the `data/` directory SHALL be created
automatically if it does not exist.

#### Scenario: default-home-returns-lock-pid

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the `ZSIGA_HOME` environment variable is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` equals `<ZSIGA_HOME>/data/lock.pid` and the `data/` directory exists

#### Scenario: custom-home-creates-data-dir

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** `ZSIGA_HOME` is set to a writable temporary directory with no `data/` subdirectory
- **When** `_lock_path()` is called
- **Then** the `data/` directory exists after the call

---

### Requirement: daemon-state-path-resolution
`_daemon_state_path()` SHALL return the path to `data/daemon_state.json`
under the resolved home directory (same resolution logic as `_lock_path`).

#### Scenario: custom-home-state-path

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** `ZSIGA_HOME` is set to a custom directory
- **When** `_daemon_state_path()` is called
- **Then** the returned path equals `<ZSIGA_HOME>/data/daemon_state.json`

---

### Requirement: read-daemon-state-robustness
`_read_daemon_state()` SHALL return the parsed JSON dictionary from the
daemon state file when it exists and is valid JSON.  It MUST return an empty
dictionary (`{}`) when the file does not exist, when the JSON is malformed,
or when the file cannot be read due to an `OSError`.

#### Scenario: missing-file-returns-empty-dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist (ZSIGA_HOME points to empty tmp dir)
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

#### Scenario: valid-json-returns-parsed-dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `{"pid": 1234, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{"pid": 1234, "state": "running"}`

#### Scenario: corrupted-json-returns-empty-dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `{{{invalid`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`
