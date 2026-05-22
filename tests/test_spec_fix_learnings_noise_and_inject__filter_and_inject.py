"""Tests for spec: filter-and-inject.md — Learnings Write Validation Gate.

Covers:
- Empty/short takeaway in record_lesson
- daemon.cycle_error pattern_key in record_outcome
- code.unknown pattern_key in record_outcome
- Valid learning written normally
"""

import json

import pytest

from zsiga.memory.learn import record_lesson, record_outcome


@pytest.fixture
def memory_dir(tmp_path, monkeypatch):
    """Patch _MEMORY_DIR to a temp dir so writes go to tmp_path."""
    import zsiga.memory.learn as learn_mod
    monkeypatch.setattr(learn_mod, "_MEMORY_DIR", tmp_path)
    return tmp_path


def _read_jsonl(path):
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    return [json.loads(line) for line in lines if line.strip()]


# ---------------------------------------------------------------
# Scenario: Empty takeaway in record_lesson
# ---------------------------------------------------------------


class TestEmptyTakeawaySkipped:
    def test_empty_takeaway_not_written(self, memory_dir):
        lf = memory_dir / "learnings.jsonl"
        record_lesson(
            title="Some title",
            context="Some context",
            takeaway="",
            pattern_key="pipeline.fail.test",
        )
        assert not lf.exists()

    def test_short_takeaway_not_written(self, memory_dir):
        lf = memory_dir / "learnings.jsonl"
        record_lesson(
            title="Some title",
            context="Some context",
            takeaway="short",  # 5 chars < 10
            pattern_key="pipeline.fail.test",
        )
        assert not lf.exists()

    def test_takeaway_exactly_9_chars_skipped(self, memory_dir):
        lf = memory_dir / "learnings.jsonl"
        record_lesson(
            title="Title",
            context="Ctx",
            takeaway="123456789",  # exactly 9
            pattern_key="pipeline.fail.test",
        )
        assert not lf.exists()


# ---------------------------------------------------------------
# Scenario: daemon.cycle_error pattern_key in record_outcome
# ---------------------------------------------------------------


class TestDaemonCycleErrorSkipped:
    def test_daemon_cycle_error_outcome_not_written(self, memory_dir):
        lf = memory_dir / "learnings.jsonl"
        record_outcome(
            change_name="test-change",
            project="zsiga",
            success=False,
            phase="implement",
            detail="fatal: tag already exists",
            error_domain="daemon",
            root_cause="cycle_error",
            prevention="Skip already-tagged repos",
        )
        assert not lf.exists()

    def test_daemon_cycle_error_prefix_outcome_not_written(self, memory_dir):
        """Any pattern_key starting with daemon.cycle_error is noise."""
        lf = memory_dir / "learnings.jsonl"
        record_outcome(
            change_name="test-change",
            project="zsiga",
            success=False,
            phase="implement",
            detail="some daemon issue",
            error_domain="daemon",
            root_cause="cycle_error.variant",
            prevention="Fix daemon loop",
        )
        assert not lf.exists()


# ---------------------------------------------------------------
# Scenario: code.unknown pattern_key in record_outcome
# ---------------------------------------------------------------


class TestCodeUnknownSkipped:
    def test_code_unknown_outcome_not_written(self, memory_dir):
        lf = memory_dir / "learnings.jsonl"
        record_outcome(
            change_name="test-change",
            project="zsiga",
            success=False,
            phase="implement",
            detail="some unclassifiable error happened here",
            error_domain="code",
            root_cause="unknown",
            prevention="review error and adjust approach",
        )
        assert not lf.exists()


# ---------------------------------------------------------------
# Scenario: Valid learning is written normally
# ---------------------------------------------------------------


class TestValidLearningWritten:
    def test_valid_record_lesson_written(self, memory_dir):
        lf = memory_dir / "learnings.jsonl"
        record_lesson(
            title="Test failure",
            context="implement phase",
            takeaway="Always check for None before accessing attributes",
            pattern_key="pipeline.fail.implement",
        )
        entries = _read_jsonl(lf)
        assert len(entries) == 1
        assert entries[0]["takeaway"] == "Always check for None before accessing attributes"
        assert entries[0]["pattern_key"] == "pipeline.fail.implement"

    def test_valid_record_outcome_written(self, memory_dir):
        lf = memory_dir / "learnings.jsonl"
        record_outcome(
            change_name="test-change",
            project="zsiga",
            success=False,
            phase="implement",
            detail="AssertionError: expected 5 but got 3",
            error_domain="code",
            root_cause="test.assertion",
            prevention="Verify test expectations match implementation",
        )
        entries = _read_jsonl(lf)
        assert len(entries) == 1
        assert entries[0]["pattern_key"] == "code.test.assertion"

    def test_takeaway_exactly_10_chars_written(self, memory_dir):
        lf = memory_dir / "learnings.jsonl"
        record_lesson(
            title="Title",
            context="Ctx",
            takeaway="1234567890",  # exactly 10 chars → boundary
            pattern_key="pipeline.fail.verify",
        )
        entries = _read_jsonl(lf)
        assert len(entries) == 1
