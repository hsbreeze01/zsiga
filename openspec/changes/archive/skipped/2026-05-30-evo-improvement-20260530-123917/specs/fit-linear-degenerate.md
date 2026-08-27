# fit_linear_degenerate

## ADDED Requirements

### Requirement: _fit_linear handles degenerate inputs gracefully

When the normal-equation matrix is singular (determinant near zero), `_fit_linear`
MUST NOT raise an exception. It SHALL return `(0.0, 0.0, mean_y)` where
`mean_y` is the arithmetic mean of `ys`.

#### Scenario: collinear features fall back to mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1` and `xs2` that are perfectly linearly dependent (e.g. `xs2 = 2 * xs1`) with non-constant `ys`
- **When** `_fit_linear` is called
- **Then** the returned tuple SHALL be `(0.0, 0.0, mean_of_ys)`

#### Scenario: all identical inputs fall back to mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** all `xs1`, `xs2` and `ys` are constant (e.g. all `1.0`)
- **When** `_fit_linear` is called
- **Then** the returned tuple SHALL be `(0.0, 0.0, 1.0)` (mean of all identical ys)

#### Scenario: single data point falls back to mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** a single-element list for each input (`xs1=[5.0], xs2=[3.0], ys=[10.0]`)
- **When** `_fit_linear` is called
- **Then** the returned tuple SHALL be `(0.0, 0.0, 10.0)`
