"""Tests for _health_check function and /api/health endpoint.

Spec: health-check-endpoint.md
"""

import json
import sqlite3

from zsiga.daemon import _build_status_json, _health_check


# ---------------------------------------------------------------------------
# _health_check — pure function tests
# ---------------------------------------------------------------------------


class TestHealthCheckHealthy:
    """Scenario: Healthy database returns healthy status with record count."""

    def test_healthy_db_returns_healthy_with_count(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE changes (id INTEGER PRIMARY KEY, name TEXT)"
        )
        for i in range(5):
            conn.execute("INSERT INTO changes (name) VALUES (?)", (f"c{i}",))
        conn.commit()
        conn.close()

        result = _health_check(db_path)
        assert result["status"] == "healthy"
        assert result["db_records"] == 5

    def test_healthy_db_zero_records(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE changes (id INTEGER PRIMARY KEY, name TEXT)"
        )
        conn.commit()
        conn.close()

        result = _health_check(db_path)
        assert result["status"] == "healthy"
        assert result["db_records"] == 0


class TestHealthCheckMissingFile:
    """Scenario: Missing database file returns unhealthy status."""

    def test_missing_db_returns_unhealthy(self, tmp_path):
        db_path = str(tmp_path / "nonexistent.db")
        result = _health_check(db_path)
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert isinstance(result["error"], str)
        assert len(result["error"]) > 0


class TestHealthCheckNoChangesTable:
    """Scenario: Database without changes table returns unhealthy status."""

    def test_no_changes_table_returns_unhealthy(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE other_table (id INTEGER PRIMARY KEY)"
        )
        conn.commit()
        conn.close()

        result = _health_check(db_path)
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert isinstance(result["error"], str)
        assert len(result["error"]) > 0


class TestHealthCheckReadOnly:
    """The function shall not mutate any state."""

    def test_does_not_modify_database(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE changes (id INTEGER PRIMARY KEY, name TEXT)"
        )
        conn.execute("INSERT INTO changes (name) VALUES ('a')")
        conn.commit()
        conn.close()

        _health_check(db_path)

        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM changes").fetchone()[0]
        conn.close()
        assert count == 1


# ---------------------------------------------------------------------------
# Existing endpoints remain functional after adding health check
# ---------------------------------------------------------------------------


class TestExistingEndpointsUnchanged:
    """Scenario: Existing endpoints remain functional after adding health check."""

    def test_build_status_json_returns_valid_structure(self):
        payload = _build_status_json()
        data = json.loads(payload)
        assert "daemon" in data
        assert "queue" in data
