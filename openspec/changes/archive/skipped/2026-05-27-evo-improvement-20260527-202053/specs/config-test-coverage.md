# config-test-coverage

## ADDED Requirements

### Requirement: config-differentiated-test-file

A test file `tests/test_config.py` SHALL exist and contain differentiated unit
tests for `zsiga/config.py` public functions. Tests MUST NOT semantically
duplicate the 52 existing tests in `tests/test_config_validation.py`,
`tests/test_spec_evo_improvement_20260527_125207__config_unit_coverage.py`, and
`tests/test_spec_evo_improvement_20260527_125207__config_load_robustness.py`.

The file SHALL contain at least 3 `def test_` functions, including functions
named `test__find_config`, `test__resolve_env_vars`, and `test_validate_config`.
All tests MUST pass with pytest exit code 0 and have zero ruff lint errors.

#### Scenario: test-config-file-exists

- **testable**: true
- **target**: tests/test_config.py
- **Given** the project test directory
- **When** checking for the file `tests/test_config.py`
- **Then** the file SHALL exist on disk

#### Scenario: test-config-file-has-required-function-names

- **testable**: true
- **target**: tests/test_config.py
- **Given** the file `tests/test_config.py`
- **When** parsing the file's function definitions via AST
- **Then** the file SHALL contain function definitions named
  `test__find_config`, `test__resolve_env_vars`, and `test_validate_config`

#### Scenario: test-config-file-has-minimum-test-count

- **testable**: true
- **target**: tests/test_config.py
- **Given** the file `tests/test_config.py`
- **When** counting all `def test_` function definitions (including inside classes)
- **Then** the count SHALL be at least 3

#### Scenario: test-config-file-all-tests-pass

- **testable**: true
- **target**: tests/test_config.py
- **Given** the file `tests/test_config.py` and a working pytest environment
- **When** running `python -m pytest tests/test_config.py -x`
- **Then** the exit code SHALL be 0

#### Scenario: test-config-file-no-lint-errors

- **testable**: true
- **target**: tests/test_config.py
- **Given** the file `tests/test_config.py`
- **When** running `ruff check tests/test_config.py`
- **Then** the exit code SHALL be 0 and no errors SHALL be reported

#### Scenario: test-config-tests-have-real-assertions

- **testable**: true
- **target**: tests/test_config.py
- **Given** the file `tests/test_config.py`
- **When** inspecting each `def test_` function body via AST analysis
- **Then** every test function SHALL contain at least one `assert` statement
  or `pytest.raises` context manager (no `pass`-only or `assert True` bodies)

### Requirement: config-gap-find-config-home-fallback

The `test__find_config` function in `tests/test_config.py` SHALL test the
scenario where `zsiga.yaml` is NOT found in the current working directory but
IS found in `~/.zsiga/zsiga.yaml`. This gap exists because existing tests only
cover the cwd path and the FileNotFoundError case — the home-directory fallback
path at `Path.home() / ".zsiga" / "zsiga.yaml"` has zero coverage.

#### Scenario: find-config-home-fallback-tested

- **testable**: false
- **Given** the `test__find_config` function in `tests/test_config.py`
- **When** reviewing its test body
- **Then** it SHALL contain at least one test case where `_find_config()` returns
  `Path.home() / ".zsiga" / "zsiga.yaml"` after failing to find the file in cwd,
  using monkeypatch to control both `Path.home()` and `os.getcwd()`

### Requirement: config-gap-resolve-env-vars-edge-cases

The `test__resolve_env_vars` function in `tests/test_config.py` SHALL test edge
cases not covered by the existing 6 tests for `_resolve_env_vars`. Specifically:
(1) `None` input SHALL pass through as `None`; (2) a string containing `${VAR}`
embedded in other text (e.g., `"prefix${VAR}suffix"`) SHALL pass through unchanged
because the function only matches strings that both start with `${` AND end with `}`.

#### Scenario: resolve-env-vars-none-input

- **testable**: false
- **Given** the `test__resolve_env_vars` function in `tests/test_config.py`
- **When** reviewing its test body
- **Then** it SHALL assert that `_resolve_env_vars(None)` returns `None`

#### Scenario: resolve-env-vars-partial-pattern

- **testable**: false
- **Given** the `test__resolve_env_vars` function in `tests/test_config.py`
- **When** reviewing its test body
- **Then** it SHALL assert that `_resolve_env_vars("prefix${VAR}suffix")` returns
  `"prefix${VAR}suffix"` unchanged (not resolving the embedded variable)

### Requirement: config-gap-validate-config-accumulation

The `test_validate_config` function in `tests/test_config.py` SHALL test that
`validate_config` correctly accumulates multiple errors and warnings
simultaneously. Existing tests check each validation rule in isolation; no test
verifies that a config with multiple problems produces a `ValidationResult`
containing all applicable errors and warnings together.

#### Scenario: validate-config-multiple-errors-accumulated

- **testable**: false
- **Given** the `test_validate_config` function in `tests/test_config.py`
- **When** reviewing its test body
- **Then** it SHALL assert that calling `validate_config` with a config that has
  multiple errors (e.g., missing provider AND empty targets AND invalid transport)
  produces a `ValidationResult` with `valid == False` and at least 3 errors in
  the `errors` list

#### Scenario: validate-config-mixed-errors-and-warnings

- **testable**: false
- **Given** the `test_validate_config` function in `tests/test_config.py`
- **When** reviewing its test body
- **Then** it SHALL assert that `validate_config` can return a result with both
  non-empty `errors` and non-empty `warnings` simultaneously (e.g., missing api_key
  produces an error while temperature=5.0 produces a warning)

### Requirement: config-gap-validate-config-boundaries

The `test_validate_config` function SHALL test boundary values for numeric range
checks. Existing tests use 0 or extreme values but do not test the exact boundary
values (0.0 and 2.0 for temperature, 1 and 20 for fix_attempts).

#### Scenario: validate-config-temperature-boundary-in-range

- **testable**: false
- **Given** the `test_validate_config` function in `tests/test_config.py`
- **When** reviewing its test body
- **Then** it SHALL assert that `validate_config` with `temperature=0.0` and
  `temperature=2.0` produces no temperature-related warning (both are in range)

#### Scenario: validate-config-fix-attempts-upper-boundary

- **testable**: false
- **Given** the `test_validate_config` function in `tests/test_config.py`
- **When** reviewing its test body
- **Then** it SHALL assert that `validate_config` with `fix_attempts=20` produces
  no fix_attempts warning (boundary is inclusive [1, 20]),
  and `fix_attempts=21` DOES produce a warning

### Requirement: config-gap-load-config-section-parsing

The new tests in `tests/test_config.py` SHALL cover `load_config` parsing of
sections not tested by existing files. Existing tests cover: validation error
handling, warning printing, basic LLM config, LLMFastConfig, and error cases.
The following sections have zero integration test coverage:

- **SSH target**: a target with `transport: ssh` and full `ssh:` subsection
  SHALL be parsed into a `TargetConfig` with a non-None `SSHConfig`
- **Logging section**: the `logging:` section SHALL populate `LoggingConfig`
  with `level`, `format`, and `file` fields
- **Budget profiles**: custom `budget_profiles` SHALL override defaults
- **Compaction config**: custom `compaction:` subsection SHALL override defaults

#### Scenario: load-config-ssh-target-parsed

- **testable**: false
- **Given** the `tests/test_config.py` test file
- **When** reviewing test bodies that call `load_config`
- **Then** at least one test SHALL provide a YAML config with an SSH target
  (including `ssh.host`, `ssh.user`, `ssh.port`) and assert that the resulting
  `ZsigaConfig.targets` entry has a non-None `ssh` attribute with correct values

#### Scenario: load-config-logging-section-parsed

- **testable**: false
- **Given** the `tests/test_config.py` test file
- **When** reviewing test bodies that call `load_config`
- **Then** at least one test SHALL provide a YAML config with a `logging:` section
  containing `level: DEBUG`, `format: json`, and `file: /tmp/zsiga.log`,
  and assert that `config.logging_config.level == "DEBUG"`,
  `config.logging_config.fmt == "json"`, and `config.logging_config.file == "/tmp/zsiga.log"`

#### Scenario: load-config-budget-profiles-override

- **testable**: false
- **Given** the `tests/test_config.py` test file
- **When** reviewing test bodies that call `load_config`
- **Then** at least one test SHALL provide custom `budget_profiles` in the YAML
  and assert that `config.pipeline.budget_profiles` contains the custom values
  while retaining defaults for keys not overridden
