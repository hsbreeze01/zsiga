# daemon-utility-coverage

## ADDED Requirements

### Requirement: Path resolution functions produce correct locations

`_lock_path()` and `_daemon_state_path()` SHALL return `Path` objects under the
`data/` subdirectory of either `ZSIGA_HOME` (when set) or the repo root.

#### Scenario: _lock_path returns path ending in data/lock.pid

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the environment variable `ZSIGA_HOME` is set to a known directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid`

#### Scenario: _lock_path respects ZSIGA_HOME override

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** `ZSIGA_HOME` is set to `/tmp/custom_home`
- **When** `_lock_path()` is called
- **Then** the returned path starts with `/tmp/custom_home`

#### Scenario: _daemon_state_path returns path ending in data/daemon_state.json

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the environment variable `ZSIGA_HOME` is set to a known directory
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` ends with `data/daemon_state.json`

### Requirement: _read_daemon_state handles missing and corrupt files

`_read_daemon_state()` SHALL return an empty dict when the state file does not
exist or contains invalid JSON, and return the parsed dict when valid.

#### Scenario: Returns empty dict when file does not exist

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `_daemon_state_path()` points to a non-existent file
- **When** `_read_daemon_state()` is called
- **Then** the result is `{}`

#### Scenario: Returns empty dict for corrupt JSON content

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `_daemon_state_path()` points to a file containing `{invalid json`
- **When** `_read_daemon_state()` is called
- **Then** the result is `{}`

#### Scenario: Returns parsed dict for valid JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `_daemon_state_path()` points to a file containing `{"state": "running", "cycle": 5}`
- **When** `_read_daemon_state()` is called
- **Then** the result is `{"state": "running", "cycle": 5}`

### Requirement: Lock acquire and release round-trip

`acquire_lock()` SHALL create and exclusively lock a PID file, returning `(fd, True)`.
`release_lock(fd)` SHALL close the file descriptor and remove the lock file.

#### Scenario: acquire_lock succeeds on first call

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no existing lock file
- **When** `acquire_lock()` is called
- **Then** the return tuple's second element is `True` and the lock file exists

#### Scenario: acquire_lock fails when already held

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** a lock file is already held by the current process via a prior `acquire_lock()` call
- **When** a second `acquire_lock()` is called from the same process
- **Then** the call raises an exception (the function attempts `fd.read()` on a write-only file descriptor in its error handler, which is a known bug)

#### Scenario: release_lock removes the lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock has been acquired via `acquire_lock()`
- **When** `release_lock(fd)` is called with the acquired file descriptor
- **Then** the lock file no longer exists on disk
