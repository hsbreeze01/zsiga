# spec: no-op-redundant-tests

> **Verdict: NO-OP** — This change requires no implementation.
> The proposal `add-tests-runner` is based on a false premise.

## Context

Proposal `add-tests-runner` requests creating `tests/test_runner.py` for module
`zsiga/harness/runner.py`, claiming the module "lacks test coverage".  This
claim is **false**: `tests/test_harness_runner.py` already exists with 277 lines
and 28 `def test_` functions, providing comprehensive coverage of all 10 public
classes (TestEvent, TestStarted, TestPassed, TestFailed, TestError, HarnessResult,
HarnessRunner, QualificationReport, TestReport, and the internal
_HarnessCollectorPlugin).

This proposal has cycled through the pipeline **26+ times**, always reaching
skip/reject, because the auto-evolution engine only matches `test_{basename}.py`
(e.g. `test_runner.py`) and ignores `test_{parent}_{basename}.py` patterns
(e.g. `test_harness_runner.py`).

## ADDED Requirements

None.

## MODIFIED Requirements

None.

## REMOVED Requirements

### Requirement: reject-redundant-test-runner-file

The system SHALL NOT create `tests/test_runner.py` as it would be a redundant
duplicate of the existing `tests/test_harness_runner.py`.

#### Scenario: redundant test file is not created

- **testable**: true
- **target**: tests/test_runner.py
- **Given** the file `tests/test_harness_runner.py` exists with ≥20 test functions covering `zsiga.harness.runner`
- **When** the change pipeline completes
- **Then** the file `tests/test_runner.py` SHALL NOT exist on disk

#### Scenario: existing harness runner tests pass

- **testable**: true
- **target**: tests/test_harness_runner.py
- **Given** the existing test file `tests/test_harness_runner.py`
- **When** `python -m pytest tests/test_harness_runner.py` is executed
- **Then** the exit code SHALL be 0

## Root Cause Analysis

The auto-evolution engine's test-discovery logic uses a filename-only heuristic:
`test_{module_basename}.py`.  For module `zsiga/harness/runner.py` it searches for
`test_runner.py` and concludes "no tests exist".  The actual test file is named
`test_harness_runner.py` (using the full path-based convention), which the heuristic
cannot find.

**Recommended fix**: Extend the engine's discovery to scan all `test_*.py` files for
`import` statements referencing the target module, rather than relying on filename
pattern alone.
