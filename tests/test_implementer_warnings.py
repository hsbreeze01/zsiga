"""Tests for _build_pattern_warnings() in pipeline/implementer.py."""

from unittest.mock import patch

from zsiga.memory.pattern_miner import Pattern
from zsiga.pipeline.implementer import _build_pattern_warnings


def _make_pattern(key, count, severity, recent_takeaways=None):
    return Pattern(
        key=key,
        count=count,
        severity=severity,
        recent_takeaways=recent_takeaways or [],
    )


class TestBuildPatternWarningsEmpty:
    """Returns empty string when no high-severity pipeline.fail.* patterns."""

    def test_no_patterns_at_all(self):
        with patch("zsiga.pipeline.implementer.mine_patterns", return_value=[]):
            assert _build_pattern_warnings() == ""

    def test_only_low_severity(self):
        patterns = [_make_pattern("pipeline.pass.deliver", 10, "low")]
        with patch("zsiga.pipeline.implementer.mine_patterns", return_value=patterns):
            assert _build_pattern_warnings() == ""

    def test_only_medium_severity(self):
        patterns = [_make_pattern("pipeline.cross_project", 5, "medium")]
        with patch("zsiga.pipeline.implementer.mine_patterns", return_value=patterns):
            assert _build_pattern_warnings() == ""

    def test_high_but_not_pipeline_fail(self):
        patterns = [_make_pattern("code.unknown", 3, "high")]
        with patch("zsiga.pipeline.implementer.mine_patterns", return_value=patterns):
            assert _build_pattern_warnings() == ""


class TestBuildPatternWarningsFormatted:
    """Returns formatted markdown when patterns exist."""

    def test_single_pattern(self):
        p = _make_pattern("pipeline.fail.lint", 6, "high", ["E701 error", "fix it"])
        with patch("zsiga.pipeline.implementer.mine_patterns", return_value=[p]):
            result = _build_pattern_warnings()
        assert "## Known Failure Patterns (AVOID)" in result
        assert "pipeline.fail.lint" in result
        assert "occurred 6 times" in result
        assert "E701 error" in result

    def test_limits_to_top_3(self):
        patterns = [
            _make_pattern(f"pipeline.fail.type{i}", 10 - i, "high", [f"tw{i}"])
            for i in range(5)
        ]
        with patch("zsiga.pipeline.implementer.mine_patterns", return_value=patterns):
            result = _build_pattern_warnings()
        assert "pipeline.fail.type0" in result
        assert "pipeline.fail.type1" in result
        assert "pipeline.fail.type2" in result
        assert "pipeline.fail.type3" not in result
        assert "pipeline.fail.type4" not in result

    def test_limits_takeaways_to_2(self):
        p = _make_pattern(
            "pipeline.fail.lint", 6, "high",
            ["tw1", "tw2", "tw3"],
        )
        with patch("zsiga.pipeline.implementer.mine_patterns", return_value=[p]):
            result = _build_pattern_warnings()
        assert "tw1" in result
        assert "tw2" in result
        assert "tw3" not in result
