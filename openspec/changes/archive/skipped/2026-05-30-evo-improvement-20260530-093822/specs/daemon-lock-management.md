# daemon-lock-management

## ADDED Requirements

### Requirement: acquire_lock SHALL create PID lock with exclusive flock

`acquire_lock()` SHALL create (or open) the lock file, acquire an
exclusive non-blocking flock, write the current PID, and return
`(fd, True)`. On flock failure it SHALL return `(None, False)`.

#### Scenario: successful lock acquisition

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the lock file
- **When** `acquire_lock()` is called
- **Then** it SHALL return a tuple `(fd, True)` where `fd` is an open file descriptor, and the lock file SHALL contain the current process PID as text

#### Scenario: lock contention returns failure

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** another file descriptor already holds an exclusive flock on the lock file
- **When** `acquire_lock()` is called
- **Then** it SHALL return `(None, False)`

---

### Requirement: release_lock SHALL close fd and remove lock file

`release_lock(fd)` SHALL close the file descriptor and unlink the lock
file. It SHALL NOT raise if the file was already removed.

#### Scenario: successful release

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a locked file descriptor `fd` from `acquire_lock()`
- **When** `release_lock(fd)` is called
- **Then** the lock file SHALL no longer exist on disk and `fd` SHALL be closed

#### Scenario: release handles missing file gracefully

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a locked file descriptor `fd` whose lock file has been manually deleted
- **When** `release_lock(fd)` is called
- **Then** no exception SHALL be raised
