"""Unit tests for agent/reviewer.py: parse_review_verdict, _has_critical, _build_fix_prompt, ReviewLoopResult."""

import os

from zsiga.agent.reviewer import (
    ReviewLoopResult,
    _build_fix_prompt,
    _has_critical,
    parse_review_verdict,
)


class TestParseReviewVerdict:
    """Tests for parse_review_verdict function."""

    def _write_review(self, content: str, tmpdir: str) -> str:
        """Write review.md and return the directory path."""
        path = os.path.join(tmpdir, "review.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return tmpdir

    def test_parse_clean_verdict(self, tmp_path):
        """CLEAN verdict returns no issues."""
        change_dir = self._write_review(
            "Verdict: CLEAN\n\nAll specs covered.", str(tmp_path)
        )
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "CLEAN"
        assert issues == []

    def test_parse_issues_found_with_mixed_severities(self, tmp_path):
        """ISSUES_FOUND verdict returns CRITICAL and SUGGESTION issues."""
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "Issues:\n"
            "1. [CRITICAL] Missing error handling in foo.py line 42\n"
            "2. [SUGGESTION] Consider using a more descriptive variable name\n"
            "3. [CRITICAL] Dead code detected in bar.py\n"
        )
        change_dir = self._write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 3
        assert issues[0]["severity"] == "CRITICAL"
        assert "Missing error handling" in issues[0]["description"]
        assert issues[1]["severity"] == "SUGGESTION"
        assert issues[2]["severity"] == "CRITICAL"
        assert "Dead code" in issues[2]["description"]

    def test_parse_missing_file_returns_unknown(self, tmp_path):
        """Missing review.md returns UNKNOWN verdict."""
        verdict, issues = parse_review_verdict(str(tmp_path))
        assert verdict == "UNKNOWN"
        assert issues == []

    def test_parse_malformed_no_verdict_line(self, tmp_path):
        """File without Verdict: line returns UNKNOWN."""
        change_dir = self._write_review(
            "This is just some random text\nNo verdict here.", str(tmp_path)
        )
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "UNKNOWN"
        assert issues == []

    def test_parse_issues_found_only_suggestions(self, tmp_path):
        """ISSUES_FOUND with only SUGGESTION issues."""
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "Issues:\n"
            "1. [SUGGESTION] Variable name could be more descriptive\n"
            "2. [SUGGESTION] Consider adding type hints\n"
        )
        change_dir = self._write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 2
        assert all(i["severity"] == "SUGGESTION" for i in issues)

    def test_parse_issues_found_only_critical(self, tmp_path):
        """ISSUES_FOUND with only CRITICAL issues."""
        content = (
            "Verdict: ISSUES_FOUND\n\n"
            "Issues:\n"
            "1. [CRITICAL] Missing spec requirement: error handling\n"
        )
        change_dir = self._write_review(content, str(tmp_path))
        verdict, issues = parse_review_verdict(change_dir)
        assert verdict == "ISSUES_FOUND"
        assert len(issues) == 1
        assert issues[0]["severity"] == "CRITICAL"


class TestHasCritical:
    """Tests for _has_critical helper."""

    def test_empty_list(self):
        assert _has_critical([]) is False

    def test_no_critical(self):
        issues = [
            {"severity": "SUGGESTION", "description": "naming"},
        ]
        assert _has_critical(issues) is False

    def test_with_critical(self):
        issues = [
            {"severity": "SUGGESTION", "description": "naming"},
            {"severity": "CRITICAL", "description": "missing error handling"},
        ]
        assert _has_critical(issues) is True

    def test_only_critical(self):
        issues = [
            {"severity": "CRITICAL", "description": "dead code"},
        ]
        assert _has_critical(issues) is True

    def test_missing_severity_key(self):
        issues = [{"description": "something"}]
        assert _has_critical(issues) is False


class TestBuildFixPrompt:
    """Tests for _build_fix_prompt helper."""

    def test_returns_system_and_user(self):
        issues = [
            {"severity": "CRITICAL", "description": "Missing error handling"},
            {"severity": "SUGGESTION", "description": "Naming issue"},
        ]
        system, user = _build_fix_prompt(issues, ["foo.py", "bar.py"], "/project")
        assert "CRITICAL" in system or "CRITICAL" in user
        assert "Missing error handling" in user
        assert "foo.py" in user
        assert "bar.py" in user
        assert "/project" in user

    def test_only_critical_in_prompt(self):
        """Only CRITICAL issues should appear in the fix prompt."""
        issues = [
            {"severity": "CRITICAL", "description": "Bug in auth"},
            {"severity": "SUGGESTION", "description": "Naming"},
        ]
        system, user = _build_fix_prompt(issues, ["auth.py"], "/proj")
        assert "Bug in auth" in user
        assert "Naming" not in user

    def test_empty_changed_files(self):
        issues = [{"severity": "CRITICAL", "description": "Bug"}]
        system, user = _build_fix_prompt(issues, [], "/proj")
        assert "无" in user


class TestReviewLoopResult:
    """Tests for ReviewLoopResult dataclass defaults."""

    def test_defaults(self):
        result = ReviewLoopResult(
            final_verdict="CLEAN",
            rounds_executed=1,
            fix_attempts=0,
            elapsed_seconds=5.0,
        )
        assert result.final_verdict == "CLEAN"
        assert result.rounds_executed == 1
        assert result.fix_attempts == 0
        assert result.elapsed_seconds == 5.0
        assert result.last_issues == []
        assert result.had_critical is False
        assert result.llm_calls == 0
        assert result.tool_calls == 0
        assert result.prompt_tokens == 0
        assert result.completion_tokens == 0

    def test_with_issues(self):
        issues = [
            {"severity": "CRITICAL", "description": "Missing handler"},
        ]
        result = ReviewLoopResult(
            final_verdict="ISSUES_FOUND",
            rounds_executed=2,
            fix_attempts=1,
            elapsed_seconds=30.0,
            last_issues=issues,
            had_critical=True,
        )
        assert result.final_verdict == "ISSUES_FOUND"
        assert result.had_critical is True
        assert len(result.last_issues) == 1

    def test_metrics_set_explicitly(self):
        """Metrics fields can be set with explicit values."""
        result = ReviewLoopResult(
            final_verdict="CLEAN",
            rounds_executed=2,
            fix_attempts=1,
            elapsed_seconds=10.0,
            llm_calls=12,
            tool_calls=24,
            prompt_tokens=13000,
            completion_tokens=3500,
        )
        assert result.llm_calls == 12
        assert result.tool_calls == 24
        assert result.prompt_tokens == 13000
        assert result.completion_tokens == 3500
