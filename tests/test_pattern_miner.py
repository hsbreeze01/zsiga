"""Tests for memory/pattern_miner.py"""

import json
from pathlib import Path

from zsiga.memory.pattern_miner import mine_patterns, generate_warnings, Pattern


def _write_learnings(path: Path, records: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_mine_patterns_empty_file(tmp_path):
    f = tmp_path / "learnings.jsonl"
    f.write_text("")
    assert mine_patterns(learnings_path=f) == []


def test_mine_patterns_below_threshold(tmp_path):
    f = tmp_path / "learnings.jsonl"
    _write_learnings(f, [
        {"pattern_key": "rare.event", "takeaway": "once", "ts": "2026-01-01"},
        {"pattern_key": "rare.event", "takeaway": "twice", "ts": "2026-01-02"},
    ])
    assert mine_patterns(min_occurrences=3, learnings_path=f) == []


def test_mine_patterns_extracts_recurring(tmp_path):
    f = tmp_path / "learnings.jsonl"
    records = [
        {"pattern_key": "pipeline.fail.implement", "takeaway": f"fail {i}", "ts": f"2026-01-{i+1:02d}"}
        for i in range(5)
    ] + [
        {"pattern_key": "pipeline.pass.deliver", "takeaway": f"pass {i}", "ts": f"2026-02-{i+1:02d}"}
        for i in range(3)
    ]
    _write_learnings(f, records)

    patterns = mine_patterns(min_occurrences=3, learnings_path=f)
    assert len(patterns) == 2
    assert patterns[0].key == "pipeline.fail.implement"
    assert patterns[0].count == 5
    assert patterns[0].severity == "high"
    assert len(patterns[0].recent_takeaways) == 3
    assert patterns[1].key == "pipeline.pass.deliver"
    assert patterns[1].severity == "low"


def test_severity_classification(tmp_path):
    f = tmp_path / "learnings.jsonl"
    records = [
        {"pattern_key": "pipeline.fail.test", "takeaway": "a"},
        {"pattern_key": "pipeline.fail.test", "takeaway": "b"},
        {"pattern_key": "pipeline.fail.test", "takeaway": "c"},
        {"pattern_key": "pipeline.pass.enrich", "takeaway": "d"},
        {"pattern_key": "pipeline.pass.enrich", "takeaway": "e"},
        {"pattern_key": "pipeline.pass.enrich", "takeaway": "f"},
        {"pattern_key": "tools.venv_detection", "takeaway": "g"},
        {"pattern_key": "tools.venv_detection", "takeaway": "h"},
        {"pattern_key": "tools.venv_detection", "takeaway": "i"},
    ]
    _write_learnings(f, records)

    patterns = mine_patterns(min_occurrences=3, learnings_path=f)
    by_key = {p.key: p for p in patterns}
    assert by_key["pipeline.fail.test"].severity == "high"
    assert by_key["pipeline.pass.enrich"].severity == "low"
    assert by_key["tools.venv_detection"].severity == "medium"


def test_generate_warnings_format(tmp_path):
    patterns = [
        Pattern(key="pipeline.fail.implement", count=6, severity="high",
                recent_takeaways=["check imports", "verify test setup"]),
        Pattern(key="pipeline.pass.deliver", count=17, severity="low",
                recent_takeaways=["smooth delivery"]),
    ]
    text = generate_warnings(patterns)
    assert "pipeline.fail.implement" in text
    assert "6 次" in text
    assert "high" in text
    assert "check imports" in text


def test_generate_warnings_empty():
    assert generate_warnings([]) == ""


def test_mine_patterns_skips_no_key(tmp_path):
    f = tmp_path / "learnings.jsonl"
    _write_learnings(f, [
        {"takeaway": "no key"},
        {"pattern_key": "has.key", "takeaway": "a"},
        {"pattern_key": "has.key", "takeaway": "b"},
        {"pattern_key": "has.key", "takeaway": "c"},
    ])
    patterns = mine_patterns(min_occurrences=3, learnings_path=f)
    assert len(patterns) == 1
    assert patterns[0].key == "has.key"
