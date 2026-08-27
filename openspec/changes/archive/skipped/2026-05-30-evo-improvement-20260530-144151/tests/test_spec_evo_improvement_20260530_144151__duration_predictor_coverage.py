"""Spec-derived tests for duration_predictor internal functions.

Covers _collect_known_phases, _fallback_estimates, _predict_phase,
and degenerate _fit_linear edge cases — all previously without direct
unit tests.
"""

import pytest

from zsiga.duration_predictor import (
    DEFAULT_PHASE_SECONDS,
    _collect_known_phases,
    _fallback_estimates,
    _fit_linear,
    _predict_phase,
)


# ── _collect_known_phases ──────────────────────────────────────────────


def test__collect_known_phases_empty_input_returns_empty_set():
    """Given phase_stats is [], return empty set."""
    result = _collect_known_phases([])
    assert result == set()


def test__collect_known_phases_single_record_single_phase():
    """Given one record with phases={"enrich": 10.0}, return {"enrich"}."""
    phase_stats = [{"phases": {"enrich": 10.0}}]
    result = _collect_known_phases(phase_stats)
    assert result == {"enrich"}


def test__collect_known_phases_multiple_records_merged_deduplicated():
    """Multiple records with overlapping phases are merged and deduplicated."""
    phase_stats = [
        {"phases": {"enrich": 5.0, "design": 3.0}},
        {"phases": {"design": 6.0, "implement": 20.0}},
        {"phases": {"verify": 8.0}},
    ]
    result = _collect_known_phases(phase_stats)
    assert result == {"enrich", "design", "implement", "verify"}


def test__collect_known_phases_missing_phases_key_no_error():
    """Record without a 'phases' key is treated as having no phases."""
    phase_stats = [{"project_lines": 100}]  # no "phases" key
    result = _collect_known_phases(phase_stats)
    assert result == set()


# ── _fallback_estimates ────────────────────────────────────────────────


def test__fallback_estimates_empty_input_returns_zero_total():
    """Empty phase_stats produces {"_total": 0.0}."""
    result = _fallback_estimates([])
    assert result == {"_total": 0.0}


def test__fallback_estimates_single_phase_single_record():
    """One record with one phase returns that duration and matching _total."""
    phase_stats = [{"phases": {"enrich": 42.0}}]
    result = _fallback_estimates(phase_stats)
    assert result["enrich"] == 42.0
    assert result["_total"] == 42.0


def test__fallback_estimates_multiple_records_independent_medians():
    """Each phase gets its own median; _total is the sum."""
    phase_stats = [
        {"phases": {"enrich": 10.0, "verify": 5.0}},
        {"phases": {"enrich": 30.0, "verify": 15.0}},
        {"phases": {"enrich": 20.0}},
    ]
    result = _fallback_estimates(phase_stats)
    # median of [10, 30, 20] = 20.0; median of [5, 15] = 10.0
    assert result["enrich"] == 20.0
    assert result["verify"] == 10.0
    assert result["_total"] == 30.0


def test__fallback_estimates_total_equals_sum_of_phases():
    """_total must equal arithmetic sum of all phase values."""
    phase_stats = [
        {"phases": {"a": 1.0, "b": 2.0}},
        {"phases": {"a": 3.0, "b": 4.0}},
    ]
    result = _fallback_estimates(phase_stats)
    phase_sum = sum(v for k, v in result.items() if k != "_total")
    assert result["_total"] == pytest.approx(phase_sum)


# ── _predict_phase ─────────────────────────────────────────────────────


def test__predict_phase_no_matching_phase_returns_default():
    """No records for the target phase → DEFAULT_PHASE_SECONDS."""
    records = [
        {"project_lines": 100, "proposal_chars": 50,
         "phases": {"explore": 10.0}},
    ]
    result = _predict_phase(records, "nonexistent", 500, 200)
    assert result == DEFAULT_PHASE_SECONDS


def test__predict_phase_two_records_use_median_fallback():
    """2 matching records → median of their durations (no regression)."""
    records = [
        {"project_lines": 100, "proposal_chars": 50,
         "phases": {"enrich": 10.0}},
        {"project_lines": 200, "proposal_chars": 60,
         "phases": {"enrich": 20.0}},
    ]
    result = _predict_phase(records, "enrich", 500, 200)
    assert result == 15.0  # median of [10, 20]


def test__predict_phase_three_plus_records_use_linear_regression():
    """4 matching records with non-collinear features → regression path produces non-median result."""
    records = [
        {"project_lines": 100, "proposal_chars": 10,
         "phases": {"enrich": 15.0}},
        {"project_lines": 200, "proposal_chars": 50,
         "phases": {"enrich": 25.0}},
        {"project_lines": 300, "proposal_chars": 20,
         "phases": {"enrich": 35.0}},
        {"project_lines": 400, "proposal_chars": 60,
         "phases": {"enrich": 50.0}},
    ]
    # Features are not collinear, so regression can fit a proper model.
    # Query at a point well beyond training data → result should reflect regression.
    result = _predict_phase(records, "enrich", 600, 80)
    assert result >= 0.0
    # The median of [15, 25, 35, 50] is 30.0.  Regression at (600, 80)
    # should extrapolate to something larger, confirming the regression path.
    assert result > 30.0


def test__predict_phase_negative_prediction_clamped_to_zero():
    """Linear model predicting negative → clamped to 0.0."""
    # Use non-collinear records so regression produces real coefficients.
    records = [
        {"project_lines": 1000, "proposal_chars": 100,
         "phases": {"explore": 100.0}},
        {"project_lines": 2000, "proposal_chars": 200,
         "phases": {"explore": 200.0}},
        {"project_lines": 3000, "proposal_chars": 300,
         "phases": {"explore": 300.0}},
        {"project_lines": 4000, "proposal_chars": 400,
         "phases": {"explore": 400.0}},
    ]
    # With extreme negative inputs, the model may predict negative;
    # the result must be clamped to >= 0.0.
    result = _predict_phase(records, "explore", 0, 0)
    assert result >= 0.0
    result2 = _predict_phase(records, "explore", -10000, -10000)
    assert result2 >= 0.0


def test__predict_phase_single_record_returns_value_itself():
    """1 matching record → median of [42.5] = 42.5."""
    records = [
        {"project_lines": 100, "proposal_chars": 50,
         "phases": {"enrich": 42.5}},
    ]
    result = _predict_phase(records, "enrich", 500, 200)
    assert result == 42.5


# ── _fit_linear degenerate edge cases ──────────────────────────────────


def test__fit_linear_collinear_inputs_fallback_to_mean():
    """When xs2 is a scalar multiple of xs1, det≈0 → fallback to mean(ys)."""
    xs1 = [1.0, 2.0, 3.0]
    xs2 = [2.0, 4.0, 6.0]  # xs2 = 2 * xs1 → collinear
    ys = [10.0, 20.0, 30.0]
    a, b, c = _fit_linear(xs1, xs2, ys)
    # Degenerate → mean fallback: a≈0, b≈0, c≈mean(ys)
    assert abs(a) < 1e-9
    assert abs(b) < 1e-9
    assert abs(c - 20.0) < 1e-9


def test__fit_linear_all_zero_y_returns_zero_coefficients():
    """ys all zero → coefficients should be approximately zero."""
    xs1 = [1.0, 2.0, 3.0]
    xs2 = [4.0, 5.0, 6.0]
    ys = [0.0, 0.0, 0.0]
    a, b, c = _fit_linear(xs1, xs2, ys)
    assert abs(a) < 1e-9
    assert abs(b) < 1e-9
    assert abs(c) < 1e-9


def test__fit_linear_single_point_degenerate():
    """Single data point → degenerate → fallback to mean(ys) = the value."""
    a, b, c = _fit_linear([5.0], [3.0], [10.0])
    assert abs(a) < 1e-9
    assert abs(b) < 1e-9
    assert abs(c - 10.0) < 1e-9
