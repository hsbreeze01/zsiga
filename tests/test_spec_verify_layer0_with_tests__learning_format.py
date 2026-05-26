"""Spec tests for learning-format-upgrade.md.

Covers record_lesson, record_outcome (case/why/rule fields) and
load_recent_lessons [RULE] prefix formatting.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_learnings_dir(tmp_path, monkeypatch):
    """Redirect learn.py and context.py to use a temporary learnings.jsonl."""
    import zsiga.memory.learn as learn_mod
    import zsiga.memory.context as ctx_mod

    monkeypatch.setattr(learn_mod, "_MEMORY_DIR", tmp_path)
    monkeypatch.setattr(ctx_mod, "_MEMORY_DIR", tmp_path)

    yield tmp_path


def _read_last_line(learnings_file: Path) -> dict:
    """Read the last non-empty line from learnings.jsonl as JSON."""
    assert learnings_file.exists(), f"{learnings_file} does not exist"
    lines = learnings_file.read_text(encoding="utf-8").strip().split("\n")
    assert lines, "learnings.jsonl is empty"
    return json.loads(lines[-1])


# ===================== Scenario tests =====================


def test_record_lesson_with_case_why_rule(tmp_learnings_dir):
    """record_lesson persists case, why, rule fields in learnings.jsonl."""
    from zsiga.memory.learn import record_lesson

    record_lesson(
        title="test",
        context="ctx",
        takeaway="tw",
        case={"what": "something"},
        why="because",
        rule="do X",
    )

    entry = _read_last_line(tmp_learnings_dir / "learnings.jsonl")
    assert entry["case"] == {"what": "something"}
    assert entry["why"] == "because"
    assert entry["rule"] == "do X"


def test_record_outcome_with_case_why_rule(tmp_learnings_dir):
    """record_outcome persists case, why, rule fields for failed outcomes."""
    from zsiga.memory.learn import record_outcome

    record_outcome(
        change_name="test-change",
        project="proj",
        success=False,
        phase="verify",
        case={"what": "w"},
        why="y",
        rule="r",
    )

    entry = _read_last_line(tmp_learnings_dir / "learnings.jsonl")
    assert entry["case"] == {"what": "w"}
    assert entry["why"] == "y"
    assert entry["rule"] == "r"


def test_load_recent_lessons_prefers_rule(tmp_learnings_dir):
    """load_recent_lessons formats [RULE] entries and [pattern_key] entries."""
    from zsiga.memory.learn import record_lesson
    from zsiga.memory.context import load_recent_lessons

    # Entry WITH rule
    record_lesson(
        title="t1",
        context="c1",
        takeaway="takeaway with rule",
        pattern_key="some.key",
        rule="do X",
    )
    # Entry WITHOUT rule, WITH pattern_key
    record_lesson(
        title="t2",
        context="c2",
        takeaway="plain takeaway",
        pattern_key="test.key",
    )

    lessons = load_recent_lessons(n=10)
    assert len(lessons) >= 2

    # First lesson (most recent) has no rule → [pattern_key] prefix
    assert lessons[-2].startswith("[RULE]") or any(
        l.startswith("[RULE]") for l in lessons
    ), f"Expected [RULE] prefix in lessons, got: {lessons}"

    # Check pattern_key format exists
    pattern_entries = [l for l in lessons if l.startswith("[test.key]")]
    assert len(pattern_entries) >= 1, f"No [test.key] entry found in: {lessons}"
