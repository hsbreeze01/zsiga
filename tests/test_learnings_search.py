"""Tests for search_learnings in zsiga/memory/learn.py."""

import json

import pytest

from zsiga.memory.learn import search_learnings


@pytest.fixture
def learnings_file(tmp_path, monkeypatch):
    """Create a temporary learnings.jsonl and patch _MEMORY_DIR."""
    import zsiga.memory.learn as learn_mod

    monkeypatch.setattr(learn_mod, "_MEMORY_DIR", tmp_path)
    lf = tmp_path / "learnings.jsonl"
    return lf


def _write_entries(learnings_file, entries):
    with open(learnings_file, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


SAMPLE_ENTRIES = [
    {
        "type": "lesson",
        "ts": "2025-01-10T10:00:00",
        "title": "Pipeline implement failure",
        "context": "Failed at implement stage",
        "takeaway": "Check lint errors before commit",
        "pattern_key": "pipeline.fail.implement",
    },
    {
        "type": "lesson",
        "ts": "2025-01-11T10:00:00",
        "title": "Test timeout",
        "context": "Test suite timed out",
        "takeaway": "Reduce scope of changes",
        "pattern_key": "pipeline.fail.verify",
    },
    {
        "type": "lesson",
        "ts": "2025-01-12T10:00:00",
        "title": "Deploy success pattern",
        "context": "Smooth pipeline deploy",
        "takeaway": "Keep changes small and focused",
        "pattern_key": "pipeline.pass.deliver",
    },
]


class TestBasicKeywordMatch:
    def test_single_keyword_match(self, learnings_file):
        _write_entries(learnings_file, SAMPLE_ENTRIES)
        results = search_learnings(["pipeline"])
        assert len(results) >= 1
        assert all("pipeline" in r["title"].lower() or
                    "pipeline" in r["context"].lower() or
                    "pipeline" in r["takeaway"].lower()
                    for r in results)

    def test_multiple_keywords_returns_ranked(self, learnings_file):
        _write_entries(learnings_file, SAMPLE_ENTRIES)
        results = search_learnings(["pipeline", "implement"])
        # First entry matches both keywords
        assert results[0]["_score"] >= 2
        # Results with higher score come first
        scores = [r["_score"] for r in results]
        assert scores == sorted(scores, reverse=True)


class TestNoMatch:
    def test_no_matching_keywords_returns_empty(self, learnings_file):
        _write_entries(learnings_file, SAMPLE_ENTRIES)
        results = search_learnings(["xyzzy_nonexistent"])
        assert results == []


class TestMissingFile:
    def test_missing_file_returns_empty(self, tmp_path, monkeypatch):
        import zsiga.memory.learn as learn_mod
        monkeypatch.setattr(learn_mod, "_MEMORY_DIR", tmp_path)
        # No learnings.jsonl created
        results = search_learnings(["anything"])
        assert results == []


class TestPatternKeyFilter:
    def test_filter_by_exact_pattern_key(self, learnings_file):
        _write_entries(learnings_file, SAMPLE_ENTRIES)
        results = search_learnings(["pipeline"], pattern_key="pipeline.fail.implement")
        assert all(r["pattern_key"] == "pipeline.fail.implement" for r in results)

    def test_combined_keyword_and_pattern_key(self, learnings_file):
        _write_entries(learnings_file, SAMPLE_ENTRIES)
        results = search_learnings(["lint"], pattern_key="pipeline.fail.implement")
        # Only entries with both keyword match and pattern_key match
        assert all(r["pattern_key"] == "pipeline.fail.implement" for r in results)
        assert all(r["_score"] >= 1 for r in results)


class TestRelevanceRanking:
    def test_more_keyword_matches_rank_higher(self, learnings_file):
        _write_entries(learnings_file, SAMPLE_ENTRIES)
        results = search_learnings(["pipeline", "implement", "failure"])
        if len(results) >= 2:
            assert results[0]["_score"] >= results[1]["_score"]

    def test_tie_break_by_recency(self, learnings_file):
        # Entry with same score should be sorted by ts descending
        entries = [
            {"type": "lesson", "ts": "2025-01-01T10:00:00",
             "title": "alpha beta", "context": "", "takeaway": "",
             "pattern_key": "a"},
            {"type": "lesson", "ts": "2025-01-02T10:00:00",
             "title": "alpha beta", "context": "", "takeaway": "",
             "pattern_key": "b"},
        ]
        _write_entries(learnings_file, entries)
        results = search_learnings(["alpha", "beta"])
        assert len(results) == 2
        # Both have score 2, newer one (ts=2025-01-02) should be first
        assert results[0]["ts"] == "2025-01-02T10:00:00"


class TestCaseInsensitive:
    def test_case_insensitive_match(self, learnings_file):
        _write_entries(learnings_file, [
            {"type": "lesson", "ts": "2025-01-10T10:00:00",
             "title": "Lowercase test", "context": "",
             "takeaway": "Failed at implement: lint error",
             "pattern_key": "test"},
        ])
        results = search_learnings(["LINT"])
        assert len(results) == 1
        assert results[0]["_score"] >= 1


class TestResultFormat:
    def test_result_includes_score(self, learnings_file):
        _write_entries(learnings_file, SAMPLE_ENTRIES)
        results = search_learnings(["pipeline"])
        assert len(results) >= 1
        for r in results:
            assert "_score" in r
            assert isinstance(r["_score"], int)
            assert r["_score"] >= 1

    def test_result_preserves_original_fields(self, learnings_file):
        _write_entries(learnings_file, SAMPLE_ENTRIES)
        results = search_learnings(["pipeline"])
        assert len(results) >= 1
        r = results[0]
        assert "title" in r
        assert "context" in r
        assert "takeaway" in r
        assert "ts" in r
