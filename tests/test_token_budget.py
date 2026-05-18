"""Unit tests for TokenBudget and CompactionConfig budget fields."""
from zsiga.agent.token_budget import TokenBudget
from zsiga.agent.compaction import estimate_tokens
from zsiga.config import CompactionConfig


# ---------------------------------------------------------------------------
# REQ-BUDGET-001: Token tracking
# ---------------------------------------------------------------------------


class TestTokenTracking:
    def test_record_single_usage(self):
        budget = TokenBudget(total_budget=200000)
        status = budget.record(5000, 800)
        assert status["used"] == 5800
        assert status["remaining"] == 200000 - 5800

    def test_accumulate_multiple_calls(self):
        budget = TokenBudget(total_budget=200000)
        budget.record(4000, 500)
        status = budget.record(6000, 1200)
        assert status["used"] == 11700


# ---------------------------------------------------------------------------
# REQ-BUDGET-002: Per-turn limit
# ---------------------------------------------------------------------------


class TestPerTurnLimit:
    def test_turn_exceeded(self):
        budget = TokenBudget(total_budget=200000, per_turn_limit=4096)
        status = budget.record(1000, 5000)
        assert status["turn_exceeded"] is True

    def test_turn_within_limit(self):
        budget = TokenBudget(total_budget=200000, per_turn_limit=4096)
        status = budget.record(1000, 3000)
        assert status["turn_exceeded"] is False


# ---------------------------------------------------------------------------
# REQ-BUDGET-003: Session budget enforcement
# ---------------------------------------------------------------------------


class TestSessionBudget:
    def test_session_exceeded(self):
        budget = TokenBudget(total_budget=10000)
        budget.record(5000, 3000)
        status = budget.record(1000, 1500)
        assert status["session_exceeded"] is True

    def test_session_not_exceeded(self):
        budget = TokenBudget(total_budget=100000)
        status = budget.record(40000, 40000)
        assert status["session_exceeded"] is False


# ---------------------------------------------------------------------------
# REQ-BUDGET-004: Proactive compaction trigger
# ---------------------------------------------------------------------------


class TestShouldCompact:
    def test_compact_triggered_at_ratio(self):
        budget = TokenBudget(
            compaction_threshold=60000,
            compaction_ratio=0.8,
        )
        # 49000 >= 60000 * 0.8 = 48000
        messages = [{"role": "user", "content": "x" * 49000}]
        assert budget.should_compact(messages, estimate_tokens) is True

    def test_compact_not_triggered_below_ratio(self):
        budget = TokenBudget(
            compaction_threshold=60000,
            compaction_ratio=0.8,
        )
        # Well below 48000 threshold
        messages = [{"role": "user", "content": "short"}]
        assert budget.should_compact(messages, estimate_tokens) is False


# ---------------------------------------------------------------------------
# REQ-BUDGET-005: Configuration defaults and custom values
# ---------------------------------------------------------------------------


class TestCompactionConfigBudgetFields:
    def test_default_values(self):
        cfg = CompactionConfig()
        assert cfg.total_budget == 200000
        assert cfg.per_turn_limit == 8192
        assert cfg.compaction_ratio == 0.8

    def test_custom_values(self):
        cfg = CompactionConfig(
            total_budget=150000,
            per_turn_limit=4096,
            compaction_ratio=0.7,
        )
        assert cfg.total_budget == 150000
        assert cfg.per_turn_limit == 4096
        assert cfg.compaction_ratio == 0.7


# ---------------------------------------------------------------------------
# REQ-BUDGET-006: Snapshot reporting
# ---------------------------------------------------------------------------


class TestSnapshot:
    def test_snapshot_returns_state(self):
        budget = TokenBudget(total_budget=100000, per_turn_limit=4096)
        budget.record(20000, 15000)
        snap = budget.snapshot()
        assert snap["total_budget"] == 100000
        assert snap["used"] == 35000
        assert snap["remaining"] == 65000
        assert abs(snap["usage_ratio"] - 0.35) < 1e-9
