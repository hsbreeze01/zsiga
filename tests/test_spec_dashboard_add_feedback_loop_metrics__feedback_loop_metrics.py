"""
Tests for spec: feedback-loop-metrics.md
Change: dashboard-add-feedback-loop-metrics

Each testable scenario maps to a test function.
These tests validate the metrics computation functions before implementation exists.
"""

import json
import sqlite3
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helper: create a temporary learnings.jsonl file
# ---------------------------------------------------------------------------
def _write_learnings(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def _make_learning(pattern_key: str, timestamp: str) -> dict:
    return {"pattern_key": pattern_key, "timestamp": timestamp}


# ---------------------------------------------------------------------------
# Scenario: Compute metrics from a populated learnings file
# ---------------------------------------------------------------------------
def test_compute_learnings_health_populated(tmp_path):
    """Scenario: Compute metrics from a populated learnings file"""
    from zsiga.feedback_loop_metrics import compute_learnings_health

    entries = [
        *[_make_learning("daemon.cycle_error", f"2025-06-01T0{i}:00:00") for i in range(3)],
        *[_make_learning(f"other.pattern_{i}", f"2025-06-02T{i}:00:00") for i in range(7)],
    ]
    learnings_path = tmp_path / "memory" / "learnings.jsonl"
    _write_learnings(learnings_path, entries)

    result = compute_learnings_health(str(learnings_path))

    assert result["total"] == 10
    assert result["active"] == 10
    assert len(result["top_patterns"]) <= 5
    assert result["top_patterns"][0]["pattern_key"] == "daemon.cycle_error"
    assert result["top_patterns"][0]["count"] == 3
    assert result["last_write"] is not None
    # Validate ISO-8601-ish format
    assert "2025-06-02" in result["last_write"]


# ---------------------------------------------------------------------------
# Scenario: Compute metrics from missing learnings file
# ---------------------------------------------------------------------------
def test_compute_learnings_health_missing_file(tmp_path):
    """Scenario: Compute metrics from missing learnings file"""
    from zsiga.feedback_loop_metrics import compute_learnings_health

    missing_path = tmp_path / "nonexistent" / "learnings.jsonl"
    result = compute_learnings_health(str(missing_path))

    assert result["total"] == 0
    assert result["active"] == 0
    assert result["top_patterns"] == []
    assert result["last_write"] is None


# ---------------------------------------------------------------------------
# Scenario: Compute metrics from empty learnings file
# ---------------------------------------------------------------------------
def test_compute_learnings_health_empty_file(tmp_path):
    """Scenario: Compute metrics from empty learnings file"""
    from zsiga.feedback_loop_metrics import compute_learnings_health

    learnings_path = tmp_path / "memory" / "learnings.jsonl"
    learnings_path.parent.mkdir(parents=True, exist_ok=True)
    learnings_path.write_text("")

    result = compute_learnings_health(str(learnings_path))

    assert result["total"] == 0
    assert result["active"] == 0
    assert result["top_patterns"] == []
    assert result["last_write"] is None


# ---------------------------------------------------------------------------
# Helper: create learning_injections table in an in-memory DB
# ---------------------------------------------------------------------------
def _create_injections_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS learning_injections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_id TEXT NOT NULL,
            phase TEXT NOT NULL,
            injected_count INTEGER NOT NULL DEFAULT 0,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Scenario: Compute injection rate with mixed data
# ---------------------------------------------------------------------------
def test_compute_injection_rate_mixed():
    """Scenario: Compute injection rate with mixed data"""
    from zsiga.feedback_loop_metrics import compute_injection_rate

    conn = sqlite3.connect(":memory:")
    _create_injections_table(conn)
    conn.executemany(
        "INSERT INTO learning_injections (change_id, phase, injected_count, timestamp) VALUES (?, ?, ?, ?)",
        [
            ("c1", "IMPLEMENT", 3, "2025-06-01T10:00:00"),
            ("c1", "IMPLEMENT", 0, "2025-06-01T11:00:00"),
            ("c2", "ENRICH", 5, "2025-06-02T10:00:00"),
            ("c2", "ENRICH", 2, "2025-06-02T11:00:00"),
        ],
    )
    conn.commit()

    result = compute_injection_rate(conn)

    # IMPLEMENT: 1 out of 2 had injections (injected_count > 0)
    assert "1/2 (50%)" in result["implement_rate"]
    # ENRICH: 2 out of 2 had injections
    assert "2/2 (100%)" in result["enrich_rate"]
    assert result["avg_injected"] == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# Scenario: Compute injection rate with empty table
# ---------------------------------------------------------------------------
def test_compute_injection_rate_empty_table():
    """Scenario: Compute injection rate with empty table"""
    from zsiga.feedback_loop_metrics import compute_injection_rate

    conn = sqlite3.connect(":memory:")
    _create_injections_table(conn)

    result = compute_injection_rate(conn)

    assert result["implement_rate"] == "N/A"
    assert result["enrich_rate"] == "N/A"
    assert result["avg_injected"] is None


# ---------------------------------------------------------------------------
# Scenario: Compute injection rate when table does not exist
# ---------------------------------------------------------------------------
def test_compute_injection_rate_no_table():
    """Scenario: Compute injection rate when table does not exist"""
    from zsiga.feedback_loop_metrics import compute_injection_rate

    conn = sqlite3.connect(":memory:")
    # No table created

    result = compute_injection_rate(conn)

    assert result["implement_rate"] == "N/A"
    assert result["enrich_rate"] == "N/A"
    assert result["avg_injected"] is None


# ---------------------------------------------------------------------------
# Scenario: Compute auto-proposal success with varied outcomes
# ---------------------------------------------------------------------------
def test_compute_auto_proposal_success_varied():
    """Scenario: Compute auto-proposal success with varied outcomes"""
    from zsiga.feedback_loop_metrics import compute_auto_proposal_success

    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE changes (
            change_id TEXT PRIMARY KEY,
            source TEXT,
            status TEXT
        )
        """
    )
    conn.executemany(
        "INSERT INTO changes (change_id, source, status) VALUES (?, ?, ?)",
        [
            ("auto-1", "auto", "SUCCESS"),
            ("auto-2", "auto", "SUCCESS"),
            ("auto-3", "auto", "FAIL"),
            ("auto-4", "auto", "STUCK"),
            ("auto-5", "auto", "STUCK"),
        ],
    )
    conn.commit()

    result = compute_auto_proposal_success(conn)

    assert result["total"] == 5
    assert result["success"] == 2
    assert result["failed"] == 1
    assert result["stuck"] == 2
    assert "%" in result["success_rate"]
    assert len(result["stuck_list"]) == 2


# ---------------------------------------------------------------------------
# Scenario: Compute auto-proposal success with empty changes
# ---------------------------------------------------------------------------
def test_compute_auto_proposal_success_empty():
    """Scenario: Compute auto-proposal success with empty changes"""
    from zsiga.feedback_loop_metrics import compute_auto_proposal_success

    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE changes (
            change_id TEXT PRIMARY KEY,
            source TEXT,
            status TEXT
        )
        """
    )
    conn.commit()

    result = compute_auto_proposal_success(conn)

    assert result["total"] == 0
    assert result["success_rate"] == "N/A"
    assert result["stuck_list"] == []


# ---------------------------------------------------------------------------
# Scenario: Compute self-assessment coverage with partial data
# ---------------------------------------------------------------------------
def test_compute_self_assessment_coverage_partial():
    """Scenario: Compute self-assessment coverage with partial data"""
    from zsiga.feedback_loop_metrics import compute_self_assessment_coverage

    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE changes (
            change_id TEXT PRIMARY KEY
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE self_assessment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_id TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT INTO changes (change_id) VALUES (?)",
        [("c1",), ("c2",), ("c3",), ("c4",)],
    )
    conn.executemany(
        "INSERT INTO self_assessment (change_id, timestamp) VALUES (?, ?)",
        [
            ("c1", "2025-05-01T10:00:00"),
            ("c2", "2025-05-20T10:00:00"),
            ("c3", "2025-06-01T12:00:00"),
        ],
    )
    conn.commit()

    result = compute_self_assessment_coverage(conn)

    assert result["total_changes"] == 4
    assert result["assessed"] == 3
    assert result["coverage"] == "75%"
    assert result["last_assessment"] == "2025-06-01T12:00:00"


# ---------------------------------------------------------------------------
# Scenario: Compute self-assessment coverage with empty tables
# ---------------------------------------------------------------------------
def test_compute_self_assessment_coverage_empty():
    """Scenario: Compute self-assessment coverage with empty tables"""
    from zsiga.feedback_loop_metrics import compute_self_assessment_coverage

    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE changes (change_id TEXT PRIMARY KEY)")
    conn.execute(
        "CREATE TABLE self_assessment (id INTEGER PRIMARY KEY AUTOINCREMENT, change_id TEXT NOT NULL, timestamp TEXT NOT NULL)"
    )
    conn.commit()

    result = compute_self_assessment_coverage(conn)

    assert result["total_changes"] == 0
    assert result["assessed"] == 0
    assert result["coverage"] == "N/A"
    assert result["last_assessment"] is None


# ---------------------------------------------------------------------------
# Scenario: Aggregate metrics with all valid data sources
# ---------------------------------------------------------------------------
def test_compute_all_feedback_metrics_with_data(tmp_path):
    """Scenario: Aggregate metrics with all valid data sources"""
    from zsiga.feedback_loop_metrics import compute_all_feedback_metrics

    # Create learnings file
    entries = [_make_learning("test.pattern", "2025-06-01T10:00:00") for _ in range(3)]
    learnings_path = tmp_path / "memory" / "learnings.jsonl"
    _write_learnings(learnings_path, entries)

    # Create DB with tables
    db_path = tmp_path / "data" / "zsiga.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    _create_injections_table(conn)
    conn.execute(
        "INSERT INTO learning_injections (change_id, phase, injected_count, timestamp) VALUES (?, ?, ?, ?)",
        ("c1", "IMPLEMENT", 2, "2025-06-01T10:00:00"),
    )
    conn.execute("CREATE TABLE changes (change_id TEXT PRIMARY KEY, source TEXT, status TEXT)")
    conn.execute("INSERT INTO changes VALUES ('c1', 'auto', 'SUCCESS')")
    conn.execute(
        "CREATE TABLE self_assessment (id INTEGER PRIMARY KEY AUTOINCREMENT, change_id TEXT NOT NULL, timestamp TEXT NOT NULL)"
    )
    conn.execute("INSERT INTO self_assessment (change_id, timestamp) VALUES ('c1', '2025-06-01T10:00:00')")
    conn.commit()
    conn.close()

    result = compute_all_feedback_metrics(str(learnings_path), str(db_path))

    assert "learnings_health" in result
    assert "injection_rate" in result
    assert "auto_proposal_success" in result
    assert "self_assessment_coverage" in result

    assert result["learnings_health"]["total"] == 3
    assert result["injection_rate"]["implement_rate"] != "N/A"
    assert result["auto_proposal_success"]["total"] >= 1
    assert result["self_assessment_coverage"]["assessed"] >= 1


# ---------------------------------------------------------------------------
# Scenario: Aggregate metrics with missing data sources
# ---------------------------------------------------------------------------
def test_compute_all_feedback_metrics_missing_sources(tmp_path):
    """Scenario: Aggregate metrics with missing data sources"""
    from zsiga.feedback_loop_metrics import compute_all_feedback_metrics

    missing_learnings = tmp_path / "nonexistent" / "learnings.jsonl"
    db_path = tmp_path / "data" / "zsiga.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.commit()
    conn.close()

    result = compute_all_feedback_metrics(str(missing_learnings), str(db_path))

    assert "learnings_health" in result
    assert "injection_rate" in result
    assert "auto_proposal_success" in result
    assert "self_assessment_coverage" in result

    # All should be safe defaults
    assert result["learnings_health"]["total"] == 0
    assert result["injection_rate"]["implement_rate"] == "N/A"
    assert result["auto_proposal_success"]["success_rate"] == "N/A"
    assert result["self_assessment_coverage"]["coverage"] == "N/A"
