"""Tests for feedback loop metrics aggregation spec.

Spec: dashboard-add-feedback-loop-metrics / feedback-loop-metrics-aggregation
"""
import json
import sqlite3
from pathlib import Path


# ---------------------------------------------------------------------------
# Helper: create a fresh DB with the standard schema
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

CREATE TABLE IF NOT EXISTS lessons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT NOT NULL,
    pattern_key     TEXT DEFAULT '',
    category        TEXT DEFAULT '',
    text            TEXT NOT NULL,
    created_at      TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS self_assessment (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    change_name       TEXT NOT NULL,
    task_type         TEXT NOT NULL,
    predicted_tokens  INTEGER DEFAULT 0,
    actual_tokens     INTEGER DEFAULT 0,
    predicted_steps   INTEGER DEFAULT 0,
    actual_steps      INTEGER DEFAULT 0,
    fix_attempts      INTEGER DEFAULT 0,
    outcome           TEXT NOT NULL,
    self_rating       TEXT NOT NULL,
    strengths         TEXT DEFAULT '[]',
    weaknesses        TEXT DEFAULT '[]',
    lessons           TEXT DEFAULT '[]',
    created_at        TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%f', 'now'))
);
"""


def _make_db(tmp_path: Path) -> Path:
    """Create a temporary sqlite3 DB with the standard schema, return its path."""
    db_path = tmp_path / "test_metrics.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_SCHEMA)
    conn.close()
    return db_path


# ---------------------------------------------------------------------------
# Scenario: Empty database returns safe defaults
# ---------------------------------------------------------------------------
def test_empty_db_returns_safe_defaults(tmp_path):
    from zsiga.metrics.feedback import compute_feedback_metrics

    db_path = _make_db(tmp_path)
    result = compute_feedback_metrics(db_path=db_path)

    # Top-level keys
    assert set(result.keys()) == {
        "learnings_health",
        "injection_rate",
        "auto_proposal_success",
        "self_assessment_coverage",
    }

    lh = result["learnings_health"]
    assert lh["total"] == 0
    assert lh["top_patterns"] == []
    assert lh["last_write_ts"] == ""

    ir = result["injection_rate"]
    assert ir["implement_rate_pct"] == 0.0
    assert ir["enrich_rate_pct"] == 0.0
    assert ir["avg_lessons_per_session"] == 0.0

    aps = result["auto_proposal_success"]
    assert aps["total"] == 0
    assert aps["success"] == 0
    assert aps["reverted"] == 0
    assert aps["stuck"] == 0
    assert aps["success_rate_pct"] == 0.0

    sac = result["self_assessment_coverage"]
    assert sac["total_changes"] == 0
    assert sac["assessed_changes"] == 0
    assert sac["coverage_pct"] == 0.0
    assert sac["last_assessment_ts"] == ""


# ---------------------------------------------------------------------------
# Scenario: Learnings health computed from lessons table
# ---------------------------------------------------------------------------
def test_learnings_health_from_lessons_table(tmp_path):
    from zsiga.metrics.feedback import compute_feedback_metrics

    db_path = _make_db(tmp_path)
    conn = sqlite3.connect(str(db_path))

    # Insert 10 lessons: 3 with same pattern_key, 2 with another, 5 distinct
    pattern_keys = (
        ["pipeline.fail.implement"] * 3
        + ["code.unknown"] * 2
        + ["tools.venv_detection", "prompt.verify_efficiency",
           "verify.changed_files_only", "daemon.cycle_error", "misc.other"]
    )
    for i, pk in enumerate(pattern_keys):
        conn.execute(
            "INSERT INTO lessons (ts, pattern_key, category, text) VALUES (?, ?, ?, ?)",
            (f"2026-06-01T1{i:02d}:00", pk, "test", f"lesson {i}"),
        )
    conn.commit()
    conn.close()

    result = compute_feedback_metrics(db_path=db_path)
    lh = result["learnings_health"]

    assert lh["total"] == 10
    # First element in top_patterns should be the most frequent
    assert lh["top_patterns"][0] == ("pipeline.fail.implement", 3)
    assert len(lh["top_patterns"]) <= 5
    # last_write_ts should be non-empty
    assert lh["last_write_ts"].startswith("2026-06-01")


# ---------------------------------------------------------------------------
# Scenario: Auto-proposal success rate from changes table
# ---------------------------------------------------------------------------
def test_auto_proposal_success_rate(tmp_path):
    from zsiga.metrics.feedback import compute_feedback_metrics

    db_path = _make_db(tmp_path)
    conn = sqlite3.connect(str(db_path))

    # 2 auto-success
    for i in range(2):
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"auto-fix-{i}", "zsiga", "success", 0, "[]"),
        )
    # 1 auto-reverted (not stuck: only 1 fail phase)
    conn.execute(
        "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
        "VALUES (?, ?, ?, ?, ?)",
        ("auto-revert-1", "zsiga", "reverted", 0,
         json.dumps([{"phase": "implement", "outcome": "fail"}])),
    )
    # 1 auto-reverted (stuck: 3 fail phases)
    conn.execute(
        "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
        "VALUES (?, ?, ?, ?, ?)",
        ("auto-stuck-1", "zsiga", "reverted", 0,
         json.dumps([
             {"phase": "implement", "outcome": "fail"},
             {"phase": "verify", "outcome": "fail"},
             {"phase": "review", "outcome": "fail"},
         ])),
    )
    # 1 auto-reverted (not stuck: 2 fail phases, < 3)
    conn.execute(
        "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
        "VALUES (?, ?, ?, ?, ?)",
        ("auto-revert-2", "zsiga", "reverted", 0,
         json.dumps([
             {"phase": "implement", "outcome": "fail"},
             {"phase": "verify", "outcome": "fail"},
         ])),
    )
    conn.commit()
    conn.close()

    result = compute_feedback_metrics(db_path=db_path)
    aps = result["auto_proposal_success"]

    assert aps["total"] == 5
    assert aps["success"] == 2
    assert aps["reverted"] == 3  # 3 reverted total
    assert aps["stuck"] == 1     # only 1 with >=3 fail phases
    assert aps["success_rate_pct"] == 40.0


# ---------------------------------------------------------------------------
# Scenario: Self-assessment coverage
# ---------------------------------------------------------------------------
def test_self_assessment_coverage(tmp_path):
    from zsiga.metrics.feedback import compute_feedback_metrics

    db_path = _make_db(tmp_path)
    conn = sqlite3.connect(str(db_path))

    # 10 changes
    for i in range(10):
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"change-{i}", "zsiga", "success", 0, "[]"),
        )

    # 4 self-assessments covering 4 distinct change names
    for i in range(4):
        conn.execute(
            "INSERT INTO self_assessment "
            "(change_name, task_type, outcome, self_rating) VALUES (?, ?, ?, ?)",
            (f"change-{i}", "implement", "success", "good"),
        )
    conn.commit()
    conn.close()

    result = compute_feedback_metrics(db_path=db_path)
    sac = result["self_assessment_coverage"]

    assert sac["total_changes"] == 10
    assert sac["assessed_changes"] == 4
    assert sac["coverage_pct"] == 40.0


# ---------------------------------------------------------------------------
# Scenario: Injection rate derived from lessons_count and phase data
# ---------------------------------------------------------------------------
def test_injection_rate(tmp_path):
    from zsiga.metrics.feedback import compute_feedback_metrics

    db_path = _make_db(tmp_path)
    conn = sqlite3.connect(str(db_path))

    # 5 changes, each with IMPLEMENT phase
    # 3 have lessons_count > 0 (injected), 2 have lessons_count = 0
    # 4 have ENRICH phase, 2 of those have lessons_count > 0
    for i in range(5):
        lessons_count = 3 if i < 3 else 0
        phases = [{"phase": "implement", "outcome": "success"}]
        if i < 4:
            phases.append({"phase": "enrich", "outcome": "success"})
            enrich_lessons = 5 if i < 2 else 0
        else:
            enrich_lessons = 0
        total_lessons = lessons_count + enrich_lessons
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"change-{i}", "zsiga", "success", total_lessons, json.dumps(phases)),
        )
    conn.commit()
    conn.close()

    result = compute_feedback_metrics(db_path=db_path)
    ir = result["injection_rate"]

    # IMPLEMENT: 3 out of 5 have lessons_count > 0 = 60%
    assert ir["implement_rate_pct"] == 60.0
    # ENRICH: 4 changes have ENRICH phase, 2 of those have lessons_count > 0 = 50%
    assert ir["enrich_rate_pct"] == 50.0


# ---------------------------------------------------------------------------
# Scenario: Malformed phases_json handled gracefully
# ---------------------------------------------------------------------------
def test_malformed_phases_json_graceful(tmp_path):
    from zsiga.metrics.feedback import compute_feedback_metrics

    db_path = _make_db(tmp_path)
    conn = sqlite3.connect(str(db_path))

    # Insert one valid change
    conn.execute(
        "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
        "VALUES (?, ?, ?, ?, ?)",
        ("auto-good-1", "zsiga", "success", 0, json.dumps([{"phase": "implement", "outcome": "success"}])),
    )
    # Insert one with malformed phases_json
    conn.execute(
        "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
        "VALUES (?, ?, ?, ?, ?)",
        ("auto-bad-1", "zsiga", "reverted", 0, "not valid json"),
    )
    conn.commit()
    conn.close()

    # Should NOT raise
    result = compute_feedback_metrics(db_path=db_path)
    aps = result["auto_proposal_success"]
    assert aps["total"] == 2
    assert aps["success"] == 1


# ---------------------------------------------------------------------------
# Scenario: Mixed auto and non-auto changes
# ---------------------------------------------------------------------------
def test_mixed_auto_and_non_auto_changes(tmp_path):
    from zsiga.metrics.feedback import compute_feedback_metrics

    db_path = _make_db(tmp_path)
    conn = sqlite3.connect(str(db_path))

    # 3 auto changes (all success)
    for i in range(3):
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"auto-fix-{i}", "zsiga", "success", 0, "[]"),
        )
    # 5 non-auto changes (mixed)
    for i in range(5):
        outcome = "success" if i % 2 == 0 else "reverted"
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"manual-change-{i}", "zsiga", outcome, 0, "[]"),
        )
    conn.commit()
    conn.close()

    result = compute_feedback_metrics(db_path=db_path)
    aps = result["auto_proposal_success"]

    # Only auto-* changes counted
    assert aps["total"] == 3
    assert aps["success"] == 3


# ---------------------------------------------------------------------------
# Scenario: Custom db_path used
# ---------------------------------------------------------------------------
def test_custom_db_path(tmp_path):
    from zsiga.metrics.feedback import compute_feedback_metrics

    # Create two separate DBs
    db_a = _make_db(tmp_path / "a")
    db_b = _make_db(tmp_path / "b")

    conn_a = sqlite3.connect(str(db_a))
    conn_a.execute(
        "INSERT INTO lessons (ts, pattern_key, category, text) VALUES (?, ?, ?, ?)",
        ("2026-01-01T00:00:00", "test.pattern", "cat", "text"),
    )
    conn_a.commit()
    conn_a.close()

    result_a = compute_feedback_metrics(db_path=db_a)
    result_b = compute_feedback_metrics(db_path=db_b)

    assert result_a["learnings_health"]["total"] == 1
    assert result_b["learnings_health"]["total"] == 0
