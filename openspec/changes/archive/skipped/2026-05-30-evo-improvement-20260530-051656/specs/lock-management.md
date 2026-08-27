# lock-management

## ADDED Requirements

### Requirement: acquire_lock SHALL provide exclusive PID lock via fcntl

`acquire_lock()` SHALL open the PID lock file, attempt a non-blocking
exclusive `flock`, write the current PID on success, and return
`(fd, True)`. On failure (another process holds the lock), it SHALL
close the fd and return `(None, False)`.

#### Scenario: acquire_lock succeeds when no other lock exists

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** ZSIGA_HOME points to a clean temporary directory with no existing lock file
- **When** `acquire_lock()` is called
- **Then** the return value SHALL be a tuple where the second element is `True`,
  and the lock file on disk SHALL contain the current PID as a string

#### Scenario: acquire_lock fails when lock already held

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** another file descriptor already holds an exclusive flock on the lock file
- **When** `acquire_lock()` is called
- **Then** the return value SHALL be `(None, False)`

### Requirement: release_lock SHALL remove the lock file

`release_lock(fd)` SHALL close the file descriptor and unlink the lock
file. If the file is already gone (race condition), it SHALL not raise.

#### Scenario: release_lock removes lock file from disk

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists on disk and a file descriptor `fd` is open on it
- **When** `release_lock(fd)` is called
- **Then** the lock file SHALL no longer exist on disk and no exception SHALL be raised

#### Scenario: release_lock tolerates already-deleted lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a file descriptor `fd` was opened on the lock file but the file
  was already deleted externally
- **When** `release_lock(fd)` is called
- **Then** no exception SHALL be raised
