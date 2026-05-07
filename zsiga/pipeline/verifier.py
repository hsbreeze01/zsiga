import re
from pathlib import Path

from ..agent.loop import AgentLoop
from ..agent.tools import register_tools
from .. import git_ops

VERIFIER_SYSTEM = """你是 zsiga 的验证引擎。

你的任务：验证实现是否匹配 OpenSpec specs。

检查三个维度：

1. COMPLETENESS（完整性）
   - 每个 ADDED Requirement 是否有对应代码实现
   - 每个 Scenario（Given/When/Then）是否被覆盖
   - 所有 tasks.md 中的 task 是否已勾选 - [x]

2. CORRECTNESS（正确性）
   - 实现是否真正满足 spec 中的行为描述
   - 错误状态是否匹配 spec 中的定义
   - 运行 pytest 确认测试通过

3. COHERENCE（一致性）
   - design.md 中的架构决策是否在代码中体现
   - 命名和模式是否与项目现有代码一致

输出格式（写入 verify.md）：
  Verdict: PASS 或 FAIL
  Completeness: ✓/✗ 详细说明
  Correctness: ✓/✗ 详细说明
  Coherence: ✓/✗ 详细说明
  Issues: (如果有)
    1. [CRITICAL/WARNING] 描述"""


async def verify(agent: AgentLoop, change_dir: str, target_path: str,
                pre_impl_sha: str):
    from .implementer import _read_all_specs

    specs = _read_all_specs(change_dir)
    design_path = Path(change_dir, "design.md")
    design = design_path.read_text() if design_path.exists() else ""
    tasks = Path(change_dir, "tasks.md").read_text()
    diff = git_ops.diff(target_path, pre_impl_sha)

    user_prompt = f"""## Change: {change_dir}

### specs:
{specs}

### design.md:
{design}

### tasks.md:
{tasks}

### 实际改动 (git diff):
{diff[:15000]}

验证实现是否匹配 specs。运行 pytest 确认。
将结果写入 {change_dir}/verify.md"""

    return await agent.run(VERIFIER_SYSTEM, user_prompt)


def read_verdict(change_dir: str) -> str:
    verify_file = Path(change_dir) / "verify.md"
    if not verify_file.exists():
        return "UNKNOWN"
    content = verify_file.read_text()
    match = re.search(r"Verdict:\s*(PASS|FAIL)", content)
    return match.group(1) if match else "UNKNOWN"
