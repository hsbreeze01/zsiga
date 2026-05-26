"""Tests for issue pattern matching spec.

Generated from: specs/issue-pattern-matching.md
Change: fix-review-verdict-parser

Covers testable scenarios:
- Numbered list issues are extracted
- Bullet list issues are extracted
- Bare severity issues are extracted
- Multi-line issue description is merged
- Mixed format issues are all extracted
- CLEAN verdict returns empty issues list
"""

import os

from zsiga.agent.reviewer import parse_review_verdict


def _write_review(content: str, tmpdir: str) -> str:
    """Write review.md and return the directory path."""
    path = os.path.join(tmpdir, "review.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return tmpdir


class TestNumberedListIssues:
    """Scenario: Numbered list issues are extracted."""

    def test_numbered_critical_and_suggestion(self, tmp_path):
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "Issues:\n"
            "1. [CRITICAL] Missing error handling in foo.py line 42\n"
            "2. [SUGGESTION] Variable naming could be improved\n"
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 2
        assert issues[0]["severity"] == "CRITICAL"
        assert "Missing error handling" in issues[0]["description"]
        assert issues[1]["severity"] == "SUGGESTION"
        assert "Variable naming" in issues[1]["description"]


class TestBulletListIssues:
    """Scenario: Bullet list issues are extracted."""

    def test_bullet_critical_and_suggestion(self, tmp_path):
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "Issues:\n"
            "- [CRITICAL] Dead code detected in bar.py\n"
            "- [SUGGESTION] Add type hints to function signature\n"
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 2
        assert issues[0]["severity"] == "CRITICAL"
        assert "Dead code" in issues[0]["description"]
        assert issues[1]["severity"] == "SUGGESTION"
        assert "Add type hints" in issues[1]["description"]


class TestBareSeverityIssues:
    """Scenario: Bare severity issues are extracted."""

    def test_bare_critical_and_suggestion(self, tmp_path):
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "Issues:\n"
            "[CRITICAL] Missing import statement\n"
            "[SUGGESTION] Use f-string instead of format\n"
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 2
        assert issues[0]["severity"] == "CRITICAL"
        assert "Missing import" in issues[0]["description"]
        assert issues[1]["severity"] == "SUGGESTION"
        assert "f-string" in issues[1]["description"]


class TestMultiLineIssueDescription:
    """Scenario: Multi-line issue description is merged."""

    def test_numbered_issue_spans_multiple_lines(self, tmp_path):
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "Issues:\n"
            "1. [CRITICAL] Missing error handling in foo.py line 42\n"
            "   The function does not catch ValueError which may be raised\n"
            "   by the parser when input is malformed\n"
            "2. [SUGGESTION] Consider using a context manager\n"
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 2
        # First issue should contain multi-line description
        assert "Missing error handling" in issues[0]["description"]
        assert "ValueError" in issues[0]["description"] or "parser" in issues[0]["description"]

    def test_bullet_issue_spans_multiple_lines(self, tmp_path):
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "Issues:\n"
            "- [CRITICAL] Dead code in bar.py\n"
            "  Lines 10-15 are unreachable after the return statement\n"
            "- [SUGGESTION] Rename variable x\n"
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 2
        assert "Dead code" in issues[0]["description"]
        assert "unreachable" in issues[0]["description"]


class TestMixedFormatIssues:
    """Scenario: Mixed format issues are all extracted."""

    def test_mixed_numbered_bullet_and_bare(self, tmp_path):
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "1. [CRITICAL] Missing error handling\n"
            "- [CRITICAL] Dead code detected\n"
            "[SUGGESTION] Use better naming\n"
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 3
        severities = [i["severity"] for i in issues]
        assert severities.count("CRITICAL") == 2
        assert severities.count("SUGGESTION") == 1
        # All descriptions must be non-empty
        for issue in issues:
            assert len(issue["description"].strip()) > 0


class TestCleanVerdictBackwardCompat:
    """Scenario: CLEAN verdict returns empty issues list."""

    def test_clean_verdict_no_regression(self, tmp_path):
        content = "Verdict: CLEAN\n\nAll specs covered."
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "CLEAN"
        assert issues == []

    def test_clean_verdict_with_extra_text(self, tmp_path):
        content = (
            "Verdict: CLEAN\n\n"
            "The implementation looks good. All spec requirements are met.\n"
            "1. [CRITICAL] This is just text, not a real issue since verdict is CLEAN\n"
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "CLEAN"
        assert issues == []
