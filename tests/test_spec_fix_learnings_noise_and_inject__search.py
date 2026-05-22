"""Tests for spec: filter-and-inject.md — Relevant Learnings Search.

Covers:
- Match by change_name token
- Match pipeline.fail wildcard
- Results capped at max_results
- No matching learnings returns empty list
"""

import json
from pathlib import Path

import pytest


def _write_jsonl(path: Path, entries: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


@pytest.fixture
def memory_dir(tmp_path, monkeypatch):
    import zsiga.memory.learn as learn_mod
    monkeypatch.setattr(learn_mod, "_MEMORY_DIR", tmp_path)
    return tmp_path


SAMPLE_LEARNINGS = [
    {
        "type": "lesson",
        "pattern_key": "pipeline.fail.implement",
        "takeaway": "E701 lint error on line 42",
        "title": "FAIL: fix-lint at implement",
        "context": "project=zsiga",
        "ts": "2025-01-10T10:00:00",
    },
    {
        "type": "lesson",
        "pattern_key": "pipeline.fail.verify.diagnosed",
        "takeaway": "Missing import in test file",
        "title": "FAIL: add-feature at verify",
        "context": "project=zsiga",
        "ts": "2025-01-11T10:00:00",
    },
    {
        "type": "lesson",
        "pattern_key": "pipeline.pass.deliver",
        "takeaway": "Small focused changes work well",
        "title": "Success: fix-typo",
        "context": "project=zsiga",
        "ts": "2025-01-12T10:00:00",
    },
    {
        "type": "lesson",
        "pattern_key": "daemon.cycle_error",
        "takeaway": "tag already exists noise",
        "title": "Noise",
        "context": "daemon",
        "ts": "2025-01-13T10:00:00",
    },
    {
        "type": "lesson",
        "pattern_key": "code.unknown",
        "takeaway": "review error and adjust approach",
        "title": "Unknown error",
        "context": "code",
        "ts": "2025-01-14T10:00:00",
    },
]


# ---------------------------------------------------------------
# Scenario: Match by change_name token
# ---------------------------------------------------------------


class TestMatchByChangeNameToken:
    def test_token_from_change_name_matches(self, memory_dir):
        from zsiga.memory.learn import find_relevant_learnings
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, SAMPLE_LEARNINGS)

        results = find_relevant_learnings("fix-implement-bug", max_results=5)
        pks = [r["pattern_key"] for r in results]
        assert "pipeline.fail.implement" in pks

    def test_verify_token_matches(self, memory_dir):
        from zsiga.memory.learn import find_relevant_learnings
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, SAMPLE_LEARNINGS)

        results = find_relevant_learnings("improve-verify-pass-rate", max_results=5)
        pks = [r["pattern_key"] for r in results]
        assert "pipeline.fail.verify.diagnosed" in pks


# ---------------------------------------------------------------
# Scenario: Match pipeline.fail wildcard
# ---------------------------------------------------------------


class TestMatchPipelineFailWildcard:
    def test_pipeline_fail_entries_always_match(self, memory_dir):
        from zsiga.memory.learn import find_relevant_learnings
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, SAMPLE_LEARNINGS)

        results = find_relevant_learnings("totally-unrelated-change", max_results=10)
        pks = [r["pattern_key"] for r in results]
        # pipeline.fail.* entries should match even with unrelated change name
        assert "pipeline.fail.implement" in pks
        assert "pipeline.fail.verify.diagnosed" in pks

    def test_pipeline_pass_entries_always_match(self, memory_dir):
        from zsiga.memory.learn import find_relevant_learnings
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, SAMPLE_LEARNINGS)

        results = find_relevant_learnings("totally-unrelated-change", max_results=10)
        pks = [r["pattern_key"] for r in results]
        assert "pipeline.pass.deliver" in pks


# ---------------------------------------------------------------
# Scenario: Results capped at max_results
# ---------------------------------------------------------------


class TestResultsCapped:
    def test_capped_at_max_results(self, memory_dir):
        from zsiga.memory.learn import find_relevant_learnings
        lf = memory_dir / "learnings.jsonl"
        # Write 10 pipeline.fail entries
        entries = []
        for i in range(10):
            entries.append({
                "type": "lesson",
                "pattern_key": f"pipeline.fail.type{i}",
                "takeaway": f"Failure lesson number {i} with enough text",
                "title": f"FAIL: change-{i}",
                "context": "project=zsiga",
                "ts": f"2025-01-{10+i:02d}T10:00:00",
            })
        _write_jsonl(lf, entries)

        results = find_relevant_learnings("any-change", max_results=3)
        assert len(results) == 3

    def test_uncapped_when_fewer_than_max(self, memory_dir):
        from zsiga.memory.learn import find_relevant_learnings
        lf = memory_dir / "learnings.jsonl"
        _write_jsonl(lf, SAMPLE_LEARNINGS[:3])  # 3 clean entries

        results = find_relevant_learnings("any-change", max_results=5)
        assert len(results) <= 5


# ---------------------------------------------------------------
# Scenario: No matching learnings returns empty list
# ---------------------------------------------------------------


class TestNoMatchingLearnings:
    def test_noise_only_returns_empty(self, memory_dir):
        from zsiga.memory.learn import find_relevant_learnings
        lf = memory_dir / "learnings.jsonl"
        # Only noise entries
        noise = [
            {"type": "lesson", "pattern_key": "daemon.cycle_error", "takeaway": "noise text here", "ts": "2025-01-01T00:00:00"},
            {"type": "lesson", "pattern_key": "code.unknown", "takeaway": "review error and adjust approach", "ts": "2025-01-02T00:00:00"},
        ]
        _write_jsonl(lf, noise)

        results = find_relevant_learnings("any-change", max_results=5)
        assert results == []

    def test_empty_file_returns_empty(self, memory_dir):
        from zsiga.memory.learn import find_relevant_learnings
        lf = memory_dir / "learnings.jsonl"
        lf.write_text("", encoding="utf-8")

        results = find_relevant_learnings("any-change", max_results=5)
        assert results == []

    def test_missing_file_returns_empty(self, memory_dir):
        from zsiga.memory.learn import find_relevant_learnings
        # Don't create the file
        results = find_relevant_learnings("any-change", max_results=5)
        assert results == []
