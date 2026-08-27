# fit-linear-edges

## ADDED Requirements

### Requirement: _fit_linear handles degenerate inputs gracefully

The `_fit_linear` function SHALL solve normal equations for `y = a*x1 + b*x2 + c`
and return coefficients `(a, b, c)`. When the system is degenerate (determinant ≈ 0),
it SHALL fall back to `(0.0, 0.0, mean_y)`.

#### Scenario: single data point returns mean fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** a single point: `xs1=[1.0], xs2=[1.0], ys=[10.0]`
- **When** `_fit_linear` is called
- **Then** the returned `c` SHALL equal `10.0` (the mean of ys)
- **And** `a` and `b` SHALL both be `0.0`

#### Scenario: collinear points produce degenerate system

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** collinear points where `xs1` is identical to `xs2` for all entries (e.g., `xs1=[1,2,3], xs2=[1,2,3], ys=[2,4,6]`)
- **When** `_fit_linear` is called
- **Then** the function SHALL return `(0.0, 0.0, mean_y)` where `mean_y` is the average of `ys`
- **And** no exception SHALL be raised

#### Scenario: two data points with identical xs produce mean fallback

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** two points with identical x values: `xs1=[5.0, 5.0], xs2=[3.0, 3.0], ys=[10.0, 20.0]`
- **When** `_fit_linear` is called
- **Then** the result SHALL be `(0.0, 0.0, 15.0)` — the mean of ys

#### Scenario: well-conditioned system recovers coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** a set of non-collinear points that follow `y = 1.5*x1 - 2.0*x2 + 7.0` exactly
- **When** `_fit_linear` is called with at least 5 points
- **Then** the recovered `a` SHALL be within `1e-6` of `1.5`
- **And** `b` SHALL be within `1e-6` of `-2.0`
- **And** `c` SHALL be within `1e-6` of `7.0`

#### Scenario: all-zero xs and ys returns zero coefficients

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1=[0.0, 0.0, 0.0], xs2=[0.0, 0.0, 0.0], ys=[0.0, 0.0, 0.0]`
- **When** `_fit_linear` is called
- **Then** the result SHALL be `(0.0, 0.0, 0.0)`
