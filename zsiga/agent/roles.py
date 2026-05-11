"""专业子代理角色定义：explore（只读搜索）、implement（写代码）、review（验证）。"""

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    EXPLORE = "explore"
    IMPLEMENT = "implement"
    REVIEW = "review"


@dataclass
class RoleConfig:
    name: str
    max_turns: int
    read_only: bool
    allowed_tools: list[str]
    system_prompt: str


_EXPLORE_PROMPT = """你是 zsiga 的探索子代理。你的唯一职责是快速搜索和分析代码，回答问题。

规则：
- 只能使用只读工具（bash、read_file、search、list_files、ast_search）
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

_REVIEW_PROMPT = """你是 zsiga 的验证子代理。你的职责是审查代码变更，判断是否满足规格。

规则：
- 只能使用只读工具
- 逐条检查规格要求是否被代码覆盖
- 运行测试查看结果
- 输出格式：
  ## Verdict: PASS 或 FAIL
  ## Evidence:
  - 每条规格对应的代码证据
  ## Issues (如有):
  - 发现的问题列表
- 最多 8 轮工具调用"""

_ROLES: dict[Role, RoleConfig] = {
    Role.EXPLORE: RoleConfig(
        name="explore",
        max_turns=5,
        read_only=True,
        allowed_tools=["bash", "read_file", "search", "list_files", "ast_search"],
        system_prompt=_EXPLORE_PROMPT,
    ),
    Role.IMPLEMENT: RoleConfig(
        name="implement",
        max_turns=15,
        read_only=False,
        allowed_tools=[
            "bash", "read_file", "write_file", "edit_file",
            "search", "list_files", "ast_search", "ast_replace",
        ],
        system_prompt=_IMPLEMENT_PROMPT,
    ),
    Role.REVIEW: RoleConfig(
        name="review",
        max_turns=8,
        read_only=True,
        allowed_tools=["bash", "read_file", "search", "list_files", "ast_search"],
        system_prompt=_REVIEW_PROMPT,
    ),
}


def get_role_config(role: Role) -> RoleConfig:
    return _ROLES[role]


def get_role_system_prompt(role: Role) -> str:
    return _ROLES[role].system_prompt


def get_all_roles() -> dict[Role, RoleConfig]:
    return dict(_ROLES)
