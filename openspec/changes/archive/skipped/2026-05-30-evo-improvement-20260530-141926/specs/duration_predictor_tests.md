# duration_predictor_tests

## ADDED Requirements

### Requirement: test-duration-predictor-file

The project SHALL contain a test file `tests/test_duration_predictor.py` that provides
direct unit tests for the private helper functions in `zsiga/duration_predictor.py`
which lack dedicated test coverage in the existing `tests/test_phase_duration.py`.

The file MUST import from `zsiga.duration_predictor` and contain at least three
`def test_` functions, including `test__collect_known_phases`, `test__fit_linear`,
and `test__predict_phase`.

All tests in this file MUST pass when executed via `python -m pytest tests/test_duration_predictor.py`.

#### Scenario: file-exists-and-importable

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the project test directory
- **When** the test runner loads `tests/test_duration_predictor.py`
- **Then** the file exists and is a valid Python module importable by pytest

#### Scenario: collect-known-phases-from-records

- **testable**: true
- **target**: tests/test_duration_predictor.py::test__collect_known_phases
- **Given** a list of phase_stats records where each record has a `phases` dict with phase names as keys
- **When** `_collect_known_phases` is called with that list
- **Then** it returns the set of all unique phase names found across all records

#### Scenario: collect-known-phases-empty-input

- **testable**: true
- **target**: tests/test_duration_predictor.py::test__collect_known_phases
- **Given** an empty list of phase_stats
- **When** `_collect_known_phases` is called with `[]`
- **Then** it returns an empty set

#### Scenario: fit-linear-recovers-coefficients

- **testable**: true
- **target**: tests/test_duration_predictor.py::test__fit_linear
- **Given** synthetic data generated from a known linear model `y = a*x1 + b*x2 + c`
- **When** `_fit_linear` is called with the feature vectors and target vector
- **Then** it recovers coefficients `a`, `b`, `c` within floating-point tolerance

#### Scenario: predict-phase-insufficient-data

- **testable**: true
- **target**: tests/test_duration_predictor.py::test__predict_phase
- **Given** fewer than 3 historical records containing the target phase
- **When** `_predict_phase` is called for that phase
- **Then** it returns the median of available durations if any exist, or `DEFAULT_PHASE_SECONDS` (30.0) if none

#### Scenario: predict-phase-clamps-negative

- **testable**: true
- **target**: tests/test_duration_predictor.py::test__predict_phase
- **Given** at least 3 records and prediction inputs that would produce a negative linear estimate
- **When** `_predict_phase` computes the prediction
- **Then** the result is clamped to 0.0 (never negative)

#### Scenario: existing-tests-unaffected

- **testable**: true
- **target**: tests/test_phase_duration.py
- **Given** the existing test file `tests/test_phase_duration.py`
- **When** `python -m pytest tests/test_phase_duration.py` is run
- **Then** all existing tests continue to pass (exit code 0)
