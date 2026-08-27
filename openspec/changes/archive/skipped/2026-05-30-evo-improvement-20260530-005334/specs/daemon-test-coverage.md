# daemon-test-coverage

## ADDED Requirements

### Requirement: Test file for daemon module utility functions

The project SHALL contain a test file `tests/test_daemon.py` that covers
utility functions from `zsiga/daemon.py` which are **not** already tested in
`tests/test_daemon_state.py`, `tests/test_daemon_scheduling.py`, or
`tests/test_daemon_cycle_resilience.py`.

#### Scenario: Lock path returns Path under ZSIGA_HOME/data

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` equals `<ZSIGA_HOME>/data/lock.pid` and
  the `data/` directory has been created

#### Scenario: Lock path falls back to repo root when ZSIGA_HOME unset

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is **not** set
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` and its parent
  directory exists

#### Scenario: Daemon state path returns correct JSON path

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` equals `<ZSIGA_HOME>/data/daemon_state.json`

#### Scenario: Read daemon state returns empty dict for missing file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist on disk
- **When** `_read_daemon_state()` is called
- **Then** an empty `dict` is returned

#### Scenario: Read daemon state returns parsed JSON for existing file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a daemon state file exists containing valid JSON `{"pid": 42, "cycle": 7}`
- **When** `_read_daemon_state()` is called
- **Then** the returned dict equals `{"pid": 42, "cycle": 7}`

#### Scenario: Read daemon state returns empty dict for corrupt JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a daemon state file exists containing invalid JSON text `{{{broken`
- **When** `_read_daemon_state()` is called
- **Then** an empty `dict` is returned (no exception raised)

---

### Requirement: Lock management function tests

The test file SHALL cover `acquire_lock()` and `release_lock(fd)` with
isolated temporary directories.

#### Scenario: Acquire lock succeeds on fresh directory

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** a temporary directory with no existing lock file and
  `_lock_path` is patched to return a path inside it
- **When** `acquire_lock()` is called
- **Then** the return is a tuple `(fd, True)` where `fd` is an open file
  descriptor and the lock file contains the current PID as text

#### Scenario: Acquire lock fails when already held

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** another `acquire_lock()` call has already succeeded on the same
  lock path (the file is flock'd)
- **When** a second `acquire_lock()` is called (e.g. in a child process or
  via `fcntl.LOCK_NB` conflict)
- **Then** the return is `(None, False)`

#### Scenario: Release lock removes lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists at the path returned by `_lock_path()`
  and an open file descriptor `fd` held on it
- **When** `release_lock(fd)` is called
- **Then** the lock file is unlinked from disk

#### Scenario: Release lock tolerates already-deleted file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file has already been deleted from disk
  and an open file descriptor `fd` held on it
- **When** `release_lock(fd)` is called
- **Then** no exception is raised (FileNotFoundError is silently caught)

---

### Requirement: Compute uptime seconds tests

#### Scenario: Compute uptime returns positive float for valid ISO timestamp

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is a valid ISO timestamp 100 seconds in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a `float` ≥ 99.0 and ≤ 101.0

#### Scenario: Compute uptime returns None for None input

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: Compute uptime returns None for invalid string

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is the string `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

---

### Requirement: Scan proposal queue tests

The test file SHALL cover `_scan_proposal_queue(changes_dir)` by constructing
temporary directory layouts without touching the real filesystem.

#### Scenario: Empty changes dir returns empty list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` is a temporary directory containing no sub-directories
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** an empty list is returned

#### Scenario: Non-directory changes dir returns empty list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` is `None` and `ZSIGA_HOME` points to a directory
  where `openspec/changes/` does not exist
- **When** `_scan_proposal_queue(None)` is called
- **Then** an empty list is returned

#### Scenario: Proposals with proposal.md are discovered

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains sub-directories `alpha/` and `beta/`,
      where `alpha/proposal.md` has first heading `# Fix alpha bug` and
      `beta/proposal.md` has first heading `# Add beta feature`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the returned list has length 2, each entry has a `name` key
  matching the directory name and a `summary` key matching the heading text

#### Scenario: Directories without proposal.md are skipped

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** `changes_dir` contains sub-directories `valid/` with
      `proposal.md` and `invalid/` without `proposal.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** only `valid` appears in the returned list

#### Scenario: Phase detection from output files

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains only `proposal.md`
      (no `clarify.md`, no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"CLARIFY"`

#### Scenario: Phase advances to ENRICH when clarify.md exists

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains `proposal.md` and `clarify.md`
      but no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"ENRICH"`

#### Scenario: Phase advances to IMPLEMENT when specs directory has markdown

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains `proposal.md`, `clarify.md`,
      and `specs/some-spec.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"IMPLEMENT"`

#### Scenario: Manual pause via .paused file

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal directory contains `proposal.md` and `.paused`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry has `paused` set to `True` and `lifecycle` is
  `"paused"`

---

### Requirement: Status and metrics JSON builder tests

#### Scenario: Build status json returns valid JSON with daemon and queue keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** `_read_daemon_state` is mocked to return `{"pid": 1, "state": "running", "started_at": "2025-01-01T00:00:00"}`
      and `_scan_proposal_queue` is mocked to return `[]`
- **When** `_build_status_json()` is called
- **Then** the result is a valid JSON string that parses to a dict with
  keys `"daemon"` and `"queue"`

#### Scenario: Build metrics json returns error JSON on failure

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** the import of `compute_stats` raises an exception
- **When** `_build_metrics_json()` is called
- **Then** the result is a JSON string containing an `"error"` key

#### Scenario: Build current json includes phase progress

- **testable**: true
- **target**: zsiga/daemon.py::_build_current_json
- **Given** `_read_daemon_state` is mocked to return
      `{"pid": 1, "state": "running", "current_phase": "IMPLEMENT", "started_at": "2025-01-01T00:00:00"}`
      and `_scan_proposal_queue` is mocked to return `[]`
- **When** `_build_current_json()` is called
- **Then** the parsed JSON contains `current.phase_progress` as a list
      where the entry with `name == "IMPLEMENT"` has `status == "active"`
      and entries before it have `status == "done"`

---

### Requirement: Health check tests

#### Scenario: Health check returns healthy for valid database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** a SQLite database at `db_path` with a `changes` table
      containing 5 rows
- **When** `_health_check(db_path)` is called
- **Then** the result is `{"status": "healthy", "db_records": 5}`

#### Scenario: Health check returns unhealthy for missing database

- **testable**: true
- **target**: zsiga/daemon.py::_health_check
- **Given** `db_path` points to a non-existent file
- **When** `_health_check(db_path)` is called
- **Then** the result has `"status"` equal to `"unhealthy"` and an `"error"` key

---

### Requirement: Pipeline status builder tests

#### Scenario: Build pipeline status with no active proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` is mocked to return `{}`,
      a temporary `base_path` with an empty `openspec/changes/` directory,
      and a valid (but empty) SQLite database at `db_path`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result dict has `active_proposal` equal to `None` and
      `queue` is an empty list

#### Scenario: Build pipeline status identifies active proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** `_read_daemon_state` returns `{"current_change": "my-proposal", "started_at": "2025-01-01T00:00:00"}`,
      a temporary `base_path` with `openspec/changes/my-proposal/proposal.md`,
      and a valid SQLite database
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** `result["active_proposal"]` equals `"my-proposal"` and
      the corresponding queue entry has `is_active == True`

---

### Requirement: Proposal detail builder tests

#### Scenario: Build proposal detail returns error for missing proposal

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path` has `openspec/changes/` without a sub-directory
      named `nonexistent` and no matching archive entry
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent")` is called
- **Then** the result dict contains an `"error"` key and
      `proposal_name` equals `"nonexistent"`

#### Scenario: Build proposal detail reads files from change directory

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** `base_path/openspec/changes/test-proposal/` contains
      `proposal.md` with content `# Hello` and
      a valid SQLite database at `db_path`
- **When** `_build_proposal_detail(db_path, base_path, "test-proposal")` is called
- **Then** `result["files"]["proposal.md"]` starts with `"# Hello"` and
      `result["change_dir"]` contains `"test-proposal"`

---

### Requirement: Proposal stats JSON builder tests

#### Scenario: Build proposal stats returns error for missing database

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** `db_path` points to a non-existent file
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result dict contains an `"error"` key

#### Scenario: Build proposal stats returns aggregated data

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_stats_json
- **Given** a SQLite database at `db_path` with a `changes` table
      containing rows with known outcomes
- **When** `_build_proposal_stats_json(db_path)` is called
- **Then** the result dict has keys `"total"`, `"by_outcome"`,
      `"avg_duration_seconds"`, and `"recent"`

---

### Requirement: Evolution status builder tests

#### Scenario: Build evolution status returns structured dict

- **testable**: false
- **Given** `_build_evolution_status` is called with a base path containing
      a `zsiga.yaml` config file and `openspec/changes/` directory
- **When** the function is invoked
- **Then** the returned dict contains keys `enabled`, `window`, `state`,
      `paused`, and `timestamp`
- **Note**: This scenario requires heavy mocking of `EvolutionEngine`,
      `load_config`, and `_build_langfuse_summary`. It is included as a
      stretch goal — mechanical testability is limited by deep import chains.

---

### Requirement: Test file quality constraints

The test file `tests/test_daemon.py` SHALL:

- contain at least 10 `def test_` functions
- pass `python -m pytest tests/test_daemon.py -x` with exit code 0
- pass `python -m ruff check tests/test_daemon.py` with no errors
- not import or depend on modules that require network access
- use `monkeypatch` or `unittest.mock.patch` to isolate all file I/O,
  database access, and external module imports

#### Scenario: Test file passes pytest

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the file `tests/test_daemon.py` exists
- **When** `python -m pytest tests/test_daemon.py -x` is executed
- **Then** the exit code is 0

#### Scenario: Test file passes ruff check

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the file `tests/test_daemon.py` exists
- **When** `python -m ruff check tests/test_daemon.py` is executed
- **Then** the exit code is 0 and no errors are reported

#### Scenario: Test file contains minimum 10 test functions

- **testable**: true
- **target**: tests/test_daemon.py
- **Given** the file `tests/test_daemon.py` exists
- **When** the number of lines matching `def test_` is counted
- **Then** the count is at least 10
