# runner-harness-core

## ADDED Requirements

### Requirement: HarnessRunner constructor stores fixtures parameter

`HarnessRunner.__init__` SHALL accept an optional `fixtures` parameter and
store it as `_fixtures`. When omitted, `_fixtures` SHALL default to an empty
list. The runner SHALL initialize an empty `_test_files` list and a fresh
`HarnessResult` as `_result`.

#### Scenario: HarnessRunner stores provided fixtures

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** `HarnessRunner(fixtures=[1, 2, 3])`
- **When** `runner._fixtures` is accessed
- **Then** it equals `[1, 2, 3]`

#### Scenario: HarnessRunner defaults fixtures to empty list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__
- **Given** `HarnessRunner()` with no arguments
- **When** `runner._fixtures` is accessed
- **Then** it equals `[]`

### Requirement: HarnessRunner discover finds and sorts test files

`HarnessRunner.discover` SHALL find all files matching `test_*.py` in the
given directory, store them internally, and return them in sorted order.
If the directory does not exist, it SHALL raise `FileNotFoundError`.

#### Scenario: discover returns sorted file list

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.discover
- **Given** a temporary directory containing `test_zeta.py`, `test_alpha.py`, `test_mid.py`
- **When** `runner.discover(directory)` is called
- **Then** the returned list is `[test_alpha.py, test_mid.py, test_zeta.py]` (sorted alphabetically)

#### Scenario: discover raises FileNotFoundError for missing directory

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.discover
- **Given** a path to a non-existent directory
- **When** `runner.discover(path)` is called
- **Then** `FileNotFoundError` is raised

### Requirement: HarnessRunner _run_file handles unloadable modules

`HarnessRunner._run_file` SHALL handle files that cannot be loaded as Python
modules by recording a `TestError` event and incrementing `result.errors`
without propagating the exception.

#### Scenario: _run_file records TestError for invalid module

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file
- **Given** a file containing invalid Python syntax and a `HarnessRunner` with a fresh `HarnessResult`
- **When** `_run_file` is called with the invalid file path
- **Then** `result.errors >= 1` and at least one `TestError` event exists in `result.events`

### Requirement: HarnessRunner run returns HarnessResult

`HarnessRunner.run` SHALL execute every discovered test file and return a
`HarnessResult` with `total` matching the number of discovered files.

#### Scenario: run returns HarnessResult with total matching discovered files

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.run
- **Given** a temporary directory with 2 valid test files
- **When** `runner.discover(directory)` then `runner.run()` are called
- **Then** the returned `HarnessResult.total == 2`

### Requirement: HarnessRunner results property

`HarnessRunner.results` SHALL return the most recent `HarnessResult`.

#### Scenario: results property returns current HarnessResult

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.results
- **Given** a freshly constructed `HarnessRunner`
- **When** `runner.results` is accessed
- **Then** it returns a `HarnessResult` instance with default values
