# daemon-file-lock

## ADDED Requirements

### Requirement: PID lock acquisition

`acquire_lock()` SHALL attempt an exclusive, non-blocking `flock` on the lock
file.  On success it SHALL write the current process PID to the file and return
`(fd, True)`.  On failure (another process holds the lock) it SHALL close the
file descriptor and return `(None, False)`.

#### Scenario: Acquire lock succeeds when no other holder exists

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the lock file
- **When** `acquire_lock()` is called
- **Then** the return value is a tuple whose second element is `True`, and the
  lock file on disk contains the string representation of the current PID

#### Scenario: Acquire lock fails when another process holds it

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** another file descriptor already holds an exclusive `flock` on the
  lock file
- **When** `acquire_lock()` is called
- **Then** the return value is `(None, False)`

### Requirement: PID lock release

`release_lock(fd)` SHALL close the given file descriptor and remove the lock
file from disk.  If the lock file has already been removed, it SHALL not raise
an exception.

#### Scenario: Release lock removes the lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists on disk and an open file descriptor to it
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk

#### Scenario: Release lock is safe when file already removed

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** the lock file has been deleted from disk but the file descriptor is
  still open
- **When** `release_lock(fd)` is called
- **Then** no exception is raised
