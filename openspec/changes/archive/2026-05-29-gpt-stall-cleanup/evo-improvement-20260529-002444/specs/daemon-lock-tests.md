# daemon-lock-tests

## ADDED Requirements

### Requirement: acquire_lock SHALL provide mutual exclusion via PID file

`acquire_lock()` SHALL return `(fd, True)` when no other process holds the
lock. When the lock is already held, it SHALL return `(None, False)` without
raising.

#### Scenario: acquire_lock succeeds on fresh lock file

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** the lock file does not exist and `_lock_path()` is monkeypatched to a temp path
- **When** `acquire_lock()` is called
- **Then** it returns a tuple where the second element is `True`
- **And** the lock file on disk contains the current PID as text

#### Scenario: acquire_lock fails when lock already held

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** the lock file is already locked by another file descriptor (using `fcntl.LOCK_EX | fcntl.LOCK_NB`)
- **When** `acquire_lock()` is called
- **Then** it returns `(None, False)`

---

### Requirement: release_lock SHALL clean up the PID file

`release_lock()` SHALL close the file descriptor and remove the lock file.
It MUST NOT raise `FileNotFoundError` when the lock file has already been
removed.

#### Scenario: release_lock removes lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists and a file descriptor `fd` is open on it
- **When** `release_lock(fd)` is called
- **Then** the lock file no longer exists on disk

#### Scenario: release_lock tolerates already-deleted file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** the lock file has been deleted externally but `fd` is still open
- **When** `release_lock(fd)` is called
- **Then** no exception is raised
