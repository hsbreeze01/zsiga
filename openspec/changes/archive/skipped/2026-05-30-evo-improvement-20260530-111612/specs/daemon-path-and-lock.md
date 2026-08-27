# daemon-path-and-lock

## ADDED Requirements

### Requirement: Lock file path resolution

`_lock_path()` SHALL return a `Path` ending in `data/lock.pid`.  When the
environment variable `ZSIGA_HOME` is set, it SHALL be used as the root;
otherwise the repository root (parent of the `zsiga` package directory) SHALL
be used.  The `data/` sub-directory SHALL be created if it does not exist.

#### Scenario: Default lock path without ZSIGA_HOME

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the environment variable `ZSIGA_HOME` is **not** set
- **When** `_lock_path()` is called
- **Then** the returned path ends with `data/lock.pid` and the `data` directory exists

#### Scenario: Lock path respects ZSIGA_HOME

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned path starts with that temporary directory and ends with `data/lock.pid`

---

### Requirement: Daemon state file path resolution

`_daemon_state_path()` SHALL return a `Path` ending in
`data/daemon_state.json`.  It SHALL respect the `ZSIGA_HOME` environment
variable the same way `_lock_path()` does.

#### Scenario: Default state path without ZSIGA_HOME

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the environment variable `ZSIGA_HOME` is **not** set
- **When** `_daemon_state_path()` is called
- **Then** the returned path ends with `data/daemon_state.json`

#### Scenario: State path respects ZSIGA_HOME

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned path starts with that temporary directory and ends with `data/daemon_state.json`

---

### Requirement: Read daemon state with graceful fallback

`_read_daemon_state()` SHALL read and parse `daemon_state.json`.  If the file
does not exist or contains invalid JSON, it SHALL return an empty dict `{}`.

#### Scenario: File does not exist returns empty dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** no `daemon_state.json` file exists in the configured data directory
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

#### Scenario: Invalid JSON returns empty dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` exists but contains `not-valid-json`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

#### Scenario: Valid JSON returns parsed content

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** `daemon_state.json` exists and contains `{"pid": 123, "state": "running"}`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{"pid": 123, "state": "running"}`

---

### Requirement: Acquire PID lock

`acquire_lock()` SHALL attempt an exclusive, non-blocking `flock` on the lock
file.  On success it SHALL return `(fd, True)` and write the current PID into
the lock file.  On failure (another process holds the lock) it SHALL return
`(None, False)`.

#### Scenario: First acquisition succeeds

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the lock
- **When** `acquire_lock()` is called
- **Then** the return tuple's second element is `True`, and the lock file contains the current PID string

#### Scenario: Second acquisition fails while first holds lock

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** another file descriptor already holds an exclusive lock on the lock file
- **When** `acquire_lock()` is called
- **Then** the return tuple's second element is `False` and the first element is `None`

---

### Requirement: Release PID lock

`release_lock(fd)` SHALL close the file descriptor and remove the lock file.
If the lock file has already been removed, it SHALL not raise an error.

#### Scenario: Release removes lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists and an open file descriptor `fd` holds it
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists

#### Scenario: Release tolerates missing lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** the lock file has already been deleted but a valid `fd` is passed
- **When** `release_lock(fd)` is called
- **Then** no exception is raised
