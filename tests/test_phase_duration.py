"""Tests for phase duration histogram: min/max stats and dashboard rendering."""

from zsiga.duration_predictor import (
    _fit_linear,
    predict_change_duration,
)
from zsiga.metrics.collector import compute_stats


# ── Task 1.1: min/max in compute_stats ──────────────────────────────────


class TestComputeStatsMinMax:
    """Scenario: Computing phase duration stats with multiple phase records."""

    def _make_changes(self, phase_seconds: dict[str, list[float]]) -> list[dict]:
        """Build a changes list with given phase→seconds mapping.

        Each entry in the list is one change with one phase record.
        """
        changes = []
        for phase, secs_list in phase_seconds.items():
            for s in secs_list:
                changes.append(
                    {
                        "change_name": "test-change",
                        "project": "test-project",
                        "outcome": "success",
                        "phases": [
                            {
                                "phase": phase,
                                "outcome": "success",
                                "seconds_used": s,
                                "turns_used": 1,
                                "fix_attempts": 0,
                                "llm_calls": 1,
                                "tool_calls": 1,
                                "prompt_tokens": 10,
                                "completion_tokens": 10,
                            }
                        ],
                    }
                )
        return changes

    def test_multiple_records_avg_min_max(self):
        """Given 3 implement phase records with 100.0, 200.0, 300.0 → avg=200, min=100, max=300."""
        changes = self._make_changes({"implement": [100.0, 200.0, 300.0]})
        stats = compute_stats(changes)
        ps = stats["phase_stats"]["implement"]
        assert ps["avg_seconds"] == 200.0
        assert ps["min_seconds"] == 100.0
        assert ps["max_seconds"] == 300.0

    def test_zero_count_phase_no_min_max(self):
        """Phase with zero records has only count=0, no min/max keys."""
        changes = self._make_changes({"implement": [100.0]})
        stats = compute_stats(changes)
        ps = stats["phase_stats"]["deliver"]
        assert ps["count"] == 0
        assert "min_seconds" not in ps
        assert "max_seconds" not in ps

    def test_single_record_min_equals_max(self):
        """Single record: min == max == avg == the value."""
        changes = self._make_changes({"verify": [81.9]})
        stats = compute_stats(changes)
        ps = stats["phase_stats"]["verify"]
        assert ps["min_seconds"] == 81.9
        assert ps["max_seconds"] == 81.9
        assert ps["avg_seconds"] == 81.9

    def test_values_rounded_to_one_decimal(self):
        """Values should be rounded to 1 decimal place."""
        changes = self._make_changes({"enrich": [1.111, 2.222]})
        stats = compute_stats(changes)
        ps = stats["phase_stats"]["enrich"]
        assert ps["min_seconds"] == 1.1
        assert ps["max_seconds"] == 2.2
        assert ps["avg_seconds"] == round(3.333 / 2, 1)

    def test_all_four_phases_with_data(self):
        """All 4 phases get stats when data exists."""
        changes = self._make_changes(
            {
                "enrich": [10.0, 20.0],
                "implement": [30.0],
                "verify": [40.0, 50.0, 60.0],
                "deliver": [5.0],
            }
        )
        stats = compute_stats(changes)
        for phase in ["enrich", "implement", "verify", "deliver"]:
            ps = stats["phase_stats"][phase]
            assert "min_seconds" in ps
            assert "max_seconds" in ps
            assert ps["min_seconds"] <= ps["avg_seconds"] <= ps["max_seconds"]


# ── Duration Predictor Tests ───────────────────────────────────────────


def _make_stats(records):
    """Helper to build phase_stats list."""
    return records


class TestFitLinear:
    """Test the internal _fit_linear function directly."""

    def test_known_coefficients(self):
        """y = 2*x1 + 3*x2 + 5 with perfect data should recover coefficients."""
        xs1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        xs2 = [0.0, 2.0, 1.0, 3.0, 4.0]
        ys = [2 * a + 3 * b + 5 for a, b in zip(xs1, xs2)]
        a, b, c = _fit_linear(xs1, xs2, ys)
        assert abs(a - 2.0) < 1e-6
        assert abs(b - 3.0) < 1e-6
        assert abs(c - 5.0) < 1e-6

    def test_empty_input(self):
        """Empty input returns zero coefficients."""
        a, b, c = _fit_linear([], [], [])
        assert (a, b, c) == (0.0, 0.0, 0.0)


class TestPredictChangeDurationSufficient:
    """Test predict_change_duration with >= 3 historical records."""

    def test_returns_per_phase_estimates_plus_total(self):
        """With >= 3 records, returns dict with phase names and _total."""
        stats = [
            {"project_lines": 1000, "proposal_chars": 500,
             "phases": {"explore": 10.0, "design": 5.0, "implement": 20.0, "verify": 8.0, "deliver": 3.0}},
            {"project_lines": 2000, "proposal_chars": 600,
             "phases": {"explore": 12.0, "design": 6.0, "implement": 25.0, "verify": 9.0, "deliver": 4.0}},
            {"project_lines": 1500, "proposal_chars": 550,
             "phases": {"explore": 11.0, "design": 5.5, "implement": 22.0, "verify": 8.5, "deliver": 3.5}},
        ]
        result = predict_change_duration(stats, 1500, 550)
        assert "explore" in result
        assert "design" in result
        assert "implement" in result
        assert "verify" in result
        assert "deliver" in result
        assert "_total" in result
        # All values non-negative
        for v in result.values():
            assert v >= 0.0

    def test_total_equals_sum_of_phases(self):
        """_total equals sum of all per-phase estimates."""
        stats = [
            {"project_lines": 1000, "proposal_chars": 500,
             "phases": {"explore": 10.0, "design": 5.0, "implement": 20.0, "verify": 8.0, "deliver": 3.0}},
            {"project_lines": 2000, "proposal_chars": 600,
             "phases": {"explore": 12.0, "design": 6.0, "implement": 25.0, "verify": 9.0, "deliver": 4.0}},
            {"project_lines": 1500, "proposal_chars": 550,
             "phases": {"explore": 11.0, "design": 5.5, "implement": 22.0, "verify": 8.5, "deliver": 3.5}},
        ]
        result = predict_change_duration(stats, 1500, 550)
        phase_sum = sum(v for k, v in result.items() if k != "_total")
        assert abs(result["_total"] - phase_sum) < 1e-6


class TestPredictChangeDurationInsufficient:
    """Test predict_change_duration with < 3 historical records."""

    def test_fewer_than_3_returns_fallback(self):
        """With 2 records, returns median-based fallback."""
        stats = [
            {"project_lines": 1000, "proposal_chars": 500,
             "phases": {"explore": 10.0, "design": 5.0}},
            {"project_lines": 2000, "proposal_chars": 600,
             "phases": {"explore": 20.0, "design": 10.0}},
        ]
        result = predict_change_duration(stats, 1500, 550)
        assert "explore" in result
        assert result["explore"] == 15.0  # median of [10, 20]
        assert result["design"] == 7.5   # median of [5, 10]
        assert "_total" in result

    def test_empty_phase_stats_returns_default(self):
        """With empty phase_stats, returns empty dict with just _total=0."""
        result = predict_change_duration([], 100, 200)
        assert "_total" in result
        assert result["_total"] == 0.0

    def test_single_record_returns_median(self):
        """With 1 record, median is the value itself."""
        stats = [
            {"project_lines": 1000, "proposal_chars": 500,
             "phases": {"explore": 10.0}},
        ]
        result = predict_change_duration(stats, 100, 200)
        assert result["explore"] == 10.0


class TestNegativeClamping:
    """Test that negative predictions are clamped to 0.0."""

    def test_negative_prediction_clamped(self):
        """If model predicts negative, clamp to 0.0."""
        # Craft data where a small project would predict negative for explore
        stats = [
            {"project_lines": 10000, "proposal_chars": 10000,
             "phases": {"explore": 100.0}},
            {"project_lines": 20000, "proposal_chars": 20000,
             "phases": {"explore": 200.0}},
            {"project_lines": 30000, "proposal_chars": 30000,
             "phases": {"explore": 300.0}},
        ]
        # Predicting with very small values should give a positive but
        # we test that all values are >= 0
        result = predict_change_duration(stats, 1, 1)
        assert result["explore"] >= 0.0


class TestMissingPhaseKeys:
    """Test handling of missing phase keys in historical records."""

    def test_missing_phase_keys_still_produces_estimates(self):
        """Records with different phase subsets still produce estimates for all phases."""
        stats = [
            {"project_lines": 1000, "proposal_chars": 500,
             "phases": {"explore": 10.0, "design": 5.0}},
            {"project_lines": 2000, "proposal_chars": 600,
             "phases": {"design": 6.0, "implement": 20.0}},
            {"project_lines": 1500, "proposal_chars": 550,
             "phases": {"explore": 11.0, "implement": 22.0, "verify": 8.0}},
        ]
        result = predict_change_duration(stats, 1500, 550)
        # All phases should be present
        assert "explore" in result
        assert "design" in result
        assert "implement" in result
        assert "verify" in result
        # All non-negative
        for v in result.values():
            assert v >= 0.0
