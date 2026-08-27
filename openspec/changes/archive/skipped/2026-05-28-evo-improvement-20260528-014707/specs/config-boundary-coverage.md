# config-boundary-coverage

> Delta spec for change `evo-improvement-20260528-014707`
> Supplements existing tests by covering boundary scenarios not exercised by
> `test_config_validation.py`, `test_spec_evo_..._config_unit_coverage.py`, or
> `test_spec_evo_..._config_load_robustness.py`.

---

## ADDED Requirements

### Requirement: _find_config home directory fallback and priority

`_find_config()` SHALL search candidates in priority order: first `zsiga.yaml` in
the current working directory, then `~/.zsiga/zsiga.yaml`. It SHALL return the
first existing candidate. This supplements existing tests that only cover the
cwd-found and not-found scenarios.

#### Scenario: Finds config in home directory when absent from cwd

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** current working directory has no `zsiga.yaml` AND `~/.zsiga/zsiga.yaml` exists
- **When** `_find_config()` is called
- **Then** it SHALL return a `Path` whose `str` representation contains `.zsiga` and `zsiga.yaml`

#### Scenario: Cwd config takes priority over home config

- **testable**: true
- **target**: zsiga/config.py::_find_config
- **Given** both `zsiga.yaml` in cwd AND `~/.zsiga/zsiga.yaml` exist
- **When** `_find_config()` is called
- **Then** it SHALL return the cwd path (`Path("zsiga.yaml")`), not the home path

---

### Requirement: _resolve_env_vars edge cases for non-typical types

`_resolve_env_vars()` SHALL pass through empty strings, booleans, and `None`
unchanged. These types differ from the already-tested cases (non-empty strings,
ints, dicts, lists).

#### Scenario: Empty string passes through unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** `_resolve_env_vars` is called with `""`
- **When** the result is inspected
- **Then** it SHALL return `""` (empty string, not modified)

#### Scenario: Boolean True passes through unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** `_resolve_env_vars` is called with `True`
- **When** the result is inspected
- **Then** it SHALL return `True` (boolean, not string)

#### Scenario: None passes through unchanged

- **testable**: true
- **target**: zsiga/config.py::_resolve_env_vars
- **Given** `_resolve_env_vars` is called with `None`
- **When** the result is inspected
- **Then** it SHALL return `None` (not string, not error)

---

### Requirement: validate_config domain warning for unrecognized domain value

`validate_config()` SHALL emit a warning (not an error) when a target's `domain`
field is neither `""` nor `"self"` nor `"external"`. The result SHALL still be
valid (no errors). When domain is `"self"` or `""` or `"external"`, no domain
warning SHALL be emitted.

#### Scenario: Invalid domain value produces a warning but no errors

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` with a target whose `domain` is `"production"`
- **When** `validate_config()` is called
- **Then** the result `valid` SHALL be `True` AND `warnings` SHALL contain at least one entry mentioning `"domain"`

#### Scenario: Domain value self produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` with a target whose `domain` is `"self"`
- **When** `validate_config()` is called
- **Then** the result `warnings` SHALL NOT contain any entry mentioning `"domain"`

---

### Requirement: validate_config pipeline parameter boundary warnings

`validate_config()` SHALL emit warnings when `pipeline.fix_attempts` exceeds 20
or when `pipeline.max_changes_per_cycle` is at the boundary value 10 (within range,
no warning). This supplements existing tests that only cover zero values.

#### Scenario: fix_attempts above 20 produces a warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` where `pipeline.fix_attempts` is `25`
- **When** `validate_config()` is called
- **Then** the result `valid` SHALL be `True` AND `warnings` SHALL contain at least one entry mentioning `"fix_attempts"`

#### Scenario: max_changes_per_cycle at boundary value 10 produces no warning

- **testable**: true
- **target**: zsiga/config.py::validate_config
- **Given** a valid `ZsigaConfig` where `pipeline.max_changes_per_cycle` is `10`
- **When** `validate_config()` is called
- **Then** the result `warnings` SHALL NOT contain any entry mentioning `"max_changes_per_cycle"`

---

### Requirement: load_config parses github section

`load_config()` SHALL parse the `github` top-level section from YAML into a
`GithubConfig` object with `token`, `owner`, and `issue_integration` fields.

#### Scenario: load_config parses github section with all fields

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with a `github` section containing `token: "ghp_abc"`, `owner: "myorg"`, `issue_integration: true`
- **When** `load_config()` is called with that file path
- **Then** `config.github` SHALL not be `None`, `config.github.token` SHALL be `"ghp_abc"`, `config.github.owner` SHALL be `"myorg"`, `config.github.issue_integration` SHALL be `True`

---

### Requirement: load_config parses logging section

`load_config()` SHALL parse the `logging` top-level section from YAML into a
`LoggingConfig` object, with `level` normalized to uppercase.

#### Scenario: load_config parses logging section with level normalization

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `logging.level: "debug"`, `logging.format: "json"`, `logging.file: "/tmp/zsiga.log"`
- **When** `load_config()` is called
- **Then** `config.logging_config.level` SHALL be `"DEBUG"` (normalized), `config.logging_config.fmt` SHALL be `"json"`, `config.logging_config.file` SHALL be `"/tmp/zsiga.log"`

---

### Requirement: load_config parses active_target field

`load_config()` SHALL read the `active_target` top-level key from YAML and set it
on the resulting `ZsigaConfig`.

#### Scenario: load_config reads active_target from YAML

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `active_target: "my-project"`
- **When** `load_config()` is called
- **Then** `config.active_target` SHALL be `"my-project"`

---

### Requirement: load_config resolves environment variables in YAML values

`load_config()` SHALL apply `_resolve_env_vars` to the raw parsed YAML before
constructing config objects, so that `${VAR}` placeholders in any string field are
replaced with the environment variable value.

#### Scenario: load_config resolves env var in api_key field

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file where `api_key` is `"${ZSIGA_TEST_LOAD_KEY}"` AND the env var `ZSIGA_TEST_LOAD_KEY` is set to `"resolved-secret"`
- **When** `load_config()` is called
- **Then** `config.llm.api_key` SHALL be `"resolved-secret"`

---

### Requirement: load_config parses safety section

`load_config()` SHALL parse the `safety` top-level section from YAML into a
`SafetyConfig` object.

#### Scenario: load_config parses safety section with non-default values

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `safety.require_approval: false`, `safety.max_files_per_task: 5`, `safety.dry_run: true`
- **When** `load_config()` is called
- **Then** `config.safety.require_approval` SHALL be `False`, `config.safety.max_files_per_task` SHALL be `5`, `config.safety.dry_run` SHALL be `True`

---

### Requirement: load_config parses compaction subsection under pipeline

`load_config()` SHALL parse the `pipeline.compaction` nested section from YAML
into a `CompactionConfig` object attached to the `PipelineConfig`.

#### Scenario: load_config parses pipeline.compaction with custom values

- **testable**: true
- **target**: zsiga/config.py::load_config
- **Given** a YAML config file with `pipeline.compaction.threshold_chars: 50000` and `pipeline.compaction.compaction_ratio: 0.5`
- **When** `load_config()` is called
- **Then** `config.pipeline.compaction.threshold_chars` SHALL be `50000` and `config.pipeline.compaction.compaction_ratio` SHALL be `0.5`
