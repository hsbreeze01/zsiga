# Spec: Config Unit Coverage

## ADDED Requirements

### Requirement: _find_config path resolution

The test suite SHALL verify that `_find_config()` resolves configuration file paths
according to the documented priority order: first `zsiga.yaml` in the current working
directory, then `~/.zsiga/zsiga.yaml`. When neither candidate exists, it MUST raise
`FileNotFoundError`.

#### Scenario: find config in current directory

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** a temporary directory containing a file named `zsiga.yaml` as the current working directory
- **When** `_find_config()` is called
- **Then** the returned Path SHALL equal `Path("zsiga.yaml")`

#### Scenario: raise FileNotFoundError when no config exists

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** neither `zsiga.yaml` nor `~/.zsiga/zsiga.yaml` exists (cwd is a temp dir and home fallback is absent)
- **When** `_find_config()` is called
- **Then** it SHALL raise `FileNotFoundError`

---

### Requirement: _resolve_env_vars substitution

The test suite SHALL verify that `_resolve_env_vars()` correctly resolves `${VAR}`
placeholders, recurses into nested dicts and lists, and returns non-string values
unchanged.

#### Scenario: resolve single env var placeholder

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `MY_KEY` is set to `"secret123"`
- **When** `_resolve_env_vars("${MY_KEY}")` is called
- **Then** the result SHALL equal `"secret123"`

#### Scenario: fallback to empty string for unset env var

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `UNSET_VAR_XYZ` is not set
- **When** `_resolve_env_vars("${UNSET_VAR_XYZ}")` is called
- **Then** the result SHALL equal `""`

#### Scenario: recurse through dict values

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `HOST` is set to `"example.com"`
- **When** `_resolve_env_vars({"key": "${HOST}", "other": "plain"})` is called
- **Then** the result SHALL equal `{"key": "example.com", "other": "plain"}`

#### Scenario: recurse through list values

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** environment variable `ITEM` is set to `"resolved"`
- **When** `_resolve_env_vars(["${ITEM}", 42])` is called
- **Then** the result SHALL equal `["resolved", 42]`

#### Scenario: pass through non-placeholder strings unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** no special environment
- **When** `_resolve_env_vars("plain_string")` is called
- **Then** the result SHALL equal `"plain_string"`

#### Scenario: pass through non-string values unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** no special environment
- **When** `_resolve_env_vars(42)` is called
- **Then** the result SHALL equal `42`

---

### Requirement: _runtime_state_path computation

The test suite SHALL verify that `_runtime_state_path()` resolves based on
`ZSIGA_HOME` environment variable or falls back to the config file's parent
directory.

#### Scenario: use ZSIGA_HOME when set

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** environment variable `ZSIGA_HOME` is set to `"/tmp/zsiga_home"`
- **When** `_runtime_state_path()` is called
- **Then** the result SHALL equal `Path("/tmp/zsiga_home") / "data" / "runtime_state.yaml"`

#### Scenario: fallback to config parent directory when ZSIGA_HOME unset

- **testable**: true
- **target**: zsiga/config.py::_runtime_state_path
- **Given** `ZSIGA_HOME` is not set and a `zsiga.yaml` exists in the current working directory
- **When** `_runtime_state_path()` is called
- **Then** the result SHALL equal the parent directory of the found config joined with `"data" / "runtime_state.yaml"`

---

### Requirement: load_runtime_state and save_runtime_state round-trip

The test suite SHALL verify that `save_runtime_state` persists state to disk and
`load_runtime_state` reads it back faithfully. When the state file does not exist,
`load_runtime_state` MUST return an empty dict. When the file contains invalid YAML,
`load_runtime_state` MUST return an empty dict without raising.

#### Scenario: round-trip save and load

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** a temporary directory used as the runtime state location (via ZSIGA_HOME)
- **When** `save_runtime_state({"active_target": "myproj", "count": 3})` is called, then `load_runtime_state()` is called
- **Then** the loaded dict SHALL equal `{"active_target": "myproj", "count": 3}`

#### Scenario: return empty dict when state file missing

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** no runtime state file exists at the computed path
- **When** `load_runtime_state()` is called
- **Then** the result SHALL equal `{}`

#### Scenario: return empty dict for corrupted YAML

- **testable**: true
- **target**: zsiga/config.py::load_runtime_state
- **Given** the runtime state file exists but contains invalid YAML content `": [invalid"`
- **When** `load_runtime_state()` is called
- **Then** the result SHALL equal `{}`

---

### Requirement: validate_config edge cases

The test suite SHALL verify edge cases of `validate_config()` that are NOT covered by
`tests/test_config_validation.py`. These include: empty targets dict, invalid transport
value, SSH transport without SSH config, temperature out-of-range warning, max_tokens
non-positive warning, and invalid domain warning.

#### Scenario: error when targets dict is empty

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with valid LLM fields and an empty `targets` dict
- **When** `validate_config(config)` is called
- **Then** the `ValidationResult.errors` list SHALL contain the string `"at least one target is required"`

#### Scenario: error for invalid transport value

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `transport` is `"ftp"`
- **When** `validate_config(config)` is called
- **Then** the `ValidationResult.errors` list SHALL contain a string including `"transport must be 'local' or 'ssh'"`

#### Scenario: error for ssh transport with missing ssh host

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `transport` is `"ssh"` and `ssh` is `None`
- **When** `validate_config(config)` is called
- **Then** the `ValidationResult.errors` list SHALL contain a string including `"SSH transport requires ssh config"`

#### Scenario: warning for temperature outside recommended range

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `llm.temperature` set to `3.0`
- **When** `validate_config(config)` is called
- **Then** the `ValidationResult.warnings` list SHALL contain a string including `"temperature"` and `"outside the recommended range"`

#### Scenario: warning for non-positive max_tokens

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with `llm.max_tokens` set to `0`
- **When** `validate_config(config)` is called
- **Then** the `ValidationResult.warnings` list SHALL contain `"llm.max_tokens should be a positive integer"`

#### Scenario: warning for invalid domain value

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a `ZsigaConfig` with a target whose `domain` is `"invalid"`
- **When** `validate_config(config)` is called
- **Then** the `ValidationResult.warnings` list SHALL contain a string including `"domain should be 'self' or 'external'"`

---

### Requirement: config dataclass constructor defaults

The test suite SHALL verify that `SSHConfig`, `TargetConfig`, `LLMConfig`, `LLMFastConfig`,
`CompactionConfig`, `SafetyConfig`, `GithubConfig`, and `LoggingConfig` constructors
assign correct default values and accept explicit parameter overrides.

#### Scenario: SSHConfig defaults

- **testable**: true
- **target**: zsiga/config.py::SSHConfig.__init__
- **Given** no special conditions
- **When** `SSHConfig(host="myhost")` is constructed
- **Then** `user` SHALL be `None`, `port` SHALL be `22`, `key_path` SHALL be `None`

#### Scenario: TargetConfig defaults

- **testable**: true
- **target**: zsiga/config.py::TargetConfig.__init__
- **Given** no special conditions
- **When** `TargetConfig(name="t", path="/tmp")` is constructed
- **Then** `transport` SHALL be `"local"`, `deploy_branch` SHALL be `"main"`, `merge_to_branches` SHALL equal `[]`, `tech_stack` SHALL equal `[]`

#### Scenario: LLMConfig explicit parameters

- **testable**: true
- **target**: zsiga/config.py::LLMConfig.__init__
- **Given** no special conditions
- **When** `LLMConfig(provider="openai", model="gpt-4", api_key="k", temperature=0.7)` is constructed
- **Then** `temperature` SHALL be `0.7`, `max_tokens` SHALL be `4096`, `base_url` SHALL be `None`

#### Scenario: LLMFastConfig defaults

- **testable**: true
- **target**: zsiga/config.py::LLMFastConfig.__init__
- **Given** no special conditions
- **When** `LLMFastConfig(api_key="fast")` is constructed
- **Then** `model` SHALL be `"glm-4-flash"`, `base_url` SHALL be `"https://open.bigmodel.cn/api/paas/v4"`

#### Scenario: CompactionConfig defaults

- **testable**: true
- **target**: zsiga/config.py::CompactionConfig.__init__
- **Given** no special conditions
- **When** `CompactionConfig()` is constructed
- **Then** `enabled` SHALL be `True`, `threshold_chars` SHALL be `30000`, `keep_recent` SHALL be `3`

#### Scenario: SafetyConfig defaults

- **testable**: true
- **target**: zsiga/config.py::SafetyConfig.__init__
- **Given** no special conditions
- **When** `SafetyConfig()` is constructed
- **Then** `require_approval` SHALL be `True`, `max_files_per_task` SHALL be `3`, `dry_run` SHALL be `False`

#### Scenario: GithubConfig defaults

- **testable**: true
- **target**: zsiga/config.py::GithubConfig.__init__
- **Given** no special conditions
- **When** `GithubConfig()` is constructed
- **Then** `token` SHALL be `""`, `issue_integration` SHALL be `False`

#### Scenario: LoggingConfig defaults and upper-case normalization

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig.__init__
- **Given** no special conditions
- **When** `LoggingConfig()` is constructed
- **Then** `level` SHALL be `"INFO"`, `fmt` SHALL be `"text"`, `file` SHALL be `None`

#### Scenario: LoggingConfig level normalization to upper case

- **testable**: true
- **target**: zsiga/config.py::LoggingConfig.__init__
- **Given** no special conditions
- **When** `LoggingConfig(level="debug")` is constructed
- **Then** `level` SHALL be `"DEBUG"`

---

### Requirement: test file isolation and compatibility

The new test file `tests/test_config.py` SHALL coexist with `tests/test_config_validation.py`
without fixture pollution or naming conflicts. All tests in both files SHALL pass when
run together.

#### Scenario: both test files pass together

- **testable**: true
- **target**: tests/test_config.py
- **Given** `tests/test_config.py` exists with sufficient test functions and `tests/test_config_validation.py` exists
- **When** `python -m pytest tests/test_config.py tests/test_config_validation.py` is executed
- **Then** the exit code SHALL be 0

#### Scenario: new test file has sufficient coverage

- **testable**: true
- **target**: tests/test_config.py
- **Given** `tests/test_config.py` exists
- **When** the file is scanned for `def test_` function definitions
- **Then** there SHALL be at least 8 such functions
