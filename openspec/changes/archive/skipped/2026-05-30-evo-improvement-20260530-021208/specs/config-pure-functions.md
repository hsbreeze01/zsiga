# config-pure-functions

## ADDED Requirements

### Requirement: _find_config returns first existing candidate

`_find_config()` SHALL search two candidate paths in order: `Path("zsiga.yaml")`
and `Path.home() / ".zsiga" / "zsiga.yaml"`. It SHALL return the first candidate
that exists. If none exists, it SHALL raise `FileNotFoundError`.

#### Scenario: config file found in current directory

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** a temporary directory containing a file named `zsiga.yaml`
- **When** `_find_config()` is called with the current working directory set to that temporary directory
- **Then** it SHALL return `Path("zsiga.yaml")`

#### Scenario: config file found in home fallback directory

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in the current directory, but a file at `~/.zsiga/zsiga.yaml`
- **When** `_find_config()` is called
- **Then** it SHALL return `Path.home() / ".zsiga" / "zsiga.yaml"`

#### Scenario: no config file found anywhere

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** no `zsiga.yaml` in the current directory or `~/.zsiga/`
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError`

### Requirement: _resolve_env_vars interpolates environment variables

`_resolve_env_vars(value)` SHALL recursively resolve `${ENV_VAR}` patterns
in strings, dicts, and lists. For a plain `${VAR}` string, it SHALL return
`os.environ.get(VAR, "")`. Non-matching values SHALL be returned unchanged.

#### Scenario: simple env var string resolved

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_TEST_KEY` is set to `"secret123"`
- **When** `_resolve_env_vars("${MY_TEST_KEY}")` is called
- **Then** it SHALL return `"secret123"`

#### Scenario: unset env var returns empty string

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `NONEXISTENT_VAR_XYZ` is not set
- **When** `_resolve_env_vars("${NONEXISTENT_VAR_XYZ}")` is called
- **Then** it SHALL return `""`

#### Scenario: non-env-var string returned unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** any plain string that does not match `${...}` pattern
- **When** `_resolve_env_vars("just_a_string")` is called
- **Then** it SHALL return `"just_a_string"` unchanged

#### Scenario: dict values resolved recursively

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_DICT_KEY` is set to `"resolved_val"`
- **When** `_resolve_env_vars({"key": "${MY_DICT_KEY}", "plain": 42})` is called
- **Then** it SHALL return `{"key": "resolved_val", "plain": 42}`

#### Scenario: list values resolved recursively

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `LIST_VAR` is set to `"item_val"`
- **When** `_resolve_env_vars(["${LIST_VAR}", 100])` is called
- **Then** it SHALL return `["item_val", 100]`

#### Scenario: non-string non-dict non-list value returned unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** an integer value `42`
- **When** `_resolve_env_vars(42)` is called
- **Then** it SHALL return `42`

### Requirement: _runtime_state_path resolves state file location

`_runtime_state_path()` SHALL return the path to `data/runtime_state.yaml`
relative to either `ZSIGA_HOME` environment variable (if set) or the parent
directory of the config file found by `_find_config()`.

#### Scenario: ZSIGA_HOME env var set

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `/tmp/zsiga_home_test`
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `Path("/tmp/zsiga_home_test") / "data" / "runtime_state.yaml"`

#### Scenario: ZSIGA_HOME not set falls back to config parent

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** `ZSIGA_HOME` is not set and a `zsiga.yaml` exists in the current directory
- **When** `_runtime_state_path()` is called
- **Then** it SHALL return `Path("zsiga.yaml").parent / "data" / "runtime_state.yaml"`
