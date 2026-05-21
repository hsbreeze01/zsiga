"""Tests for Feedback Loop metrics computation and dashboard rendering."""
import json
import sqlite3
from unittest.mock import patch

import pytest

from zsiga.metrics.feedback_loop import (
    compute_auto_proposal_rate,
    compute_injection_rate,
    compute_learnings_health,
    compute_self_assessment_coverage,
)
from zsiga.metrics.dashboard import _render_feedback_loop


@pytest.fixture()
def tmp_db(tmp_path):
    """Create a temporary DB with schema applied."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    # Apply schema from zsiga.metrics.db
    from zsiga.metrics.db import _SCHEMA
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture()
def tmp_learnings(tmp_path):
    """Create a temporary learnings.jsonl."""
    return tmp_path / "learnings.jsonl"


# ── Learnings Health ─────────────────────────────────────────


class TestLearningsHealth:
    """Tests for compute_learnings_health."""

    def test_no_learnings_file(self, tmp_learnings):
        result = compute_learnings_health(learnings_path=tmp_learnings)
        assert result["total"] == 0
        assert result["active"] == 0
        assert result["top_patterns"] == []
        assert result["last_write"] == ""

    def test_empty_learnings_file(self, tmp_learnings):
        tmp_learnings.write_text("", encoding="utf-8")
        result = compute_learnings_health(learnings_path=tmp_learnings)
        assert result["total"] == 0

    def test_learnings_exist(self, tmp_learnings):
        entries = [
            {
                "type": "lesson",
                "ts": "2026-05-07T10:00:00",
                "pattern_key": "pipeline.fail.implement",
                "title": "test 1",
            },
            {
                "type": "lesson",
                "ts": "2026-05-08T12:00:00",
                "pattern_key": "pipeline.pass.deliver",
                "title": "test 2",
            },
            {
                "type": "lesson",
                "ts": "2026-05-09T14:00:00",
                "pattern_key": "pipeline.fail.implement",
                "title": "test 3",
            },
        ]
        tmp_learnings.write_text(
            "\n".join(json.dumps(e) for e in entries),
            encoding="utf-8",
        )
        result = compute_learnings_health(learnings_path=tmp_learnings)
        assert result["total"] == 3
        assert result["active"] == 3
        assert len(result["top_patterns"]) == 2
        assert result["top_patterns"][0]["pattern_key"] == "pipeline.fail.implement"
        assert result["top_patterns"][0]["count"] == 2
        assert result["last_write"] == "2026-05-09T14:00:00"

    def test_noise_excluded_from_active(self, tmp_learnings):
        entries = [
            {
                "type": "lesson",
                "ts": "2026-05-07T10:00:00",
                "pattern_key": "daemon.cycle_error",
                "title": "noise",
            },
            {
                "type": "lesson",
                "ts": "2026-05-08T12:00:00",
                "pattern_key": "pipeline.fail.implement",
                "title": "real",
            },
        ]
        tmp_learnings.write_text(
            "\n".join(json.dumps(e) for e in entries),
            encoding="utf-8",
        )
        result = compute_learnings_health(learnings_path=tmp_learnings)
        assert result["total"] == 2
        assert result["active"] == 1

    def test_top_5_patterns_limited(self, tmp_learnings):
        entries = []
        for i in range(10):
            entries.append(
                {
                    "type": "lesson",
                    "ts": f"2026-05-{i+1:02d}T10:00:00",
                    "pattern_key": f"pattern.{i}",
                    "title": f"test {i}",
                }
            )
        tmp_learnings.write_text(
            "\n".join(json.dumps(e) for e in entries),
            encoding="utf-8",
        )
        result = compute_learnings_health(learnings_path=tmp_learnings)
        assert len(result["top_patterns"]) == 5

    def test_malformed_json_skipped(self, tmp_learnings):
        tmp_learnings.write_text(
            "not json\n"
            + json.dumps(
                {
                    "type": "lesson",
                    "ts": "2026-05-07T10:00:00",
                    "pattern_key": "ok",
                    "title": "valid",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        result = compute_learnings_health(learnings_path=tmp_learnings)
        assert result["total"] == 1


# ── Injection Rate ────────────────────────────────────────────


class TestInjectionRate:
    """Tests for compute_injection_rate."""

    def test_no_changes(self, tmp_db):
        result = compute_injection_rate(db_path=tmp_db)
        assert result["implement_rate"] == 0
        assert result["enrich_rate"] == 0
        assert result["avg_per_session"] == 0

    def test_with_injection_data(self, tmp_db):
        conn = sqlite3.connect(str(tmp_db))
        # Change 1: has lessons_count > 0, has implement + enrich
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                "feat-x",
                "proj",
                "success",
                3,
                json.dumps(
                    [
                        {"phase": "implement", "outcome": "success"},
                        {"phase": "enrich", "outcome": "success"},
                    ]
                ),
            ),
        )
        # Change 2: no lessons, has implement
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome, lessons_count, phases_json) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                "feat-y",
                "proj",
                "success",
                0,
                json.dumps(
                    [{"phase": "implement", "outcome": "success"}]
                ),
            ),
        )
        conn.commit()
        conn.close()

        result = compute_injection_rate(db_path=tmp_db)
        # 1 of 2 IMPLEMENT phases had lessons > 0 → 50%
        assert result["implement_rate"] == 50.0
        # 1 of 1 ENRICH phases had lessons > 0 → 100%
        assert result["enrich_rate"] == 100.0
        # avg = 3 lessons / 2 sessions = 1.5
        assert result["avg_per_session"] == 1.5


# ── Auto-Proposal Rate ───────────────────────────────────────


class TestAutoProposalRate:
    """Tests for compute_auto_proposal_rate."""

    def test_no_auto_proposals(self, tmp_db):
        result = compute_auto_proposal_rate(db_path=tmp_db)
        assert result["total"] == 0
        assert result["success"] == 0
        assert result["success_rate"] == 0

    def test_auto_proposals_exist(self, tmp_db):
        conn = sqlite3.connect(str(tmp_db))
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome) "
            "VALUES (?, ?, ?)",
            ("auto-fix-1", "proj", "success"),
        )
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome) "
            "VALUES (?, ?, ?)",
            ("auto-fix-2", "proj", "reverted"),
        )
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome) "
            "VALUES (?, ?, ?)",
            ("manual-change", "proj", "success"),
        )
        conn.commit()
        conn.close()

        result = compute_auto_proposal_rate(db_path=tmp_db)
        assert result["total"] == 2
        assert result["success"] == 1
        assert result["reverted"] == 1
        assert result["success_rate"] == 50.0

    def test_stuck_detection(self, tmp_db):
        """A change_name with >= 3 reverted attempts is stuck."""
        conn = sqlite3.connect(str(tmp_db))
        for _ in range(3):
            conn.execute(
                "INSERT INTO changes (change_name, project, outcome) "
                "VALUES (?, ?, ?)",
                ("auto-stuck-1", "proj", "reverted"),
            )
        conn.commit()
        conn.close()

        result = compute_auto_proposal_rate(db_path=tmp_db)
        assert result["total"] == 3
        assert result["reverted"] == 3
        assert result["stuck"] == 1
        assert result["success_rate"] == 0


# ── Self-Assessment Coverage ──────────────────────────────────


class TestSelfAssessmentCoverage:
    """Tests for compute_self_assessment_coverage."""

    def test_no_data(self, tmp_db):
        result = compute_self_assessment_coverage(db_path=tmp_db)
        assert result["total_changes"] == 0
        assert result["assessed_changes"] == 0
        assert result["coverage_pct"] == 0
        assert result["last_assessment"] == ""

    def test_with_assessments(self, tmp_db):
        conn = sqlite3.connect(str(tmp_db))
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome) "
            "VALUES (?, ?, ?)",
            ("change-1", "proj", "success"),
        )
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome) "
            "VALUES (?, ?, ?)",
            ("change-2", "proj", "reverted"),
        )
        conn.execute(
            "INSERT INTO changes (change_name, project, outcome) "
            "VALUES (?, ?, ?)",
            ("change-3", "proj", "success"),
        )
        conn.execute(
            "INSERT INTO self_assessment "
            "(change_name, task_type, outcome, self_rating) "
            "VALUES (?, ?, ?, ?)",
            ("change-1", "impl", "success", "good"),
        )
        conn.execute(
            "INSERT INTO self_assessment "
            "(change_name, task_type, outcome, self_rating) "
            "VALUES (?, ?, ?, ?)",
            ("change-3", "impl", "success", "ok"),
        )
        conn.commit()
        conn.close()

        result = compute_self_assessment_coverage(db_path=tmp_db)
        assert result["total_changes"] == 3
        assert result["assessed_changes"] == 2
        assert result["coverage_pct"] == pytest.approx(66.7, abs=0.1)
        assert result["last_assessment"] != ""


# ── Dashboard HTML Rendering ─────────────────────────────────


class TestFeedbackLoopRendering:
    """Tests for _render_feedback_loop HTML output."""

    def test_renders_feedback_loop_section(self):
        html = _render_feedback_loop()
        assert "Feedback Loop" in html

    def test_renders_four_cards(self):
        html = _render_feedback_loop()
        assert "Learnings Health" in html
        assert "Injection Rate" in html
        assert "Auto-Proposal" in html
        assert "Self-Assessment" in html

    def test_no_crash_on_empty_data(self):
        """Rendering should not raise even with no data."""
        self._assert_empty_state_fallbacks()

    def test_empty_state_fallback_messages(self):
        """Each card SHALL show its specific fallback when data is empty.

        Spec requires:
        - 'No learnings yet'       when learnings total == 0
        - 'No injection data yet'  when implement_rate and enrich_rate == 0
        - 'No auto-proposals yet'  when auto-proposal total == 0
        - 'No self-assessments recorded' when assessed_changes == 0
        """
        html = self._assert_empty_state_fallbacks()
        assert "No learnings yet" in html
        assert "No injection data yet" in html
        assert "No auto-proposals yet" in html
        assert "No self-assessments recorded" in html

    @staticmethod
    def _assert_empty_state_fallbacks() -> str:
        """Patch all metric functions to return zero-state and return HTML."""
        with patch(
            "zsiga.metrics.feedback_loop.compute_learnings_health",
            return_value={
                "total": 0,
                "active": 0,
                "top_patterns": [],
                "last_write": "",
            },
        ):
            with patch(
                "zsiga.metrics.feedback_loop.compute_injection_rate",
                return_value={
                    "implement_rate": 0,
                    "enrich_rate": 0,
                    "avg_per_session": 0,
                },
            ):
                with patch(
                    "zsiga.metrics.feedback_loop.compute_auto_proposal_rate",
                    return_value={
                        "total": 0,
                        "success": 0,
                        "reverted": 0,
                        "stuck": 0,
                        "success_rate": 0,
                    },
                ):
                    with patch(
                        "zsiga.metrics.feedback_loop.compute_self_assessment_coverage",
                        return_value={
                            "total_changes": 0,
                            "assessed_changes": 0,
                            "coverage_pct": 0,
                            "last_assessment": "",
                        },
                    ):
                        return _render_feedback_loop()

    def test_renders_with_data(self):
        with patch(
            "zsiga.metrics.feedback_loop.compute_learnings_health",
            return_value={
                "total": 42,
                "active": 38,
                "top_patterns": [
                    {"pattern_key": "pipeline.fail.implement", "count": 10}
                ],
                "last_write": "2026-05-21T16:00:00",
            },
        ):
            with patch(
                "zsiga.metrics.feedback_loop.compute_injection_rate",
                return_value={
                    "implement_rate": 75.0,
                    "enrich_rate": 60.0,
                    "avg_per_session": 2.5,
                },
            ):
                with patch(
                    "zsiga.metrics.feedback_loop.compute_auto_proposal_rate",
                    return_value={
                        "total": 10,
                        "success": 7,
                        "reverted": 3,
                        "stuck": 1,
                        "success_rate": 70.0,
                    },
                ):
                    with patch(
                        "zsiga.metrics.feedback_loop.compute_self_assessment_coverage",
                        return_value={
                            "total_changes": 50,
                            "assessed_changes": 25,
                            "coverage_pct": 50.0,
                            "last_assessment": "2026-05-21T15:00:00",
                        },
                    ):
                        html = _render_feedback_loop()
                        assert "42" in html
                        assert "75.0%" in html
                        assert "70.0%" in html
                        assert "50.0%" in html
