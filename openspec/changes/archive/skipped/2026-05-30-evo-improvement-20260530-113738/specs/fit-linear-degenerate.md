# fit-linear-degenerate

## ADDED Requirements

### Requirement: _fit_linear handles degenerate input gracefully

The function `_fit_linear` SHALL return `(0.0, 0.0, mean_y)` when the normal-equation matrix determinant is near zero (|D| < 1e-12), indicating collinear or otherwise degenerate input. The `mean_y` value SHALL be the arithmetic mean of `ys` (or `0.0` when `n == 0`, which is already covered by existing tests).

#### Scenario: collinear input falls back to mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1 = [1.0, 2.0, 3.0]`, `xs2 = [2.0, 4.0, 6.0]` (xs2 = 2 * xs1, perfectly collinear), `ys = [10.0, 20.0, 30.0]`
- **When** `_fit_linear` is called
- **Then** the result SHALL be `(0.0, 0.0, 20.0)` where 20.0 is the mean of `ys`

#### Scenario: all identical values falls back to mean

- **testable**: true
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1 = [5.0, 5.0, 5.0]`, `xs2 = [3.0, 3.0, 3.0]`, `ys = [7.0, 7.0, 7.0]` (all values identical)
- **When** `_fit_linear` is called
- **Then** the result SHALL be `(0.0, 0.0, 7.0)` where 7.0 is the mean of `ys`
