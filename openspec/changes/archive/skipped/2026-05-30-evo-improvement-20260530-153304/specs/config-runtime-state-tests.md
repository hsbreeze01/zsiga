# Spec: config-runtime-state-tests

> Covers direct unit tests for `_runtime_state_path()`, `load_runtime_state()`, and `save_runtime_state()`
> in `zsiga/config.py`. These three functions are the **only genuinely uncovered** entry points;
> all other functions (`_find_config`, `_resolve_env_vars`, `validate_config`, `load_config`) and all
> 13 data classes are already covered by `tests/test_config_validation.py` (39 tests) and
> `tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py` (8 tests).

## ADDED Requirements

### Requirement: runtime-state-path-with-zsiga-home

The system SHALL resolve `_runtime_state_path()` to `$ZSIGA_HOME/data/runtime_state.yaml` when the
`ZSIGA_HOME` environment variable is set.

#### Scenario: zsiga-home-env-set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** the `ZSIGA_HOME` environment variable is set to a valid directory path
- **When** `_runtime_state_path()` is called
- **Then** the returned path SHALL equal `Path(ZSIGA_HOME) / "data" / "runtime_state.yaml"`

---

### Requirement: runtime-state-path-without-zsiga-home

The system SHALL resolve `_runtime_state_path()` to `<config_dir>/data/runtime_state.yaml` when the
`ZSIGA_HOME` environment variable is not set, falling back to `_find_config()` parent directory.

#### Scenario: zsiga-home-env-unset

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** the `ZSIGA_HOME` environment variable is unset or empty
- **When** `_runtime_state_path()` is called
- **Then** the returned path SHALL end with `data/runtime_state.yaml` and its parent SHALL equal the
  directory `<config_dir>/data` where `<config_dir>` is the parent of the config file found by `_find_config()`

---

### Requirement: load-runtime-state-existing-file

The system SHALL read and parse a YAML file when `load_runtime_state()` is called and the
runtime state file exists with valid YAML content.

#### Scenario: load-existing-valid-yaml

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** a runtime state file exists at `_runtime_state_path()` with valid YAML content
  `{"active_target": "zsiga", "pending_switch": null}`
- **When** `load_runtime_state()` is called
- **Then** it SHALL return a dict matching the YAML content

---

### Requirement: load-runtime-state-missing-file

The system SHALL return an empty dict when `load_runtime_state()` is called and the runtime
state file does not exist.

#### Scenario: load-missing-file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** no runtime state file exists at `_runtime_state_path()`
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

---

### Requirement: load-runtime-state-corrupted-yaml

The system SHALL return an empty dict when `load_runtime_state()` is called and the runtime
state file contains corrupted/unparseable YAML, without raising an exception.

#### Scenario: load-corrupted-yaml

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** a runtime state file exists at `_runtime_state_path()` with content `": invalid: [yaml"`
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}` without raising any exception

---

### Requirement: load-runtime-state-empty-file

The system SHALL return an empty dict when `load_runtime_state()` is called and the runtime
state file is empty (0 bytes).

#### Scenario: load-empty-file

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** a runtime state file exists at `_runtime_state_path()` with empty content
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

---

### Requirement: save-runtime-state-writes-yaml

The system SHALL write a valid YAML file when `save_runtime_state()` is called with a dict,
creating parent directories as needed.

#### Scenario: save-creates-file-and-dirs

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** the `_runtime_state_path()` points to a path whose parent directory does not exist
- **When** `save_runtime_state({"active_target": "factory", "counter": 42})` is called
- **Then** the parent directory SHALL be created, and the file SHALL exist containing valid YAML
  that round-trips to the same dict

---

### Requirement: save-runtime-state-round-trip

The system SHALL preserve data through a save→load round-trip, including unicode and nested
structures.

#### Scenario: save-load-round-trip

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** a writable runtime state path
- **When** `save_runtime_state({"active": "zsiga", "tags": ["evolution", "测试"], "nested": {"k": 1}})`
  is called, followed by `load_runtime_state()`
- **Then** the loaded dict SHALL equal the saved dict

---

### Requirement: test-file-nonconflict

The new test file `tests/test_config.py` SHALL NOT re-export or re-test symbols already covered
by `tests/test_config_validation.py` in a way that creates import conflicts or fixture name
collisions.

#### Scenario: no-fixture-name-collision

- **testable**: false
- **Given** the existing `tests/test_config_validation.py` defines fixtures `_make_config`
- **When** the new `tests/test_config.py` is loaded by pytest
- **Then** no fixture name defined in the new file SHALL shadow a fixture from the existing file
  (verified by manual review; no mechanical check exists for this invariant)

---

### Requirement: test-file-minimal-structure

The new file `tests/test_config.py` SHALL contain at least 3 `def test_` functions that pass
when executed with `python -m pytest tests/test_config.py`.

#### Scenario: file-exists-and-passes

- **testable**: true
- **target**: tests/test_config.py
- **Given** the file `tests/test_config.py` exists on disk
- **When** `python -m pytest tests/test_config.py` is executed
- **Then** the exit code SHALL be 0 and the number of collected test items SHALL be ≥ 3

