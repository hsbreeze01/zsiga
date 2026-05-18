# Tasks: Change Duration Predictor

## 1. Core Predictor Module

- [x] **1.1** Create `zsiga/duration_predictor.py` with full implementation:
  - `predict_change_duration(phase_stats, project_lines, proposal_chars)` — main entry point
  - `_fit_linear(xs1, xs2, ys)` — least-squares linear regression for 2 features
  - `_predict_phase(records, phase_name, project_lines, proposal_chars)` — per-phase prediction with clamping
  - `_fallback_estimates(phase_stats)` — median-based fallback for < 3 records
  - `_collect_known_phases(phase_stats)` — extract all unique phase names from records
  - Default fallback constant `DEFAULT_PHASE_SECONDS = 30.0`

## 2. Tests

- [x] **2.1** Add predictor tests to `tests/test_phase_duration.py`:
  - Test `predict_change_duration` with sufficient data (≥3 records) → returns per-phase estimates + `_total`
  - Test with insufficient data (<3 records) → returns fallback estimates
  - Test with empty `phase_stats` → returns fallback with default 30.0s per phase
  - Test negative prediction clamping → all values ≥ 0.0
  - Test missing phase keys in historical records → still produces estimates for available phases
  - Test `_total` equals sum of per-phase estimates
  - Test `_fit_linear` directly with known values → correct coefficients
