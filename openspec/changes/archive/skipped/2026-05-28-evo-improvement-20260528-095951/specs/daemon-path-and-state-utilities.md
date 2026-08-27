# daemon-path-and-state-utilities

Delta spec for `zsiga/daemon.py` path resolution and state reading functions.

## ADDED Requirements

### Requirement: Path Resolution for Lock and State Files

`_lock_path()` and `_daemon_state_path()` SHALL resolve their return values
based on the `ZSIGA_HOME` environment variable. When `ZSIGA_HOME` is set, the
function MUST return a `Path` rooted under that directory. When `ZSIGA_HOME` is
unset, the function SHALL fall back to the parent directory of `zsiga/daemon.py`.

#### Scenario: lock path uses ZSIGA_HOME env var

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the environment variable `ZSIGA_HOME` is set to a custom directory
- **When** `_lock_path()` is called
- **Then** the returned Path SHALL be `<ZSIGA_HOME>/data/lock.pid`
- **And** the `data/` directory SHALL be created if it does not exist

#### Scenario: lock path falls back to repo root

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the environment variable `ZSIGA_HOME` is unset
- **When** `_lock_path()` is called
- **Then** the returned Path SHALL end with `data/lock.pid`
- **And** the parent of the parent of the returned path SHALL contain `zsiga/`

#### Scenario: daemon state path uses ZSIGA_HOME env var

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the environment variable `ZSIGA_HOME` is set to a custom directory
- **When** `_daemon_state_path()` is called
- **Then** the returned Path SHALL be `<ZSIGA_HOME>/data/daemon_state.json`

### Requirement: Daemon State File Reading

`_read_daemon_state()` SHALL read and parse `daemon_state.json`. It MUST return
an empty dict when the file does not exist, contains invalid JSON, or cannot be
read.

#### Scenario: read daemon state from missing file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` does not exist at the state path
- **When** `_read_daemon_state()` is called
- **Then** the result SHALL be an empty dict `{}`

#### Scenario: read daemon state from valid JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` exists and contains valid JSON
- **When** `_read_daemon_state()` is called
- **Then** the result SHALL equal the parsed JSON content

#### Scenario: read daemon state from malformed JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` exists but contains invalid JSON
- **When** `_read_daemon_state()` is called
- **Then** the result SHALL be an empty dict `{}`

#### Scenario: read daemon state from unreadable file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` exists but is not readable (OSError)
- **When** `_read_daemon_state()` is called
- **Then** the result SHALL be an empty dict `{}`
