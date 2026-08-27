# daemon-lock-management

Delta spec for `zsiga/daemon.py` lock acquisition and release functions.

## ADDED Requirements

### Requirement: PID Lock Acquisition

`acquire_lock()` SHALL create an exclusive PID lock file using `fcntl`. It MUST
return `(fd, True)` on success and `(None, False)` when another process holds
the lock.

#### Scenario: acquire lock succeeds on fresh lock file

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no existing lock file or the lock file is not held by another process
- **When** `acquire_lock()` is called
- **Then** the return value SHALL be a tuple `(fd, True)` where `fd` is a writable file descriptor
- **And** the lock file SHALL contain the current process PID as text

#### Scenario: acquire lock fails when already held

- **testable**: false
- **Given** another process already holds an exclusive lock on the lock file
- **When** `acquire_lock()` is called
- **Then** the return value SHALL be `(None, False)`
- **Note**: Source code bug at L101 — `fd.read()` on write-only file handle raises
  `UnsupportedOperation`; cannot be tested without modifying source.

### Requirement: PID Lock Release

`release_lock(fd)` SHALL close the file descriptor and remove the lock file.
It MUST NOT raise when the lock file has already been removed.

#### Scenario: release lock closes fd and removes file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a valid lock file descriptor obtained from `acquire_lock()`
- **When** `release_lock(fd)` is called
- **Then** the lock file SHALL no longer exist on disk

#### Scenario: release lock tolerates missing lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** the lock file was already deleted externally
- **When** `release_lock(fd)` is called
- **Then** no exception SHALL be raised
