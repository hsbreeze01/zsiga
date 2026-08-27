# Spec: test-discovery-coverage

## MODIFIED Requirements

### Requirement: Import-aware test coverage discovery

The EvolutionEngine's `_scan_code_structure` method SHALL determine whether a
source module has existing test coverage by scanning the **import statements**
inside all `test_*.py` files, not solely by matching the module's basename against
the test filename prefix.

Currently the algorithm strips `test_` from test filenames (e.g.
`test_harness_runner.py` → `harness_runner`) and checks if the source module's
basename (e.g. `runner`) is in that set. This causes false-negatives for modules
whose test files use a compound name (`test_<parent>_<module>.py`).

The new algorithm MUST:

1. Walk `tests/test_*.py` and parse each file's top-level imports with `ast`.
2. Build a mapping: **dotted import path → test file**.  For example, from
   `from zsiga.harness.runner import HarnessRunner` the mapping records
   `zsiga.harness.runner → tests/test_harness_runner.py`.
3. For each source module under `zsiga/`, convert its relative path to a dotted
   module path (e.g. `zsiga/harness/runner.py` → `zsiga.harness.runner`) and look
   it up in the mapping.
4. A module is considered "covered" if its dotted path appears as a key in the
   import-to-test-file mapping.
5. The old basename-matching logic MAY be kept as a fallback **only** for test
   files that contain no import of any `zsiga.*` module.

#### Scenario: Module with compound-named test file is correctly detected as covered

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source module at `zsiga/harness/runner.py` and a test file
  `tests/test_harness_runner.py` that contains
  `from zsiga.harness.runner import HarnessRunner`
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/harness/runner.py` SHALL NOT appear in the returned
  `modules_without_tests` list

#### Scenario: Module with no test file is correctly detected as uncovered

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source module at `zsiga/harness/runner.py` and NO test file under
  `tests/` that imports from `zsiga.harness.runner`
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/harness/runner.py` SHALL appear in the returned
  `modules_without_tests` list

#### Scenario: Module with basename-matching test file still works

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source module at `zsiga/git_ops.py` and a test file
  `tests/test_git_ops.py` (basename match)
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/git_ops.py` SHALL NOT appear in the returned
  `modules_without_tests` list

#### Scenario: Test file importing multiple modules covers all of them

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a test file `tests/test_foo.py` containing both
  `from zsiga.transport import Transport` and
  `from zsiga.config import load_config`
- **When** `_scan_code_structure()` is called
- **Then** both `zsiga/transport.py` and `zsiga/config.py` SHALL NOT appear in
  the returned `modules_without_tests` list

#### Scenario: Test file with no zsiga imports falls back to basename matching

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a test file `tests/test_bar.py` that imports nothing from `zsiga.*`
  modules, and a source module `zsiga/bar.py`
- **When** `_scan_code_structure()` is called
- **Then** `zsiga/bar.py` SHALL NOT appear in the returned
  `modules_without_tests` list (basename fallback)
