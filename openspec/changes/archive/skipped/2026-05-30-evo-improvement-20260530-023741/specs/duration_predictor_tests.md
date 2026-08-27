# duration_predictor_tests.md — Delta Spec

## ADDED Requirements

### Requirement: collect_known_phases extracts phase names

The system SHALL provide a function `_collect_known_phases(phase_stats)` that returns
the set of all unique phase names found in the `"phases"` sub-dict of each record.

- When `phase_stats` is an empty list, the returned set SHALL be empty.
- When a record has no `"phases"` key, that record SHALL be skipped.
- When a record has `"phases": {}`, no phase names SHALL be contributed.
- When multiple records contain the same phase name, the name SHALL appear once.

#### Scenario: empty input returns empty set

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** an empty list `phase_stats = []`
- **When** `_collect_known_phases` is called
- **Then** the result is an empty `set()`

#### Scenario: records without phases key are skipped

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** `phase_stats = [{"project_lines": 100}]` (no `"phases"` key)
- **When** `_collect_known_phases` is called
- **Then** the result is an empty `set()`

#### Scenario: deduplicates phase names across records

- **testable**: true
- **target**: zsiga/duration_predictor.py::_collect_known_phases
- **Given** two records both containing `"explore"` and `"implement"` in their `"phases"` dicts
- **When** `_collect_known_phases` is called
- **Then** the result is `{"explore", "implement"}` (each name appears once)

---

### Requirement: fit_linear solves least-squares regression

The system SHALL provide `_fit_linear(xs1, xs2, ys)` returning coefficients `(a, b, c)`
for the model `y = a*x1 + b*x2 + c`.

- When inputs are empty, the result SHALL be `(0.0, 0.0, 0.0)`.
- When the determinant is near-zero (degenerate / collinear data), the result SHALL be
  `(0.0, 0.0, mean_y)` where `mean_y` is the arithmetic mean of `ys`.
- For well-conditioned data, the coefficients SHALL satisfy the normal equations
  within floating-point tolerance.

#### Scenario: empty input returns zero coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1 = []`, `xs2 = []`, `ys = []`
- **When** `_fit_linear` is called
- **Then** the result is exactly `(0.0, 0.0, 0.0)`

#### Scenario: degenerate collinear data returns mean fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1 = [1.0, 1.0, 1.0]`, `xs2 = [1.0, 1.0, 1.0]`, `ys = [10.0, 20.0, 30.0]`
  (all x-values identical → degenerate matrix)
- **When** `_fit_linear` is called
- **Then** the result is `(0.0, 0.0, 20.0)` where `20.0` is the mean of `ys`

---

### Requirement: predict_phase uses regression or median fallback

The system SHALL provide `_predict_phase(records, phase_name, project_lines, proposal_chars)`
that returns a predicted duration in seconds (clamped ≥ 0).

- When fewer than 3 records contain the target phase, the function SHALL return the
  median of available durations, or `DEFAULT_PHASE_SECONDS` (30.0) if none.
- When ≥ 3 records are available, the function SHALL use `_fit_linear` regression and
  clamp negative predictions to 0.0.

#### Scenario: no records for target phase returns default

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** records that contain `"explore"` but not `"verify"`
- **When** `_predict_phase` is called with `phase_name="verify"`
- **Then** the result is `30.0` (`DEFAULT_PHASE_SECONDS`)

#### Scenario: one record returns that value as median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** a single record with `phases = {"explore": 42.0}`
- **When** `_predict_phase` is called with `phase_name="explore"`
- **Then** the result is `42.0`

#### Scenario: two records return median

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** two records with `"explore"` durations `10.0` and `30.0`
- **When** `_predict_phase` is called with `phase_name="explore"`
- **Then** the result is `20.0` (median of `[10.0, 30.0]`)

#### Scenario: sufficient data uses regression result

- **testable**: true
- **target**: zsiga/duration_predictor.py::_predict_phase
- **Given** 4 records where `y = 2*x1 + 3*x2 + 1` with non-degenerate x2 values
- **When** `_predict_phase` is called with `project_lines=5, proposal_chars=1`
- **Then** the result is approximately `14.0` (`2*5 + 3*1 + 1`)

---

### Requirement: fallback_estimates computes median per phase

The system SHALL provide `_fallback_estimates(phase_stats)` returning a `dict[str, float]`
mapping each known phase name to its median duration, plus a `_total` key.

- When `phase_stats` is empty, the result SHALL be `{"_total": 0.0}`.
- For each phase, the median of all available durations SHALL be used.
- `_total` SHALL equal the sum of all non-`_total` values.

#### Scenario: empty phase_stats returns total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** `phase_stats = []`
- **When** `_fallback_estimates` is called
- **Then** the result is `{"_total": 0.0}`

#### Scenario: single phase with single value returns that value

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** one record with `phases = {"explore": 15.0}`
- **When** `_fallback_estimates` is called
- **Then** the result is `{"explore": 15.0, "_total": 15.0}`

#### Scenario: multiple phases with multiple values returns medians

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fallback_estimates
- **Given** two records: first has `explore=10, design=5`, second has `explore=20, design=15`
- **When** `_fallback_estimates` is called
- **Then** the result contains `"explore": 15.0`, `"design": 10.0`, and `"_total": 25.0`

---

### Requirement: predict_change_duration orchestrates per-phase estimation

The system SHALL provide `predict_change_duration(phase_stats, project_lines, proposal_chars)`
as the public entry point.

- When `phase_stats` has fewer than 3 records, `_fallback_estimates` SHALL be used.
- When `phase_stats` has ≥ 3 records, regression SHALL be applied per-phase.
- The returned dict SHALL contain a `_total` key whose value equals the sum of all
  per-phase estimates.

#### Scenario: empty stats returns total zero

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** `phase_stats = []`
- **When** `predict_change_duration` is called with any `project_lines` and `proposal_chars`
- **Then** the result is `{"_total": 0.0}`

#### Scenario: total equals sum of phase estimates

- **testable**: true
- **target**: zsiga/duration_predictor.py::predict_change_duration
- **Given** 3 records with phases `"explore"` and `"design"`
- **When** `predict_change_duration` is called
- **Then** `result["_total"]` equals `sum(v for k, v in result.items() if k != "_total")`
