# daemon-path-utilities

## ADDED Requirements

### REQ-PU-01: Lock path resolution

The daemon SHALL resolve the PID lock file path by reading `ZSIGA_HOME` environment
variable, falling back to the repository root (parent of `zsiga/` package directory)
when the variable is unset. The lock file SHALL be located at `<home>/data/lock.pid`
and the `data/` directory SHALL be created automatically if it does not exist.

#### Scenario: lock-path-with-zsiga-home-env

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` under the `ZSIGA_HOME` directory
  and the `data/` subdirectory exists on disk

#### Scenario: lock-path-defaults-to-parent-dir

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is **not** set
- **When** `_lock_path()` is called
- **Then** the returned `Path` resolves to `<repo_root>/data/lock.pid`

#### Scenario: lock-path-creates-data-dir

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** a `ZSIGA_HOME` directory that has no `data/` subdirectory
- **When** `_lock_path()` is called
- **Then** `<ZSIGA_HOME>/data/` directory is created and exists

### REQ-PU-02: Daemon state path resolution

The daemon SHALL resolve the daemon state file path at
`<home>/data/daemon_state.json` using the same `ZSIGA_HOME` resolution logic as
`_lock_path`. Unlike `_lock_path`, this function SHALL NOT create any directories.

#### Scenario: state-path-with-zsiga-home-env

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` is `<ZSIGA_HOME>/data/daemon_state.json`

### REQ-PU-03: Daemon state file reading

`_read_daemon_state` SHALL read and parse `daemon_state.json`. When the file does
not exist, contains invalid JSON, or cannot be read, it SHALL return an empty dict
without raising an exception.

#### Scenario: read-state-no-file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** no `daemon_state.json` file exists
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

#### Scenario: read-state-valid-json

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` contains `{"pid": 123, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{"pid": 123, "state": "running"}`

#### Scenario: read-state-corrupt-json

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` contains `{invalid json!!!`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}` without raising an exception

### REQ-PU-04: Lock acquisition and release

`acquire_lock` SHALL use `fcntl.LOCK_EX | fcntl.LOCK_NB` for non-blocking
exclusive locking. On success it SHALL return `(fd, True)` with the current PID
written to the lock file. On failure (another process holds the lock) it SHALL
return `(None, False)`.

`release_lock` SHALL close the file descriptor and remove the lock file. It SHALL
tolerate the lock file being already deleted (`FileNotFoundError`).

#### Scenario: acquire-lock-success

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no existing lock file and `_lock_path` is monkeypatched to a temp path
- **When** `acquire_lock()` is called
- **Then** returns a tuple `(fd, True)` where fd is a file object and the lock file
  contains the current process PID as a string

#### Scenario: acquire-lock-conflict

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** an existing lock file held by another process (simulated by mocking
  `fcntl.flock` to raise `OSError`)
- **When** `acquire_lock()` is called
- **Then** returns `(None, False)`

#### Scenario: release-lock-removes-file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file with an open file descriptor
- **When** `release_lock(fd)` is called
- **Then** the lock file is removed from disk

#### Scenario: release-lock-missing-file-no-error

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** the lock file has been externally deleted after opening
- **When** `release_lock(fd)` is called
- **Then** no exception is raised
