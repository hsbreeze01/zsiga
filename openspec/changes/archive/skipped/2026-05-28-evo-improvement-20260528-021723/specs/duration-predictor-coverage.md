# duration-predictor-coverage

## ADDED Requirements

### REQ-DP-01: `_collect_known_phases` extracts unique phase names

The function `_collect_known_phases` SHALL return the set of all unique phase
names found across the `"phases"` dictionaries in every record of the input
list. Records lacking a `"phases"` key SHALL be treated as having an empty
phase dictionary.

#### Scenario: Empty input returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `[]`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `set()`

#### Scenario: Single record returns its phase names

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing one record `[{"phases": {"clarify": 10, "implement": 20}}]`
- **When** `_collect_known_phases` is called
- **Then** the result SHALL equal `{"clarify", "implement"}`

#### Scenario: Multiple records merge all phase names

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list of two records with disjoint phase names
- **When** `_collect_known_phases` is called
- **Then** the result SHALL be the union of all phase names from all records

#### Scenario: Record missing phases key treated as empty

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** a list containing a record without a `"phases"` key
- **When** `_collect_known_phases` is called
- **Then** the function SHALL NOT raise and the missing key SHALL be treated as an empty dict

---

### REQ-DP-02: `_fit_linear` computes least-squares coefficients

The function `_fit_linear` SHALL solve for coefficients `(a, b, c)` in the
model `y = a*x1 + b*x2 + c` using least-squares. It MUST return `(0.0, 0.0,
0.0)` for empty input. It MUST return `(0.0, 0.0, mean_y)` when the system
is degenerate (determinant near zero).

#### Scenario: Empty input returns zero coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** empty lists `xs1=[], xs2=[], ys=[]`
- **When** `_fit_linear` is called
- **Then** the result SHALL equal `(0.0, 0.0, 0.0)`

#### Scenario: Exact linear fit recovers coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** data generated from a known linear model `y = 2*x1 + 3*x2 + 5`
- **When** `_fit_linear` is called with at least 3 data points
- **Then** the returned coefficients SHALL approximate `(2.0, 3.0, 5.0)` within tolerance `1e-6`

#### Scenario: Degenerate collinear data returns mean fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** collinear data where `xs2` is always `2 * xs1` (making columns linearly dependent)
- **When** `_fit_linear` is called
- **Then** the result SHALL equal `(0.0, 0.0, mean_y)` where `mean_y` is the mean of `ys`

---

### REQ-DP-03: `_predict_phase` predicts single-phase duration with clamping

The function `_predict_phase` SHALL return a non-negative float. When fewer
than 3 matching data points exist for the given `phase_name`, it MUST use the
median of available durations as the estimate. When zero data points exist,
it MUST return `DEFAULT_PHASE_SECONDS` (30.0). When 3 or more data points
exist, it MUST use linear regression and clamp the result to `>= 0.0`.

#### Scenario: No matching records returns default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that do not contain the requested phase name
- **When** `_predict_phase` is called
- **Then** the result SHALL equal `30.0`

#### Scenario: One or two matching records returns median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** exactly 2 records with durations `[10.0, 20.0]` for the requested phase
- **When** `_predict_phase` is called
- **Then** the result SHALL equal `median([10.0, 20.0])` which is `15.0`

#### Scenario: Three or more records uses regression

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 4 records with known linear relationship for the phase
- **When** `_predict_phase` is called with corresponding project_lines and proposal_chars
- **Then** the result SHALL be close to the linear prediction (within tolerance `1e-3`)

#### Scenario: Negative prediction clamped to zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 3+ records that produce a negative regression prediction
- **When** `_predict_phase` is called with extreme project_lines/proposal_chars values
- **Then** the result SHALL be `>= 0.0`

---

### REQ-DP-04: `_fallback_estimates` computes median-based estimates

The function `_fallback_estimates` SHALL return a dict mapping each known
phase name to its median duration across all records. It MUST include a
`"_total"` key equal to the sum of all per-phase values. Phases with no
duration data SHALL use `DEFAULT_PHASE_SECONDS`.

#### Scenario: Empty stats returns only _total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** an empty list `[]`
- **When** `_fallback_estimates` is called
- **Then** the result SHALL equal `{"_total": 0.0}`

#### Scenario: Stats with known phases returns median per phase

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** stats with 3 records all containing phase `"clarify"` with durations `[10, 20, 30]`
- **When** `_fallback_estimates` is called
- **Then** `result["clarify"]` SHALL equal `20.0` and `result["_total"]` SHALL equal `20.0`

#### Scenario: Phase with no data uses default seconds

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** stats where a phase name appears in `_collect_known_phases` but no record has duration data for it
- **When** `_fallback_estimates` is called
- **Then** that phase's value SHALL equal `DEFAULT_PHASE_SECONDS` (30.0)

---

### REQ-DP-05: `predict_change_duration` orchestrates estimation

The function `predict_change_duration` is the public entry point. When
`phase_stats` has fewer than 3 records it SHALL delegate to
`_fallback_estimates`. When it has 3 or more records it SHALL use
`_predict_phase` for each known phase. The result MUST always include a
`"_total"` key equal to the sum of all per-phase estimates.

#### Scenario: Fewer than 3 stats uses fallback path

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** a list of 2 historical records
- **When** `predict_change_duration` is called
- **Then** the result SHALL contain `"_total"` and phase keys consistent with `_fallback_estimates`

#### Scenario: Three or more stats uses regression path

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** a list of 4 historical records with consistent phase data
- **When** `predict_change_duration` is called
- **Then** the result SHALL contain estimates per phase and `"_total"` equal to their sum

#### Scenario: Result _total equals sum of per-phase values

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** any valid `phase_stats` input
- **When** `predict_change_duration` is called
- **Then** `result["_total"]` SHALL equal the sum of all values in `result` except `"_total"`
