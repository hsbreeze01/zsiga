"""Tests for spec: filter-and-inject.md — One-time Learnings Cleanup.

Covers:
- Remove daemon.cycle_error entries from JSONL
- Remove code.unknown entries from JSONL
- Remove empty-text entries from JSONL
- Remove noisy entries from DB lessons table
- Cleanup is idempotent
"""

import json
from pathlib import Path

import pytest


def _write_jsonl(path: Path, entries: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").strip().split("\n") if line.strip()
    ]


@pytest.fixture
def memory_dir(tmp_path, monkeypatch):
    import zsiga.memory.learn as learn_mod
    monkeypatch.setattr(learn_mod, "_MEMORY_DIR", tmp_path)
    return tmp_path


NOISY_AND_CLEAN = [
    # noisy entries
    {"type": "lesson", "pattern_key": "daemon.cycle_error", "takeaway": "tag already exists", "ts": "2025-01-01T00:00:00"},
    {"type": "lesson", "pattern_key": "code.unknown", "takeaway": "review error and adjust approach", "ts": "2025-01-02T00:00:00"},
    {"type": "lesson", "pattern_key": "pipeline.fail.verify", "takeaway": "", "ts": "2025-01-03T00:00:00"},
    {"type": "lesson", "pattern_key": "pipeline.fail.implement", "takeaway": "short", "ts": "2025-01-04T00:00:00"},
    # clean entries
    {"type": "lesson", "pattern_key": "pipeline.fail.verify.diagnosed", "takeaway": "Diagnosed root cause: missing import", "ts": "2025-01-05T00:00:00"},
    {"type": "lesson", "pattern_key": "pipeline.pass.deliver", "takeaway": "Success pattern: small focused changes", "ts": "2025-01-06T00:00:00"},
    {"type": "lesson", "pattern_key": "pipeline.fail.implement", "takeaway": "Lint E701 error on line 42 caused test failure", "ts": "2025-01-07T00:00:00"},
]


# ---------------------------------------------------------------
# Scenario: Remove daemon.cycle_error entries from JSONL
# ---------------------------------------------------------------


class TestRemoveDaemonCycleErrorFromJsonl:
    def test_daemon_cycle_error_removed(self, memory_dir):
        from zsiga.memory.learn import clean_noisy_learnings
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, NOISY_AND_CLEAN)

        clean_noisy_learnings(str(memory_dir))

        remaining = _read_jsonl(lf)
        assert all(not e.get("pattern_key", "").startswith("daemon.cycle_error") for e in remaining)

    def test_daemon_cycle_error_with_variant_removed(self, memory_dir):
        from zsiga.memory.learn import clean_noisy_learnings
        lf = memory_dir / "learnings.jsonl"
        entries = [
            {"type": "lesson", "pattern_key": "daemon.cycle_error.tag_exists", "takeaway": "noise", "ts": "2025-01-01T00:00:00"},
            {"type": "lesson", "pattern_key": "pipeline.pass.deliver", "takeaway": "Good result to keep", "ts": "2025-01-02T00:00:00"},
        ]
        _write_jsonl(lf, entries)

        clean_noisy_learnings(str(memory_dir))

        remaining = _read_jsonl(lf)
        assert len(remaining) == 1
        assert remaining[0]["pattern_key"] == "pipeline.pass.deliver"


# ---------------------------------------------------------------
# Scenario: Remove code.unknown entries from JSONL
# ---------------------------------------------------------------


class TestRemoveCodeUnknownFromJsonl:
    def test_code_unknown_removed(self, memory_dir):
        from zsiga.memory.learn import clean_noisy_learnings
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, NOISY_AND_CLEAN)

        clean_noisy_learnings(str(memory_dir))

        remaining = _read_jsonl(lf)
        assert all(e.get("pattern_key") != "code.unknown" for e in remaining)


# ---------------------------------------------------------------
# Scenario: Remove empty-text entries from JSONL
# ---------------------------------------------------------------


class TestRemoveEmptyTextFromJsonl:
    def test_empty_takeaway_removed(self, memory_dir):
        from zsiga.memory.learn import clean_noisy_learnings
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, NOISY_AND_CLEAN)

        clean_noisy_learnings(str(memory_dir))

        remaining = _read_jsonl(lf)
        for e in remaining:
            tak = e.get("takeaway", "")
            assert len(tak) >= 10 or tak == "" and False, f"Short takeaway survived: {tak!r}"
            assert len(tak) >= 10, f"Entry with short takeaway survived: {tak!r}"

    def test_short_takeaway_removed(self, memory_dir):
        from zsiga.memory.learn import clean_noisy_learnings
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, NOISY_AND_CLEAN)

        clean_noisy_learnings(str(memory_dir))

        remaining = _read_jsonl(lf)
        assert all(len(e.get("takeaway", "")) >= 10 for e in remaining)


# ---------------------------------------------------------------
# Scenario: Remove noisy entries from DB lessons table
# ---------------------------------------------------------------


class TestRemoveNoisyFromDb:
    def test_daemon_cycle_error_removed_from_db(self, tmp_path):
        from zsiga.metrics.db import _get_conn, record_lesson as db_record_lesson
        from zsiga.memory.learn import clean_noisy_learnings

        db_path = tmp_path / "test.db"
        conn = _get_conn(db_path)
        conn.close()

        # Insert noisy entries
        db_record_lesson(text="valid lesson text here", pattern_key="daemon.cycle_error", db_path=db_path)
        db_record_lesson(text="another valid lesson", pattern_key="code.unknown", db_path=db_path)
        db_record_lesson(text="keep this one intact please", pattern_key="pipeline.fail.verify", db_path=db_path)

        # Clean with db_path provided
        clean_noisy_learnings(str(tmp_path), db_path=db_path)

        conn = _get_conn(db_path)
        remaining = conn.execute("SELECT pattern_key FROM lessons").fetchall()
        conn.close()

        keys = [r["pattern_key"] for r in remaining]
        assert "daemon.cycle_error" not in keys
        assert "code.unknown" not in keys
        assert "pipeline.fail.verify" in keys


# ---------------------------------------------------------------
# Scenario: Cleanup is idempotent
# ---------------------------------------------------------------


class TestCleanupIdempotent:
    def test_double_cleanup_same_result(self, memory_dir):
        from zsiga.memory.learn import clean_noisy_learnings
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, NOISY_AND_CLEAN)

        clean_noisy_learnings(str(memory_dir))
        first_remaining = _read_jsonl(lf)

        clean_noisy_learnings(str(memory_dir))
        second_remaining = _read_jsonl(lf)

        assert len(first_remaining) == len(second_remaining)
        assert first_remaining == second_remaining
