# harness-runner-boundaries

## ADDED Requirements

### Requirement: HarnessRunner._run_file emits TestError for unloadable modules

When `spec.loader.exec_module` raises any exception during module loading,
`_run_file` SHALL append a `TestError` event to the result and increment
`errors` by 1. The `error_message` SHALL contain the traceback text.

#### Scenario: Module with import error produces TestError event

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file

- **Given** a `HarnessRunner` with `_test_files` containing a Python file
  whose body is `import nonexistent_xyz_module_999`
- **When** `run()` is called
- **Then** the result SHALL have `errors >= 1` and at least one `TestError`
  event whose `error_message` is non-empty

### Requirement: HarnessRunner._run_file handles null spec gracefully

When `importlib.util.spec_from_file_location` returns `None` or a spec with
`loader=None`, `_run_file` SHALL emit a `TestError` and increment `errors`.
This path ensures robustness against non-loadable file types.

#### Scenario: Non-Python-file path produces TestError

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file

- **Given** a `HarnessRunner` with `_test_files` containing a path whose
  content is binary garbage (not valid Python)
- **When** `run()` is called
- **Then** the result SHALL have `errors >= 1`

### Requirement: HarnessRunner constructor stores fixtures parameter

`HarnessRunner.__init__` SHALL accept an optional `fixtures` parameter (list
or None). When `None` or omitted, `_fixtures` SHALL default to an empty list.
When a list is provided, `_fixtures` SHALL store it.

#### Scenario: Default fixtures is empty list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__

- **Given** `HarnessRunner()` is constructed with no arguments
- **When** `runner._fixtures` is inspected
- **Then** it SHALL equal `[]`

#### Scenario: Provided fixtures are stored

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__

- **Given** `HarnessRunner(fixtures=["a", "b"])` is constructed
- **When** `runner._fixtures` is inspected
- **Then** it SHALL equal `["a", "b"]`
