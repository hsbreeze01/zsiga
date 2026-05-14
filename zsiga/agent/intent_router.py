"""意图路由器 — 请求分类引擎

将用户输入分类为四种意图，并路由到对应执行路径。
基于关键词模式匹配 + 启发式规则，无需 LLM 调用。
"""
import re
from enum import Enum
from dataclasses import dataclass


class IntentType(str, Enum):
    TRIVIAL = "trivial"
    EXPLORATION = "exploration"
    IMPLEMENTATION = "implementation"
    AMBIGUOUS = "ambiguous"


@dataclass
class Intent:
    intent_type: IntentType
    confidence: float
    reasoning: str
    suggested_action: str


# ---------------------------------------------------------------------------
# 关键词模式
# ---------------------------------------------------------------------------

_IMPL_KEYWORDS = re.compile(
    r"实现|添加|创建|增加|写|开发|构建|部署|安装|修复|fix|implement|add|create|"
    r"build|deploy|install|write|refactor|重构|优化|optimize|配置|config|setup",
    re.IGNORECASE,
)

_EXPLORE_KEYWORDS = re.compile(
    r"怎么|如何|为什么|是什么|解释|查看|查找|搜索|找到|分析|了解|"
    r"how|what|why|explain|find|search|explore|investigate|check|"
    r"看看|查一下|找一下|help|帮助",
    re.IGNORECASE,
)

_TRIVIAL_KEYWORDS = re.compile(
    r"^(hi|hello|hey|你好|嗨|ok|好的|yes|no|是|否|谢谢|thanks|done|完成)$",
    re.IGNORECASE,
)


def classify(message: str) -> Intent:
    """分类用户消息的意图。

    Parameters
    ----------
    message : str
        用户输入的原始消息

    Returns
    -------
    Intent
        分类结果，包含类型、置信度、理由和建议动作
    """
    text = message.strip()

    if not text:
        return Intent(
            intent_type=IntentType.AMBIGUOUS,
            confidence=0.9,
            reasoning="空消息",
            suggested_action="ask_user: 请提供更多信息",
        )

    # 1. Trivial 检测（问候、确认）
    if _TRIVIAL_KEYWORDS.match(text):
        return Intent(
            intent_type=IntentType.TRIVIAL,
            confidence=0.85,
            reasoning="短消息或问候/确认类关键词",
            suggested_action="respond_directly: 直接回复",
        )

    # 2. Implementation 检测（强信号）
    impl_matches = _IMPL_KEYWORDS.findall(text)
    if len(impl_matches) >= 1:
        # 实现类关键词 + 具体目标 = 高置信度
        has_target = bool(re.search(r"[\w]+功能|[\w]+模块|[\w]+接口|feature|endpoint|API|函数|类|class", text, re.IGNORECASE))
        confidence = 0.9 if has_target else 0.7
        return Intent(
            intent_type=IntentType.IMPLEMENTATION,
            confidence=confidence,
            reasoning=f"实现类关键词 ({len(impl_matches)} 个匹配)" + (" + 具体目标" if has_target else ""),
            suggested_action="pipeline: 创建 proposal → ENRICH → IMPLEMENT → VERIFY → DELIVER",
        )

    # 3. Exploration 检测
    explore_matches = _EXPLORE_KEYWORDS.findall(text)
    if explore_matches:
        return Intent(
            intent_type=IntentType.EXPLORATION,
            confidence=0.75,
            reasoning=f"探索类关键词 ({len(explore_matches)} 个匹配)",
            suggested_action="explore: 派发 explore agent 搜索代码库",
        )

    # 4. 混合信号 — 同时有实现和探索关键词
    if impl_matches and explore_matches:
        return Intent(
            intent_type=IntentType.AMBIGUOUS,
            confidence=0.5,
            reasoning="同时包含实现和探索类关键词，意图不明确",
            suggested_action="ask_user: 请明确是要实现功能还是了解现有代码",
        )

    # 5. 无法判断 → ambiguous
    return Intent(
        intent_type=IntentType.AMBIGUOUS,
        confidence=0.4,
        reasoning="未匹配到明确的意图关键词",
        suggested_action="ask_user: 请提供更多上下文",
    )


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
        IntentType.TRIVIAL: "respond_directly",
        IntentType.EXPLORATION: "dispatch_explore",
        IntentType.IMPLEMENTATION: "pipeline",
        IntentType.AMBIGUOUS: "ask_user",
    }
    return routing.get(intent.intent_type, "ask_user")
