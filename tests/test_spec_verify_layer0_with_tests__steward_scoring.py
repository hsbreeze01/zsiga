"""Spec tests for steward-scoring-dimensions.md.

Covers _STEWARD_PROMPT dimensions, _parse_verdict /12 and /10 parsing,
and PipelineConfig default gate thresholds.
"""
from __future__ import annotations

import pytest


# ===================== Scenario tests =====================


def test_steward_prompt_has_6_dimensions_and_12_scale():
    """_STEWARD_PROMPT contains all 6 dimension names and /12 scale."""
    from zsiga.agent.roles import _STEWARD_PROMPT

    # All 6 dimension names must be present
    required_dims = [
        "可行性",
        "可执行性",
        "能力匹配",
        "历史风险",
        "范围合理性",
        "验收可测性",
    ]
    for dim in required_dims:
        assert dim in _STEWARD_PROMPT, f"Missing dimension: {dim}"

    # Must use /12 scale
    assert "/12" in _STEWARD_PROMPT, "Missing /12 scale marker"


def test_parse_verdict_12_point_score():
    """_parse_verdict extracts PUSHBACK verdict and 10/12 score."""
    from zsiga.pipeline.proposal_gate import GateVerdict, _parse_verdict

    text = "## Verdict: PUSHBACK\n\n## 评分详情\n- 总分: 10/12\n"
    verdict, score = _parse_verdict(text)

    assert verdict == GateVerdict.PUSHBACK
    assert score == 10


def test_parse_verdict_10_point_fallback():
    """_parse_verdict handles legacy /10 format correctly."""
    from zsiga.pipeline.proposal_gate import GateVerdict, _parse_verdict

    text = "## Verdict: ACCEPT\n\n- 总分: 7/10\n"
    verdict, score = _parse_verdict(text)

    assert verdict == GateVerdict.ACCEPT
    assert score == 7


def test_config_default_thresholds():
    """PipelineConfig defaults match the 12-point steward scale."""
    from zsiga.config import PipelineConfig

    cfg = PipelineConfig()
    assert cfg.proposal_gate_score_accept == 10
    assert cfg.proposal_gate_score_pushback == 6
