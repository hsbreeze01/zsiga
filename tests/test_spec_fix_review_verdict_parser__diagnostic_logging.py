"""Tests for diagnostic logging spec.

Generated from: specs/diagnostic-logging.md
Change: fix-review-verdict-parser

Covers testable scenarios:
- Warning emitted when ISSUES_FOUND but zero issues
- No warning when ISSUES_FOUND with valid issues
- No warning when verdict is CLEAN
"""

import logging
import os

from zsiga.agent.reviewer import parse_review_verdict


def _write_review(content: str, tmpdir: str) -> str:
    """Write review.md and return the directory path."""
    path = os.path.join(tmpdir, "review.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return tmpdir


class TestWarningOnEmptyIssues:
    """Scenario: Warning emitted when ISSUES_FOUND but zero issues."""

    def test_warning_logged_with_content_preview(self, tmp_path, caplog):
        """When ISSUES_FOUND has no parseable issues, WARNING is logged."""
        # Content with ISSUES_FOUND but prose-style issues (no [SEVERITY] markers)
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "There are some problems with the implementation.\n"
            "The error handling is missing and there is dead code.\n"
        )
        change_dir = _write_review(content, str(tmp_path))
        with caplog.at_level(logging.WARNING, logger="zsiga.agent.reviewer"):
            verdict, issues = parse_review_verdict(change_dir)

        assert verdict == "ISSUES_FOUND"
        assert issues == []
        # There MUST be at least one WARNING log mentioning the empty parse
        warning_msgs = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        assert len(warning_msgs) >= 1, (
            f"Expected at least one WARNING log, got records: {caplog.records}"
        )
        # The log should contain a preview of the content
        combined = " ".join(warning_msgs)
        assert "ISSUES_FOUND" in combined or "0 issue" in combined or "empty" in combined.lower() or "no issue" in combined.lower()

    def test_warning_includes_content_preview(self, tmp_path, caplog):
        """The WARNING log includes a prefix of the raw content."""
        long_body = "A" * 600
        content = f"Verdict: ISSUES_FOUND\n\n{long_body}\n"
        change_dir = _write_review(content, str(tmp_path))
        with caplog.at_level(logging.WARNING, logger="zsiga.agent.reviewer"):
            verdict, issues = parse_review_verdict(change_dir)

        assert verdict == "ISSUES_FOUND"
        assert issues == []
        warning_msgs = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        combined = " ".join(warning_msgs)
        # The log should include some of the raw content (not necessarily all 600 chars)
        assert "AAA" in combined or len(combined) > 50


class TestNoWarningWithValidIssues:
    """Scenario: No warning when ISSUES_FOUND with valid issues."""

    def test_no_empty_issues_warning_with_numbered_issues(self, tmp_path, caplog):
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "1. [CRITICAL] Missing error handling\n"
        )
        change_dir = _write_review(content, str(tmp_path))
        with caplog.at_level(logging.WARNING, logger="zsiga.agent.reviewer"):
            verdict, issues = parse_review_verdict(change_dir)

        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 1
        # Check that the specific "empty issues" warning is NOT present
        empty_warnings = [
            r for r in caplog.records
            if r.levelno >= logging.WARNING
            and ("0 issue" in r.message or "no issue" in r.message.lower() or "empty" in r.message.lower())
        ]
        assert len(empty_warnings) == 0, (
            f"Unexpected empty-issues warning: {[r.message for r in empty_warnings]}"
        )

    def test_no_empty_issues_warning_with_bullet_issues(self, tmp_path, caplog):
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "- [CRITICAL] Dead code\n"
        )
        change_dir = _write_review(content, str(tmp_path))
        with caplog.at_level(logging.WARNING, logger="zsiga.agent.reviewer"):
            verdict, issues = parse_review_verdict(change_dir)

        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 1
        empty_warnings = [
            r for r in caplog.records
            if r.levelno >= logging.WARNING
            and ("0 issue" in r.message or "no issue" in r.message.lower() or "empty" in r.message.lower())
        ]
        assert len(empty_warnings) == 0


class TestNoWarningWhenClean:
    """Scenario: No warning when verdict is CLEAN."""

    def test_clean_verdict_no_warning(self, tmp_path, caplog):
        content = "Verdict: CLEAN\n\nAll good.\n"
        change_dir = _write_review(content, str(tmp_path))
        with caplog.at_level(logging.WARNING, logger="zsiga.agent.reviewer"):
            verdict, issues = parse_review_verdict(change_dir)

        assert verdict == "CLEAN"
        assert issues == []
        # No "empty issues" warning should fire for CLEAN verdict
        empty_warnings = [
            r for r in caplog.records
            if r.levelno >= logging.WARNING
            and ("0 issue" in r.message or "no issue" in r.message.lower() or "empty" in r.message.lower())
        ]
        assert len(empty_warnings) == 0
