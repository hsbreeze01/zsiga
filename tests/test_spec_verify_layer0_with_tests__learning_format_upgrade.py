"""Spec tests for learning-format-upgrade.md — case/why/rule fields and [RULE] prefix."""

from __future__ import annotations

import json

import pytest


@pytest.fixture(autouse=True)
def _isolate_learnings(tmp_path, monkeypatch):
    """Redirect learnings.jsonl to a temp file for every test."""
    import zsiga.memory.learn as learn_mod
    import zsiga.memory.context as ctx_mod

    monkeypatch.setattr(learn_mod, "_MEMORY_DIR", tmp_path)
    monkeypatch.setattr(ctx_mod, "_MEMORY_DIR", tmp_path)
    yield tmp_path / "learnings.jsonl"


def test_record_lesson_with_case_why_rule(_isolate_learnings):
    """record_lesson SHALL persist case, why, rule as top-level keys."""
    learnings_file = _isolate_learnings
    from zsiga.memory.learn import record_lesson

    record_lesson(
        title="test_title",
        context="test_context",
        takeaway="test_takeaway",
        case={"what": "something"},
        why="because",
        rule="do X",
    )

    lines = learnings_file.read_text().strip().split("\n")
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["case"] == {"what": "something"}
    assert entry["why"] == "because"
    assert entry["rule"] == "do X"


def test_record_outcome_with_case_why_rule(_isolate_learnings):
    """record_outcome SHALL persist case, why, rule as top-level keys."""
    learnings_file = _isolate_learnings
    from zsiga.memory.learn import record_outcome

    record_outcome(
        change_name="test_change",
        project="test_project",
        success=False,
        phase="verify",
        case={"what": "w"},
        why="y",
        rule="r",
    )

    lines = learnings_file.read_text().strip().split("\n")
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["case"] == {"what": "w"}
    assert entry["why"] == "y"
    assert entry["rule"] == "r"


def test_load_recent_lessons_prefers_rule(_isolate_learnings):
    """Entries with rule field SHALL get [RULE] prefix; others SHALL NOT."""
    learnings_file = _isolate_learnings
    from zsiga.memory.context import load_recent_lessons

    # Write two entries: one with rule, one without
    entry_with_rule = json.dumps({
        "type": "lesson",
        "title": "r1",
        "context": "c1",
        "takeaway": "some takeaway",
        "rule": "always do X",
    })
    entry_without_rule = json.dumps({
        "type": "lesson",
        "title": "r2",
        "context": "c2",
        "takeaway": "another lesson",
        "pattern_key": "some_pattern",
    })
    learnings_file.write_text(entry_with_rule + "\n" + entry_without_rule + "\n")

    lessons = load_recent_lessons(n=20)
    rule_entries = [item for item in lessons if item.startswith("[RULE]")]
    non_rule_entries = [item for item in lessons if not item.startswith("[RULE]")]

    assert len(rule_entries) == 1
    assert "always do X" in rule_entries[0]
    assert len(non_rule_entries) == 1
    assert "another lesson" in non_rule_entries[0]
