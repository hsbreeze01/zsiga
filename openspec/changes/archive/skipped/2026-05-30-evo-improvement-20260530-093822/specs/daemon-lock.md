# daemon-lock.md

## ADDED Requirements

### Requirement: acquire_lock provides mutual exclusion via PID file

`acquire_lock()` SHALL return `(fd, True)` when no other process holds the lock,
and `(None, False)` when the lock is already held. The lock file SHALL contain
the current process PID after successful acquisition.

#### Scenario: first acquisition succeeds

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock

- **Given** no lock file exists on disk
- **When** `acquire_lock()` is called
- **Then** the return value is `(fd, True)` where `fd` is a file object, and the lock file contains the current PID as text

#### Scenario: second acquisition fails while first holds lock

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::acquire_lock

- **Given** another file descriptor already holds an exclusive `fcntl.flock` on the lock file
- **When** `acquire_lock()` is called from a different context
- **Then** the return value is `(None, False)`

### Requirement: release_lock removes lock file

`release_lock(fd)` SHALL close the file descriptor and remove the lock file.
If the lock file has already been removed, it SHALL NOT raise an error.

#### Scenario: release removes lock file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock

- **Given** a lock file exists and a file descriptor `fd` is open on it
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk and `fd` is closed

#### Scenario: release tolerates already-removed lock file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/daemon.py::release_lock

- **Given** the lock file has been deleted but a file descriptor is still open
- **When** `release_lock(fd)` is called
- **Then** no exception is raised

