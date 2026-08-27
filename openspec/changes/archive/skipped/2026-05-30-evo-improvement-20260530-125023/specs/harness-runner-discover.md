# harness-runner-discover

## ADDED Requirements

### Requirement: HarnessRunner.discover Test File Discovery

The test file `tests/test_runner.py` SHALL contain unit tests for
`HarnessRunner.discover()` that verify file discovery, empty-directory handling,
and error raising for nonexistent directories, using `tmp_path` for filesystem
isolation.

#### Scenario: Discover finds only files matching test_*.py

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.discover

- **Given** a temporary directory containing `test_alpha.py`, `test_beta.py`, and `helper.py`
- **When** `HarnessRunner().discover(directory)` is called
- **Then** the returned list contains `test_alpha.py` and `test_beta.py` but not `helper.py`

#### Scenario: Discover returns empty list for empty directory

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.discover

- **Given** an empty temporary directory
- **When** `HarnessRunner().discover(directory)` is called
- **Then** the returned list is `[]`

#### Scenario: Discover raises FileNotFoundError for nonexistent directory

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.discover

- **Given** a path that does not exist on the filesystem
- **When** `HarnessRunner().discover(nonexistent_path)` is called
- **Then** `FileNotFoundError` is raised

#### Scenario: Discover returns sorted results

- **testable**: true
- **target**: zsiga/harness/runner.py::HarnessRunner.discover

- **Given** a temporary directory containing `test_z.py`, `test_a.py`, `test_m.py`
- **When** `HarnessRunner().discover(directory)` is called
- **Then** the returned list is sorted alphabetically by filename
