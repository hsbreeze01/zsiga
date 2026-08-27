# daemon-path-utilities

## ADDED Requirements

### Requirement: Path helpers SHALL resolve via ZSIGA_HOME or repo root

`_lock_path()` and `_daemon_state_path()` SHALL derive their return values from
the `ZSIGA_HOME` environment variable when set, falling back to the repository
root (parent of the `zsiga` package directory) when unset.

`_lock_path()` SHALL ensure the `data/` subdirectory exists before returning,
creating it with `parents=True` if necessary.

#### Scenario: lock path resolves under ZSIGA_HOME

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path

- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/alt-home`
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid`
- **And** the parent directory `data/` exists on disk

#### Scenario: lock path resolves under repo root when ZSIGA_HOME unset

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path

- **Given** environment variable `ZSIGA_HOME` is not set
- **When** `_lock_path()` is called
- **Then** the returned `Path` string contains `data/lock.pid`
- **And** the path is rooted under the zsiga package's parent directory

#### Scenario: daemon state path resolves under ZSIGA_HOME

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path

- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/alt-home`
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` equals `/tmp/alt-home/data/daemon_state.json`

### Requirement: _read_daemon_state SHALL return dict with safe defaults

`_read_daemon_state()` SHALL read and parse `daemon_state.json`. When the file
does not exist, is unreadable, or contains malformed JSON, it SHALL return an
empty dict `{}` without raising.

#### Scenario: valid JSON file returns parsed dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state

- **Given** a `daemon_state.json` file exists containing `{"pid": 123, "state": "running"}`
- **When** `_read_daemon_state()` is called (with `_daemon_state_path` patched to that file)
- **Then** the returned dict equals `{"pid": 123, "state": "running"}`

#### Scenario: missing file returns empty dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state

- **Given** no `daemon_state.json` file exists at the resolved path
- **When** `_read_daemon_state()` is called
- **Then** the returned value equals `{}`

#### Scenario: malformed JSON returns empty dict

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state

- **Given** a `daemon_state.json` file exists containing `NOT JSON{{{`
- **When** `_read_daemon_state()` is called
- **Then** the returned value equals `{}`
- **And** no exception is raised

### Requirement: _compute_uptime_seconds SHALL return elapsed time or None

`_compute_uptime_seconds(started_at)` SHALL parse the ISO-format `started_at`
string and return the elapsed seconds since that timestamp, rounded to 1
decimal place. It SHALL return `None` when `started_at` is falsy or unparseable.

#### Scenario: valid ISO timestamp returns positive float

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds

- **Given** a `started_at` string 5 seconds in the past
- **When** `_compute_uptime_seconds(started_at)` is called
- **Then** the result is a `float` >= 4.0
- **And** the result is rounded to 1 decimal place

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

#### Scenario: invalid timestamp string returns None

- **testable**: true
- **target**: zsiga/daemon.py::_compute_uptime_seconds

- **Given** `started_at` is `"not-a-date"`
- **When** `_compute_uptime_seconds("not-a-date")` is called
- **Then** the result is `None`
