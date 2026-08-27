# runtime-state-persistence

## ADDED Requirements

### Requirement: load_runtime_state returns empty dict when state file absent

The system SHALL return an empty dict `{}` from `load_runtime_state()` when no
runtime state file exists on disk.

#### Scenario: state file does not exist

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** `_runtime_state_path()` returns a path to a non-existent file
- **When** `load_runtime_state()` is called
- **Then** the return value SHALL be an empty dict `{}`

---

### Requirement: load_runtime_state reads existing YAML state

The system SHALL parse the YAML content of an existing state file and return
the resulting dict.

#### Scenario: state file contains valid YAML dict

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** `_runtime_state_path()` returns a path to a file containing
  `active_target: my-project\nlast_cycle: "2026-01-01"`
- **When** `load_runtime_state()` is called
- **Then** the return value SHALL equal
  `{"active_target": "my-project", "last_cycle": "2026-01-01"}`

---

### Requirement: load_runtime_state graceful on malformed YAML

The system SHALL swallow exceptions from malformed YAML and return an empty
dict instead of propagating the error.

#### Scenario: state file contains invalid YAML

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** `_runtime_state_path()` returns a path to a file containing `": bad yaml [`
- **When** `load_runtime_state()` is called
- **Then** the return value SHALL be an empty dict `{}`

---

### Requirement: load_runtime_state returns empty dict for empty YAML file

The system SHALL treat a file that `yaml.safe_load` returns `None` for (e.g.
empty file) as an empty dict.

#### Scenario: state file is empty

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** `_runtime_state_path()` returns a path to an empty file
- **When** `load_runtime_state()` is called
- **Then** the return value SHALL be an empty dict `{}`

---

### Requirement: save_runtime_state writes YAML to disk

The system SHALL serialize the provided dict as YAML and write it to the path
returned by `_runtime_state_path()`.

#### Scenario: save then read back

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** a writable temporary directory and `_runtime_state_path()` pointing
  to a file inside it
- **When** `save_runtime_state({"active_target": "zsiga"})` is called
- **Then** the file at `_runtime_state_path()` SHALL exist and contain parseable
  YAML with key `active_target` equal to `"zsiga"`

---

### Requirement: save_runtime_state creates parent directories

The system SHALL create all intermediate parent directories if they do not
exist.

#### Scenario: parent directories do not exist

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** `_runtime_state_path()` returns a path whose parent directory does
  not exist
- **When** `save_runtime_state({"key": "value"})` is called
- **Then** the parent directory SHALL be created and the file SHALL exist

---

### Requirement: runtime state round-trip preserves data

Data written by `save_runtime_state` SHALL be faithfully readable by
`load_runtime_state`.

#### Scenario: round-trip with nested data

- **testable**: true
- **target**: zsiga/config.py::save_runtime_state
- **Given** a writable temporary directory
- **When** `save_runtime_state({"active_target": "zsiga", "count": 42,
  "tags": ["a", "b"]})` is called, followed by `load_runtime_state()`
- **Then** the loaded dict SHALL equal the original dict
