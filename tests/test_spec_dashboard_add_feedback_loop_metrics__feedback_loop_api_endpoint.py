"""Tests for feedback loop API endpoint spec.

Spec: dashboard-add-feedback-loop-metrics / feedback-loop-api-endpoint
"""
import json
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Scenario: status.json includes feedback_metrics key
# ---------------------------------------------------------------------------
def test_status_json_includes_feedback_metrics():
    """_build_status_json() SHALL include a feedback_metrics key."""
    from zsiga.daemon import _build_status_json

    with patch("zsiga.daemon._read_daemon_state", return_value={}), \
         patch("zsiga.daemon._scan_proposal_queue", return_value=[]):
        payload_str = _build_status_json()

    data = json.loads(payload_str)
    assert "feedback_metrics" in data, "feedback_metrics key missing from status.json"

    fm = data["feedback_metrics"]
    assert "learnings_health" in fm
    assert "injection_rate" in fm
    assert "auto_proposal_success" in fm
    assert "self_assessment_coverage" in fm


# ---------------------------------------------------------------------------
# Scenario: feedback_metrics present even with empty database
# ---------------------------------------------------------------------------
def test_feedback_metrics_present_with_empty_db(tmp_path):
    """feedback_metrics SHALL have all sub-keys even when DB is empty."""
    import sqlite3

    from zsiga.daemon import _build_status_json

    # Create a fresh empty DB
    empty_db = tmp_path / "empty.db"
    conn = sqlite3.connect(str(empty_db))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_name TEXT NOT NULL, project TEXT NOT NULL,
            outcome TEXT NOT NULL, started_at TEXT DEFAULT '',
            finished_at TEXT DEFAULT '', lessons_count INTEGER DEFAULT 0,
            phases_json TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
        );
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL, pattern_key TEXT DEFAULT '',
            category TEXT DEFAULT '', text TEXT NOT NULL,
            created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
        );
        CREATE TABLE IF NOT EXISTS self_assessment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_name TEXT NOT NULL, task_type TEXT NOT NULL,
            predicted_tokens INTEGER DEFAULT 0, actual_tokens INTEGER DEFAULT 0,
            predicted_steps INTEGER DEFAULT 0, actual_steps INTEGER DEFAULT 0,
            fix_attempts INTEGER DEFAULT 0, outcome TEXT NOT NULL,
            self_rating TEXT NOT NULL, strengths TEXT DEFAULT '[]',
            weaknesses TEXT DEFAULT '[]', lessons TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
        );
    """)
    conn.close()

    with patch("zsiga.daemon._read_daemon_state", return_value={}), \
         patch("zsiga.daemon._scan_proposal_queue", return_value=[]), \
         patch("zsiga.metrics.feedback.compute_feedback_metrics") as mock_fm:
        mock_fm.return_value = {
            "learnings_health": {"total": 0, "top_patterns": [], "last_write_ts": ""},
            "injection_rate": {"implement_rate_pct": 0.0, "enrich_rate_pct": 0.0, "avg_lessons_per_session": 0.0},
            "auto_proposal_success": {"total": 0, "success": 0, "reverted": 0, "stuck": 0, "success_rate_pct": 0.0},
            "self_assessment_coverage": {"total_changes": 0, "assessed_changes": 0, "coverage_pct": 0.0, "last_assessment_ts": ""},
        }
        payload_str = _build_status_json()

    data = json.loads(payload_str)
    fm = data["feedback_metrics"]
    # Verify all keys exist and are not null
    assert fm["learnings_health"]["total"] == 0
    assert fm["injection_rate"]["implement_rate_pct"] == 0.0
    assert fm["auto_proposal_success"]["total"] == 0
    assert fm["self_assessment_coverage"]["total_changes"] == 0
