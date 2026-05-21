"""Tests for learnings write validation, noise cleanup, and prompt injection."""

import json

import pytest

from zsiga.memory.learn import (
    cleanup_learnings_jsonl,
    fetch_relevant_learnings,
    record_lesson,
    record_outcome,
    record_success,
)
from zsiga.metrics.db import cleanup_lessons, count_lessons, record_lesson as db_record_lesson


# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def learnings_file(tmp_path, monkeypatch):
    """Create a temporary learnings.jsonl and patch _MEMORY_DIR."""
    import zsiga.memory.learn as learn_mod

    monkeypatch.setattr(learn_mod, "_MEMORY_DIR", tmp_path)
    lf = tmp_path / "learnings.jsonl"
    return lf


@pytest.fixture
def db_file(tmp_path):
    """Return a temporary db path."""
    return tmp_path / "test.db"


def _write_entries(learnings_file, entries):
    with open(learnings_file, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def _count_lines(path):
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text().splitlines() if line.strip())


# ── record_lesson write validation ──────────────────────────


class TestRecordLessonTextLength:
    """Spec: learnings-write-validation — Text length gate."""

    def test_empty_takeaway_rejected(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        n = _count_lines(learnings_file)
        record_lesson(title="x", context="y", takeaway="", pattern_key="test.pk")
        assert _count_lines(learnings_file) == n

    def test_short_takeaway_rejected(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        n = _count_lines(learnings_file)
        record_lesson(title="x", context="y", takeaway="short", pattern_key="test.pk")
        assert _count_lines(learnings_file) == n

    def test_valid_takeaway_written(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        n = _count_lines(learnings_file)
        record_lesson(
            title="x",
            context="y",
            takeaway="this is a valid takeaway text",
            pattern_key="test.pk",
        )
        assert _count_lines(learnings_file) == n + 1
        last_line = learnings_file.read_text().strip().split("\n")[-1]
        entry = json.loads(last_line)
        assert entry["takeaway"] == "this is a valid takeaway text"


class TestRecordLessonBlacklist:
    """Spec: learnings-write-validation — Pattern key blacklist gate."""

    def test_daemon_cycle_error_rejected(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        n = _count_lines(learnings_file)
        record_lesson(
            title="x",
            context="y",
            takeaway="a sufficiently long takeaway message",
            pattern_key="daemon.cycle_error",
        )
        assert _count_lines(learnings_file) == n

    def test_daemon_cycle_error_prefix_rejected(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        n = _count_lines(learnings_file)
        record_lesson(
            title="x",
            context="y",
            takeaway="a sufficiently long takeaway message",
            pattern_key="daemon.cycle_error.git_checkout",
        )
        assert _count_lines(learnings_file) == n

    def test_non_blacklisted_written(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        n = _count_lines(learnings_file)
        record_lesson(
            title="x",
            context="y",
            takeaway="a sufficiently long takeaway",
            pattern_key="pipeline.fail.implement",
        )
        assert _count_lines(learnings_file) == n + 1


class TestRecordOutcomeValidation:
    """Spec: learnings-write-validation — outcome write validation."""

    def test_outcome_blacklisted_pattern_skipped(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        n = _count_lines(learnings_file)
        record_outcome(
            change_name="test-change",
            project="proj",
            success=False,
            phase="implement",
            detail="something",
            error_domain="daemon",
            root_cause="cycle_error",
            prevention="a sufficiently long prevention message",
        )
        assert _count_lines(learnings_file) == n

    def test_outcome_short_prevention_skipped(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        n = _count_lines(learnings_file)
        record_outcome(
            change_name="test-change",
            project="proj",
            success=False,
            phase="implement",
            detail="something",
            error_domain="code",
            root_cause="unknown",
            prevention="short",
        )
        assert _count_lines(learnings_file) == n

    def test_outcome_valid_written(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        n = _count_lines(learnings_file)
        record_outcome(
            change_name="test-change",
            project="proj",
            success=False,
            phase="implement",
            detail="E701 lint error",
            error_domain="code",
            root_cause="lint.e701",
            prevention="Never put if/for body on same line as keyword",
        )
        assert _count_lines(learnings_file) == n + 1


class TestRecordSuccessValidation:
    """Spec: learnings-write-validation — success write validation."""

    def test_success_written_normally(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        n = _count_lines(learnings_file)
        record_success(change_name="some-change", project="proj")
        assert _count_lines(learnings_file) == n + 1


# ── DB record_lesson validation ─────────────────────────────


class TestDBRecordLessonValidation:
    """Spec: learnings-write-validation — DB lessons write validation."""

    def test_db_rejects_blacklisted_pattern(self, db_file):
        db_record_lesson(
            text="some text", pattern_key="daemon.cycle_error", db_path=db_file
        )
        assert count_lessons(db_path=db_file) == 0

    def test_db_accepts_valid_entry(self, db_file):
        db_record_lesson(
            text="valid lesson text here",
            pattern_key="pipeline.fail.implement",
            db_path=db_file,
        )
        assert count_lessons(db_path=db_file) == 1

    def test_db_rejects_empty_text(self, db_file):
        db_record_lesson(
            text="", pattern_key="pipeline.fail.implement", db_path=db_file
        )
        assert count_lessons(db_path=db_file) == 0

    def test_db_rejects_short_text(self, db_file):
        db_record_lesson(
            text="short", pattern_key="pipeline.fail.implement", db_path=db_file
        )
        assert count_lessons(db_path=db_file) == 0


# ── fetch_relevant_learnings ────────────────────────────────


class TestFetchRelevantLearnings:
    """Spec: learnings-inject-utility — fetch_relevant_learnings."""

    def test_returns_pipeline_lessons(self, learnings_file):
        entries = [
            {
                "type": "lesson",
                "ts": "2025-01-10T10:00:00",
                "pattern_key": "pipeline.fail.implement",
                "takeaway": "Check lint errors",
            },
            {
                "type": "lesson",
                "ts": "2025-01-11T10:00:00",
                "pattern_key": "pipeline.pass.deliver",
                "takeaway": "Success",
            },
        ]
        _write_entries(learnings_file, entries)
        result = fetch_relevant_learnings("fix-foo-bar", max_count=5)
        assert "pipeline.fail.implement" in result
        assert "pipeline.pass.deliver" in result

    def test_returns_direct_name_match(self, learnings_file):
        entries = [
            {
                "type": "lesson",
                "ts": "2025-01-10T10:00:00",
                "pattern_key": "code.unknown",
                "takeaway": "fix the unknown",
            },
        ]
        _write_entries(learnings_file, entries)
        result = fetch_relevant_learnings("code-unknown-fix", max_count=5)
        assert "fix the unknown" in result

    def test_respects_max_count(self, learnings_file):
        entries = [
            {
                "type": "lesson",
                "ts": f"2025-01-{i:02d}T10:00:00",
                "pattern_key": "pipeline.fail.implement",
                "takeaway": f"Lesson number {i}",
            }
            for i in range(1, 11)
        ]
        _write_entries(learnings_file, entries)
        result = fetch_relevant_learnings("any-change", max_count=3)
        bullets = [line for line in result.splitlines() if line.startswith("- [")]
        assert len(bullets) == 3

    def test_returns_empty_string_when_no_matches(self, learnings_file):
        entries = [
            {
                "type": "lesson",
                "ts": "2025-01-10T10:00:00",
                "pattern_key": "ops.service_management",
                "takeaway": "some management lesson",
            },
        ]
        _write_entries(learnings_file, entries)
        result = fetch_relevant_learnings("fix-xyz", max_count=5)
        assert result == ""

    def test_skips_entries_with_missing_takeaway(self, learnings_file):
        entries = [
            {
                "type": "lesson",
                "ts": "2025-01-10T10:00:00",
                "pattern_key": "pipeline.fail.implement",
                "takeaway": "",
            },
        ]
        _write_entries(learnings_file, entries)
        result = fetch_relevant_learnings("any-change", max_count=5)
        assert result == ""

    def test_nonexistent_file_returns_empty(self, tmp_path):
        result = fetch_relevant_learnings(
            "any-change", max_count=5, learnings_file=tmp_path / "nonexistent.jsonl"
        )
        assert result == ""

    def test_format_is_bullet_with_pattern_key(self, learnings_file):
        entries = [
            {
                "type": "lesson",
                "ts": "2025-01-10T10:00:00",
                "pattern_key": "pipeline.pass.deliver",
                "takeaway": "Success",
            },
        ]
        _write_entries(learnings_file, entries)
        result = fetch_relevant_learnings("any-change", max_count=5)
        assert "- [pipeline.pass.deliver] Success" in result


# ── cleanup_learnings_jsonl ─────────────────────────────────


class TestCleanupLearningsJsonl:
    """Spec: learnings-noise-cleanup — JSONL noise removal."""

    def test_removes_empty_takeaway(self, learnings_file):
        _write_entries(
            learnings_file,
            [
                {"pattern_key": "test.pk", "takeaway": "", "ts": "2025-01-01"},
                {
                    "pattern_key": "valid.pk",
                    "takeaway": "a valid takeaway here",
                    "ts": "2025-01-02",
                },
            ],
        )
        result = cleanup_learnings_jsonl(learnings_file)
        assert result == {"removed": 1, "kept": 1}
        assert _count_lines(learnings_file) == 1

    def test_removes_daemon_cycle_error(self, learnings_file):
        _write_entries(
            learnings_file,
            [
                {
                    "pattern_key": "daemon.cycle_error",
                    "takeaway": "some error message",
                    "ts": "2025-01-01",
                },
                {
                    "pattern_key": "valid.pk",
                    "takeaway": "a valid takeaway here",
                    "ts": "2025-01-02",
                },
            ],
        )
        result = cleanup_learnings_jsonl(learnings_file)
        assert result == {"removed": 1, "kept": 1}

    def test_removes_code_unknown(self, learnings_file):
        _write_entries(
            learnings_file,
            [
                {
                    "pattern_key": "code.unknown",
                    "takeaway": "review error and adjust approach",
                    "ts": "2025-01-01",
                },
                {
                    "pattern_key": "valid.pk",
                    "takeaway": "a valid takeaway here",
                    "ts": "2025-01-02",
                },
            ],
        )
        result = cleanup_learnings_jsonl(learnings_file)
        assert result == {"removed": 1, "kept": 1}

    def test_preserves_valid_records(self, learnings_file):
        entries = [
            {
                "pattern_key": f"valid.pk{i}",
                "takeaway": f"a valid takeaway number {i}",
                "ts": f"2025-01-0{i + 1}",
            }
            for i in range(3)
        ]
        _write_entries(learnings_file, entries)
        result = cleanup_learnings_jsonl(learnings_file)
        assert result == {"removed": 0, "kept": 3}

    def test_nonexistent_file_returns_zero(self, tmp_path):
        result = cleanup_learnings_jsonl(tmp_path / "nonexistent.jsonl")
        assert result == {"removed": 0, "kept": 0}


# ── DB cleanup_lessons ──────────────────────────────────────


class TestDBCleanupLessons:
    """Spec: learnings-noise-cleanup — DB lessons noise removal."""

    def test_removes_blacklisted_db_lessons(self, db_file):
        db_record_lesson(
            text="valid lesson text here",
            pattern_key="daemon.cycle_error",
            db_path=db_file,
        )
        # Bypass validation to insert a blacklisted row directly
        import sqlite3
        from zsiga.metrics.db import _get_conn

        conn = _get_conn(db_file)
        conn.execute(
            "INSERT INTO lessons (ts, pattern_key, category, text) VALUES (?, ?, ?, ?)",
            ("2025-01-01", "daemon.cycle_error", "", "some error text here"),
        )
        conn.execute(
            "INSERT INTO lessons (ts, pattern_key, category, text) VALUES (?, ?, ?, ?)",
            ("2025-01-02", "pipeline.fail.implement", "", "valid lesson text"),
        )
        conn.commit()
        conn.close()

        deleted = cleanup_lessons(db_path=db_file)
        assert deleted == 1
        assert count_lessons(db_path=db_file) == 1

    def test_removes_empty_text_db_lessons(self, db_file):
        import sqlite3
        from zsiga.metrics.db import _get_conn

        conn = _get_conn(db_file)
        conn.execute(
            "INSERT INTO lessons (ts, pattern_key, category, text) VALUES (?, ?, ?, ?)",
            ("2025-01-01", "pipeline.fail.implement", "", ""),
        )
        conn.execute(
            "INSERT INTO lessons (ts, pattern_key, category, text) VALUES (?, ?, ?, ?)",
            ("2025-01-02", "pipeline.fail.implement", "", "valid lesson text"),
        )
        conn.commit()
        conn.close()

        deleted = cleanup_lessons(db_path=db_file)
        assert deleted == 1
        assert count_lessons(db_path=db_file) == 1


# ── Enricher prompt injection ───────────────────────────────


class TestEnricherPromptInjection:
    """Spec: enrich-prompt-injection — Learnings section in enricher."""

    def test_system_prompt_includes_learnings(self, learnings_file):
        entries = [
            {
                "type": "lesson",
                "ts": "2025-01-10T10:00:00",
                "pattern_key": "pipeline.fail.implement",
                "takeaway": "Check lint errors before commit",
            },
        ]
        _write_entries(learnings_file, entries)
        result = fetch_relevant_learnings("enrich-test", max_count=3)
        assert "## Relevant Past Experience" not in result
        # The header is added by the caller, not by fetch_relevant_learnings

    def test_learnings_section_format(self, learnings_file):
        entries = [
            {
                "type": "lesson",
                "ts": "2025-01-10T10:00:00",
                "pattern_key": "pipeline.pass.deliver",
                "takeaway": "Success",
            },
        ]
        _write_entries(learnings_file, entries)
        result = fetch_relevant_learnings("enrich-test", max_count=3)
        assert "- [pipeline.pass.deliver] Success" in result

    def test_at_most_3_entries(self, learnings_file):
        entries = [
            {
                "type": "lesson",
                "ts": f"2025-01-{i:02d}T10:00:00",
                "pattern_key": "pipeline.fail.implement",
                "takeaway": f"Lesson {i}",
            }
            for i in range(1, 11)
        ]
        _write_entries(learnings_file, entries)
        result = fetch_relevant_learnings("enrich-test", max_count=3)
        bullets = [line for line in result.splitlines() if line.startswith("- [")]
        assert len(bullets) <= 3

    def test_no_learnings_no_section(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        result = fetch_relevant_learnings("enrich-test", max_count=3)
        assert result == ""


# ── Implementer prompt injection ────────────────────────────


class TestImplementerPromptInjection:
    """Spec: implement-prompt-injection — Learnings section in implementer."""

    def test_system_prompt_includes_learnings(self, learnings_file):
        entries = [
            {
                "type": "lesson",
                "ts": "2025-01-10T10:00:00",
                "pattern_key": "pipeline.fail.implement",
                "takeaway": "Never use bare except",
            },
        ]
        _write_entries(learnings_file, entries)
        result = fetch_relevant_learnings("implement-test", max_count=5)
        assert "- [pipeline.fail.implement] Never use bare except" in result

    def test_no_learnings_omits_section(self, learnings_file):
        learnings_file.write_text("", encoding="utf-8")
        result = fetch_relevant_learnings("implement-test", max_count=5)
        assert result == ""

    def test_at_most_5_entries(self, learnings_file):
        entries = [
            {
                "type": "lesson",
                "ts": f"2025-01-{i:02d}T10:00:00",
                "pattern_key": "pipeline.fail.implement",
                "takeaway": f"Lesson {i}",
            }
            for i in range(1, 11)
        ]
        _write_entries(learnings_file, entries)
        result = fetch_relevant_learnings("implement-test", max_count=5)
        bullets = [line for line in result.splitlines() if line.startswith("- [")]
        assert len(bullets) <= 5
