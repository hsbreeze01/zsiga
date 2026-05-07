import re
from pathlib import Path

from ..agent.loop import AgentLoop
from ..agent.tools import register_tools

IMPLEMENTER_SYSTEM = """你是 zsiga 的实现引擎。

你的任务：按照 tasks.md 逐个完成实现。

工作流：
1. 读取 tasks.md — 找到第一个未勾选的 task（- [ ]）
2. 读取相关 specs/ — 理解这个 task 对应的行为要求
3. 读取 design.md — 理解技术方案
4. 读取相关代码 — 理解现有模式
5. 写测试 — 基于 specs 中的 Scenario 写测试用例
6. 写实现 — 最小改动实现 task
7. 运行 pytest — 确保通过
8. 运行 ruff check . — 确保 lint 通过
9. 在 tasks.md 中勾选这个 task: 将 - [ ] 替换为 - [x]
10. 提交: bash("git add -A && git commit -m 'feat: <task描述>'")
11. 回到步骤 1 — 处理下一个 task

规则：
- 按 tasks.md 顺序执行，不跳过
- 每个 task 独立提交
- 如果 pytest 失败，修复后重试（最多5次）
- 如果5次都失败，回滚（git checkout -- .）并报告
- 只改 task 要求的文件，不做额外重构"""


async def implement(agent: AgentLoop, change_dir: str, target_path: str):
    proposal = Path(change_dir, "proposal.md").read_text()
    specs = _read_all_specs(change_dir)
    design_path = Path(change_dir, "design.md")
    design = design_path.read_text() if design_path.exists() else ""
    tasks = Path(change_dir, "tasks.md").read_text()

    user_prompt = f"""## Change: {change_dir}
## 目标项目: {target_path}

### proposal.md:
{proposal}

### specs:
{specs}

### design.md:
{design}

### tasks.md:
{tasks}

从第一个 - [ ] 开始实现。完成所有 task 后停止。"""

    return await agent.run(IMPLEMENTER_SYSTEM, user_prompt)


def _read_all_specs(change_dir: str) -> str:
    specs_dir = Path(change_dir) / "specs"
    if not specs_dir.exists():
        return ""
    parts = []
    for f in sorted(specs_dir.rglob("*.md")):
        parts.append(f"## {f.relative_to(specs_dir)}\n{f.read_text()}")
    return "\n\n".join(parts)
