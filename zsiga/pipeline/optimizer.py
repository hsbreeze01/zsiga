"""OPTIMIZE phase: post-verify norm alignment.

Optional phase after VERIFY: pattern consistency, redundancy removal,
readability, and performance review.  Only touches files changed in the
current implementation.
"""

import logging

from ..agent.loop import AgentLoop, RunResult
from ..pipeline.utils import read_file, _get_changed_files
from .. import git_ops
from ..transport import Transport, LocalTransport

log = logging.getLogger(__name__)

OPTIMIZE_SYSTEM = """你是 zsiga 的代码优化引擎。你的任务是对本次实现的代码做规范对齐。

你只会收到本次变更涉及的文件列表和 git diff。只修改这些文件。

检查维度（按优先级）：
1. **模式一致性**：项目如果有 BaseModel/BaseDB/BaseService 等基类，新代码应使用
2. **冗余剔除**：删除死代码、未使用的 import、重复逻辑
3. **可读性**：函数超过 50 行应拆分、命名应与项目风格一致
4. **性能**：N+1 查询、不必要的全量加载、明显可优化的循环

规则：
- 只修改本次变更涉及的文件（上方列出的）
- 不要添加新功能、新路由、新端点
- 不要大规模重构，只做增量改进
- 每次修改后运行 ruff check 确认无 lint 错误
- 如果没有明显可优化的地方，回复 NO_OPTIMIZATION_NEEDED"""


async def optimize(
    agent: AgentLoop,
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport = None,
    max_turns: int = 5,
    timeout_seconds: int = 180,
) -> RunResult:
    """OPTIMIZE phase: norm alignment on changed files.

    Returns RunResult.  If the agent responds NO_OPTIMIZATION_NEEDED,
    the caller treats it as a no-op pass.
    """
    transport = transport or LocalTransport()

    # Read clarify.md for constraints
    clarify_content = read_file(f"{change_dir}/clarify.md", transport) or ""
    constraints_section = ""
    if clarify_content:
        # Extract the 约束 section
        import re
        constraint_match = re.search(
            r"(## 约束.*?)(?=\n## |\Z)", clarify_content, re.DOTALL
        )
        if constraint_match:
            constraints_section = f"\n### 需求约束（来自 clarify.md）\n{constraint_match.group(1)}\n"

    # Get changed files and diff
    changed_files = _get_changed_files(target_path, pre_impl_sha, transport)
    diff = git_ops.diff(target_path, pre_impl_sha, transport=transport)

    changed_info = (
        "\n本次变更的文件（只修这些）:\n"
        + ("\n".join(f"  - {f}" for f in changed_files) if changed_files else "  无")
    )

    user_prompt = f"""## 项目: {target_path}
{changed_info}
{constraints_section}

### git diff:
{diff[:15000]}

基于以上信息，对本次变更的代码做规范对齐优化。如果没有明显可优化的地方，回复 NO_OPTIMIZATION_NEEDED。"""

    result = await agent.run(
        OPTIMIZE_SYSTEM, user_prompt,
        max_turns=max_turns, timeout_seconds=timeout_seconds,
    )

    return result
