"""Tests for SRE intent routing spec."""
from zsiga.agent.intent_router import (
    IntentType,
    Intent,
    classify,
    route,
    _verbalize,
)


# ---------------------------------------------------------------------------
# Scenario: Route returns dispatch_sre for SRE intent type
# ---------------------------------------------------------------------------
def test_route_returns_dispatch_sre_for_sre_intent():
    intent = Intent(
        verbalization="User wants to restart a service",
        intent_type=IntentType.SRE,
        confidence=0.9,
        reasoning="SRE keywords detected",
        suggested_action="dispatch_sre",
    )
    assert route(intent) == "dispatch_sre"


# ---------------------------------------------------------------------------
# Scenario: SRE value in IntentType enum
# ---------------------------------------------------------------------------
def test_sre_value_in_intent_type_enum():
    assert IntentType("sre") is IntentType.SRE
    assert IntentType.SRE.value == "sre"


# ---------------------------------------------------------------------------
# Scenario: Chinese SRE keywords classified as SRE intent
# ---------------------------------------------------------------------------
def test_chinese_sre_keywords_classified_as_sre():
    msg = "服务重启，磁盘满了"
    result = classify(msg)
    assert result.intent_type == IntentType.SRE


# ---------------------------------------------------------------------------
# Scenario: English SRE keywords classified as SRE intent
# ---------------------------------------------------------------------------
def test_english_sre_keywords_classified_as_sre():
    msg = "restart the nginx service and check health"
    result = classify(msg)
    assert result.intent_type == IntentType.SRE


# ---------------------------------------------------------------------------
# Scenario: SRE intent takes priority over implementation keywords
# ---------------------------------------------------------------------------
def test_sre_priority_over_implementation():
    msg = "清理磁盘空间"
    result = classify(msg)
    assert result.intent_type == IntentType.SRE


# ---------------------------------------------------------------------------
# Scenario: FIX intent is not overridden by SRE keywords
# ---------------------------------------------------------------------------
def test_fix_intent_not_overridden_by_sre():
    msg = "修复日志错误"
    result = classify(msg)
    assert result.intent_type == IntentType.FIX


# ---------------------------------------------------------------------------
# Scenario: Pure implementation message not misclassified as SRE
# ---------------------------------------------------------------------------
def test_pure_implementation_not_misclassified_as_sre():
    msg = "实现一个新功能模块"
    result = classify(msg)
    assert result.intent_type == IntentType.IMPLEMENTATION


# ---------------------------------------------------------------------------
# Scenario: Empty message does not produce SRE intent
# ---------------------------------------------------------------------------
def test_empty_message_not_sre():
    result = classify("")
    assert result.intent_type == IntentType.OPEN_ENDED


# ---------------------------------------------------------------------------
# Scenario: Chinese SRE verbalization
# ---------------------------------------------------------------------------
def test_chinese_sre_verbalization():
    msg = "重启服务检查健康状态"
    verb = _verbalize(msg)
    assert any(kw in verb for kw in ("运维", "基础设施", "SRE"))


# ---------------------------------------------------------------------------
# Scenario: English SRE verbalization
# ---------------------------------------------------------------------------
def test_english_sre_verbalization():
    msg = "restart service and check health status"
    verb = _verbalize(msg)
    assert any(kw in verb for kw in ("infrastructure", "SRE", "operations"))


# ---------------------------------------------------------------------------
# Scenario: SRE intent not also classified as implementation
# ---------------------------------------------------------------------------
def test_sre_not_also_implementation():
    msg = "检查服务健康状态"
    result = classify(msg)
    assert result.intent_type == IntentType.SRE
    assert result.intent_type != IntentType.IMPLEMENTATION


# ---------------------------------------------------------------------------
# Scenario: Implementation intent not classified as SRE
# ---------------------------------------------------------------------------
def test_implementation_not_classified_as_sre():
    msg = "实现用户登录模块"
    result = classify(msg)
    assert result.intent_type == IntentType.IMPLEMENTATION
    assert result.intent_type != IntentType.SRE
