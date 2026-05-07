import re

from ..agent.loop import AgentLoop
from ..agent.tools import register_tools
from ..transport import Transport, LocalTransport
from .utils import read_file, file_exists, dir_exists, list_files_recursive

IMPLEMENTER_SYSTEM = """你是 zsiga 的实现引擎。

你的任务：按照 tasks.md 逐个完成实现。所有 specs/design/tasks 和项目架构已在下方提供。

工作流：
1. 找到第一个未勾选的 task（- [ ]）
2. 写测试 — 基于 specs 中的 Scenario
3. 写实现 — 最小改动实现 task
4. 运行 pytest — 确保通过（只跑相关测试文件，不要全项目跑）
5. 在 tasks.md 中勾选: 将 - [ ] 替换为 - [x]
6. 提交: bash("git add -A && git commit -m 'feat: <task描述>'")
7. 回到步骤 1

规则：
- specs/design/tasks 已在下方提供，不需要再用 read_file 读取
- 只在需要理解具体代码细节时才用 read_file
- 按 tasks.md 顺序执行，不跳过
- 每个 task 独立提交
- 如果 pytest 失败，修复后重试（最多5次）
- 如果5次都失败，回滚（git checkout -- .）并报告
- 只改 task 要求的文件，不做额外重构
- 不要运行 ruff format 或 ruff check . — lint 验证由系统自动处理
- 只运行与当前 task 相关的测试文件，不要全项目 pytest"""


async def implement(agent: AgentLoop, change_dir: str, target_path: str,
                    transport: Transport = None, project_context: str = "", **kwargs):
    transport = transport or LocalTransport()
    specs = _read_all_specs(change_dir, transport)
    design = read_file(f"{change_dir}/design.md", transport) or ""
    tasks = read_file(f"{change_dir}/tasks.md", transport) or ""

    ctx_section = ""
    if project_context:
        ctx_section = f"\n## 项目代码上下文（已预读）\n{project_context}\n"

    user_prompt = f"""## Change: {change_dir}
## 目标项目: {target_path}
{ctx_section}
### specs:
{specs}

### design.md:
{design}

### tasks.md:
{tasks}

specs/design/tasks 已在上方提供。从第一个 - [ ] 开始实现，不需要再读取这些文件。"""

    return await agent.run(IMPLEMENTER_SYSTEM, user_prompt,
                          **kwargs)


def _read_all_specs(change_dir: str, transport: Transport = None) -> str:
    transport = transport or LocalTransport()
    specs_dir = f"{change_dir}/specs"
    if not dir_exists(specs_dir, transport):
        return ""
    files = list_files_recursive(specs_dir, "*.md", transport)
    parts = []
    for fpath in files:
        rel = fpath[len(specs_dir) + 1:]
        content = read_file(fpath, transport)
        if content is not None:
            parts.append(f"## {rel}\n{content}")
    return "\n\n".join(parts)
