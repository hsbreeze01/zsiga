"""Tests for session summary export (export_session, load_sessions)."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from zsiga.metrics.db import _get_conn
from zsiga.memory.journal import export_session, load_sessions


@pytest.fixture
def tmp_env(tmp_path, monkeypatch):
    """Set up isolated temp dirs for DB, memory/sessions, and learnings.jsonl."""
    db_path = tmp_path / "zsiga.db"
    memory_dir = tmp_path / "memory"
    sessions_dir = memory_dir / "sessions"
    learnings_file = memory_dir / "learnings.jsonl"

    monkeypatch.setattr("zsiga.memory.journal._db_load_changes", lambda db_path=None: _load_changes(db_path or db_path))
    monkeypatch.setattr("zsiga.memory.journal._SESSIONS_DIR", sessions_dir)
    monkeypatch.setattr("zsiga.memory.journal._MEMORY_DIR", memory_dir)

    return {
        "db_path": db_path,
        "memory_dir": memory_dir,
        "sessions_dir": sessions_dir,
        "learnings_file": learnings_file,
    }


def _load_changes(db_path: Path) -> list[dict]:
    """Helper to load changes from a specific DB path."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute("SELECT * FROM changes ORDER BY id ASC").fetchall()
        results = []
        for r in rows:
            row = dict(r)
            results.append({
                "change_name": row["change_name"],
                "project": row["project"],
                "outcome": row["outcome"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "lessons_count": row["lessons_count"],
                "phases": json.loads(row["phases_json"]) if row["phases_json"] else [],
            })
        return results
    finally:
        conn.close()


def _insert_change(db_path: Path, change_name: str, project: str = "test-project",
                   outcome: str = "success", phases: list = None):
    """Insert a change record directly into the test DB."""
    phases_json = json.dumps(phases or [], ensure_ascii=False)
    conn = _get_conn(db_path)
    try:
        conn.execute(
            """INSERT INTO changes (change_name, project, outcome, started_at,
               finished_at, lessons_count, phases_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                change_name,
                project,
                outcome,
                "2026-05-15T14:00:00",
                "2026-05-15T14:05:00",
                0,
                phases_json,
            ),
        )
        conn.commit()
    finally:
        conn.close()


class TestExportSession:
    def test_export_writes_correct_json_structure(self, tmp_env):
        """REQ-SE-01/02: Export writes a JSON file with all required keys."""
        db_path = tmp_env["db_path"]
        _insert_change(db_path, "add-health-endpoint", phases=[
            {
                "phase": "enrich",
                "outcome": "success",
                "turns_used": 3,
                "seconds_used": 10.5,
                "fix_attempts": 0,
                "llm_calls": 2,
                "tool_calls": 5,
                "prompt_tokens": 1000,
                "completion_tokens": 500,
            },
            {
                "phase": "implement",
                "outcome": "success",
                "turns_used": 5,
                "seconds_used": 42.3,
                "fix_attempts": 0,
                "llm_calls": 3,
                "tool_calls": 12,
                "prompt_tokens": 5000,
                "completion_tokens": 2000,
            },
        ])

        result = export_session("add-health-endpoint", db_path=db_path)
        assert result is not None

        filepath = Path(result)
        assert filepath.exists()
        assert filepath.name.endswith("-add-health-endpoint.json")

        data = json.loads(filepath.read_text(encoding="utf-8"))

        # Verify all top-level keys (REQ-SE-02)
        expected_keys = {
            "session_id", "change_name", "project", "exported_at",
            "outcome", "started_at", "finished_at", "total_runtime_seconds",
            "phases", "lessons", "metrics",
        }
        assert set(data.keys()) == expected_keys

        assert data["change_name"] == "add-health-endpoint"
        assert data["project"] == "test-project"
        assert data["outcome"] == "success"
        assert data["started_at"] == "2026-05-15T14:00:00"
        assert data["finished_at"] == "2026-05-15T14:05:00"
        assert data["total_runtime_seconds"] == 52.8

        # Verify phases
        assert len(data["phases"]) == 2
        phase_keys = {
            "phase", "outcome", "turns_used", "seconds_used",
            "fix_attempts", "llm_calls", "tool_calls",
            "prompt_tokens", "completion_tokens",
        }
        assert set(data["phases"][0].keys()) == phase_keys
        assert data["phases"][0]["phase"] == "enrich"
        assert data["phases"][1]["llm_calls"] == 3

        # Verify metrics
        assert data["metrics"]["total_llm_calls"] == 5
        assert data["metrics"]["total_tool_calls"] == 17
        assert data["metrics"]["total_prompt_tokens"] == 6000
        assert data["metrics"]["total_completion_tokens"] == 2500

        # Verify session_id format
        assert data["session_id"].startswith("add-health-endpoint-")
        assert len(data["session_id"].split("-")[-1]) == 8

    def test_export_returns_none_for_nonexistent_change(self, tmp_env):
        """REQ-SE-01: Return None for non-existent change, no exception."""
        result = export_session("nonexistent-change", db_path=tmp_env["db_path"])
        assert result is None

        # No sessions directory should have been created
        assert not tmp_env["sessions_dir"].exists()

    def test_export_failed_change_with_lessons(self, tmp_env):
        """REQ-SE-01: Export summary for a failed change includes lessons."""
        db_path = tmp_env["db_path"]
        learnings_file = tmp_env["learnings_file"]

        _insert_change(db_path, "crawler-domain-strategy", outcome="fail", phases=[
            {"phase": "implement", "outcome": "fail", "turns_used": 0,
             "seconds_used": 30, "fix_attempts": 3, "llm_calls": 5,
             "tool_calls": 10, "prompt_tokens": 3000, "completion_tokens": 1500},
        ])

        # Write learnings that match the change name
        learnings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(learnings_file, "w", encoding="utf-8") as f:
            f.write(json.dumps({
                "title": "FAIL: crawler-domain-strategy at implement",
                "pattern_key": "pipeline.fail.implement",
                "takeaway": "lint error",
            }) + "\n")
            f.write(json.dumps({
                "title": "FAIL: crawler-domain-strategy at implement",
                "pattern_key": "pipeline.fail.implement",
                "takeaway": "test failure",
            }) + "\n")
            # This one should NOT match
            f.write(json.dumps({
                "title": "FAIL: other-change at verify",
                "pattern_key": "pipeline.fail.verify",
                "takeaway": "unrelated",
            }) + "\n")

        result = export_session("crawler-domain-strategy", db_path=db_path)
        assert result is not None

        data = json.loads(Path(result).read_text(encoding="utf-8"))
        assert data["outcome"] == "fail"
        assert len(data["lessons"]) == 2
        assert all(
            item["pattern_key"] == "pipeline.fail.implement" for item in data["lessons"]
        )
        assert len(data["phases"]) == 1

    def test_export_no_lessons(self, tmp_env):
        """REQ-SE-04: Empty lessons array when no lessons recorded."""
        db_path = tmp_env["db_path"]
        _insert_change(db_path, "clean-change")

        result = export_session("clean-change", db_path=db_path)
        assert result is not None

        data = json.loads(Path(result).read_text(encoding="utf-8"))
        assert data["lessons"] == []

    def test_file_naming_convention(self, tmp_env):
        """REQ-SE-03: File naming follows {YYYYMMDD-HHmmss}-{change_name}.json."""
        db_path = tmp_env["db_path"]
        _insert_change(db_path, "add-health-endpoint")

        fixed_time = datetime(2026, 5, 15, 14, 30, 0)
        with patch("zsiga.memory.journal.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_time
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = export_session("add-health-endpoint", db_path=db_path)

        assert result is not None
        filepath = Path(result)
        assert filepath.name == "20260515-143000-add-health-endpoint.json"

    def test_auto_creates_sessions_directory(self, tmp_env):
        """REQ-SE-06: memory/sessions/ is auto-created on first export."""
        db_path = tmp_env["db_path"]
        _insert_change(db_path, "first-change")

        assert not tmp_env["sessions_dir"].exists()

        result = export_session("first-change", db_path=db_path)
        assert result is not None
        assert tmp_env["sessions_dir"].exists()

        # Verify file was written
        files = list(tmp_env["sessions_dir"].glob("*.json"))
        assert len(files) == 1


class TestLoadSessions:
    def test_returns_recent_sessions_in_order(self, tmp_env):
        """REQ-SE-05: load_sessions returns sessions oldest-first."""
        sessions_dir = tmp_env["sessions_dir"]
        sessions_dir.mkdir(parents=True)

        # Create session files with different timestamps
        for i, name in enumerate(["alpha", "beta", "gamma", "delta", "epsilon"]):
            ts = f"2026051{i}-120000"
            filepath = sessions_dir / f"{ts}-{name}.json"
            filepath.write_text(json.dumps({"change_name": name}), encoding="utf-8")

        result = load_sessions(limit=3)
        assert len(result) == 3
        # Last 3 by filename: gamma, delta, epsilon — oldest first
        assert result[0]["change_name"] == "gamma"
        assert result[1]["change_name"] == "delta"
        assert result[2]["change_name"] == "epsilon"

    def test_returns_all_when_no_limit(self, tmp_env):
        """REQ-SE-05: No limit returns all sessions."""
        sessions_dir = tmp_env["sessions_dir"]
        sessions_dir.mkdir(parents=True)

        for i in range(5):
            filepath = sessions_dir / f"202605{i:02d}-120000-change{i}.json"
            filepath.write_text(json.dumps({"change_name": f"change{i}"}), encoding="utf-8")

        result = load_sessions()
        assert len(result) == 5

    def test_returns_empty_when_no_directory(self, tmp_path, monkeypatch):
        """REQ-SE-05: Returns [] when sessions directory doesn't exist."""
        nonexistent = tmp_path / "no_sessions_here"
        monkeypatch.setattr("zsiga.memory.journal._SESSIONS_DIR", nonexistent)
        result = load_sessions()
        assert result == []

    def test_returns_empty_when_directory_empty(self, tmp_env):
        """REQ-SE-05: Returns [] when sessions directory is empty."""
        tmp_env["sessions_dir"].mkdir(parents=True)
        result = load_sessions()
        assert result == []
