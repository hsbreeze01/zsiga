# daemon-file-lock

## ADDED Requirements

### Requirement: acquire_lock SHALL provide exclusive PID-based locking

`acquire_lock()` SHALL attempt to create and exclusively lock a PID file at the
path returned by `_lock_path()`. On success it SHALL return `(fd, True)` where
`fd` is the open file descriptor with the current PID written to it. On failure
(another process holds the lock) it SHALL return `(None, False)`.

#### Scenario: first acquisition succeeds with PID written

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock

- **Given** no existing lock file at the lock path
- **And** `_lock_path` is patched to return a path under `tmp_path`
- **When** `acquire_lock()` is called
- **Then** the return is `(fd, True)` where `fd` is not `None`
- **And** the lock file contains the string representation of `os.getpid()`

#### Scenario: second acquisition fails when lock already held

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock

- **Given** a lock file at the lock path is already exclusively held by another fd
- **When** `acquire_lock()` is called
- **Then** the return is `(None, False)`

### Requirement: release_lock SHALL clean up lock file

`release_lock(fd)` SHALL close the file descriptor and remove the lock file.
It SHALL silently tolerate `FileNotFoundError` if the lock file was already
removed.

#### Scenario: release removes lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock

- **Given** a lock file exists and an open fd holds it
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk

#### Scenario: release tolerates missing lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock

- **Given** a lock file has been manually deleted but an fd is still open
- **When** `release_lock(fd)` is called
- **Then** no exception is raised
