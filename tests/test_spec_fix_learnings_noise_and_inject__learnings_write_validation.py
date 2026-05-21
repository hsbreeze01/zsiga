"""Tests for spec: learnings-write-validation.

Covers text length gate, pattern key blacklist, and DB write validation.
"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# record_lesson in zsiga.memory.learn — text length gate
# ---------------------------------------------------------------------------

class TestRecordLessonTextLengthGate:
    """Verify record_lesson skips entries with empty or short takeaway."""

    def _count_lines(self, fpath: Path) -> int:
        return sum(1 for _ in fpath.open() if _.strip())

    def test_empty_takeaway_rejected(self, tmp_path):
        jsonl = tmp_path / "learnings.jsonl"
        jsonl.write_text("", encoding="utf-8")
        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path):
            from zsiga.memory.learn import record_lesson
            record_lesson(
                title="x", context="y", takeaway="",
                pattern_key="test.pk",
            )
        assert self._count_lines(jsonl) == 0

    def test_short_takeaway_rejected(self, tmp_path):
        jsonl = tmp_path / "learnings.jsonl"
        jsonl.write_text("", encoding="utf-8")
        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path):
            from zsiga.memory.learn import record_lesson
            record_lesson(
                title="x", context="y", takeaway="short",
                pattern_key="test.pk",
            )
        assert self._count_lines(jsonl) == 0

    def test_valid_takeaway_written(self, tmp_path):
        jsonl = tmp_path / "learnings.jsonl"
        jsonl.write_text("", encoding="utf-8")
        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path):
            from zsiga.memory.learn import record_lesson
            record_lesson(
                title="x", context="y",
                takeaway="this is a valid takeaway text",
                pattern_key="test.pk",
            )
        assert self._count_lines(jsonl) == 1
        last = jsonl.read_text().strip().split("\n")[-1]
        entry = json.loads(last)
        assert entry["takeaway"] == "this is a valid takeaway text"


# ---------------------------------------------------------------------------
# record_lesson — pattern key blacklist gate
# ---------------------------------------------------------------------------

class TestRecordLessonBlacklistGate:
    """Verify record_lesson skips entries with blacklisted pattern_key."""

    def _count_lines(self, fpath: Path) -> int:
        return sum(1 for _ in fpath.open() if _.strip())

    def test_daemon_cycle_error_rejected(self, tmp_path):
        jsonl = tmp_path / "learnings.jsonl"
        jsonl.write_text("", encoding="utf-8")
        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path):
            from zsiga.memory.learn import record_lesson
            record_lesson(
                title="x", context="y",
                takeaway="a sufficiently long takeaway message",
                pattern_key="daemon.cycle_error",
            )
        assert self._count_lines(jsonl) == 0

    def test_daemon_cycle_error_prefix_rejected(self, tmp_path):
        jsonl = tmp_path / "learnings.jsonl"
        jsonl.write_text("", encoding="utf-8")
        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path):
            from zsiga.memory.learn import record_lesson
            record_lesson(
                title="x", context="y",
                takeaway="a sufficiently long takeaway message",
                pattern_key="daemon.cycle_error.git_checkout",
            )
        assert self._count_lines(jsonl) == 0

    def test_non_blacklisted_pattern_written(self, tmp_path):
        jsonl = tmp_path / "learnings.jsonl"
        jsonl.write_text("", encoding="utf-8")
        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path):
            from zsiga.memory.learn import record_lesson
            record_lesson(
                title="x", context="y",
                takeaway="a sufficiently long takeaway",
                pattern_key="pipeline.fail.implement",
            )
        assert self._count_lines(jsonl) == 1


# ---------------------------------------------------------------------------
# DB record_lesson validation in zsiga.metrics.db
# ---------------------------------------------------------------------------

class TestDBRecordLessonValidation:
    """Verify DB record_lesson applies the same gates."""

    @pytest.fixture(autouse=True)
    def _use_tmp_db(self, tmp_path):
        self.db_path = tmp_path / "test.db"
        with patch("zsiga.metrics.db._DB_PATH", self.db_path):
            # Initialize schema
            from zsiga.metrics.db import _get_conn
            conn = _get_conn(self.db_path)
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS lessons (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts          TEXT NOT NULL,
                    pattern_key TEXT DEFAULT '',
                    category    TEXT DEFAULT '',
                    text        TEXT NOT NULL,
                    created_at  TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f','now'))
                );
                """
            )
            conn.close()
            yield

    def _count(self):
        from zsiga.metrics.db import count_lessons
        return count_lessons(db_path=self.db_path)

    def test_db_rejects_blacklisted_pattern(self):
        from zsiga.metrics.db import record_lesson
        record_lesson(text="some text", pattern_key="daemon.cycle_error",
                      db_path=self.db_path)
        assert self._count() == 0

    def test_db_accepts_valid_entry(self):
        from zsiga.metrics.db import record_lesson
        record_lesson(text="valid lesson text here",
                      pattern_key="pipeline.fail.implement",
                      db_path=self.db_path)
        assert self._count() == 1

    def test_db_rejects_empty_text(self):
        from zsiga.metrics.db import record_lesson
        record_lesson(text="", pattern_key="pipeline.fail.implement",
                      db_path=self.db_path)
        assert self._count() == 0
