# Spec: config-utility-functions

Coverage for low-level utility functions in `zsiga/config.py` that are
currently untested: `_find_config`, `_resolve_env_vars`, `_runtime_state_path`,
`load_runtime_state`, `save_runtime_state`.

## ADDED Requirements

### Requirement: _find_config returns first existing candidate path

`_find_config()` SHALL scan candidate paths in order (`zsiga.yaml` in CWD,
then `~/.zsiga/zsiga.yaml`) and return the first one that exists as a `Path`.

#### Scenario: finds config in current working directory

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** a temporary directory containing a file named `zsiga.yaml`
- **When** `_find_config()` is called with the current working directory set to that directory
- **Then** it SHALL return a `Path` pointing to `<tmpdir>/zsiga.yaml`

#### Scenario: finds config in home dotfile directory

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in the current working directory and `Path.home() / ".zsiga" / "zsiga.yaml"` exists
- **When** `_find_config()` is called
- **Then** it SHALL return a `Path` pointing to `~/.zsiga/zsiga.yaml`

#### Scenario: raises FileNotFoundError when no candidate exists

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` exists in the current working directory or `~/.zsiga/`
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError` with a message containing "zsiga.yaml not found"

---

### Requirement: _resolve_env_vars recursively resolves ${VAR} placeholders

`_resolve_env_vars(value)` SHALL resolve environment variable references
in strings, dicts, and lists. Only the exact pattern `${VAR_NAME}` is
recognised. Unknown variables resolve to an empty string.

#### Scenario: resolves a single env var placeholder

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_KEY` is set to `"secret123"`
- **When** `_resolve_env_vars("${MY_KEY}")` is called
- **Then** it SHALL return `"secret123"`

#### Scenario: returns empty string for unset env var

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `NONEXISTENT_VAR_XYZ` is not set
- **When** `_resolve_env_vars("${NONEXISTENT_VAR_XYZ}")` is called
- **Then** it SHALL return `""`

#### Scenario: passes through plain strings unchanged

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** a plain string `"hello world"` without `${...}` syntax
- **When** `_resolve_env_vars("hello world")` is called
- **Then** it SHALL return `"hello world"`

#### Scenario: recursively resolves dict values

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `DB_HOST` is set to `"localhost"`
- **When** `_resolve_env_vars({"host": "${DB_HOST}", "port": 5432})` is called
- **Then** it SHALL return `{"host": "localhost", "port": 5432}`

#### Scenario: recursively resolves list items

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ITEM` is set to `"resolved"`
- **When** `_resolve_env_vars(["${ITEM}", "plain", 42])` is called
- **Then** it SHALL return `["resolved", "plain", 42]`

#### Scenario: returns non-string non-dict non-list values unchanged

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** an integer value `42`
- **When** `_resolve_env_vars(42)` is called
- **Then** it SHALL return `42`

---

### Requirement: _runtime_state_path respects ZSIGA_HOME and falls back to config parent

`_runtime_state_path()` SHALL return a Path to `data/runtime_state.yaml`
under `ZSIGA_HOME` when that env var is set, otherwise under the parent
directory of the config file.

#### Scenario: uses ZSIGA_HOME when set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/zsiga_home_test`
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `Path("/tmp/zsiga_home_test") / "data" / "runtime_state.yaml"`

#### Scenario: falls back to config parent when ZSIGA_HOME is not set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** `ZSIGA_HOME` is not set and a `zsiga.yaml` exists in CWD
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return a Path ending with `data/runtime_state.yaml` whose parent directory is the same as the config file's parent

---

### Requirement: load_runtime_state reads YAML or returns empty dict

`load_runtime_state()` SHALL return the parsed YAML content of the
runtime state file if it exists and is valid, or an empty dict otherwise.

#### Scenario: returns parsed dict when file exists and is valid YAML

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** a runtime state file containing `active_target: myproject\n`
- **When** `load_runtime_state()` is called with that file path
- **Then** it SHALL return `{"active_target": "myproject"}`

#### Scenario: returns empty dict when file does not exist

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** no runtime state file exists
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

#### Scenario: returns empty dict when file contains invalid YAML

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::load_runtime_state
- **Given** a runtime state file containing invalid YAML content
- **When** `load_runtime_state()` is called
- **Then** it SHALL return `{}`

---

### Requirement: save_runtime_state writes YAML and creates parent directories

`save_runtime_state(state)` SHALL serialize the given dict to YAML and
write it to the runtime state file, creating parent directories as needed.

#### Scenario: writes state dict as YAML

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** a dict `{"active_target": "proj-a"}`
- **When** `save_runtime_state({"active_target": "proj-a"})` is called
- **Then** the runtime state file SHALL contain valid YAML with key `active_target` equal to `"proj-a"`

#### Scenario: creates parent directories if missing

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::save_runtime_state
- **Given** the runtime state file's parent directory does not exist
- **When** `save_runtime_state({"key": "val"})` is called
- **Then** the parent directory SHALL be created and the file SHALL exist

