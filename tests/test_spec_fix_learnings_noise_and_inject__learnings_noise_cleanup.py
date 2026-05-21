"""Tests for spec: learnings-noise-cleanup.

Covers JSONL and DB cleanup of noisy learnings records.
"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest


def _write_jsonl(fpath: Path, records: list[dict]):
    with open(fpath, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _read_jsonl(fpath: Path) -> list[dict]:
    records = []
    with open(fpath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# JSONL noise cleanup
# ---------------------------------------------------------------------------

class TestCleanupLearningsJsonl:
    """Verify cleanup_learnings_jsonl removes noisy records."""

    def test_removes_empty_takeaway_records(self, tmp_path):
        jsonl = tmp_path / "learnings.jsonl"
        _write_jsonl(jsonl, [
            {"pattern_key": "test.pk", "takeaway": ""},
            {"pattern_key": "valid.pk", "takeaway": "a valid takeaway"},
        ])
        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path):
            from zsiga.memory.learn import cleanup_learnings_jsonl
            summary = cleanup_learnings_jsonl()
        remaining = _read_jsonl(jsonl)
        assert len(remaining) == 1
        assert remaining[0]["pattern_key"] == "valid.pk"
        assert summary["removed"] == 1
        assert summary["kept"] == 1

    def test_removes_daemon_cycle_error_records(self, tmp_path):
        jsonl = tmp_path / "learnings.jsonl"
        _write_jsonl(jsonl, [
            {"pattern_key": "daemon.cycle_error", "takeaway": "some text"},
            {"pattern_key": "valid.pk", "takeaway": "a valid takeaway"},
        ])
        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path):
            from zsiga.memory.learn import cleanup_learnings_jsonl
            summary = cleanup_learnings_jsonl()
        remaining = _read_jsonl(jsonl)
        assert len(remaining) == 1
        assert remaining[0]["pattern_key"] == "valid.pk"
        assert summary["removed"] == 1

    def test_removes_code_unknown_records(self, tmp_path):
        jsonl = tmp_path / "learnings.jsonl"
        _write_jsonl(jsonl, [
            {"pattern_key": "code.unknown", "takeaway": "some text"},
            {"pattern_key": "valid.pk", "takeaway": "a valid takeaway"},
        ])
        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path):
            from zsiga.memory.learn import cleanup_learnings_jsonl
            summary = cleanup_learnings_jsonl()
        remaining = _read_jsonl(jsonl)
        assert len(remaining) == 1
        assert remaining[0]["pattern_key"] == "valid.pk"
        assert summary["removed"] == 1

    def test_preserves_valid_records(self, tmp_path):
        jsonl = tmp_path / "learnings.jsonl"
        _write_jsonl(jsonl, [
            {"pattern_key": "pipeline.fail.implement", "takeaway": "lesson 1"},
            {"pattern_key": "ops.service_management", "takeaway": "lesson 2"},
            {"pattern_key": "pipeline.pass.deliver", "takeaway": "lesson 3"},
        ])
        with patch("zsiga.memory.learn._MEMORY_DIR", tmp_path):
            from zsiga.memory.learn import cleanup_learnings_jsonl
            summary = cleanup_learnings_jsonl()
        remaining = _read_jsonl(jsonl)
        assert len(remaining) == 3
        assert summary["removed"] == 0
        assert summary["kept"] == 3


# ---------------------------------------------------------------------------
# DB lessons cleanup
# ---------------------------------------------------------------------------

class TestDBCleanupLessons:
    """Verify DB cleanup_lessons removes noisy rows."""

    @pytest.fixture(autouse=True)
    def _setup_db(self, tmp_path):
        self.db_path = tmp_path / "test.db"
        with patch("zsiga.metrics.db._DB_PATH", self.db_path):
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

    def _insert(self, pattern_key: str, text: str):
        from zsiga.metrics.db import _get_conn
        conn = _get_conn(self.db_path)
        conn.execute(
            "INSERT INTO lessons (ts, pattern_key, text) VALUES (?, ?, ?)",
            ("2026-01-01T00:00:00", pattern_key, text),
        )
        conn.commit()
        conn.close()

    def _count(self):
        from zsiga.metrics.db import count_lessons
        return count_lessons(db_path=self.db_path)

    def test_removes_blacklisted_db_lessons(self):
        self._insert("daemon.cycle_error", "some text")
        self._insert("pipeline.fail.implement", "valid text")
        from zsiga.metrics.db import cleanup_lessons
        cleanup_lessons(db_path=self.db_path)
        assert self._count() == 1

    def test_removes_empty_text_db_lessons(self):
        self._insert("pipeline.fail.implement", "")
        self._insert("pipeline.fail.implement", "valid text")
        from zsiga.metrics.db import cleanup_lessons
        cleanup_lessons(db_path=self.db_path)
        assert self._count() == 1
