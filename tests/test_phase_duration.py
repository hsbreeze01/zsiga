"""Tests for phase duration histogram: min/max stats and dashboard rendering."""


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
