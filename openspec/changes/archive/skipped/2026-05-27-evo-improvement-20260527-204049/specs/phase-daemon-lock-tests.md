# phase-daemon-lock-tests.md

## ADDED Requirements

### Requirement: daemon-lock-tests
The test suite SHALL verify that `acquire_lock()` and `release_lock()` correctly manage the PID lock file, including successful acquisition, contention rejection, and graceful release.

#### Scenario: acquire-lock-success

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no existing lock file and `_lock_path()` monkeypatched to a temporary directory
- **When** `acquire_lock()` is called
- **Then** the return value SHALL be a tuple `(fd, True)` where `fd` is a file object and the lock file SHALL contain the current process PID as a string

#### Scenario: acquire-lock-contention

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** an existing lock file already held via `fcntl.flock` with `LOCK_EX | LOCK_NB`
- **When** `acquire_lock()` is called from a context where the lock is already held
- **Then** the return value SHALL be `(None, False)` indicating lock contention

#### Scenario: release-lock-removes-file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file was acquired successfully
- **When** `release_lock(fd)` is called with the acquired file descriptor
- **Then** the lock file SHALL no longer exist on disk

#### Scenario: release-lock-missing-file-no-error

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file was acquired but the file was manually deleted before release
- **When** `release_lock(fd)` is called
- **Then** no exception SHALL be raised (FileNotFoundError is silently caught)
