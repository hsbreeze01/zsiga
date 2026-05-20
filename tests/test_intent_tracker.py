"""Tests for zsiga.metrics.intent_tracker — Intent accuracy tracking CRUD and computation."""

import pytest

from zsiga.metrics.intent_tracker import (
    record_intent_decision,
    update_intent_outcome,
    update_intent_reclassification,
    compute_intent_accuracy,
    get_rolling_accuracy,
)


@pytest.fixture
def db_path(tmp_path):
    """Provide a temporary database path."""
    return tmp_path / "test.db"


# ── record_intent_decision ──────────────────────────────────


class TestRecordIntentDecision:
    def test_insert_returns_row_id(self, db_path):
        row_id = record_intent_decision(
            change_name="test-change",
            project="zsiga",
            predicted_intent="implementation",
            confidence=0.85,
            classification_source="keyword",
            verbalization="User wants to implement",
            reasoning="关键词匹配",
            db_path=db_path,
        )
        assert isinstance(row_id, int)
        assert row_id >= 1

    def test_default_source_is_keyword(self, db_path):
        record_intent_decision(
            change_name="c1", project="p", predicted_intent="fix",
            confidence=0.9, db_path=db_path,
        )
        stats = compute_intent_accuracy(db_path=db_path)
        assert stats["total_classified"] == 1

    def test_multiple_records(self, db_path):
        for i in range(3):
            record_intent_decision(
                change_name=f"c{i}", project="p", predicted_intent="implementation",
                confidence=0.8, db_path=db_path,
            )
        stats = compute_intent_accuracy(db_path=db_path)
        assert stats["total_classified"] == 3


# ── update_intent_outcome ───────────────────────────────────


class TestUpdateIntentOutcome:
    def test_update_sets_outcome_and_correctness(self, db_path):
        record_intent_decision(
            change_name="c1", project="p", predicted_intent="implementation",
            confidence=0.85, classification_source="keyword",
            db_path=db_path,
        )
        update_intent_outcome("c1", actual_outcome="success", is_correct=True, db_path=db_path)
        stats = compute_intent_accuracy(db_path=db_path)
        assert stats["total_resolved"] == 1
        assert stats["correct_count"] == 1
        assert stats["accuracy_pct"] == 100.0

    def test_update_with_failure(self, db_path):
        record_intent_decision(
            change_name="c1", project="p", predicted_intent="fix",
            confidence=0.7, db_path=db_path,
        )
        update_intent_outcome("c1", actual_outcome="reverted", is_correct=False, db_path=db_path)
        stats = compute_intent_accuracy(db_path=db_path)
        assert stats["total_resolved"] == 1
        assert stats["correct_count"] == 0
        assert stats["accuracy_pct"] == 0.0

    def test_openspec_override_always_correct(self, db_path):
        record_intent_decision(
            change_name="c1", project="p", predicted_intent="implementation",
            confidence=0.95, classification_source="openspec_override",
            db_path=db_path,
        )
        # Even if we pass is_correct=False
        update_intent_outcome("c1", actual_outcome="success", is_correct=False, db_path=db_path)
        stats = compute_intent_accuracy(db_path=db_path)
        assert stats["correct_count"] == 1
        assert stats["accuracy_pct"] == 100.0

    def test_missing_row_is_noop(self, db_path):
        """No row for change_name → no crash, no error."""
        update_intent_outcome("nonexistent", actual_outcome="success", is_correct=True, db_path=db_path)
        stats = compute_intent_accuracy(db_path=db_path)
        assert stats["total_classified"] == 0


# ── update_intent_reclassification ──────────────────────────


class TestUpdateIntentReclassification:
    def test_reclassification_updates_row(self, db_path):
        row_id = record_intent_decision(
            change_name="c1", project="p", predicted_intent="implementation",
            confidence=0.5, db_path=db_path,
        )
        update_intent_reclassification(
            row_id, reclassified_from="implementation", reclassified_to="fix",
            db_path=db_path,
        )
        # Verify by checking accuracy (the record still exists)
        stats = compute_intent_accuracy(db_path=db_path)
        assert stats["total_classified"] == 1


# ── compute_intent_accuracy ─────────────────────────────────


class TestComputeIntentAccuracy:
    def test_empty_table(self, db_path):
        stats = compute_intent_accuracy(db_path=db_path)
        assert stats["total_classified"] == 0
        assert stats["total_resolved"] == 0
        assert stats["correct_count"] == 0
        assert stats["accuracy_pct"] == 0.0
        assert stats["by_intent"] == {}
        assert stats["low_confidence_count"] == 0

    def test_mixed_outcomes(self, db_path):
        # 2 correct, 1 incorrect
        for i, (outcome, correct) in enumerate([
            ("success", True), ("reverted", False), ("success", True),
        ]):
            record_intent_decision(
                change_name=f"c{i}", project="p", predicted_intent="implementation",
                confidence=0.8, db_path=db_path,
            )
            update_intent_outcome(f"c{i}", actual_outcome=outcome, is_correct=correct, db_path=db_path)

        stats = compute_intent_accuracy(db_path=db_path)
        assert stats["total_classified"] == 3
        assert stats["total_resolved"] == 3
        assert stats["correct_count"] == 2
        assert stats["accuracy_pct"] == 66.7

    def test_low_confidence_count(self, db_path):
        record_intent_decision(
            change_name="c1", project="p", predicted_intent="open-ended",
            confidence=0.3, db_path=db_path,
        )
        record_intent_decision(
            change_name="c2", project="p", predicted_intent="implementation",
            confidence=0.8, db_path=db_path,
        )
        stats = compute_intent_accuracy(db_path=db_path)
        assert stats["low_confidence_count"] == 1

    def test_by_intent_breakdown(self, db_path):
        record_intent_decision(
            change_name="c1", project="p", predicted_intent="implementation",
            confidence=0.9, db_path=db_path,
        )
        update_intent_outcome("c1", "success", True, db_path=db_path)

        record_intent_decision(
            change_name="c2", project="p", predicted_intent="fix",
            confidence=0.7, db_path=db_path,
        )
        update_intent_outcome("c2", "reverted", False, db_path=db_path)

        stats = compute_intent_accuracy(db_path=db_path)
        assert "implementation" in stats["by_intent"]
        assert stats["by_intent"]["implementation"]["accuracy_pct"] == 100.0
        assert "fix" in stats["by_intent"]
        assert stats["by_intent"]["fix"]["accuracy_pct"] == 0.0

    def test_unresolved_not_counted_in_accuracy(self, db_path):
        record_intent_decision(
            change_name="c1", project="p", predicted_intent="implementation",
            confidence=0.9, db_path=db_path,
        )
        # Don't call update_intent_outcome → is_correct stays NULL
        stats = compute_intent_accuracy(db_path=db_path)
        assert stats["total_classified"] == 1
        assert stats["total_resolved"] == 0
        assert stats["accuracy_pct"] == 0.0


# ── get_rolling_accuracy ────────────────────────────────────


class TestGetRollingAccuracy:
    def test_empty_table(self, db_path):
        result = get_rolling_accuracy(window=20, db_path=db_path)
        assert result["accuracy_pct"] == 0.0
        assert result["total"] == 0

    def test_rolling_window(self, db_path):
        # Insert 10 records, 6 correct
        for i in range(10):
            record_intent_decision(
                change_name=f"c{i}", project="p", predicted_intent="implementation",
                confidence=0.8, db_path=db_path,
            )
            update_intent_outcome(
                f"c{i}", "success" if i < 6 else "reverted",
                is_correct=(i < 6), db_path=db_path,
            )
        result = get_rolling_accuracy(window=5, db_path=db_path)
        # Last 5 records: c5-correct, c6-incorrect, c7-incorrect, c8-incorrect, c9-incorrect
        # That's 1 correct out of 5 = 20.0%
        assert result["total"] == 5
        assert result["accuracy_pct"] == 20.0

    def test_per_intent_rolling(self, db_path):
        for i in range(5):
            record_intent_decision(
                change_name=f"c{i}", project="p",
                predicted_intent="implementation" if i < 3 else "fix",
                confidence=0.8, db_path=db_path,
            )
            update_intent_outcome(
                f"c{i}", "success" if i % 2 == 0 else "reverted",
                is_correct=(i % 2 == 0), db_path=db_path,
            )
        result = get_rolling_accuracy(window=20, db_path=db_path)
        assert "implementation" in result["by_intent"]
        assert "fix" in result["by_intent"]
