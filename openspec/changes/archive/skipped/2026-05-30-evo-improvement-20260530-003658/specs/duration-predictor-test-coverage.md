# duration-predictor-test-coverage

## ADDED Requirements

### Requirement: Test file exists for duration_predictor module

A test file `tests/test_duration_predictor.py` SHALL exist and contain unit tests
that cover all five functions exported by `zsiga/duration_predictor.py`:
`_collect_known_phases`, `_fit_linear`, `_predict_phase`, `_fallback_estimates`,
and `predict_change_duration`.

#### Scenario: test file present on disk

- **testable**: true
- **target**: tests/test_duration_predictor.py
- **Given** the project test directory
- **When** checking for file existence
- **Then** `tests/test_duration_predictor.py` SHALL exist as a regular file

---

### Requirement: _collect_known_phases tested

The test suite SHALL cover three behavioural paths of `_collect_known_phases`:
empty input, merged/deduplicated output from multiple records, and graceful
handling of records missing the `phases` key.

#### Scenario: empty input returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]`
- **When** calling `_collect_known_phases([])`
- **Then** the result SHALL be `set()`

#### Scenario: multiple records merged and deduplicated

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list of two records `[{"phases": {"clarify": 10, "implement": 20}}, {"phases": {"implement": 30, "verify": 40}}]`
- **When** calling `_collect_known_phases(records)`
- **Then** the result SHALL equal `{"clarify", "implement", "verify"}`

#### Scenario: missing phases key skipped

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing a record without a `phases` key `[{"phases": {"clarify": 5}}, {"no_phases": True}]`
- **When** calling `_collect_known_phases(records)`
- **Then** the result SHALL equal `{"clarify"}` (the malformed record is skipped)

---

### Requirement: _fit_linear tested

The test suite SHALL cover three behavioural paths of `_fit_linear`:
zero-length input, degenerate/collinear data (near-zero determinant), and
well-conditioned data where coefficients can be recovered within tolerance.

#### Scenario: empty input returns zero coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** empty lists `xs1=[], xs2=[], ys=[]`
- **When** calling `_fit_linear([], [], [])`
- **Then** the result SHALL equal `(0.0, 0.0, 0.0)`

#### Scenario: degenerate collinear data falls back to mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** collinear inputs where `xs1 == xs2` (e.g. `xs1=[1,2,3], xs2=[1,2,3], ys=[4,5,6]`)
- **When** calling `_fit_linear(xs1, xs2, ys)`
- **Then** the result SHALL be `(0.0, 0.0, mean_of_ys)` where `mean_of_ys = 5.0`

#### Scenario: well-conditioned synthetic data recovers coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** synthetic data generated from `y = 2*x1 + 3*x2 + 1` with at least 4 distinct points
- **When** calling `_fit_linear(xs1, xs2, ys)`
- **Then** the returned coefficients `(a, b, c)` SHALL satisfy `abs(a - 2.0) < 0.01`, `abs(b - 3.0) < 0.01`, `abs(c - 1.0) < 0.01`

---

### Requirement: _predict_phase tested

The test suite SHALL cover four behavioural paths of `_predict_phase`:
no matching records → DEFAULT_PHASE_SECONDS, fewer than 3 data points → median,
3+ data points → regression result, and negative predictions clamped to 0.

#### Scenario: no matching records returns default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that do not contain the target phase name and `phase_name="nonexistent"`
- **When** calling `_predict_phase(records, "nonexistent", 100, 500)`
- **Then** the result SHALL equal `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: fewer than three data points returns median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** two records with the target phase having durations `[10.0, 20.0]`
- **When** calling `_predict_phase(records, "clarify", 100, 500)`
- **Then** the result SHALL equal `median([10.0, 20.0])` which is `15.0`

#### Scenario: three or more data points uses regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 4 records with the target phase and varying `(project_lines, proposal_chars, duration)`
- **When** calling `_predict_phase(records, "clarify", 200, 1000)`
- **Then** the result SHALL be a non-negative float that is NOT simply the median of durations (i.e. regression was used)

#### Scenario: negative prediction clamped to zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** enough records to trigger regression but with values that produce a negative predicted duration
- **When** calling `_predict_phase(records, "clarify", project_lines, proposal_chars)` and the raw regression output is negative
- **Then** the result SHALL equal `0.0` (clamped)

---

### Requirement: _fallback_estimates tested

The test suite SHALL cover three behavioural paths of `_fallback_estimates`:
empty input, mixed data (some phases with data, some without), and `_total`
consistency with the sum of per-phase values.

#### Scenario: empty input returns only _total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]`
- **When** calling `_fallback_estimates([])`
- **Then** the result SHALL equal `{"_total": 0.0}`

#### Scenario: mixed data uses medians and defaults

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** records where phase "clarify" has data `[10.0, 20.0, 30.0]` and phase "verify" has no direct data entries
- **When** calling `_fallback_estimates(records)`
- **Then** the "clarify" value SHALL equal `median([10, 20, 30])` = 20.0, and the "verify" value SHALL equal `DEFAULT_PHASE_SECONDS` (30.0)

#### Scenario: _total equals sum of per-phase values

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** any non-empty list of records
- **When** calling `_fallback_estimates(records)`
- **Then** `result["_total"]` SHALL equal the sum of all values whose keys are not `"_total"`

---

### Requirement: predict_change_duration tested

The test suite SHALL cover four behavioural paths of `predict_change_duration`:
fewer than 3 records delegates to fallback, 3+ records uses per-phase regression,
`_total` key consistency, and zero-record boundary.

#### Scenario: fewer than three records delegates to fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** 2 records
- **When** calling `predict_change_duration(records, 100, 500)`
- **Then** the result SHALL equal `_fallback_estimates(records)` exactly

#### Scenario: three or more records uses per-phase regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** 4 records with multiple phases and varying metrics
- **When** calling `predict_change_duration(records, 200, 1000)`
- **Then** each phase key in the result SHALL be a non-negative float, and the result SHALL contain a `_total` key

#### Scenario: _total equals sum of per-phase estimates

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** any list of 3+ records
- **When** calling `predict_change_duration(records, 100, 500)`
- **Then** `result["_total"]` SHALL equal the sum of all values whose keys are not `"_total"`

#### Scenario: zero records returns only _total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** an empty list `[]`
- **When** calling `predict_change_duration([], 100, 500)`
- **Then** the result SHALL equal `{"_total": 0.0}`
