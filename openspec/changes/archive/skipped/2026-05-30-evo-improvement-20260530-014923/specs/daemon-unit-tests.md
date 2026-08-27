# daemon-unit-tests

## ADDED Requirements

### Requirement: Path utility functions return correct paths

`_lock_path()` SHALL return a `Path` ending in `data/lock.pid` under the directory
specified by `ZSIGA_HOME` (or the repo root when unset).  The `data/` directory
MUST be auto-created if absent.

`_daemon_state_path()` SHALL return a `Path` ending in `data/daemon_state.json`
under the same root, without creating any directories.

#### Scenario: lock path with ZSIGA_HOME set

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` and the `data/` directory exists

#### Scenario: lock path without ZSIGA_HOME falls back to repo root

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** `ZSIGA_HOME` is **not** set
- **When** `_lock_path()` is called
- **Then** the returned `Path` parent is the repo root's `data/` directory

#### Scenario: daemon state path with ZSIGA_HOME set

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** environment variable `ZSIGA_HOME` is set to a temporary directory
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` ends with `data/daemon_state.json`

---

### Requirement: _read_daemon_state parses JSON or returns empty dict

`_read_daemon_state()` SHALL read the daemon state file and return the parsed
dictionary.  If the file does not exist, contains invalid JSON, or cannot be
read, it SHALL return an empty `dict`.

#### Scenario: read valid state file

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** a daemon state file exists containing `{"pid": 42, "cycle": 3}`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{"pid": 42, "cycle": 3}`

#### Scenario: read missing state file returns empty dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

#### Scenario: read corrupt JSON returns empty dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `not-json`
- **When** `_read_daemon_state()` is called
- **Then** it returns `{}`

---

### Requirement: acquire_lock creates PID lock file

`acquire_lock()` SHALL attempt to acquire an exclusive non-blocking `flock` on
the lock file.  On success it SHALL write the current PID and return `(fd,
True)`.  On failure it SHALL close the file descriptor and return `(None,
False)`.

#### Scenario: successful lock acquisition

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** no other process holds the lock file
- **When** `acquire_lock()` is called
- **Then** the returned tuple is `(fd, True)` and the lock file contains the current PID string

#### Scenario: lock conflict returns failure

- **testable**: true
- **target**: zsiga/daemon.py::acquire_lock
- **Given** `fcntl.flock` raises `OSError` (simulated via mock)
- **When** `acquire_lock()` is called
- **Then** the returned tuple is `(None, False)`

---

### Requirement: release_lock closes fd and removes lock file

`release_lock(fd)` SHALL close the file descriptor and unlink the lock file.
If the file is already gone it SHALL NOT raise an exception.

#### Scenario: release removes lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** a lock file exists and an open file descriptor to it
- **When** `release_lock(fd)` is called
- **Then** the lock file is removed and the fd is closed

#### Scenario: release tolerates already-deleted lock file

- **testable**: true
- **target**: zsiga/daemon.py::release_lock
- **Given** the lock file has been manually deleted before release
- **When** `release_lock(fd)` is called
- **Then** no exception is raised

---

### Requirement: _scan_proposal_queue discovers and classifies proposals

`_scan_proposal_queue(changes_dir)` SHALL walk the given directory, identify
sub-directories containing `proposal.md`, extract the first heading as summary,
detect phase from output files (`clarify.md` → ENRICH, `specs/*.md` → IMPLEMENT,
else CLARIFY), and compute lifecycle status from metrics.  It SHALL return an
empty list when the directory does not exist or contains no valid proposals.

#### Scenario: empty directory returns empty list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` that is an empty directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: non-existent directory returns empty list

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a `changes_dir` path that does not exist on disk
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result is `[]`

#### Scenario: single proposal with proposal.md is listed

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing one sub-directory `fix-abc` with `proposal.md` whose first line is `# Fix ABC`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result list has length 1 and the entry's `name` is `"fix-abc"` and `summary` is `"Fix ABC"`

#### Scenario: proposal without proposal.md is skipped

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a changes directory containing a sub-directory with only `clarify.md` (no `proposal.md`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the result list is empty

#### Scenario: phase detection — clarify.md present sets ENRICH

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal sub-directory has `proposal.md` and `clarify.md` but no `specs/` directory
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"ENRICH"`

#### Scenario: phase detection — specs dir with .md sets IMPLEMENT

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal sub-directory has `proposal.md`, `clarify.md`, and a `specs/some-spec.md`
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"IMPLEMENT"`

#### Scenario: phase detection — only proposal.md sets CLARIFY

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal sub-directory has only `proposal.md` (no `clarify.md`, no `specs/`)
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `phase` is `"CLARIFY"`

#### Scenario: consecutive_fails defaults to zero when metrics unavailable

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal sub-directory with `proposal.md` and metrics import fails
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `consecutive_fails` is `0` and `lifecycle` is `"waiting"`

#### Scenario: manual .paused file sets paused flag

- **testable**: true
- **target**: zsiga/daemon.py::_scan_proposal_queue
- **Given** a proposal sub-directory has `proposal.md` and a `.paused` file
- **When** `_scan_proposal_queue(changes_dir)` is called
- **Then** the entry's `paused` is `True` and `lifecycle` is `"paused"`

---

### Requirement: _compute_uptime_seconds calculates elapsed time

`_compute_uptime_seconds(started_at)` SHALL return the number of seconds
elapsed since `started_at`, rounded to 1 decimal place.  It SHALL return
`None` when `started_at` is `None`, empty, or cannot be parsed.

#### Scenario: valid ISO timestamp returns positive float

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is 10 seconds ago as ISO timestamp
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a `float` ≥ 9.0 and ≤ 12.0

#### Scenario: None input returns None

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `None`
- **When** `_compute_uptime_seconds(None)` is called
- **Then** the result is `None`

#### Scenario: empty string returns None

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `""`
- **When** `_compute_uptime_seconds("")` is called
- **Then** the result is `None`

#### Scenario: unparseable string returns None

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds
- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`

---

### Requirement: _build_status_json returns valid JSON with daemon and queue keys

`_build_status_json()` SHALL return a JSON string containing a top-level
`"daemon"` object (with `pid`, `state`, `cycle`, `uptime_seconds` keys) and a
`"queue"` array.

#### Scenario: returns valid JSON with required top-level keys

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon state file contains `{"state": "running", "cycle": 1}`
- **When** `_build_status_json()` is called
- **Then** the result parses as JSON and has keys `"daemon"` and `"queue"`

#### Scenario: daemon object includes uptime_seconds from started_at

- **testable**: true
- **target**: zsiga/daemon.py::_build_status_json
- **Given** the daemon state file contains `{"state": "running", "started_at": "<10s ago>", "cycle": 1}`
- **When** `_build_status_json()` is called
- **Then** the parsed `daemon.uptime_seconds` is a positive number

---

### Requirement: _build_metrics_json returns JSON string

`_build_metrics_json()` SHALL return a JSON string.  When `compute_stats()`
fails, it SHALL return `{"error": "<message>"}` instead of raising.

#### Scenario: compute_stats failure returns error JSON

- **testable**: true
- **target**: zsiga/daemon.py::_build_metrics_json
- **Given** `compute_stats` raises an exception
- **When** `_build_metrics_json()` is called
- **Then** the returned string parses as JSON with key `"error"`

---

### Requirement: _build_pipeline_status combines daemon state and DB records

`_build_pipeline_status(db_path, base_path)` SHALL return a dict with keys
`active_proposal`, `current_phase`, `phase_progress`, `queue`, and `daemon`.
When the DB path or changes directory is empty/missing, it SHALL still return
a valid structure with empty defaults.

#### Scenario: empty changes dir returns structure with empty queue

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** a `base_path` with no `openspec/changes/` directory and no daemon state
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result dict has key `queue` with value `[]` and `active_proposal` is `None`

#### Scenario: proposal in changes dir appears in queue

- **testable**: true
- **target**: zsiga/daemon.py::_build_pipeline_status
- **Given** a `base_path` with `openspec/changes/fix-xyz/proposal.md` and a daemon state with `current_change = "fix-xyz"`
- **When** `_build_pipeline_status(db_path, base_path)` is called
- **Then** the result `queue` has an entry with `name == "fix-xyz"` and `is_active == True`

---

### Requirement: _build_proposal_detail returns proposal files and DB data

`_build_proposal_detail(db_path, base_path, proposal_name)` SHALL return a dict
with `proposal_name`, `files`, `phases`, and `phase_state` keys.  When the
proposal directory does not exist, it SHALL include an `"error"` key.

#### Scenario: non-existent proposal returns error

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a `base_path` with no matching proposal directory or archive entry
- **When** `_build_proposal_detail(db_path, base_path, "nonexistent")` is called
- **Then** the result dict contains key `"error"` with a string mentioning the proposal name

#### Scenario: existing proposal reads files

- **testable**: true
- **target**: zsiga/daemon.py::_build_proposal_detail
- **Given** a proposal directory with `proposal.md` and `clarify.md` files
- **When** `_build_proposal_detail(db_path, base_path, "<name>")` is called
- **Then** the result `files` dict contains keys `"proposal.md"` and `"clarify.md"` with string content
