# config-utility-functions.md

## ADDED Requirements

### Requirement: `_find_config` SHALL search a prioritized list of candidate paths

The `_find_config` function SHALL iterate over a fixed list of candidate paths
(in order: `zsiga.yaml` in the current working directory, then `~/.zsiga/zsiga.yaml`).
It SHALL return the first existing path as a `Path` object. If no candidate exists,
it SHALL raise `FileNotFoundError`.

#### Scenario: returns first existing candidate

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** a temporary directory containing a file named `zsiga.yaml`
- **When** `_find_config` is called with the current working directory mocked to that directory
- **Then** it SHALL return a `Path` pointing to that `zsiga.yaml` file

#### Scenario: falls back to home directory candidate

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in the current directory and a `zsiga.yaml` exists at `~/.zsiga/zsiga.yaml`
- **When** `_find_config` is called
- **Then** it SHALL return a `Path` pointing to `~/.zsiga/zsiga.yaml`

#### Scenario: raises FileNotFoundError when no candidate exists

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in the current directory or `~/.zsiga/`
- **When** `_find_config` is called
- **Then** it SHALL raise `FileNotFoundError` with a message containing "zsiga.yaml"

---

### Requirement: `_resolve_env_vars` SHALL substitute `${VAR}` placeholders with environment variable values

The `_resolve_env_vars` function SHALL recursively walk strings, dicts, and lists.
For a string matching the pattern `${VAR}`, it SHALL replace it with `os.environ.get(VAR, "")`.
Non-matching strings and non-string scalars SHALL pass through unchanged.

#### Scenario: resolves a simple env var placeholder

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_KEY` is set to `"secret123"`
- **When** `_resolve_env_vars("${MY_KEY}")` is called
- **Then** it SHALL return `"secret123"`

#### Scenario: returns empty string for unset env var

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `UNSET_VAR_XYZ` is not set
- **When** `_resolve_env_vars("${UNSET_VAR_XYZ}")` is called
- **Then** it SHALL return `""`

#### Scenario: passes through plain string unchanged

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **When** `_resolve_env_vars("hello")` is called
- **Then** it SHALL return `"hello"`

#### Scenario: passes through non-string scalar unchanged

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **When** `_resolve_env_vars(42)` is called
- **Then** it SHALL return `42`

#### Scenario: resolves env vars inside dict values

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `DB_PASS` is set to `"pw"`
- **When** `_resolve_env_vars({"key": "${DB_PASS}", "num": 10})` is called
- **Then** it SHALL return `{"key": "pw", "num": 10}`

#### Scenario: resolves env vars inside list values

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ITEM` is set to `"resolved"`
- **When** `_resolve_env_vars(["${ITEM}", 42, "plain"])` is called
- **Then** it SHALL return `["resolved", 42, "plain"]`

---

### Requirement: `_runtime_state_path` SHALL determine the runtime state file location

The `_runtime_state_path` function SHALL return a `Path` to `data/runtime_state.yaml`.
If the `ZSIGA_HOME` environment variable is set, the path SHALL be `$ZSIGA_HOME/data/runtime_state.yaml`.
Otherwise, the path SHALL be relative to the parent of the resolved config file location.

#### Scenario: uses ZSIGA_HOME when set

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/zsiga_home`
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `Path("/tmp/zsiga_home/data/runtime_state.yaml")`

#### Scenario: falls back to config parent directory

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/config.py::_runtime_state_path
- **Given** `ZSIGA_HOME` is not set and a `zsiga.yaml` exists in the current directory
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return a `Path` ending with `data/runtime_state.yaml` whose parent's parent is the directory containing `zsiga.yaml`

