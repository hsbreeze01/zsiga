"""Tests for Phase 0 Intent Gate — 6-category intent router."""
import pytest

from zsiga.agent.intent_router import (
    IntentType,
    Intent,
    _verbalize,
    classify,
    route,
)


# ============================================================================
# REQ-IG-01: Intent Classification — Six Categories
# ============================================================================

class TestClassifyResearch:
    """Scenario: Classify a research request."""

    @pytest.mark.parametrize("msg", [
        "分析一下这个模块",
        "explain how the router works",
        "how does X work",
        "这个模块的职责是什么",
        "查看一下代码结构",
        "help me understand the architecture",
    ])
    def test_research_intent(self, msg):
        result = classify(msg)
        assert result.intent_type == IntentType.RESEARCH
        assert result.confidence >= 0.6

    def test_research_confidence_range(self):
        result = classify("分析一下")
        assert 0.0 <= result.confidence <= 1.0


class TestClassifyImplementation:
    """Scenario: Classify an implementation request."""

    @pytest.mark.parametrize("msg", [
        "实现一个新功能",
        "添加用户管理模块",
        "create a new endpoint",
        "build the REST API",
        "重构一下这个接口",
        "优化性能",
    ])
    def test_implementation_intent(self, msg):
        result = classify(msg)
        assert result.intent_type == IntentType.IMPLEMENTATION
        assert result.confidence >= 0.6

    def test_implementation_high_confidence_with_target(self):
        result = classify("实现用户管理功能")
        assert result.intent_type == IntentType.IMPLEMENTATION
        assert result.confidence >= 0.8


class TestClassifyInvestigation:
    """Scenario: Classify an investigation request."""

    @pytest.mark.parametrize("msg", [
        "排查一下这个报错",
        "为什么报错了",
        "debug the crash",
        "trace the error",
        "什么原因导致崩溃",
        "stack traceback 分析",
    ])
    def test_investigation_intent(self, msg):
        result = classify(msg)
        assert result.intent_type == IntentType.INVESTIGATION
        assert result.confidence >= 0.6


class TestClassifyEvaluation:
    """Scenario: Classify an evaluation request."""

    @pytest.mark.parametrize("msg", [
        "评估一下这个方案",
        "review the code quality",
        "compare two approaches",
        "对比方案优劣",
        "代码质量怎么样",
    ])
    def test_evaluation_intent(self, msg):
        result = classify(msg)
        assert result.intent_type == IntentType.EVALUATION
        assert result.confidence >= 0.6


class TestClassifyFix:
    """Scenario: Classify a fix request."""

    @pytest.mark.parametrize("msg", [
        "修复这个 bug",
        "fix the failing test",
        "pytest 跑不过了，帮我修一下",
        "lint error 修一下",
        "修bug",
    ])
    def test_fix_intent(self, msg):
        result = classify(msg)
        assert result.intent_type == IntentType.FIX
        assert result.confidence >= 0.6


class TestClassifyOpenEnded:
    """Scenario: Classify ambiguous input."""

    @pytest.mark.parametrize("msg", [
        "嗯",
        "随便",
        "今天天气不错",
    ])
    def test_open_ended_intent(self, msg):
        result = classify(msg)
        assert result.intent_type == IntentType.OPEN_ENDED


class TestClassifyEmptyMessage:
    """Edge case: empty message."""

    def test_empty_string(self):
        result = classify("")
        assert result.intent_type == IntentType.OPEN_ENDED
        assert "空消息" in result.verbalization

    def test_whitespace_only(self):
        result = classify("   ")
        assert result.intent_type == IntentType.OPEN_ENDED
        assert "空消息" in result.verbalization


# ============================================================================
# REQ-IG-02: Verbalization — Pre-classification Intent Summary
# ============================================================================

class TestVerbalization:
    """Scenarios for verbalization output."""

    def test_verbalization_research(self):
        result = _verbalize("这个模块的职责是什么")
        assert result != ""
        assert "研究" in result or "了解" in result or "分析" in result

    def test_verbalization_fix(self):
        result = _verbalize("pytest 跑不过了，帮我修一下")
        assert result != ""
        assert "修复" in result

    def test_verbalization_empty(self):
        result = _verbalize("")
        assert result == "空消息，无法判断意图"

    def test_verbalization_whitespace(self):
        result = _verbalize("   ")
        assert result == "空消息，无法判断意图"

    def test_verbalization_english(self):
        result = _verbalize("explain how this works")
        assert result != ""
        assert "research" in result.lower() or "explore" in result.lower()

    def test_verbalization_in_intent(self):
        """Intent object has verbalization (REQ-IG-04)."""
        result = classify("分析一下代码结构")
        assert result.verbalization != ""

    def test_verbalization_non_empty_for_any_message(self):
        result = classify("some random text here")
        assert result.verbalization != ""


# ============================================================================
# REQ-IG-03: Routing Map — Intent to Execution Path
# ============================================================================

class TestRouting:
    """Scenarios for route mapping."""

    def test_research_routes_to_explore(self):
        intent = Intent(
            verbalization="test",
            intent_type=IntentType.RESEARCH,
            confidence=0.8,
            reasoning="test",
            suggested_action="test",
        )
        assert route(intent) == "dispatch_explore"

    def test_implementation_routes_to_pipeline(self):
        intent = Intent(
            verbalization="test",
            intent_type=IntentType.IMPLEMENTATION,
            confidence=0.8,
            reasoning="test",
            suggested_action="test",
        )
        assert route(intent) == "pipeline"

    def test_investigation_routes_to_diagnoser(self):
        intent = Intent(
            verbalization="test",
            intent_type=IntentType.INVESTIGATION,
            confidence=0.8,
            reasoning="test",
            suggested_action="test",
        )
        assert route(intent) == "dispatch_diagnoser"

    def test_evaluation_routes_to_review(self):
        intent = Intent(
            verbalization="test",
            intent_type=IntentType.EVALUATION,
            confidence=0.8,
            reasoning="test",
            suggested_action="test",
        )
        assert route(intent) == "dispatch_review"

    def test_fix_routes_to_pipeline_fix(self):
        intent = Intent(
            verbalization="test",
            intent_type=IntentType.FIX,
            confidence=0.8,
            reasoning="test",
            suggested_action="test",
        )
        assert route(intent) == "pipeline_fix"

    def test_open_ended_routes_to_ask_user(self):
        intent = Intent(
            verbalization="test",
            intent_type=IntentType.OPEN_ENDED,
            confidence=0.4,
            reasoning="test",
            suggested_action="test",
        )
        assert route(intent) == "ask_user"


# ============================================================================
# REQ-IG-04: Intent Data Model
# ============================================================================

class TestIntentDataModel:
    """Scenarios for Intent dataclass fields."""

    def test_intent_has_verbalization(self):
        result = classify("实现一个功能")
        assert isinstance(result.verbalization, str)
        assert result.verbalization != ""

    def test_intent_has_valid_confidence(self):
        result = classify("fix the bug")
        assert 0.0 <= result.confidence <= 1.0

    def test_intent_has_reasoning(self):
        result = classify("debug this error")
        assert result.reasoning != ""

    def test_intent_has_suggested_action(self):
        result = classify("review the code")
        assert result.suggested_action != ""

    def test_intent_type_is_enum(self):
        result = classify("explain this")
        assert isinstance(result.intent_type, IntentType)


# ============================================================================
# REQ-IG-05: Logging — Intent Gate Decision (verified via classify output)
# ============================================================================

class TestLogging:
    """Verify that classify returns all needed fields for logging."""

    def test_all_logging_fields_present(self):
        result = classify("修复一下这个错误")
        # All fields needed for logging must be non-empty
        assert result.verbalization != ""
        assert result.intent_type.value != ""
        assert result.confidence > 0
        assert result.suggested_action != ""


# ============================================================================
# Mixed / edge cases
# ============================================================================

class TestMixedKeywords:
    """Messages containing keywords from multiple categories."""

    def test_fix_and_impl_both_present_fix_wins(self):
        """Fix keywords are generally stronger — test fix wins when present."""
        result = classify("fix the broken implementation")
        assert result.intent_type == IntentType.FIX

    def test_mixed_confidence_is_reasonable(self):
        result = classify("debug the failing create endpoint")
        assert result.confidence >= 0.4


class TestIntentTypeEnum:
    """Verify the enum values."""

    def test_six_categories(self):
        assert len(IntentType) == 6

    def test_values(self):
        expected = {"research", "implementation", "investigation",
                    "evaluation", "fix", "open-ended"}
        actual = {e.value for e in IntentType}
        assert actual == expected
