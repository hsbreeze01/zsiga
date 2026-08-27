# spec-runner-boundaries

## ADDED Requirements

### Requirement: HarnessRunner handles empty test file list

When `HarnessRunner.run()` is called after `discover()` returns an empty list, the resulting `HarnessResult` SHALL have `total=0`, `passed=0`, `failed=0`, `errors=0`, and an empty `events` list.

#### Scenario: run after empty discover returns zeroed HarnessResult

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.run

- **Given** a HarnessRunner that has called `discover()` on an empty directory
- **When** `run()` is called
- **Then** `result.total == 0`, `result.passed == 0`, `result.failed == 0`, `result.errors == 0`, `result.events == []`

---

### Requirement: HarnessRunner isolates test module load failures

When a discovered test file cannot be loaded (e.g., contains a syntax error or missing import), `HarnessRunner._run_file()` SHALL emit a `TestError` event, increment `errors`, and continue processing remaining files.

#### Scenario: _run_file emits TestError for unloadable module

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner._run_file

- **Given** a HarnessRunner and a temp directory containing `test_broken.py` with invalid Python syntax
- **When** `discover(tmp_path)` then `run()` is called
- **Then** `result.errors >= 1` and at least one event is a `TestError`

---

### Requirement: HarnessRunner constructor accepts optional fixtures

The `HarnessRunner.__init__` SHALL accept an optional `fixtures` parameter (list or None). When `None` is passed, `self._fixtures` SHALL default to an empty list. When a list is passed, it SHALL be stored as-is.

#### Scenario: Constructor with no fixtures argument

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__

- **Given** `HarnessRunner()` is constructed with no arguments
- **When** `runner._fixtures` is accessed
- **Then** it SHALL equal `[]`

#### Scenario: Constructor with fixtures list

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.__init__

- **Given** `HarnessRunner(fixtures=[{"timeout": 30}])` is constructed
- **When** `runner._fixtures` is accessed
- **Then** it SHALL equal `[{"timeout": 30}]`

---

### Requirement: HarnessRunner discover returns sorted file list

The list returned by `discover()` SHALL be sorted alphabetically by path, regardless of the filesystem enumeration order.

#### Scenario: Discover returns sorted results

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/harness/runner.py::HarnessRunner.discover

- **Given** a directory containing `test_z.py`, `test_a.py`, `test_m.py`
- **When** `discover(directory)` is called
- **Then** the returned list SHALL be in order: `test_a.py`, `test_m.py`, `test_z.py`

