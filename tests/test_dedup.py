"""Tests for proposal deduplication checker (PDC-01 through PDC-05)."""

import os
import tempfile

from zsiga.pipeline.dedup import (
    ArchivedProposal,
    DuplicateMatch,
    check_duplicates,
    compute_similarity,
    load_archived_proposals,
    normalize,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_archive(tmp_path, entries: dict[str, str]):
    """Create an archive tree under *tmp_path*/archive/.

    *entries*: {subdir_name: proposal_md_content}
    """
    archive = tmp_path / "archive"
    archive.mkdir()
    for name, content in entries.items():
        d = archive / name
        d.mkdir()
        (d / "proposal.md").write_text(content)
    return str(archive)


# ===================================================================
# PDC-01 — Load Archived Proposals
# ===================================================================


class TestLoadArchivedProposals:
    def test_multiple_archived_proposals(self, tmp_path):
        archive = _make_archive(tmp_path, {
            "change-a": "Proposal A content",
            "change-b": "Proposal B content",
            "change-c": "Proposal C content",
            "change-d": "Proposal D content",
            "change-e": "Proposal E content",
        })
        result = load_archived_proposals(archive)
        assert len(result) == 5
        ids = {r.id for r in result}
        assert ids == {"change-a", "change-b", "change-c", "change-d", "change-e"}
        for r in result:
            assert r.proposal_text

    def test_empty_archive_directory(self, tmp_path):
        archive = tmp_path / "archive"
        archive.mkdir()
        result = load_archived_proposals(str(archive))
        assert result == []

    def test_nonexistent_archive_directory(self, tmp_path):
        result = load_archived_proposals(str(tmp_path / "no-such-dir"))
        assert result == []

    def test_archived_change_missing_proposal(self, tmp_path):
        """Subdirs without proposal.md are skipped."""
        archive = tmp_path / "archive"
        archive.mkdir()
        # one valid, one without proposal.md
        d_valid = archive / "has-proposal"
        d_valid.mkdir()
        (d_valid / "proposal.md").write_text("Some proposal")
        d_empty = archive / "no-proposal"
        d_empty.mkdir()
        (d_empty / "design.md").write_text("Only design")
        result = load_archived_proposals(str(archive))
        assert len(result) == 1
        assert result[0].id == "has-proposal"


# ===================================================================
# PDC-02 — Compute Similarity Score
# ===================================================================


class TestComputeSimilarity:
    def test_identical_proposals(self):
        text = "Implement a retry backoff mechanism for the pipeline"
        assert compute_similarity(text, text) == 1.0

    def test_completely_different_proposals(self):
        a = "Implement retry backoff for network requests"
        b = "Add a colourful dashboard widget for analytics"
        assert compute_similarity(a, b) < 0.3

    def test_partially_similar_proposals(self):
        a = "Implement change conflict detector for the pipeline"
        b = "Implement change conflict resolver for the pipeline"
        score = compute_similarity(a, b)
        assert 0.3 <= score <= 0.9

    def test_both_empty(self):
        assert compute_similarity("", "") == 1.0


# ===================================================================
# PDC-03 — Find Potential Duplicates
# ===================================================================


class TestCheckDuplicates:
    def test_exact_duplicate_found(self, tmp_path):
        text = "Add user authentication module"
        archive = _make_archive(tmp_path, {
            "2024-01-01-auth": text,
        })
        result = check_duplicates(text, archive)
        assert len(result) == 1
        assert result[0].score == 1.0
        assert result[0].change_id == "2024-01-01-auth"

    def test_multiple_similar_above_threshold(self, tmp_path):
        new_text = "Implement a retry backoff mechanism for pipeline tasks"
        # One high-similarity, one medium (below 0.5 default), one low
        archive = _make_archive(tmp_path, {
            "high": "Implement a retry backoff mechanism for pipeline tasks with exponential delay",
            "medium": "Add logging to pipeline tasks for debugging",
            "low": "Create a dashboard widget for analytics charts",
        })
        result = check_duplicates(new_text, archive)
        # Only 'high' should be above 0.5 default threshold
        assert len(result) == 1
        assert result[0].change_id == "high"
        assert result[0].score >= 0.5

    def test_no_duplicates_found(self, tmp_path):
        new_text = "Build a machine learning model for sentiment analysis"
        archive = _make_archive(tmp_path, {
            "a": "Fix the footer layout on the dashboard page",
            "b": "Add export to CSV functionality",
        })
        result = check_duplicates(new_text, archive)
        assert result == []

    def test_empty_archive(self, tmp_path):
        archive = tmp_path / "archive"
        archive.mkdir()
        result = check_duplicates("Some proposal", str(archive))
        assert result == []

    def test_custom_threshold(self, tmp_path):
        new_text = "Implement a retry backoff mechanism for pipeline tasks"
        archive = _make_archive(tmp_path, {
            "high": "Implement a retry backoff mechanism for pipeline tasks with extra options",
            "mid": "Add retry logic to task processing",
        })
        result = check_duplicates(new_text, archive, threshold=0.9)
        # Only proposals scoring >= 0.9 should appear
        for m in result:
            assert m.score >= 0.9

    def test_results_sorted_descending(self, tmp_path):
        new_text = "Implement caching layer for API responses"
        archive = _make_archive(tmp_path, {
            "best": "Implement caching layer for API responses with TTL support",
            "good": "Implement caching for API responses",
            "ok": "Add caching to API layer",
        })
        result = check_duplicates(new_text, archive, threshold=0.3)
        scores = [m.score for m in result]
        assert scores == sorted(scores, reverse=True)


# ===================================================================
# PDC-04 — Text Normalization
# ===================================================================


class TestNormalize:
    def test_whitespace_normalization(self):
        a = "Implement  a   retry\n\nbackoff\tmechanism"
        b = "Implement a retry backoff mechanism"
        assert compute_similarity(a, b) == 1.0

    def test_case_normalization(self):
        a = "Implement A Retry Backoff Mechanism"
        b = "implement a retry backoff mechanism"
        assert compute_similarity(a, b) == 1.0

    def test_header_prefix_stripped(self):
        a = "# Proposal: Implement change conflict detector\n\nThis is the body."
        b = "Implement change conflict detector This is the body"
        score = compute_similarity(a, b)
        assert score >= 0.9


# ===================================================================
# PDC-05 — Deterministic and No External Dependencies
# ===================================================================


class TestDeterminism:
    def test_consistent_results_across_runs(self, tmp_path):
        new_text = "Implement a caching layer for database queries"
        archive = _make_archive(tmp_path, {
            "a": "Add caching to database access layer",
            "b": "Implement a caching layer for database queries with TTL",
        })
        result1 = check_duplicates(new_text, archive, threshold=0.3)
        result2 = check_duplicates(new_text, archive, threshold=0.3)
        assert len(result1) == len(result2)
        for r1, r2 in zip(result1, result2):
            assert r1.change_id == r2.change_id
            assert r1.score == r2.score
