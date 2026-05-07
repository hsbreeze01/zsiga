import re
from pathlib import Path

from ..agent.loop import AgentLoop
from ..agent.tools import register_tools
from .. import git_ops

VERIFIER_SYSTEM = """你是 zsiga 的验证引擎。严格按照以下步骤执行，不要做额外的文件探索。

步骤（严格按序）：
1. 运行测试确认通过
2. 运行 lint 确认通过
3. 对比 specs 和 git diff，判断完整性
4. 写入 verify.md

verify.md 格式：
```
Verdict: PASS 或 FAIL
Completeness: ✓/✗ 一句话
Correctness: ✓/✗ 一句话
Coherence: ✓/✗ 一句话
Issues: (如果有)
  1. [CRITICAL/WARNING] 描述
```

规则：
- 最多 10 轮工具调用
- 不要读取你已经知道的文件
- 测试通过 + lint 通过 = Correctness ✓ 的强信号"""


async def verify(agent: AgentLoop, change_dir: str, target_path: str,
                 pre_impl_sha: str,
                 max_turns: int = 12, timeout_seconds: int = 300):
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

    return await agent.run(VERIFIER_SYSTEM, user_prompt,
                          max_turns=max_turns, timeout_seconds=timeout_seconds)


def read_verdict(change_dir: str) -> str:
    verify_file = Path(change_dir) / "verify.md"
    if not verify_file.exists():
        return "UNKNOWN"
    content = verify_file.read_text()
    match = re.search(r"Verdict:\s*(PASS|FAIL)", content)
    return match.group(1) if match else "UNKNOWN"
