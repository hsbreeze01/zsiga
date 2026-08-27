# daemon-lock-management

Delta spec for lock acquisition and release functions in `zsiga/daemon.py`.

## ADDED Requirements

### Requirement: acquire_lock obtains exclusive PID lock

The system SHALL provide `acquire_lock()` that attempts to acquire an
exclusive, non-blocking file lock via `fcntl.flock`. On success it MUST
return `(fd, True)` with the current PID written to the lock file. On
failure (lock already held) it MUST return `(None, False)`.

#### Scenario: acquire_lock succeeds when lock is available

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the PID lock
- **When** `acquire_lock()` is called
- **Then** the return tuple's second element is `True`
- **And** the returned file descriptor is not `None`
- **And** the lock file contains the current PID string

#### Scenario: acquire_lock fails when lock is already held

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** `fcntl.flock` raises `OSError` (simulating a held lock)
- **When** `acquire_lock()` is called
- **Then** the return tuple is `(None, False)`

### Requirement: release_lock releases file lock and removes lock file

The system SHALL provide `release_lock(fd)` that closes the file
descriptor and removes the lock file. It MUST silently ignore
`FileNotFoundError` if the lock file was already removed.

#### Scenario: release_lock closes fd and removes lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists and an open file descriptor for it
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists

#### Scenario: release_lock handles already-deleted lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** the lock file has been deleted externally
- **When** `release_lock(fd)` is called
- **Then** no exception is raised
