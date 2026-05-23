"""
Tests for spec: learning-injection-tracking.md
Change: dashboard-add-feedback-loop-metrics

Each testable scenario maps to a test function.
"""

import sqlite3


# ---------------------------------------------------------------------------
# Scenario: Table creation is idempotent
# ---------------------------------------------------------------------------
def test_ensure_injections_table_idempotent():
    """Scenario: Table creation is idempotent"""
    from zsiga.injection_tracker import ensure_injections_table

    conn = sqlite3.connect(":memory:")

    # First call
    ensure_injections_table(conn)

    # Insert a row between calls
    conn.execute(
        "INSERT INTO learning_injections (change_id, phase, injected_count, timestamp) "
        "VALUES ('c1', 'IMPLEMENT', 1, '2025-06-01T00:00:00')"
    )
    conn.commit()

    # Second call — should not drop existing data
    ensure_injections_table(conn)

    rows = conn.execute("SELECT COUNT(*) FROM learning_injections").fetchone()
    assert rows[0] == 1

    # Verify schema columns exist
    cursor = conn.execute("PRAGMA table_info(learning_injections)")
    columns = {row[1] for row in cursor.fetchall()}
    assert "id" in columns
    assert "change_id" in columns
    assert "phase" in columns
    assert "injected_count" in columns
    assert "timestamp" in columns

    conn.close()


# ---------------------------------------------------------------------------
# Scenario: Record a valid injection event
# ---------------------------------------------------------------------------
def test_record_injection_valid():
    """Scenario: Record a valid injection event"""
    from zsiga.injection_tracker import record_injection

    conn = sqlite3.connect(":memory:")
    record_injection(conn, change_id="change-001", phase="IMPLEMENT", injected_count=3)

    rows = conn.execute(
        "SELECT change_id, phase, injected_count, timestamp FROM learning_injections"
    ).fetchall()

    assert len(rows) == 1
    assert rows[0][0] == "change-001"
    assert rows[0][1] == "IMPLEMENT"
    assert rows[0][2] == 3
    assert rows[0][3] is not None  # timestamp auto-generated

    conn.close()


# ---------------------------------------------------------------------------
# Scenario: Record multiple injection events for different phases
# ---------------------------------------------------------------------------
def test_record_injection_multiple_phases():
    """Scenario: Record multiple injection events for different phases"""
    from zsiga.injection_tracker import record_injection

    conn = sqlite3.connect(":memory:")
    record_injection(conn, change_id="change-001", phase="IMPLEMENT", injected_count=3)
    record_injection(conn, change_id="change-001", phase="ENRICH", injected_count=5)

    rows = conn.execute(
        "SELECT phase, injected_count FROM learning_injections ORDER BY phase"
    ).fetchall()

    assert len(rows) == 2
    phases = {row[0] for row in rows}
    assert phases == {"IMPLEMENT", "ENRICH"}
    # Verify both have the correct change_id
    change_ids = conn.execute("SELECT change_id FROM learning_injections").fetchall()
    assert all(cid[0] == "change-001" for cid in change_ids)

    conn.close()


# ---------------------------------------------------------------------------
# Scenario: Record injection with zero count
# ---------------------------------------------------------------------------
def test_record_injection_zero_count():
    """Scenario: Record injection with zero count"""
    from zsiga.injection_tracker import record_injection

    conn = sqlite3.connect(":memory:")
    record_injection(conn, change_id="change-002", phase="IMPLEMENT", injected_count=0)

    rows = conn.execute(
        "SELECT injected_count FROM learning_injections"
    ).fetchall()

    assert len(rows) == 1
    assert rows[0][0] == 0

    conn.close()


# ---------------------------------------------------------------------------
# Scenario: Record injection with explicit timestamp
# ---------------------------------------------------------------------------
def test_record_injection_explicit_timestamp():
    """Scenario: Record injection with explicit timestamp"""
    from zsiga.injection_tracker import record_injection

    conn = sqlite3.connect(":memory:")
    record_injection(
        conn,
        change_id="change-003",
        phase="ENRICH",
        injected_count=1,
        timestamp="2025-06-15T10:30:00",
    )

    rows = conn.execute(
        "SELECT timestamp FROM learning_injections"
    ).fetchall()

    assert len(rows) == 1
    assert rows[0][0] == "2025-06-15T10:30:00"

    conn.close()
