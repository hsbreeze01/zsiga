"""Spec tests for duration-predictor-direct-tests.

Verifies behaviors of private functions in zsiga/duration_predictor:
  _collect_known_phases, _fallback_estimates, _predict_phase, _fit_linear

These tests provide DIRECT coverage (not via predict_change_duration)
of functions that are currently only indirectly tested.
"""

from statistics import median

import pytest

from zsiga.duration_predictor import (
    DEFAULT_PHASE_SECONDS,
    _collect_known_phases,
    _fallback_estimates,
    _fit_linear,
    _predict_phase,
)


# ── _collect_known_phases scenarios ────────────────────────────────────


def test_collect_known_phases_empty_input_returns_empty_set():
    """Given an empty list, _collect_known_phases returns an empty set."""
    result = _collect_known_phases([])
    assert result == set()


def test_collect_known_phases_single_record_with_phases():
    """Single record with two phases yields both phase names."""
    records = [{"phases": {"explore": 10.0, "implement": 20.0}}]
    result = _collect_known_phases(records)
    assert result == {"explore", "implement"}


def test_collect_known_phases_multiple_records_deduplicated():
    """Two records with overlapping phases produce a deduplicated union."""
    records = [
        {"phases": {"explore": 10.0}},
        {"phases": {"implement": 20.0, "explore": 15.0}},
    ]
    result = _collect_known_phases(records)
    assert result == {"explore", "implement"}


def test_collect_known_phases_missing_phases_key_skipped():
    """Records without a 'phases' key are silently skipped."""
    records = [
        {"project_lines": 100},  # no "phases" key
        {"phases": {"verify": 5.0}},
    ]
    result = _collect_known_phases(records)
    assert result == {"verify"}


# ── _fallback_estimates scenarios ──────────────────────────────────────


def test_fallback_estimates_empty_input_returns_total_zero():
    """Empty input list returns {"_total": 0.0}."""
    result = _fallback_estimates([])
    assert result == {"_total": 0.0}


def test_fallback_estimates_single_phase_single_record():
    """One record with one phase yields median equal to that value."""
    records = [{"phases": {"explore": 10.0}}]
    result = _fallback_estimates(records)
    assert result["explore"] == 10.0
    assert result["_total"] == 10.0


def test_fallback_estimates_multiple_records_median():
    """Three records with durations [10, 20, 30] yield median 20.0."""
    records = [
        {"phases": {"explore": 10.0}},
        {"phases": {"explore": 20.0}},
        {"phases": {"explore": 30.0}},
    ]
    result = _fallback_estimates(records)
    assert result["explore"] == 20.0
    assert result["_total"] == 20.0


def test_fallback_estimates_total_equals_sum_of_phases():
    """_total key equals the sum of all per-phase values."""
    records = [
        {"phases": {"explore": 10.0, "implement": 20.0}},
        {"phases": {"explore": 20.0, "implement": 30.0}},
    ]
    result = _fallback_estimates(records)
    phase_sum = sum(v for k, v in result.items() if k != "_total")
    assert abs(result["_total"] - phase_sum) < 1e-9


# ── _predict_phase scenarios ───────────────────────────────────────────


def test_predict_phase_no_matching_phase_returns_default():
    """When no record contains the requested phase, return DEFAULT_PHASE_SECONDS."""
    records = [
        {"project_lines": 1000, "proposal_chars": 500, "phases": {"explore": 10.0}},
    ]
    result = _predict_phase(records, "verify", 1000, 500)
    assert result == DEFAULT_PHASE_SECONDS
    assert result == 30.0


def test_predict_phase_fewer_than_3_returns_median():
    """With 2 matching records, returns median of their durations."""
    records = [
        {"project_lines": 1000, "proposal_chars": 500, "phases": {"explore": 10.0}},
        {"project_lines": 2000, "proposal_chars": 600, "phases": {"explore": 20.0}},
    ]
    result = _predict_phase(records, "explore", 1500, 550)
    assert result == 15.0  # median of [10, 20]


def test_predict_phase_3_records_uses_linear_regression():
    """With ≥3 records, linear regression is used; exact for perfectly linear data."""
    # y = 0.01*x1 + 0.02*x2, with non-collinear (x1,x2) pairs
    records = [
        {"project_lines": 100, "proposal_chars": 200, "phases": {"explore": 5.0}},
        {"project_lines": 200, "proposal_chars": 100, "phases": {"explore": 4.0}},
        {"project_lines": 300, "proposal_chars": 300, "phases": {"explore": 9.0}},
    ]
    # At (250, 250): y = 0.01*250 + 0.02*250 = 2.5 + 5.0 = 7.5
    result = _predict_phase(records, "explore", 250, 250)
    assert abs(result - 7.5) < 1e-3


def test_predict_phase_negative_clamped_to_zero():
    """Negative prediction is clamped to 0.0."""
    # Large values so extrapolating to small inputs gives negative
    records = [
        {"project_lines": 10000, "proposal_chars": 10000,
         "phases": {"explore": 100.0}},
        {"project_lines": 20000, "proposal_chars": 20000,
         "phases": {"explore": 200.0}},
        {"project_lines": 30000, "proposal_chars": 30000,
         "phases": {"explore": 300.0}},
    ]
    result = _predict_phase(records, "explore", 1, 1)
    assert result >= 0.0


def test_predict_phase_single_record_returns_value():
    """Single matching record returns that value (median of one element)."""
    records = [
        {"project_lines": 1000, "proposal_chars": 500, "phases": {"explore": 42.0}},
    ]
    result = _predict_phase(records, "explore", 100, 200)
    assert result == 42.0


# ── _fit_linear boundary / degenerate scenarios ────────────────────────


def test_fit_linear_collinear_input_mean_fallback():
    """Collinear xs1/xs2 triggers degenerate path → (0, 0, mean_y)."""
    # xs2 = 2 * xs1, so the system is rank-deficient
    xs1 = [1.0, 2.0, 3.0]
    xs2 = [2.0, 4.0, 6.0]
    ys = [10.0, 20.0, 30.0]
    a, b, c = _fit_linear(xs1, xs2, ys)
    # Degenerate → a≈0, b≈0, c≈mean(ys)
    assert abs(a) < 1e-6
    assert abs(b) < 1e-6
    assert abs(c - 20.0) < 1e-6


def test_fit_linear_all_zero_y_returns_zero_coefficients():
    """When all y values are zero, result is (0.0, 0.0, 0.0)."""
    xs1 = [1.0, 2.0, 3.0]
    xs2 = [1.0, 2.0, 3.0]
    ys = [0.0, 0.0, 0.0]
    a, b, c = _fit_linear(xs1, xs2, ys)
    assert a == 0.0
    assert b == 0.0
    assert c == 0.0


def test_fit_linear_single_point_degenerate():
    """Single data point triggers degenerate path → (0, 0, y_value)."""
    a, b, c = _fit_linear([5.0], [3.0], [10.0])
    assert a == 0.0
    assert b == 0.0
    assert c == 10.0
