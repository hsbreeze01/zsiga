"""意图路由器 — Phase 0 Intent Gate

将用户输入先 verbalize（一句话总结），再分类为六种意图，
最后路由到对应执行路径。基于关键词模式匹配 + 启发式规则，无需 LLM 调用。
"""
import re
from enum import Enum
from dataclasses import dataclass


class IntentType(str, Enum):
    RESEARCH = "research"
    IMPLEMENTATION = "implementation"
    INVESTIGATION = "investigation"
    EVALUATION = "evaluation"
    FIX = "fix"
    OPEN_ENDED = "open-ended"


@dataclass
class Intent:
    verbalization: str
    intent_type: IntentType
    confidence: float
    reasoning: str
    suggested_action: str


# ---------------------------------------------------------------------------
# 关键词模式
# ---------------------------------------------------------------------------

_RESEARCH_KEYWORDS = re.compile(
    r"分析|了解|解释|查看|查找|搜索|找到|怎么|如何|为什么|是什么|看看|查一下|找一下|"
    r"how|what|why|explain|find|search|explore|check|help|帮助|"
    r"explore|analyze|understand|describe",
    re.IGNORECASE,
)

_IMPL_KEYWORDS = re.compile(
    r"实现|添加|创建|增加|写|开发|构建|部署|安装|"
    r"implement|add|create|build|deploy|install|write|"
    r"refactor|重构|优化|optimize|配置|config|setup",
    re.IGNORECASE,
)

_INVESTIGATION_KEYWORDS = re.compile(
    r"排查|调试|追踪|诊断|报错|错误|异常|崩溃|死锁|"
    r"debug|trace|diagnose|crash|error|exception|stack|traceback|"
    r"为什么报错|什么原因|哪里出了|hang|卡住",
    re.IGNORECASE,
)

_EVALUATION_KEYWORDS = re.compile(
    r"评估|审查|对比|比较|质量|评审|review|compare|quality|assess|"
    r"evaluate|好不好|值得|优劣|选择|选型",
    re.IGNORECASE,
)

_FIX_KEYWORDS = re.compile(
    r"修复|修一下|修bug|修好|fix|patch|修补|搞定|失败|failed|"
    r"pytest.*失败|test.*fail|lint.*error|修不了|没通过|跑不过",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Verbalization
# ---------------------------------------------------------------------------

def _verbalize(message: str) -> str:
    """将用户消息总结为一句话意图描述。

    Parameters
    ----------
    message : str
        用户输入的原始消息

    Returns
    -------
    str
        一句话 verbalization
    """
    text = message.strip()

    if not text:
        return "空消息，无法判断意图"

    # Detect language: Chinese if contains CJK characters
    has_chinese = bool(re.search(r"[\u4e00-\u9fff]", text))

    # Build verbalization based on strongest keyword match
    if _FIX_KEYWORDS.search(text):
        if has_chinese:
            return "用户希望修复某个已知问题"
        return "User wants to fix a known issue"

    if _INVESTIGATION_KEYWORDS.search(text):
        if has_chinese:
            return "用户想要排查或调试某个问题"
        return "User wants to investigate or debug an issue"

    if _IMPL_KEYWORDS.search(text):
        if has_chinese:
            return "用户想要实现或创建新功能"
        return "User wants to implement or create new functionality"

    if _EVALUATION_KEYWORDS.search(text):
        if has_chinese:
            return "用户希望对代码或方案进行评估审查"
        return "User wants to evaluate or review something"

    if _RESEARCH_KEYWORDS.search(text):
        if has_chinese:
            return "用户想要了解或分析现有代码（研究性质）"
        return "User wants to explore or understand existing code (research)"

    # Ambiguous — note it
    if has_chinese:
        return "用户意图不明确，需要进一步澄清"
    return "User intent is ambiguous, needs clarification"


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(message: str) -> Intent:
    """分类用户消息的意图。

    先进行 verbalization，再基于关键词匹配分类为六种意图之一。

    Parameters
    ----------
    message : str
        用户输入的原始消息

    Returns
    -------
    Intent
        分类结果，包含 verbalization、类型、置信度、理由和建议动作
    """
    text = message.strip()

    if not text:
        return Intent(
            verbalization="空消息，无法判断意图",
            intent_type=IntentType.OPEN_ENDED,
            confidence=0.9,
            reasoning="空消息",
            suggested_action="ask_user: 请提供更多信息",
        )

    verbalization = _verbalize(text)

    # Count keyword matches for each category
    fix_matches = _FIX_KEYWORDS.findall(text)
    invest_matches = _INVESTIGATION_KEYWORDS.findall(text)
    impl_matches = _IMPL_KEYWORDS.findall(text)
    eval_matches = _EVALUATION_KEYWORDS.findall(text)
    research_matches = _RESEARCH_KEYWORDS.findall(text)

    # Score each category by match count
    scores: list[tuple[int, IntentType, str]] = []

    if fix_matches:
        scores.append((len(fix_matches), IntentType.FIX,
                       f"修复类关键词 ({len(fix_matches)} 个匹配)"))

    if invest_matches:
        scores.append((len(invest_matches), IntentType.INVESTIGATION,
                       f"排查/调试类关键词 ({len(invest_matches)} 个匹配)"))

    if impl_matches:
        has_target = bool(re.search(
            r"[\w]+功能|[\w]+模块|[\w]+接口|feature|endpoint|API|函数|类|class",
            text, re.IGNORECASE,
        ))
        # Boost score by 2 when a specific target is found for higher confidence
        impl_score = len(impl_matches) + (2 if has_target else 0)
        scores.append((impl_score, IntentType.IMPLEMENTATION,
                       f"实现类关键词 ({len(impl_matches)} 个匹配)"
                       + (" + 具体目标" if has_target else "")))

    if eval_matches:
        scores.append((len(eval_matches), IntentType.EVALUATION,
                       f"评估/审查类关键词 ({len(eval_matches)} 个匹配)"))

    if research_matches:
        scores.append((len(research_matches), IntentType.RESEARCH,
                       f"研究/探索类关键词 ({len(research_matches)} 个匹配)"))

    # No matches → open-ended
    if not scores:
        return Intent(
            verbalization=verbalization,
            intent_type=IntentType.OPEN_ENDED,
            confidence=0.4,
            reasoning="未匹配到明确的意图关键词",
            suggested_action="ask_user: 请提供更多上下文",
        )

    # Pick highest score
    scores.sort(key=lambda s: s[0], reverse=True)
    best_score, best_type, best_reasoning = scores[0]

    # Confidence based on score gap and match count
    if len(scores) == 1:
        confidence = min(0.95, 0.6 + best_score * 0.1)
    else:
        gap = best_score - scores[1][0]
        confidence = min(0.95, 0.55 + gap * 0.15 + best_score * 0.05)

    confidence = max(0.4, min(1.0, confidence))

    action_map = {
        IntentType.RESEARCH: "dispatch_explore: 派发 explore 子代理搜索代码库",
        IntentType.IMPLEMENTATION: "pipeline: ENRICH → IMPLEMENT → VERIFY → DELIVER",
        IntentType.INVESTIGATION: "dispatch_diagnoser: 派发 diagnoser 子代理排查问题",
        IntentType.EVALUATION: "dispatch_review: 派发 review 子代理评估审查",
        IntentType.FIX: "pipeline_fix: IMPLEMENT (fix) → VERIFY",
        IntentType.OPEN_ENDED: "ask_user: 请提供更多信息",
    }

    return Intent(
        verbalization=verbalization,
        intent_type=best_type,
        confidence=round(confidence, 2),
        reasoning=best_reasoning,
        suggested_action=action_map[best_type],
    )


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route(intent: Intent) -> str:
    """根据意图返回执行路径描述。

    Parameters
    ----------
    intent : Intent
        classify() 的返回结果

    Returns
    -------
    str
        执行路径名称
    """
    routing = {
        IntentType.RESEARCH: "dispatch_explore",
        IntentType.IMPLEMENTATION: "pipeline",
        IntentType.INVESTIGATION: "dispatch_diagnoser",
        IntentType.EVALUATION: "dispatch_review",
        IntentType.FIX: "pipeline_fix",
        IntentType.OPEN_ENDED: "ask_user",
    }
    return routing.get(intent.intent_type, "ask_user")
