"""Tests for Phase Token Cap — TokenBudget (phase-cap-budget spec)."""
from zsiga.agent.token_budget import TokenBudget


# ---------------------------------------------------------------------------
# Requirement: phase_cap attribute
# ---------------------------------------------------------------------------


class TestPhaseCapAttribute:
    def test_default_phase_cap_is_zero(self):
        budget = TokenBudget()
        assert budget.phase_cap == 0

    def test_phase_cap_set_via_constructor(self):
        budget = TokenBudget(phase_cap=200000)
        assert budget.phase_cap == 200000

    def test_phase_cap_is_writable_after_construction(self):
        budget = TokenBudget()
        budget.phase_cap = 400000
        assert budget.phase_cap == 400000


# ---------------------------------------------------------------------------
# Requirement: cap_exceeded in record() result
# ---------------------------------------------------------------------------


class TestCapExceededInRecord:
    def test_cap_exceeded_false_when_phase_cap_is_zero(self):
        budget = TokenBudget(total_budget=200000, phase_cap=0)
        result = budget.record(100000, 100000)
        assert result["cap_exceeded"] is False

    def test_cap_exceeded_false_while_within_cap(self):
        budget = TokenBudget(phase_cap=200)
        result = budget.record(80, 70)
        assert result["cap_exceeded"] is False

    def test_cap_exceeded_true_when_usage_exceeds_cap(self):
        budget = TokenBudget(phase_cap=200)
        result = budget.record(120, 100)
        assert result["cap_exceeded"] is True

    def test_cap_exceeded_triggers_on_subsequent_call_after_accumulating(self):
        budget = TokenBudget(phase_cap=200)
        budget.record(80, 70)  # used=150, under cap
        result = budget.record(30, 30)  # used=210 > 200
        assert result["cap_exceeded"] is True


# ---------------------------------------------------------------------------
# Requirement: reset_phase() method
# ---------------------------------------------------------------------------


class TestResetPhase:
    def test_reset_phase_resets_only_used_counter(self):
        budget = TokenBudget(total_budget=600000, phase_cap=100)
        budget.record(60, 50)  # used=110, cap_exceeded=True
        budget.reset_phase()
        result = budget.record(10, 10)  # used=20, under cap 100
        assert result["cap_exceeded"] is False

    def test_reset_phase_preserves_extended_state(self):
        budget = TokenBudget(total_budget=100)
        budget.try_extend("productive")  # no-op since used <= total_budget
        # Force extension by exceeding budget first
        budget._used = 200
        budget.try_extend("productive")  # now _extended=True
        assert budget._extended is True
        budget.reset_phase()
        assert budget._extended is True
        assert budget.effective_budget == int(100 * 1.5)

    def test_reset_phase_preserves_consecutive_stale(self):
        budget = TokenBudget()
        for _ in range(3):
            budget.record(10, 10, value_signal="stale")
        assert budget._consecutive_stale == 3
        budget.reset_phase()
        assert budget._consecutive_stale == 3

    def test_reset_phase_does_not_change_phase_cap(self):
        budget = TokenBudget(phase_cap=200000)
        budget.reset_phase()
        assert budget.phase_cap == 200000


# ---------------------------------------------------------------------------
# Requirement: Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    def test_session_exceeded_enforcement_unaffected_by_phase_cap(self):
        budget = TokenBudget(total_budget=1000, phase_cap=0)
        result = budget.record(600, 500)  # used=1100 > 1000
        assert result["session_exceeded"] is True
        assert result["cap_exceeded"] is False

    def test_both_caps_exceeded_simultaneously(self):
        budget = TokenBudget(total_budget=1000, phase_cap=500)
        result = budget.record(600, 500)  # used=1100, exceeding both
        assert result["session_exceeded"] is True
        assert result["cap_exceeded"] is True

    def test_snapshot_still_works_with_phase_cap(self):
        budget = TokenBudget(total_budget=100000, phase_cap=50000)
        budget.record(10000, 5000)
        snap = budget.snapshot()
        assert "total_budget" in snap
        assert snap["used"] == 15000
        assert "remaining" in snap
        assert "usage_ratio" in snap
        assert "effective_budget" in snap
        assert "extended" in snap
        assert "consecutive_stale" in snap
