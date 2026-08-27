# daemon-lock-management

Delta spec for daemon lock acquisition and release functions: `acquire_lock`, `release_lock`.

## ADDED Requirements

### Requirement: acquire-exclusive-lock

`acquire_lock()` SHALL attempt to acquire an exclusive, non-blocking file lock on `<ZSIGA_HOME>/data/lock.pid`. On success it SHALL write the current PID to the lock file and return `(fd, True)`. On failure (another process holds the lock) it SHALL close the file descriptor and return `(None, False)`.

#### Scenario: acquire-lock-success

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the lock on `lock.pid`
- **When** `acquire_lock()` is called
- **Then** the return value is a tuple where the second element is `True` and the lock file contains the current process PID as a string

#### Scenario: acquire-lock-conflict

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock
- **Given** `fcntl.flock` raises `OSError` (simulating another process holding the lock)
- **When** `acquire_lock()` is called
- **Then** the return value is `(None, False)`

### Requirement: release-lock

`release_lock(fd)` SHALL close the file descriptor and remove the lock file. If the lock file has already been removed, it SHALL silently succeed without raising an exception.

#### Scenario: release-lock-removes-file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists on disk and a file descriptor `fd` is open to it
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk and the file descriptor is closed

#### Scenario: release-lock-missing-file-no-error

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock
- **Given** the lock file has already been deleted from disk
- **When** `release_lock(fd)` is called
- **Then** no exception is raised

