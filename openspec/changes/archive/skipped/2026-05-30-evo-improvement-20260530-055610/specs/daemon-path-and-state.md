# daemon-path-and-state

## ADDED Requirements

### Requirement: Lock path resolution

The daemon SHALL resolve its PID lock file path as `<ZSIGA_HOME>/data/lock.pid`.
When the `ZSIGA_HOME` environment variable is not set, the path SHALL default to
`<repo_root>/data/lock.pid` where `<repo_root>` is the parent of the `zsiga`
package directory.  The `data` sub-directory SHALL be created automatically if
it does not exist.

#### Scenario: Lock path uses ZSIGA_HOME when set

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the `ZSIGA_HOME` environment variable is set to `/tmp/zsiga-test-home`
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` under that home directory

#### Scenario: Lock path falls back to package parent when ZSIGA_HOME unset

- **testable**: true
- **target**: zsiga/daemon.py::_lock_path
- **Given** the `ZSIGA_HOME` environment variable is not set
- **When** `_lock_path()` is called
- **Then** the returned `Path` ends with `data/lock.pid` and the parent
  directory is the sibling of the `zsiga` package directory

### Requirement: Daemon state path resolution

The daemon SHALL resolve its state file path as `<ZSIGA_HOME>/data/daemon_state.json`.
When the `ZSIGA_HOME` environment variable is not set, the same fallback as
`_lock_path` SHALL apply.

#### Scenario: State path uses ZSIGA_HOME when set

- **testable**: true
- **target**: zsiga/daemon.py::_daemon_state_path
- **Given** the `ZSIGA_HOME` environment variable is set to `/tmp/zsiga-test-home`
- **When** `_daemon_state_path()` is called
- **Then** the returned `Path` is `<ZSIGA_HOME>/data/daemon_state.json`

### Requirement: Read daemon state with graceful degradation

`_read_daemon_state()` SHALL return the parsed JSON object from
`daemon_state.json` when the file exists and contains valid JSON.  It SHALL
return an empty `dict` when the file does not exist, contains invalid JSON,
or cannot be read.

#### Scenario: Returns empty dict when state file is missing

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file does not exist on disk
- **When** `_read_daemon_state()` is called
- **Then** the result is `{}`

#### Scenario: Returns parsed dict when state file has valid JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `{"pid": 42, "cycle": 7}`
- **When** `_read_daemon_state()` is called
- **Then** the result is `{"pid": 42, "cycle": 7}`

#### Scenario: Returns empty dict when state file has invalid JSON

- **testable**: true
- **target**: zsiga/daemon.py::_read_daemon_state
- **Given** the daemon state file contains `not-json{`
- **When** `_read_daemon_state()` is called
- **Then** the result is `{}`
