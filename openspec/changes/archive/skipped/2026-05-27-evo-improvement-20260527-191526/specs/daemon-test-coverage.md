# daemon-test-coverage

Test coverage requirements for `zsiga/daemon.py` — a 1056-line core module
with zero dedicated unit-test file. This spec mandates the creation of
`tests/test_daemon.py` with real, passing unit tests that exercise the
module's public and internal functions using isolated filesystem and mocks.

## ADDED Requirements

### Requirement: Test file exists

A dedicated test module `tests/test_daemon.py` SHALL exist as a valid Python
module importable by pytest.

#### Scenario: test file created

- **testable**: true
- **target**: tests/test_daemon.py

- **Given** the project root directory
- **When** checking for the file `tests/test_daemon.py`
- **Then** the file SHALL exist on the filesystem

---

### Requirement: BAC-mandated test functions present

The test file SHALL contain the three test functions mandated by the
proposal's acceptance criteria: `test__lock_path`, `test__daemon_state_path`,
and `test__read_daemon_state`. Each SHALL contain at least one real assertion
(not `assert True`, `pass`, or `# TODO`).

#### Scenario: test__lock_path is defined with real assertion

- **testable**: true
- **target**: tests/test_daemon.py::test__lock_path

- **Given** the file `tests/test_daemon.py`
- **When** importing the module and inspecting `test__lock_path`
- **Then** the function SHALL be defined and callable

#### Scenario: test__daemon_state_path is defined with real assertion

- **testable**: true
- **target**: tests/test_daemon.py::test__daemon_state_path

- **Given** the file `tests/test_daemon.py`
- **When** importing the module and inspecting `test__daemon_state_path`
- **Then** the function SHALL be defined and callable

#### Scenario: test__read_daemon_state is defined with real assertion

- **testable**: true
- **target**: tests/test_daemon.py::test__read_daemon_state

- **Given** the file `tests/test_daemon.py`
- **When** importing the module and inspecting `test__read_daemon_state`
- **Then** the function SHALL be defined and callable

---

### Requirement: Minimum test function count

The test file SHALL contain at least 10 top-level `def test_` functions,
covering the six clarify.md sub-tasks (filesystem utils, queue scanning,
status/metrics builders, high-CC builders, dashboard handler, daemon loop).

#### Scenario: at least 10 test functions defined

- **testable**: true
- **target**: tests/test_daemon.py

- **Given** the file `tests/test_daemon.py`
- **When** counting all top-level `def test_` function definitions
- **Then** the count SHALL be >= 10

---

### Requirement: _lock_path behaviour verified

The test file SHALL verify that `_lock_path()` returns a `Path` ending in
`data/lock.pid` and that it creates the `data/` parent directory.

#### Scenario: _lock_path returns path ending in data/lock.pid

- **testable**: false

- **Given** a clean temporary directory set as `ZSIGA_HOME`
- **When** calling `_lock_path()`
- **Then** the returned `Path` SHALL end with `data/lock.pid`
- **And** the `data/` directory SHALL exist as a side effect

---

### Requirement: _daemon_state_path behaviour verified

The test file SHALL verify that `_daemon_state_path()` returns a `Path`
ending in `data/daemon_state.json`.

#### Scenario: _daemon_state_path returns correct path

- **testable**: false

- **Given** a clean temporary directory set as `ZSIGA_HOME`
- **When** calling `_daemon_state_path()`
- **Then** the returned `Path` SHALL end with `data/daemon_state.json`

---

### Requirement: _read_daemon_state behaviour verified

The test file SHALL verify the three main branches of `_read_daemon_state()`:
missing file returns `{}`, valid JSON returns parsed dict, invalid JSON
returns `{}`.

#### Scenario: _read_daemon_state returns empty dict on missing file

- **testable**: false

- **Given** a temporary directory set as `ZSIGA_HOME` with no `daemon_state.json`
- **When** calling `_read_daemon_state()`
- **Then** the result SHALL be `{}`

#### Scenario: _read_daemon_state returns parsed JSON from valid file

- **testable**: false

- **Given** a temporary directory with `data/daemon_state.json` containing `{"pid": 123}`
- **When** calling `_read_daemon_state()`
- **Then** the result SHALL be `{"pid": 123}`

#### Scenario: _read_daemon_state returns empty dict on invalid JSON

- **testable**: false

- **Given** a temporary directory with `data/daemon_state.json` containing `not-json`
- **When** calling `_read_daemon_state()`
- **Then** the result SHALL be `{}`

---

### Requirement: _write_daemon_state behaviour verified

The test file SHALL verify that `_write_daemon_state()` writes a valid JSON
file with all provided fields and preserves unspecified numeric fields from
the existing state file.

#### Scenario: _write_daemon_state creates file with provided fields

- **testable**: false

- **Given** a clean temporary directory set as `ZSIGA_HOME`
- **When** calling `_write_daemon_state(started_at="2025-01-01T00:00:00", cycle=1, state="running")`
- **Then** the file `data/daemon_state.json` SHALL exist
- **And** the parsed JSON SHALL contain `"started_at": "2025-01-01T00:00:00"`,
  `"cycle": 1`, and `"state": "running"`

#### Scenario: _write_daemon_state preserves existing numeric fields

- **testable**: false

- **Given** a temporary directory with existing `data/daemon_state.json` containing `{"total_cycles": 5}`
- **When** calling `_write_daemon_state(started_at="2025-01-01T00:00:00", cycle=2)`
- **Then** the resulting JSON SHALL contain `"total_cycles": 5` (preserved from existing)

---

### Requirement: acquire_lock and release_lock behaviour verified

The test file SHALL verify the lock acquire/release lifecycle: successful
acquisition returns `(fd, True)`, the lock file contains the PID, and
release removes the lock file.

#### Scenario: acquire_lock succeeds when no lock exists

- **testable**: false

- **Given** a clean temporary directory set as `ZSIGA_HOME`
- **When** calling `acquire_lock()`
- **Then** the returned tuple's second element SHALL be `True`
- **And** `data/lock.pid` SHALL exist

#### Scenario: release_lock removes lock file

- **testable**: false

- **Given** a held lock from `acquire_lock()`
- **When** calling `release_lock(fd)` with the file descriptor
- **Then** the `lock.pid` file SHALL no longer exist

---

### Requirement: DaemonState class verified

The test file SHALL verify that `DaemonState` has `paused` and `shutdown`
class-level boolean attributes, both defaulting to `False`.

#### Scenario: DaemonState defaults

- **testable**: false

- **Given** the class `DaemonState` from `zsiga.daemon`
- **When** creating an instance
- **Then** `instance.paused` SHALL be `False`
- **And** `instance.shutdown` SHALL be `False`

---

### Requirement: _scan_proposal_queue behaviour verified

The test file SHALL verify queue scanning with isolated filesystem: empty
directory, valid proposal with summary extraction, non-directory entries
skipped, and missing `proposal.md` entries skipped.

#### Scenario: _scan_proposal_queue returns empty for non-existent directory

- **testable**: false

- **Given** a `Path` to a non-existent directory
- **When** calling `_scan_proposal_queue(nonexistent_path)`
- **Then** the result SHALL be `[]`

#### Scenario: _scan_proposal_queue returns entry with extracted summary

- **testable**: false

- **Given** a temporary `changes/` directory containing `my-proposal/proposal.md`
  with first heading `# My Proposal Title`
- **When** calling `_scan_proposal_queue(changes_dir)`
- **Then** the result SHALL be a list of length 1
- **And** the entry's `name` SHALL be `"my-proposal"`
- **And** the entry's `summary` SHALL be `"My Proposal Title"`

#### Scenario: _scan_proposal_queue skips entries without proposal.md

- **testable**: false

- **Given** a temporary `changes/` directory containing a subdirectory
  `no-proposal/` with no `proposal.md` file
- **When** calling `_scan_proposal_queue(changes_dir)`
- **Then** the result SHALL be `[]`

---

### Requirement: _compute_uptime_seconds behaviour verified

The test file SHALL verify that `_compute_uptime_seconds` returns `None` for
falsy input, `None` for unparseable input, and a positive float for a valid
ISO timestamp in the past.

#### Scenario: _compute_uptime_seconds returns None for None input

- **testable**: false

- **Given** the function `_compute_uptime_seconds`
- **When** calling it with `None`
- **Then** the result SHALL be `None`

#### Scenario: _compute_uptime_seconds returns None for empty string

- **testable**: false

- **Given** the function `_compute_uptime_seconds`
- **When** calling it with `""`
- **Then** the result SHALL be `None`

#### Scenario: _compute_uptime_seconds returns positive float for valid past timestamp

- **testable**: false

- **Given** the function `_compute_uptime_seconds`
- **When** calling it with a valid ISO timestamp 60 seconds in the past
- **Then** the result SHALL be a `float` >= 59.0

#### Scenario: _compute_uptime_seconds returns None for unparseable string

- **testable**: false

- **Given** the function `_compute_uptime_seconds`
- **When** calling it with `"not-a-date"`
- **Then** the result SHALL be `None`

---

### Requirement: _build_status_json behaviour verified

The test file SHALL verify that `_build_status_json()` returns valid JSON
with `daemon` and `queue` top-level keys, using mocked dependencies.

#### Scenario: _build_status_json returns JSON with daemon and queue keys

- **testable**: false

- **Given** mocked `_read_daemon_state` returning `{"state": "running"}`
  and mocked `_scan_proposal_queue` returning `[]`
- **When** calling `_build_status_json()`
- **Then** the result SHALL be valid JSON
- **And** parsing it SHALL yield a dict with keys `"daemon"` and `"queue"`

---

### Requirement: _build_metrics_json behaviour verified

The test file SHALL verify that `_build_metrics_json()` returns valid JSON.
When the metrics module fails, it SHALL return an error JSON.

#### Scenario: _build_metrics_json returns JSON with error on import failure

- **testable**: false

- **Given** a patched `compute_stats` that raises `ImportError`
- **When** calling `_build_metrics_json()`
- **Then** the result SHALL be valid JSON
- **And** parsing it SHALL yield a dict with key `"error"`

---

### Requirement: _health_check behaviour verified

The test file SHALL verify that `_health_check` returns healthy status for a
valid database and unhealthy status when the database is missing.

#### Scenario: _health_check returns unhealthy for non-existent database

- **testable**: false

- **Given** a non-existent database path
- **When** calling `_health_check("/nonexistent/db.sqlite")`
- **Then** the result dict SHALL have `"status": "unhealthy"`

---

### Requirement: source code untouched

The file `zsiga/daemon.py` SHALL NOT be modified by this change.

#### Scenario: daemon.py git diff is empty

- **testable**: true
- **target**: zsiga/daemon.py

- **Given** the git working tree at the project root
- **When** running `git diff -- zsiga/daemon.py`
- **Then** the stdout SHALL be empty

---

### Requirement: all tests pass

Every test function in `tests/test_daemon.py` SHALL pass when executed by pytest.

#### Scenario: pytest exits cleanly

- **testable**: true
- **target**: tests/test_daemon.py

- **Given** the file `tests/test_daemon.py`
- **When** running `python -m pytest tests/test_daemon.py -x`
- **Then** the exit code SHALL be 0

---

### Requirement: lint clean

The test file SHALL pass `ruff check` with no errors.

#### Scenario: ruff check passes

- **testable**: true
- **target**: tests/test_daemon.py

- **Given** the file `tests/test_daemon.py`
- **When** running `ruff check tests/test_daemon.py`
- **Then** the exit code SHALL be 0
