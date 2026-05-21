"""Tests for spec: self-assessment-reflect-write.

Verifies that phase_reflect() correctly writes self-assessment records
for REVERTED outcomes (the bug: only SUCCESS paths were calling REFLECT).
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from zsiga.metrics.db import (
    _get_conn,
    query_self_assessment_stats,
    record_self_assessment,
)
from zsiga.metrics.types import ChangeRecord, Outcome, Phase, PhaseRecord
from zsiga.pipeline.orchestrator import ZsigaOrchestrator


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def mock_transport():
    transport = MagicMock()
    written = {}

    def capture_shell(cmd, **kwargs):
        if ">" in cmd and "reflect.md" in cmd:
            parts = cmd.split(">", 1)
            path = parts[1].strip().strip("'")
            content = parts[0].strip()
            if content.startswith("echo '") and content.endswith("'"):
                content = content[6:-1]
            written[path] = content
        return {"exit_code": 0, "stdout": ""}

    transport.run_shell.side_effect = capture_shell
    return transport, written


def _make_reverted_rec():
    """Build a ChangeRecord that simulates a reverted change."""
    return ChangeRecord(
        change_name="reverted-verify-fail-xyz",
        project="test-project",
        outcome=Outcome.REVERTED,
        phases=[
            PhaseRecord(
                phase=Phase.IMPLEMENT,
                outcome=Outcome.SUCCESS,
                fix_attempts=3,
                prompt_tokens=500,
                completion_tokens=400,
                llm_calls=4,
                tool_calls=3,
            ),
            PhaseRecord(
                phase=Phase.VERIFY,
                outcome=Outcome.FAIL,
                fix_attempts=2,
                prompt_tokens=300,
                completion_tokens=200,
                llm_calls=2,
                tool_calls=1,
            ),
        ],
    )


# ── Scenario: reflect-called-on-verify-fail ──────────────────

class TestReflectCalledOnVerifyFail:
    """phase_reflect writes a self_assessment DB row for REVERTED outcomes."""

    def test_reverted_outcome_writes_db_row(self, db_path, mock_transport):
        transport, _ = mock_transport
        rec = _make_reverted_rec()

        with patch("zsiga.metrics.db._DB_PATH", db_path), \
             patch("zsiga.pipeline.orchestrator.record_self_assessment") as mock_record:
            # Build a minimal orchestrator without real __init__
            orch = ZsigaOrchestrator.__new__(ZsigaOrchestrator)

            # Call phase_reflect directly (the method under test)
            from zsiga.metrics.db import record_self_assessment as _real_record
            mock_record.side_effect = lambda row, db_path=None: _real_record(row, db_path=db_path)

            orch.phase_reflect(
                rec,
                change_name="reverted-verify-fail-xyz",
                project_name="test-project",
                task_type="fix",
                change_dir="/tmp/test-change",
                transport=transport,
            )

        # Verify the DB row was written
        conn = _get_conn(db_path)
        try:
            row = conn.execute(
                "SELECT * FROM self_assessment WHERE change_name = 'reverted-verify-fail-xyz'"
            ).fetchone()
        finally:
            conn.close()

        assert row is not None, "No self_assessment row written for reverted change"
        assert row["outcome"] == "reverted"
        assert row["self_rating"] == "poor"
        assert row["task_type"] == "fix"

    def test_reflect_phase_record_appended(self, db_path, mock_transport):
        transport, _ = mock_transport
        rec = _make_reverted_rec()

        with patch("zsiga.metrics.db._DB_PATH", db_path):
            orch = ZsigaOrchestrator.__new__(ZsigaOrchestrator)
            orch.phase_reflect(
                rec,
                change_name="reverted-verify-fail-xyz",
                project_name="test-project",
                task_type="fix",
                change_dir="/tmp/test-change",
                transport=transport,
            )

        # Check PhaseRecord was appended
        reflect_phases = [p for p in rec.phases if p.phase == Phase.REFLECT]
        assert len(reflect_phases) == 1
        assert reflect_phases[0].outcome == Outcome.SUCCESS
        assert reflect_phases[0].detail == "poor"


# ── Scenario: reflect-md-written-on-reverted ─────────────────

class TestReflectMdWrittenOnReverted:
    """reflect.md is written to the change directory for reverted changes."""

    def test_reflect_md_contains_poor_rating(self, db_path, mock_transport):
        transport, written = mock_transport
        rec = _make_reverted_rec()

        with patch("zsiga.metrics.db._DB_PATH", db_path):
            orch = ZsigaOrchestrator.__new__(ZsigaOrchestrator)
            orch.phase_reflect(
                rec,
                change_name="reverted-verify-fail-xyz",
                project_name="test-project",
                task_type="fix",
                change_dir="/tmp/test-change",
                transport=transport,
            )

        assert len(written) == 1, f"Expected 1 file written, got {len(written)}"
        content = list(written.values())[0]
        assert "## Self-Rating" in content
        assert "**poor**" in content
        assert "## Weaknesses" in content


# ── Scenario: reverted-assessment-fields ─────────────────────

class TestRevertedAssessmentFields:
    """Verify specific fields written for reverted outcomes."""

    def test_weaknesses_include_recovery_capacity(self, db_path, mock_transport):
        transport, _ = mock_transport
        rec = _make_reverted_rec()

        with patch("zsiga.metrics.db._DB_PATH", db_path):
            orch = ZsigaOrchestrator.__new__(ZsigaOrchestrator)
            orch.phase_reflect(
                rec,
                change_name="reverted-change-fields",
                project_name="test-project",
                task_type="fix",
                change_dir="/tmp/test-change",
                transport=transport,
            )

        conn = _get_conn(db_path)
        try:
            row = conn.execute(
                "SELECT * FROM self_assessment WHERE change_name = 'reverted-change-fields'"
            ).fetchone()
        finally:
            conn.close()

        assert row is not None
        weaknesses = json.loads(row["weaknesses"])
        assert "Task exceeded recovery capacity" in weaknesses

    def test_lessons_include_reverted_review(self, db_path, mock_transport):
        transport, _ = mock_transport
        rec = _make_reverted_rec()

        with patch("zsiga.metrics.db._DB_PATH", db_path):
            orch = ZsigaOrchestrator.__new__(ZsigaOrchestrator)
            orch.phase_reflect(
                rec,
                change_name="reverted-change-lessons",
                project_name="test-project",
                task_type="fix",
                change_dir="/tmp/test-change",
                transport=transport,
            )

        conn = _get_conn(db_path)
        try:
            row = conn.execute(
                "SELECT * FROM self_assessment WHERE change_name = 'reverted-change-lessons'"
            ).fetchone()
        finally:
            conn.close()

        assert row is not None
        lessons = json.loads(row["lessons"])
        assert "Change reverted — review failure pattern" in lessons

    def test_self_rating_is_poor(self, db_path, mock_transport):
        transport, _ = mock_transport
        rec = _make_reverted_rec()

        with patch("zsiga.metrics.db._DB_PATH", db_path):
            orch = ZsigaOrchestrator.__new__(ZsigaOrchestrator)
            orch.phase_reflect(
                rec,
                change_name="reverted-change-rating",
                project_name="test-project",
                task_type="fix",
                change_dir="/tmp/test-change",
                transport=transport,
            )

        conn = _get_conn(db_path)
        try:
            row = conn.execute(
                "SELECT * FROM self_assessment WHERE change_name = 'reverted-change-rating'"
            ).fetchone()
        finally:
            conn.close()

        assert row is not None
        assert row["self_rating"] == "poor"
        assert row["outcome"] == "reverted"
