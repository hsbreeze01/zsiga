"""Tests for SRE orchestrator integration spec."""
from zsiga.agent.intent_router import IntentType, classify


# ---------------------------------------------------------------------------
# Scenario: SRE intent not also classified as implementation
# ---------------------------------------------------------------------------
def test_sre_intent_not_implementation():
    msg = "检查服务健康状态"
    result = classify(msg)
    assert result.intent_type == IntentType.SRE
    assert result.intent_type != IntentType.IMPLEMENTATION


# ---------------------------------------------------------------------------
# Scenario: Implementation intent not classified as SRE
# ---------------------------------------------------------------------------
def test_implementation_intent_not_sre():
    msg = "实现用户登录模块"
    result = classify(msg)
    assert result.intent_type == IntentType.IMPLEMENTATION
    assert result.intent_type != IntentType.SRE


# ---------------------------------------------------------------------------
# Scenario: SRE mutual exclusion — fix has priority over SRE
# ---------------------------------------------------------------------------
def test_fix_has_priority_over_sre():
    """Even with SRE keywords present, fix keywords take priority."""
    msg = "修复服务启动失败的问题"
    result = classify(msg)
    assert result.intent_type == IntentType.FIX


# ---------------------------------------------------------------------------
# Scenario: Mixed SRE + research keywords resolved to SRE
# ---------------------------------------------------------------------------
def test_mixed_sre_research_resolved_to_sre():
    msg = "查看日志分析磁盘问题"
    result = classify(msg)
    # SRE keywords should dominate research intent
    assert result.intent_type == IntentType.SRE
