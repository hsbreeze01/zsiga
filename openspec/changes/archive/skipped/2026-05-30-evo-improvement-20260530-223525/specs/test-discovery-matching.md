# test-discovery-matching

## Context

`EvolutionEngine._scan_code_structure()` uses exact basename matching to associate
test files with source modules. This causes false negatives when test filenames
include additional qualifiers that the source module's basename does not contain.

**Consequence**: `zsiga/harness/runner.py` is perpetually classified as "untested"
because `"runner"` ≠ `"harness_runner"` (derived from `test_harness_runner.py`).
This has produced 37+ identical proposals (all rejected) wasting evolution cycles.

## MODIFIED Requirements

### Requirement: flexible-test-to-module-association

`_scan_code_structure()` SHALL use suffix-based matching when checking whether a
source module has a corresponding test file, instead of exact basename equality.

A source module with basename `X` SHALL be considered "tested" if any test file
exists whose derived module name (the filename minus `test_` prefix and `.py`
suffix) **ends with** `X`, or if `X` **ends with** the derived module name.

#### Scenario: source-module-basename-is-suffix-of-test-name

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file at `zsiga/harness/runner.py` (basename `runner`) and a test file `tests/test_harness_runner.py` (derived module name `harness_runner`)
- **When** `_scan_code_structure()` builds the `modules_without_tests` list
- **Then** `zsiga/harness/runner.py` SHALL NOT appear in `modules_without_tests` because `"harness_runner".endswith("runner")` is `True`

#### Scenario: source-module-basename-is-prefix-of-test-name

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file at `zsiga/transport/local.py` (basename `local`) and a test file `tests/test_local_transport.py` (derived module name `local_transport`)
- **When** `_scan_code_structure()` builds the `modules_without_tests` list
- **Then** `zsiga/transport/local.py` SHALL NOT appear in `modules_without_tests` because `"local_transport".endswith("local")` is `False` but `"local_transport".startswith("local")` is `True` — however exact match `local` not in `local_transport` SHALL still be used; this scenario documents current behavior where `test_local_transport.py` tests `local_transport.py` not `local.py`

#### Scenario: exact-basename-match-still-works

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file at `zsiga/duration_predictor.py` (basename `duration_predictor`) and a test file `tests/test_duration_predictor.py` (derived module name `duration_predictor`)
- **When** `_scan_code_structure()` builds the `modules_without_tests` list
- **Then** `zsiga/duration_predictor.py` SHALL NOT appear in `modules_without_tests` because exact match `"duration_predictor" == "duration_predictor"` is `True`

#### Scenario: truly-untested-module-still-reported

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** a source file at `zsiga/new_feature.py` (basename `new_feature`) and NO test file whose derived module name contains `new_feature` as a suffix
- **When** `_scan_code_structure()` builds the `modules_without_tests` list
- **Then** `zsiga/new_feature.py` SHALL appear in `modules_without_tests`

### Requirement: test-file-derived-names-must-be-unique-or-most-specific

When multiple source modules could match the same test file via suffix matching,
the system SHALL prefer the longest (most specific) basename match to avoid
false positives where a test for `foo_bar.py` is incorrectly associated with
both `bar.py` and `foo_bar.py`.

#### Scenario: longer-basename-takes-precedence

- **testable**: true
- **target**: zsiga/intake/evolution.py::EvolutionEngine._scan_code_structure
- **Given** source files `zsiga/harness/runner.py` (basename `runner`) and `zsiga/foo_runner.py` (basename `foo_runner`), and a test file `tests/test_harness_runner.py` (derived module name `harness_runner`)
- **When** `_scan_code_structure()` determines which source file is covered by `test_harness_runner.py`
- **Then** the test file SHALL be associated with whichever source file's basename is the longest suffix match of `harness_runner`, and the other source file SHALL remain untested if no other test covers it
