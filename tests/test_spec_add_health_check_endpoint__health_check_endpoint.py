"""
Tests for spec: health-check-endpoint.md
Change: add-health-check-endpoint

Each testable scenario maps to a test function.
Tests validate _health_check against a real SQLite database.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

# The function under test will be implemented in zsiga/daemon.py.
# Import with a graceful skip if it does not exist yet.
try:
    from zsiga.daemon import _health_check, _build_status_json
except ImportError:
    pytest.skip(
        "_health_check not yet implemented in zsiga.daemon",
        allow_module_level=True,
    )


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


# ---------------------------------------------------------------------------
# Scenario: Healthy database returns healthy status with record count
# ---------------------------------------------------------------------------


def test_healthy_database_returns_healthy_status_with_record_count(tmp_path):
    """Scenario: Healthy database returns healthy status with record count"""
    db = _create_db(
        tmp_path / "test.db",
        [
            ("feat-a", "zsiga", "success", "2025-01-01T00:00:00", "2025-01-01T01:00:00"),
            ("feat-b", "zsiga", "success", "2025-01-01T02:00:00", "2025-01-01T03:00:00"),
            ("fix-c", "zsiga", "fail", "2025-01-01T04:00:00", ""),
            ("feat-d", "zsiga", "success", "2025-01-01T05:00:00", "2025-01-01T06:00:00"),
            ("fix-e", "zsiga", "success", "2025-01-01T07:00:00", "2025-01-01T08:00:00"),
        ],
    )

    result = _health_check(str(db))

    assert isinstance(result, dict)
    assert result["status"] == "healthy"
    assert result["db_records"] == 5


# ---------------------------------------------------------------------------
# Scenario: Missing database file returns unhealthy status
# ---------------------------------------------------------------------------


def test_missing_database_file_returns_unhealthy_status(tmp_path):
    """Scenario: Missing database file returns unhealthy status"""
    missing = tmp_path / "nonexistent" / "zsiga.db"

    result = _health_check(str(missing))

    assert isinstance(result, dict)
    assert result["status"] == "unhealthy"
    assert isinstance(result.get("error"), str)
    assert len(result["error"]) > 0


# ---------------------------------------------------------------------------
# Scenario: Database without changes table returns unhealthy status
# ---------------------------------------------------------------------------


def test_database_without_changes_table_returns_unhealthy_status(tmp_path):
    """Scenario: Database without changes table returns unhealthy status"""
    db_path = tmp_path / "empty_db.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE other_table (id INTEGER)")
    conn.commit()
    conn.close()

    result = _health_check(str(db_path))

    assert isinstance(result, dict)
    assert result["status"] == "unhealthy"
    assert isinstance(result.get("error"), str)
    assert len(result["error"]) > 0


# ---------------------------------------------------------------------------
# Scenario: Healthy response returns HTTP 200 with required fields
#   (tested at function level: _health_check returns correct dict shape)
# ---------------------------------------------------------------------------


def test_healthy_response_has_required_fields(tmp_path):
    """Scenario: Healthy response returns HTTP 200 with required fields"""
    db = _create_db(tmp_path / "test.db", [])

    result = _health_check(str(db))

    assert "status" in result
    assert result["status"] == "healthy"
    assert "db_records" in result
    assert isinstance(result["db_records"], int)
    assert result["db_records"] >= 0


# ---------------------------------------------------------------------------
# Scenario: Unhealthy response includes error description
# ---------------------------------------------------------------------------


def test_unhealthy_response_includes_error_description(tmp_path):
    """Scenario: Unhealthy response includes error description"""
    missing = tmp_path / "nowhere" / "missing.db"

    result = _health_check(str(missing))

    assert result["status"] == "unhealthy"
    assert "error" in result
    assert isinstance(result["error"], str)
    assert len(result["error"]) > 0


# ---------------------------------------------------------------------------
# Scenario: Existing endpoints remain functional after adding health check
# ---------------------------------------------------------------------------


def test_existing_endpoints_remain_functional():
    """Scenario: Existing endpoints remain functional after adding health check"""
    payload = _build_status_json()
    data = json.loads(payload)

    assert "daemon" in data
    assert "queue" in data
    assert "state" in data["daemon"]


# ---------------------------------------------------------------------------
# Edge case: Empty changes table (0 rows) is still healthy
# ---------------------------------------------------------------------------


def test_empty_changes_table_is_still_healthy(tmp_path):
    """Edge: An empty changes table (0 rows) should still report healthy."""
    db = _create_db(tmp_path / "empty.db", rows=None)

    result = _health_check(str(db))

    assert result["status"] == "healthy"
    assert result["db_records"] == 0


# ---------------------------------------------------------------------------
# Edge case: _health_check does not leak connections (repeated calls)
# ---------------------------------------------------------------------------


def test_repeated_health_checks_do_not_leak_connections(tmp_path):
    """Edge: Calling _health_check many times should not accumulate connections."""
    db = _create_db(tmp_path / "repeat.db", [])

    for _ in range(10):
        result = _health_check(str(db))
        assert result["status"] == "healthy"

    # If connections leaked, a WAL file or lock contention would likely
    # cause an error on subsequent accesses. Verify the DB is still usable.
    conn = sqlite3.connect(str(db))
    count = conn.execute("SELECT COUNT(*) FROM changes").fetchone()[0]
    conn.close()
    assert count == 0
