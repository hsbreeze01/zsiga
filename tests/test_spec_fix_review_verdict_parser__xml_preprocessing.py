"""Tests for XML preprocessing spec.

Generated from: specs/xml-preprocessing.md
Change: fix-review-verdict-parser

Covers testable scenarios:
- Verdict extracted from tool_call colon wrapper
- Issues extracted from tool_calling wrapper with numbered list
- Issues extracted from tool_call_layout wrapper with bullet list
- Nested XML with invoke and parameter tags is stripped
"""

import os

from zsiga.agent.reviewer import parse_review_verdict


def _write_review(content: str, tmpdir: str) -> str:
    """Write review.md and return the directory path."""
    path = os.path.join(tmpdir, "review.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return tmpdir


class TestToolCallColonWrapper:
    """Scenario: Verdict extracted from tool_call colon wrapper."""

    def test_clean_verdict_inside_tool_call_colon(self, tmp_path):
        content = (
            '<tool_call:write_file>\n'
            'path: changes/xyz/review.md\n'
            'content: Verdict: CLEAN\n\nAll specs covered.\n'
            '</tool_call:>\n'
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "CLEAN"
        assert issues == []

    def test_issues_found_inside_tool_call_colon(self, tmp_path):
        content = (
            '<tool_call:write_file>\n'
            'path: changes/xyz/review.md\n'
            'content: Verdict: ISSUES_FOUND\n\n'
            '1. [CRITICAL] Missing error handling\n'
            '</tool_call:>\n'
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 1
        assert issues[0]["severity"] == "CRITICAL"


class TestToolCallingWrapper:
    """Scenario: Issues extracted from tool_calling wrapper with numbered list."""

    def test_numbered_issues_inside_tool_calling(self, tmp_path):
        content = (
            '<tool_calling>\n'
            'Verdict: ISSUES_FOUND\n\n'
            '1. [CRITICAL] Missing error handling in foo.py line 42\n'
            '2. [SUGGESTION] Variable naming could be improved\n'
            '</tool_calling>\n'
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 2
        assert issues[0]["severity"] == "CRITICAL"
        assert "Missing error handling" in issues[0]["description"]
        assert issues[1]["severity"] == "SUGGESTION"


class TestToolCallLayoutWrapper:
    """Scenario: Issues extracted from tool_call_layout wrapper with bullet list."""

    def test_bullet_issues_inside_tool_call_layout(self, tmp_path):
        content = (
            '<tool_call_layout>\n'
            'Verdict: ISSUES_FOUND\n\n'
            '- [CRITICAL] Dead code in bar.py\n'
            '- [SUGGESTION] Add docstring to public function\n'
            '</tool_call_layout>\n'
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 2
        assert issues[0]["severity"] == "CRITICAL"
        assert "Dead code" in issues[0]["description"]
        assert issues[1]["severity"] == "SUGGESTION"
        assert "Add docstring" in issues[1]["description"]


class TestNestedInvokeXML:
    """Scenario: Nested XML with invoke and parameter tags is stripped."""

    def test_invoke_write_file_with_verdict_and_issue(self, tmp_path):
        content = (
            '<invoke name="write_file">\n'
            '<parameter name="path">changes/xyz/review.md</parameter>\n'
            '<parameter name="content">Verdict: ISSUES_FOUND\n'
            '1. [CRITICAL] Bug in authentication module</parameter>\n'
            '</invoke>\n'
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) >= 1
        assert issues[0]["severity"] == "CRITICAL"
        assert "Bug" in issues[0]["description"] or "authentication" in issues[0]["description"]

    def test_invoke_with_clean_verdict(self, tmp_path):
        content = (
            '<invoke name="write_file">\n'
            '<parameter name="content">Verdict: CLEAN</parameter>\n'
            '</invoke>\n'
        )
        change_dir = _write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "CLEAN"
        assert issues == []
