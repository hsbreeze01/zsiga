"""Spec tests for steward-scoring-dimensions.md — 6-dimension /12 scoring and thresholds."""

from __future__ import annotations

from zsiga.agent.roles import _STEWARD_PROMPT
from zsiga.config import PipelineConfig
from zsiga.pipeline.proposal_gate import _parse_verdict


def test_steward_prompt_has_6_dimensions():
    """_STEWARD_PROMPT SHALL contain all 6 dimensions and /12 scale."""
    dimensions = [
        "可行性",
        "可执行性",
        "能力匹配",
        "历史风险",
        "范围合理性",
        "验收可测性",
    ]
    for dim in dimensions:
        assert dim in _STEWARD_PROMPT, f"Missing dimension: {dim}"
    assert "/12" in _STEWARD_PROMPT


def test_proposal_gate_parse_verdict_12():
    """_parse_verdict SHALL extract score from '总分: N/12'."""
    verdict_tuple = _parse_verdict("总分: 10/12")
    score = verdict_tuple[1]
    assert score == 10


def test_proposal_gate_parse_verdict_10_fallback():
    """_parse_verdict SHALL extract score from '总分: N/10' for backward compat."""
    verdict_tuple = _parse_verdict("总分: 7/10")
    score = verdict_tuple[1]
    assert score == 7


def test_config_default_thresholds():
    """PipelineConfig defaults: proposal_gate_score_accept=10, proposal_gate_score_pushback=6."""
    cfg = PipelineConfig()
    assert cfg.proposal_gate_score_accept == 10
    assert cfg.proposal_gate_score_pushback == 6
