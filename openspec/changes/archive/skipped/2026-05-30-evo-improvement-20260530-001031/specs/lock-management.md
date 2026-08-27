# Delta Spec: Lock Management Functions

## ADDED Requirements

### Requirement: acquire-lock

The system SHALL provide `acquire_lock()` that attempts to exclusively-lock the
PID file via `fcntl.flock(LOCK_EX|LOCK_NB)`. On success it SHALL return
`(fd, True)` and write the current PID. On failure (another process holds the
lock) it SHALL return `(None, False)`.

#### Scenario: succeeds-when-no-existing-lock

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** `ZSIGA_HOME` is set to a temporary directory (no existing lock file)
- **When** `acquire_lock()` is called
- **Then** the return tuple is `(fd, True)` where fd is not None
- **And** the lock file contains the string representation of the current PID

#### Scenario: fails-when-lock-already-held

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** `ZSIGA_HOME` is set to a temporary directory
- **And** another file descriptor already holds an exclusive flock on the lock file
- **When** `acquire_lock()` is called
- **Then** the return tuple is `(None, False)`

### Requirement: release-lock

The system SHALL provide `release_lock(fd)` that closes the file descriptor and
removes the lock file, ignoring `FileNotFoundError` if the file is already gone.

#### Scenario: removes-lock-file-on-release

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** `ZSIGA_HOME` is set to a temporary directory
- **And** a lock file was successfully acquired via `acquire_lock()`
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk

#### Scenario: tolerates-missing-lock-file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a valid file descriptor from `acquire_lock()`
- **And** the lock file was manually deleted before release
- **When** `release_lock(fd)` is called
- **Then** no exception is raised
