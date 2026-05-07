import re

from ..agent.loop import AgentLoop
from ..agent.tools import register_tools
from ..transport import Transport, LocalTransport
from .. import git_ops
from .utils import read_file, file_exists

VERIFIER_SYSTEM = """你是 zsiga 的验证引擎。对比 specs 和实际代码改动，判断实现质量。

测试和 lint 结果已预跑，在下方提供。你只需要：
1. 对比 specs 和 git diff，判断完整性和正确性
2. 写入 verify.md

不要重复运行测试或 lint，结果已在下方。

verify.md 格式：
```
Verdict: PASS 或 FAIL
Completeness: ✓/✗ 一句话
Correctness: ✓/✗ 一句话
Coherence: ✓/✗ 一句话
Issues: (如果有)
  1. [CRITICAL/WARNING] 描述
```"""


async def verify(agent: AgentLoop, change_dir: str, target_path: str,
                 pre_impl_sha: str,
                 transport: Transport = None,
                 mech_results: dict = None, **kwargs):
    from .implementer import _read_all_specs

    specs = _read_all_specs(change_dir, transport)
    design = read_file(f"{change_dir}/design.md", transport) or ""
    tasks = read_file(f"{change_dir}/tasks.md", transport) or ""
    diff = git_ops.diff(target_path, pre_impl_sha)

    mech_section = ""
    if mech_results:
        test_status = "✅ PASSED" if mech_results["test"]["passed"] else "❌ FAILED"
        lint_status = "✅ PASSED" if mech_results["lint"]["passed"] else "❌ FAILED"
        mech_section = f"""
## 预跑测试结果（不要重复运行）
- Tests: {test_status}
  ```
  {mech_results['test']['output'][-1500:]}
  ```
- Lint: {lint_status}
  ```
  {mech_results['lint']['output'][-1500:]}
  ```
"""

    user_prompt = f"""## Change: {change_dir}

### specs:
{specs}

### design.md:
{design}

### tasks.md:
{tasks}

### 实际改动 (git diff):
{diff[:15000]}
{mech_section}
基于以上信息判断实现质量，将结果写入 {change_dir}/verify.md。不要运行测试或 lint。"""

    return await agent.run(VERIFIER_SYSTEM, user_prompt,
                          **kwargs)


def read_verdict(change_dir: str, transport: Transport = None) -> str:
    content = read_file(f"{change_dir}/verify.md", transport)
    if content is None:
        return "UNKNOWN"
    match = re.search(r"Verdict:\s*(PASS|FAIL)", content)
    return match.group(1) if match else "UNKNOWN"
