# fit_linear_degenerate

## ADDED Requirements

### Requirement: _fit_linear handles degenerate inputs gracefully

When the normal-equation determinant is near-zero (collinear features, constant inputs), `_fit_linear` SHALL fall back to returning `(0.0, 0.0, mean_y)` where `mean_y` is the arithmetic mean of the `ys` list.

#### Scenario: collinear_features_fallback_to_mean

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1 = [1.0, 2.0, 3.0]`, `xs2 = [2.0, 4.0, 6.0]` (perfectly collinear: `xs2 = 2*xs1`), `ys = [10.0, 20.0, 30.0]`
- **When** `_fit_linear` is called
- **Then** it SHALL return `(0.0, 0.0, 20.0)` — coefficients are zeroed and the intercept is the mean of `ys`

#### Scenario: constant_inputs_fallback_to_mean

- **testable**: false  <!-- demoted by zsiga: test file missing after ENRICH -->
- **target**: zsiga/duration_predictor.py::_fit_linear
- **Given** `xs1 = [5.0, 5.0, 5.0]`, `xs2 = [3.0, 3.0, 3.0]`, `ys = [12.0, 12.0, 12.0]`
- **When** `_fit_linear` is called
- **Then** it SHALL return `(0.0, 0.0, 12.0)` — degenerate constant case, intercept is the mean

