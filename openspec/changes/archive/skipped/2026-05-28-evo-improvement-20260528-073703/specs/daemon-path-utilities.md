# daemon-path-utilities

## ADDED Requirements

### Requirement: Lock file path derivation

The daemon SHALL resolve the PID lock file path by reading `ZSIGA_HOME`
from the process environment. When `ZSIGA_HOME` is set, the lock file
SHALL be `<ZSIGA_HOME>/data/lock.pid`. When unset, it SHALL fall back
to the repository root (parent of the `zsiga` package directory) and
use `<repo_root>/data/lock.pid`. The `data` directory SHALL be created
with `parents=True, exist_ok=True` if it does not exist.

#### Scenario: Lock path with ZSIGA_HOME set

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/zsiga-test-home`
- **When** `_lock_path()` is called
- **Then** the returned path equals `/tmp/zsiga-test-home/data/lock.pid`

#### Scenario: Lock path defaults to repo root

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is **not** set
- **When** `_lock_path()` is called
- **Then** the returned path ends with `data/lock.pid` and its parent
  is `<repo_root>/data`

---

### Requirement: Daemon state file path derivation

The daemon SHALL resolve the state file path as
`<home>/data/daemon_state.json` where `<home>` is `ZSIGA_HOME` or the
repository root.

#### Scenario: State path with ZSIGA_HOME set

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/zsiga-test-home`
- **When** `_daemon_state_path()` is called
- **Then** the returned path equals `/tmp/zsiga-test-home/data/daemon_state.json`

#### Scenario: State path defaults to repo root

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is **not** set
- **When** `_daemon_state_path()` is called
- **Then** the returned path ends with `data/daemon_state.json`

---

### Requirement: Read daemon state with graceful fallback

`_read_daemon_state()` SHALL return the parsed JSON dict when the state
file exists and is valid JSON. When the file does not exist, it SHALL
return an empty dict `{}`. When the file exists but contains invalid
JSON, it SHALL also return `{}`.

#### Scenario: Returns empty dict when file missing

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist
- **When** `_read_daemon_state()` is called
- **Then** the result is an empty dict `{}`

#### Scenario: Returns parsed dict when file exists and valid

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `{"pid": 123, "cycle": 5}`
- **When** `_read_daemon_state()` is called
- **Then** the result equals `{"pid": 123, "cycle": 5}`

#### Scenario: Returns empty dict on corrupt JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `{invalid json!!!`
- **When** `_read_daemon_state()` is called
- **Then** the result is an empty dict `{}`
