"""
Tests for spec: proposal-stats-endpoint.md
Change: add-proposal-stats-to-dashboard

Each testable scenario maps to a test function.
Tests validate _build_proposal_stats_json against a real SQLite database.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from zsiga.daemon import _build_proposal_stats_json, _build_status_json


# ---------------------------------------------------------------------------
# Helpers: create and populate a temporary changes table
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS changes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    change_name     TEXT NOT NULL,
    project         TEXT NOT NULL,
    outcome         TEXT NOT NULL,
    started_at      TEXT DEFAULT '',
    finished_at     TEXT DEFAULT '',
    lessons_count   INTEGER DEFAULT 0,
    phases_json     TEXT DEFAULT '[]',
    created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);
"""


def _create_db(db_path: Path, rows: list[tuple] | None = None) -> Path:
    """Create a SQLite DB at *db_path* with the `changes` table schema.

    Each row tuple: (change_name, project, outcome, started_at, finished_at)
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA)
    if rows:
        conn.executemany(
            """INSERT INTO changes
               (change_name, project, outcome, started_at, finished_at)
               VALUES (?, ?, ?, ?, ?)""",
            rows,
        )
    conn.commit()
    conn.close()
    return db_path


def _ts(minutes_ago: int) -> str:
    """ISO timestamp *minutes_ago* from now."""
    return (datetime.now() - timedelta(minutes=minutes_ago)).isoformat()


# ---------------------------------------------------------------------------
# Scenario: Query returns correct aggregates from populated table
# ---------------------------------------------------------------------------


def test_returns_correct_aggregates_from_populated_table(tmp_path):
    """Scenario: Query returns correct aggregates from populated table"""
    db = _create_db(
        tmp_path / "test.db",
        [
            ("feat-a", "zsiga", "success", _ts(120), _ts(60)),
            ("feat-b", "zsiga", "success", _ts(59), _ts(30)),
            ("fix-c", "zsiga", "fail", _ts(20), ""),
        ],
    )

    result = _build_proposal_stats_json(str(db))

    assert isinstance(result, dict)
    assert result["total"] == 3
    assert result["by_outcome"]["success"] == 2
    assert result["by_outcome"]["fail"] == 1
    assert isinstance(result["avg_duration_seconds"], float)
    assert result["avg_duration_seconds"] > 0
    assert len(result["recent"]) == 3


# ---------------------------------------------------------------------------
# Scenario: Query returns empty stats from empty table
# ---------------------------------------------------------------------------


def test_returns_empty_stats_from_empty_table(tmp_path):
    """Scenario: Query returns empty stats from empty table"""
    db = _create_db(tmp_path / "empty.db", rows=None)

    result = _build_proposal_stats_json(str(db))

    assert result["total"] == 0
    assert result["by_outcome"] == {}
    assert result["avg_duration_seconds"] is None
    assert result["recent"] == []


# ---------------------------------------------------------------------------
# Scenario: Recent list limited to 5 entries
# ---------------------------------------------------------------------------


def test_recent_list_limited_to_five(tmp_path):
    """Scenario: Recent list limited to 5 entries"""
    rows = [
        (f"change-{i}", "proj", "success", _ts(100 - i * 10), _ts(90 - i * 10))
        for i in range(8)
    ]
    db = _create_db(tmp_path / "many.db", rows)

    result = _build_proposal_stats_json(str(db))

    assert len(result["recent"]) == 5
    # Ordered by id DESC — last inserted comes first
    assert result["recent"][0]["change_name"] == "change-7"


# ---------------------------------------------------------------------------
# Scenario: Recent entries contain required fields
# ---------------------------------------------------------------------------


def test_recent_entries_contain_required_fields(tmp_path):
    """Scenario: Recent entries contain required fields"""
    db = _create_db(
        tmp_path / "fields.db",
        [
            ("my-change", "proj", "success", _ts(60), _ts(30)),
        ],
    )

    result = _build_proposal_stats_json(str(db))

    assert len(result["recent"]) == 1
    entry = result["recent"][0]
    assert "change_name" in entry
    assert "outcome" in entry
    assert "started_at" in entry
    assert "finished_at" in entry
    assert entry["change_name"] == "my-change"
    assert entry["outcome"] == "success"


# ---------------------------------------------------------------------------
# Scenario: Graceful degradation when database file does not exist
# ---------------------------------------------------------------------------


def test_graceful_degradation_missing_db(tmp_path):
    """Scenario: Graceful degradation when database file does not exist"""
    missing = tmp_path / "nonexistent" / "zsiga.db"

    result = _build_proposal_stats_json(str(missing))

    assert "error" in result
    assert isinstance(result["error"], str)
    assert len(result["error"]) > 0


# ---------------------------------------------------------------------------
# Scenario: Graceful degradation when changes table does not exist
# ---------------------------------------------------------------------------


def test_graceful_degradation_missing_table(tmp_path):
    """Scenario: Graceful degradation when changes table does not exist"""
    db_path = tmp_path / "empty_db.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE other_table (id INTEGER)")
    conn.commit()
    conn.close()

    result = _build_proposal_stats_json(str(db_path))

    assert "error" in result
    assert isinstance(result["error"], str)
    assert len(result["error"]) > 0


# ---------------------------------------------------------------------------
# Scenario: Avg duration ignores rows with empty finished_at
# ---------------------------------------------------------------------------


def test_avg_duration_ignores_empty_finished_at(tmp_path):
    """Scenario: Avg duration ignores rows with empty finished_at"""
    t0 = datetime(2025, 1, 1, 10, 0, 0)
    t1 = t0 + timedelta(hours=1)  # 3600 seconds
    rows = [
        ("with-duration", "p", "success", t0.isoformat(), t1.isoformat()),
        ("no-duration", "p", "fail", t0.isoformat(), ""),
    ]
    db = _create_db(tmp_path / "duration.db", rows)

    result = _build_proposal_stats_json(str(db))

    # Only 1 row has a valid finished_at; avg should be ~3600s
    assert result["avg_duration_seconds"] is not None
    assert abs(result["avg_duration_seconds"] - 3600.0) < 1.0
    assert result["total"] == 2


# ---------------------------------------------------------------------------
# Scenario: Existing endpoint /api/status.json still returns 200
# ---------------------------------------------------------------------------


def test_existing_status_json_still_works():
    """Scenario: Existing endpoint /api/status.json still returns 200

    Verify that adding the new route does not break _build_status_json.
    """
    payload = _build_status_json()
    data = json.loads(payload)

    assert "daemon" in data
    assert "queue" in data
    assert "state" in data["daemon"]
