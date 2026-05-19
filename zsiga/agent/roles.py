"""专业子代理角色定义：explore（只读搜索）、implement（写代码）、review（验证）。"""

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    EXPLORE = "explore"
    IMPLEMENT = "implement"
    REVIEW = "review"
    DIAGNOSER = "diagnoser"


@dataclass
class RoleConfig:
    name: str
    max_turns: int
    read_only: bool
    allowed_tools: list[str]
    system_prompt: str


_EXPLORE_PROMPT = """你是 zsiga 的探索子代理。你的唯一职责是快速搜索和分析代码，回答问题。

规则：
- 只能使用只读工具（bash、read_file、search、list_files、ast_search、goto_definition、find_references、diagnostics）
- 绝对不允许写文件或修改任何代码
- 最多 5 轮工具调用，必须给出简洁明确的结论
- 回答格式：先给结论，再列证据"""

_IMPLEMENT_PROMPT = """你是 zsiga 的实现子代理。你的职责是按规格说明编写代码和测试。

规则：
- 先写测试，再写实现
- 每次只改 1-3 个文件
- 写完后运行 pytest + ruff 验证
- 如果验证失败，修复后重新运行
- 最多 15 轮工具调用"""

_REVIEW_PROMPT = """你是 zsiga 的代码审查引擎。你的职责是审查实现变更，判断是否满足规格要求。

规则：
- 只能使用只读工具（bash、read_file、search、list_files、ast_search、goto_definition、find_references、diagnostics）
- 逐条检查每条 spec 要求是否在代码 diff 中被覆盖
- 检查常见代码质量问题（死代码、缺失错误处理、命名）
- 最多 8 轮工具调用

输出 review.md 格式（严格遵守）：

Verdict: CLEAN 或 ISSUES_FOUND

Issues:（仅在 Verdict 为 ISSUES_FOUND 时列出）
1. [CRITICAL] 描述 + 代码证据
2. [SUGGESTION] 描述 + 代码证据

如果所有 spec 要求都被覆盖且无代码质量问题，Verdict 为 CLEAN。
如果发现任何问题，Verdict 为 ISSUES_FOUND，并按严重程度分类为 CRITICAL 或 SUGGESTION。"""

_DIAGNOSER_PROMPT = """你是 zsiga 的诊断子代理。你的职责是分析验证失败，生成根因假设并探测验证。

规则：
- 只能使用只读工具（bash、read_file、search、list_files、ast_search、goto_definition、find_references、diagnostics）
- 绝对不允许写文件或修改任何代码
- 基于错误输出生成 3-5 个假设，按置信度排序
- 对每个假设运行只读探测（读文件、搜索、诊断）
- 输出格式：
  ## Root Cause: 确认的根因描述
  ## Fix Plan: 修复建议
  ## Affected Files: 受影响的文件列表
  ## Hypotheses: 每个假设及其探测结果
- 最多 6 轮工具调用"""

_ROLES: dict[Role, RoleConfig] = {
    Role.EXPLORE: RoleConfig(
        name="explore",
        max_turns=5,
        read_only=True,
        allowed_tools=["bash", "read_file", "search", "list_files", "ast_search", "goto_definition", "find_references", "diagnostics"],
        system_prompt=_EXPLORE_PROMPT,
    ),
    Role.IMPLEMENT: RoleConfig(
        name="implement",
        max_turns=15,
        read_only=False,
        allowed_tools=[
            "bash", "read_file", "write_file", "edit_file",
            "search", "list_files", "ast_search", "ast_replace",
            "goto_definition", "find_references", "diagnostics",
        ],
        system_prompt=_IMPLEMENT_PROMPT,
    ),
    Role.REVIEW: RoleConfig(
        name="review",
        max_turns=8,
        read_only=True,
        allowed_tools=["bash", "read_file", "search", "list_files", "ast_search", "goto_definition", "find_references", "diagnostics"],
        system_prompt=_REVIEW_PROMPT,
    ),
    Role.DIAGNOSER: RoleConfig(
        name="diagnose",
        max_turns=6,
        read_only=True,
        allowed_tools=["bash", "read_file", "search", "list_files", "ast_search", "goto_definition", "find_references", "diagnostics"],
        system_prompt=_DIAGNOSER_PROMPT,
    ),
}


def get_role_config(role: Role) -> RoleConfig:
    return _ROLES[role]


def get_role_system_prompt(role: Role) -> str:
    return _ROLES[role].system_prompt


def get_all_roles() -> dict[Role, RoleConfig]:
    return dict(_ROLES)
