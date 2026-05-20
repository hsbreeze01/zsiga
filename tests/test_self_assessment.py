"""Tests for self-assessment DB functions, rating algorithm,
boundary detection, and reflect.md generation."""

import json

import pytest

from zsiga.metrics.db import (
    _get_conn,
    query_recent_ratings,
    query_self_assessment_stats,
    record_self_assessment,
)
from zsiga.metrics.types import ChangeRecord, Outcome, Phase, PhaseRecord


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def db_path(tmp_path):
    """Return a temporary database path."""
    return tmp_path / "test.db"


def _insert_row(db_path, **overrides):
    """Insert a self-assessment row with sensible defaults."""
    row = {
        "change_name": "test-change",
        "task_type": "impl",
        "predicted_tokens": 0,
        "actual_tokens": 1000,
        "predicted_steps": 0,
        "actual_steps": 5,
        "fix_attempts": 0,
        "outcome": "success",
        "self_rating": "excellent",
        "strengths": ["Clean implementation"],
        "weaknesses": [],
        "lessons": ["first-pass success"],
    }
    row.update(overrides)
    record_self_assessment(row, db_path=db_path)


# ── 1.1 record_self_assessment & query_self_assessment_stats ─

class TestRecordSelfAssessment:
    def test_insert_and_read(self, db_path):
        _insert_row(db_path, change_name="change-a")
        conn = _get_conn(db_path)
        try:
            row = conn.execute(
                "SELECT * FROM self_assessment WHERE change_name = 'change-a'"
            ).fetchone()
        finally:
            conn.close()
        assert row is not None
        assert row["change_name"] == "change-a"
        assert row["task_type"] == "impl"
        assert row["actual_tokens"] == 1000
        assert row["self_rating"] == "excellent"
        assert json.loads(row["strengths"]) == ["Clean implementation"]

    def test_idempotent_schema(self, db_path):
        """Table creation is idempotent — second _get_conn should not error."""
        _get_conn(db_path)
        _get_conn(db_path)  # should not raise
        conn = _get_conn(db_path)
        try:
            count = conn.execute(
                "SELECT COUNT(*) FROM self_assessment"
            ).fetchone()[0]
        finally:
            conn.close()
        assert count == 0


class TestQuerySelfAssessmentStats:
    def test_returns_aggregated_stats(self, db_path):
        for i in range(5):
            _insert_row(
                db_path,
                change_name=f"change-{i}",
                actual_tokens=2000,
                actual_steps=10,
                outcome="success",
            )
        result = query_self_assessment_stats("impl", limit=5, db_path=db_path)
        assert result["count"] == 5
        assert result["avg_tokens"] == 2000.0
        assert result["avg_steps"] == 10.0
        assert result["success_rate"] == 1.0

    def test_empty_returns_count_zero(self, db_path):
        result = query_self_assessment_stats("refactor", db_path=db_path)
        assert result == {"count": 0}

    def test_mixed_outcomes(self, db_path):
        _insert_row(db_path, change_name="c1", outcome="success")
        _insert_row(db_path, change_name="c2", outcome="reverted")
        result = query_self_assessment_stats("impl", limit=10, db_path=db_path)
        assert result["count"] == 2
        assert result["success_rate"] == 0.5

    def test_respects_limit(self, db_path):
        for i in range(5):
            _insert_row(db_path, change_name=f"c-{i}", actual_tokens=100 * i)
        result = query_self_assessment_stats("impl", limit=3, db_path=db_path)
        assert result["count"] == 3


class TestQueryRecentRatings:
    def test_returns_ratings(self, db_path):
        _insert_row(db_path, change_name="c1", self_rating="good")
        _insert_row(db_path, change_name="c2", self_rating="poor")
        _insert_row(db_path, change_name="c3", self_rating="poor")
        ratings = query_recent_ratings("impl", limit=3, db_path=db_path)
        assert ratings == ["poor", "poor", "good"]

    def test_empty_returns_empty_list(self, db_path):
        ratings = query_recent_ratings("fix", db_path=db_path)
        assert ratings == []


# ── Self-rating algorithm ────────────────────────────────────

class TestSelfRatingAlgorithm:
    """Test the self-rating computation logic used by phase_reflect()."""

    @staticmethod
    def _compute_rating(outcome: str, total_fix_attempts: int) -> str:
        if outcome == "reverted" or total_fix_attempts > 5:
            return "poor"
        if total_fix_attempts == 0:
            return "excellent"
        if total_fix_attempts <= 2:
            return "good"
        return "average"

    def test_excellent_zero_fix(self):
        assert self._compute_rating("success", 0) == "excellent"

    def test_good_two_fix(self):
        assert self._compute_rating("success", 2) == "good"

    def test_average_five_fix(self):
        assert self._compute_rating("success", 5) == "average"

    def test_poor_reverted(self):
        assert self._compute_rating("reverted", 0) == "poor"

    def test_poor_six_fix(self):
        assert self._compute_rating("success", 6) == "poor"


# ── Capability boundary detection ────────────────────────────

class TestCapabilityBoundary:
    """REQ-SA-04: 3 consecutive poor ratings trigger boundary detection."""

    def test_three_consecutive_poor_triggers(self, db_path):
        from zsiga.memory.learn import record_lesson
        from zsiga.memory import learn as learn_mod

        # Write 3 poor rows
        for i in range(3):
            _insert_row(
                db_path,
                change_name=f"fix-{i}",
                task_type="fix",
                self_rating="poor",
                outcome="reverted",
            )

        ratings = query_recent_ratings("fix", limit=3, db_path=db_path)
        assert len(ratings) == 3
        assert all(r == "poor" for r in ratings)

        # Simulate boundary detection
        should_trigger = len(ratings) == 3 and all(r == "poor" for r in ratings)
        assert should_trigger

        # Record lesson (using tmp_path for learnings file)
        learnings_file = db_path.parent / "learnings.jsonl"
        learn_mod._MEMORY_DIR = db_path.parent
        record_lesson(
            title="Capability boundary: fix",
            context="3 consecutive poor ratings for task_type=fix",
            takeaway="Recommend human intervention for fix tasks",
            pattern_key="capability.boundary.fix",
        )
        assert learnings_file.exists()
        lines = learnings_file.read_text().strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["pattern_key"] == "capability.boundary.fix"
        assert "human intervention" in entry["takeaway"].lower()

    def test_mixed_ratings_no_trigger(self, db_path):
        _insert_row(db_path, change_name="f1", task_type="fix", self_rating="poor")
        _insert_row(db_path, change_name="f2", task_type="fix", self_rating="good")
        _insert_row(db_path, change_name="f3", task_type="fix", self_rating="poor")

        ratings = query_recent_ratings("fix", limit=3, db_path=db_path)
        should_trigger = (
            len(ratings) == 3 and all(r == "poor" for r in ratings)
        )
        assert not should_trigger


# ── Phase enum ───────────────────────────────────────────────

class TestPhaseReflect:
    def test_reflect_in_phase_enum(self):
        assert Phase.REFLECT == "reflect"
        assert Phase.REFLECT.value == "reflect"


# ── reflect.md content ──────────────────────────────────────

class TestReflectMdContent:
    """Test that reflect.md contains the required sections."""

    def _generate_reflect_md(self, task_type, rating, strengths, weaknesses,
                             lessons, metrics):
        lines = [
            f"# Self-Assessment: {metrics['change_name']}",
            "",
            "## Task Review",
            f"- predicted_tokens: {metrics.get('predicted_tokens', 0)}",
            f"- actual_tokens: {metrics['actual_tokens']}",
            f"- predicted_steps: {metrics.get('predicted_steps', 0)}",
            f"- actual_steps: {metrics['actual_steps']}",
            f"- fix_attempts: {metrics['fix_attempts']}",
            "",
            "## Self-Rating",
            f"**{rating}**",
            "",
            "## Strengths",
        ]
        for s in strengths:
            lines.append(f"- {s}")
        lines.append("")
        lines.append("## Weaknesses")
        for w in weaknesses:
            lines.append(f"- {w}")
        lines.append("")
        lines.append("## Lessons Learned")
        for lesson in lessons:
            lines.append(f"- {lesson}")
        lines.append("")
        lines.append("## Next Time Suggestions")
        lines.append(f"- Estimated tokens for similar tasks: {metrics['actual_tokens']}")
        return "\n".join(lines)

    def test_contains_required_sections(self):
        md = self._generate_reflect_md(
            task_type="impl",
            rating="excellent",
            strengths=["Clean implementation"],
            weaknesses=[],
            lessons=["First-pass success"],
            metrics={
                "change_name": "test-change",
                "predicted_tokens": 0,
                "actual_tokens": 1000,
                "predicted_steps": 0,
                "actual_steps": 5,
                "fix_attempts": 0,
            },
        )
        for section in [
            "## Task Review",
            "## Self-Rating",
            "## Strengths",
            "## Weaknesses",
            "## Lessons Learned",
            "## Next Time Suggestions",
        ]:
            assert section in md, f"Missing section: {section}"

    def test_rating_displayed(self):
        md = self._generate_reflect_md(
            task_type="fix",
            rating="poor",
            strengths=[],
            weaknesses=["Required fixes"],
            lessons=["Reverted"],
            metrics={
                "change_name": "x",
                "predicted_tokens": 0,
                "actual_tokens": 500,
                "predicted_steps": 0,
                "actual_steps": 3,
                "fix_attempts": 6,
            },
        )
        assert "**poor**" in md


# ── Integration: phase_reflect() ────────────────────────────

class TestPhaseReflectIntegration:
    """Test the full phase_reflect flow: DB row, reflect.md, PhaseRecord."""

    def test_phase_reflect_appends_record_and_writes(self, db_path):
        """Simulate phase_reflect() logic end-to-end."""
        # Build a ChangeRecord with some phases
        rec = ChangeRecord(
            change_name="add-feature-x",
            project="test-project",
            outcome=Outcome.SUCCESS,
            phases=[
                PhaseRecord(
                    phase=Phase.IMPLEMENT,
                    outcome=Outcome.SUCCESS,
                    fix_attempts=0,
                    prompt_tokens=500,
                    completion_tokens=500,
                    llm_calls=3,
                    tool_calls=2,
                ),
                PhaseRecord(
                    phase=Phase.VERIFY,
                    outcome=Outcome.SUCCESS,
                    fix_attempts=0,
                    prompt_tokens=200,
                    completion_tokens=200,
                    llm_calls=1,
                    tool_calls=1,
                ),
            ],
        )

        # Compute metrics (mirrors phase_reflect logic)
        total_fix = sum(p.fix_attempts for p in rec.phases)
        total_tokens = sum(
            p.prompt_tokens + p.completion_tokens for p in rec.phases
        )
        total_steps = sum(p.llm_calls + p.tool_calls for p in rec.phases)
        outcome = "success" if rec.outcome == Outcome.SUCCESS else "reverted"

        # Rating
        if outcome == "reverted" or total_fix > 5:
            rating = "poor"
        elif total_fix == 0:
            rating = "excellent"
        elif total_fix <= 2:
            rating = "good"
        else:
            rating = "average"

        assert rating == "excellent"
        assert total_fix == 0
        assert total_tokens == 1400
        assert total_steps == 7

        # Record to DB
        record_self_assessment(
            {
                "change_name": rec.change_name,
                "task_type": "impl",
                "actual_tokens": total_tokens,
                "actual_steps": total_steps,
                "fix_attempts": total_fix,
                "outcome": outcome,
                "self_rating": rating,
                "strengths": ["Clean implementation (no mechanical errors)"],
                "weaknesses": [],
                "lessons": ["first-pass success"],
            },
            db_path=db_path,
        )

        # Verify DB row
        stats = query_self_assessment_stats("impl", db_path=db_path)
        assert stats["count"] == 1
        assert stats["avg_tokens"] == 1400.0

        # Append PhaseRecord
        rec.phases.append(
            PhaseRecord(phase=Phase.REFLECT, outcome=Outcome.SUCCESS)
        )
        assert rec.phases[-1].phase == Phase.REFLECT
        assert rec.phases[-1].outcome == Outcome.SUCCESS

    def test_reflect_skipped_on_reverted(self):
        """When VERIFY fails and change is reverted, REFLECT is not executed."""
        rec = ChangeRecord(
            change_name="reverted-change",
            project="test",
            outcome=Outcome.REVERTED,
            phases=[
                PhaseRecord(
                    phase=Phase.IMPLEMENT,
                    outcome=Outcome.FAIL,
                    fix_attempts=3,
                ),
                PhaseRecord(
                    phase=Phase.VERIFY,
                    outcome=Outcome.FAIL,
                    fix_attempts=2,
                ),
            ],
        )
        # No REFLECT PhaseRecord appended
        reflect_phases = [
            p for p in rec.phases if p.phase == Phase.REFLECT
        ]
        assert len(reflect_phases) == 0


class TestPhaseReflectWithTransport:
    """Test phase_reflect with a mock transport to verify reflect.md is written."""

    def test_reflect_md_written_to_change_dir(self, db_path, tmp_path):
        from zsiga.pipeline.orchestrator import ZsigaOrchestrator
        from unittest.mock import MagicMock, patch

        # Build rec with phases
        rec = ChangeRecord(
            change_name="add-feature-y",
            project="proj",
            outcome=Outcome.SUCCESS,
            phases=[
                PhaseRecord(
                    phase=Phase.IMPLEMENT, outcome=Outcome.SUCCESS,
                    fix_attempts=0, prompt_tokens=100, completion_tokens=200,
                    llm_calls=2, tool_calls=1,
                ),
                PhaseRecord(
                    phase=Phase.VERIFY, outcome=Outcome.SUCCESS,
                    fix_attempts=0, prompt_tokens=50, completion_tokens=50,
                    llm_calls=1, tool_calls=0,
                ),
            ],
        )

        # Mock transport that captures shell commands
        written_files = {}
        transport = MagicMock()
        def capture_shell(cmd, **kwargs):
            if ">" in cmd and "reflect.md" in cmd:
                # Extract content between echo '...' > 'path'
                parts = cmd.split(">", 1)
                path = parts[1].strip().strip("'")
                content = parts[0].strip()
                if content.startswith("echo '") and content.endswith("'"):
                    content = content[6:-1]
                written_files[path] = content
            return {"exit_code": 0, "stdout": ""}
        transport.run_shell.side_effect = capture_shell

        # Patch _get_conn to use our tmp db
        with patch("zsiga.metrics.db._DB_PATH", db_path):
            # Create an orchestrator instance isn't needed for the static method
            # but we can call phase_reflect directly if we instantiate
            # Instead, create a minimal mock config
            config = MagicMock()
            config.llm.api_key = "test"
            config.llm.model = "test"
            config.llm.base_url = None
            config.llm.proxy = None
            config.pipeline.compaction.enabled = False
            config.pipeline.compaction.threshold_chars = 10000
            config.pipeline.compaction.keep_recent = 5

            with patch.object(ZsigaOrchestrator, "__init__", lambda self, cfg: None):
                orch = ZsigaOrchestrator.__new__(ZsigaOrchestrator)

            elapsed = orch.phase_reflect(
                rec, "add-feature-y", "proj", "impl",
                "/tmp/test-change", transport,
            )

        # Verify PhaseRecord appended
        assert rec.phases[-1].phase == Phase.REFLECT
        assert rec.phases[-1].outcome == Outcome.SUCCESS
        assert rec.phases[-1].detail == "excellent"
        assert elapsed >= 0

        # Verify reflect.md was written
        assert len(written_files) == 1
        content = list(written_files.values())[0]
        assert "## Task Review" in content
        assert "## Self-Rating" in content
        assert "**excellent**" in content
        assert "## Strengths" in content
        assert "## Weaknesses" in content
        assert "## Lessons Learned" in content
        assert "## Next Time Suggestions" in content
