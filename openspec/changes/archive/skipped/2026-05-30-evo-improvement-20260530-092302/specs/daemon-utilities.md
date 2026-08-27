# daemon-utilities.md — Path, State, and Lock Utilities

## ADDED Requirements

### Requirement: test_daemon_file_exists
The project SHALL contain a file `tests/test_daemon.py` with at least 3 `def test_` functions covering functions from `zsiga/daemon.py`.

#### Scenario: test_daemon_file_exists_and_importable

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the project root directory
- **When** checking for the existence of `tests/test_daemon.py`
- **Then** the file exists and contains at least 3 functions matching `def test_`

---

### Requirement: lock_path_derives_from_zsiga_home
`_lock_path()` SHALL return a `Path` ending in `data/lock.pid` under the directory specified by `ZSIGA_HOME` env var (or the repo root if unset). It SHALL also ensure the `data/` parent directory exists.

#### Scenario: lock_path_uses_env_var

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned path ends with `data/lock.pid` relative to that directory, and the `data/` directory has been created

#### Scenario: lock_path_falls_back_to_repo_root

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the environment variable `ZSIGA_HOME` is not set
- **When** `_lock_path()` is called
- **Then** the returned path ends with `data/lock.pid` and resolves under the daemon module's parent-parent directory

---

### Requirement: daemon_state_path_derives_from_zsiga_home
`_daemon_state_path()` SHALL return a `Path` ending in `data/daemon_state.json` under `ZSIGA_HOME`.

#### Scenario: daemon_state_path_uses_env_var

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned path is `<ZSIGA_HOME>/data/daemon_state.json`

---

### Requirement: read_daemon_state_returns_dict
`_read_daemon_state()` SHALL read and parse `daemon_state.json` if it exists and is valid JSON. It SHALL return an empty dict when the file is missing or contains invalid JSON.

#### Scenario: read_state_from_valid_file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a valid `daemon_state.json` containing `{"pid": 123, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** it returns a dict with `"pid"` key equal to `123` and `"state"` key equal to `"running"`

#### Scenario: read_state_missing_file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** no `daemon_state.json` file exists
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

#### Scenario: read_state_corrupt_json

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a `daemon_state.json` file containing invalid JSON (e.g. `"not json"`)
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

---

### Requirement: acquire_lock_creates_pid_file
`acquire_lock()` SHALL attempt an exclusive non-blocking flock on the lock file. On success it returns `(fd, True)` and writes the current PID. On failure it returns `(None, False)` and prints a message.

#### Scenario: acquire_lock_success

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the lock file
- **When** `acquire_lock()` is called
- **Then** it returns a tuple whose second element is `True`, and the lock file contains the current process PID as a string

#### Scenario: acquire_lock_fails_when_held

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** another file descriptor already holds an exclusive flock on the lock file
- **When** `acquire_lock()` is called
- **Then** an exception is raised (known issue: fd is write-only, so `fd.read()` after flock failure raises `UnsupportedOperation`)

---

### Requirement: release_lock_closes_and_removes
`release_lock(fd)` SHALL close the file descriptor and remove the lock file. If the file was already removed, it SHALL silently succeed.

#### Scenario: release_lock_removes_file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists and an open fd to it
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists and the fd is closed

#### Scenario: release_lock_handles_missing_file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock fd whose file was already deleted
- **When** `release_lock(fd)` is called
- **Then** no exception is raised
