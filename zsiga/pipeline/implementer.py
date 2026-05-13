import re

from ..agent.loop import AgentLoop
from ..agent.tools import register_tools
from ..transport import Transport, LocalTransport
from .utils import read_file, file_exists, dir_exists, list_files_recursive

IMPLEMENTER_SYSTEM = """你是 zsiga 的实现引擎。

你的任务：按照 tasks.md 逐个完成实现。所有 specs/design/tasks 和项目架构已在下方提供。

工作流：
1. 找到第一个未勾选的 task（- [ ]）
2. 读 specs → 理解行为要求
3. 读项目相关代码 → 学习模式
4. 写测试 — 基于 specs 中的 Scenario
5. 写实现 — 最小改动实现 task
6. 运行 pytest — 确保通过（只跑相关测试文件，不要全项目跑）
7. 在 tasks.md 中勾选: 将 - [ ] 替换为 - [x]
8. 回到步骤 1

## 提交策略（关键）

**不要每个 task 单独提交。按模块批量提交：**

- 同一个 tasks.md 分组内的 task（如 1.1, 1.2, 1.3 属于组 1）全部完成后一起提交
- 提交时机：当前组所有 task 都勾选为 - [x] 后
- 提交命令：`git add -A && git commit -m 'feat: <组描述>'`
- 如果一个组只有 1 个 task，也正常提交

**节省轮次的技巧：**
- 写完多个文件的修改后，一次性提交，不要写一个文件就提交一次
- 读文件时优先用 search 工具定位，不要全文读取大文件
- 勾选多个 task 时一次 edit_file 替换所有，不要逐个替换

规则：
- specs/design/tasks 已在下方提供，不需要再用 read_file 读取
- 只在需要理解具体代码细节时才用 read_file
- 按 tasks.md 顺序执行，不跳过
- 如果 pytest 失败，修复后重试（最多5次）
- 如果5次都失败，回滚（git checkout -- .）并报告
- 只改 task 要求的文件，不做额外重构
- 不要运行 ruff format 或 ruff check . — lint 验证由系统自动处理
- 只运行与当前 task 相关的测试文件，不要全项目 pytest
- 如果 task 标记为 `scope: frontend`，跳过该 task 并标记 - [x]（前端由人工完成）
- 如果 tasks.md 中包含不属于当前项目的任务（如引用了其他项目的路径或文件），跳过这些任务并标记 - [x]，只处理当前 target_path 下的文件"""


async def implement(agent: AgentLoop, change_dir: str, target_path: str,
                    transport: Transport = None, project_context: str = "",
                    venv_python: str = None, **kwargs):
    transport = transport or LocalTransport()
    specs = _read_all_specs(change_dir, transport)
    design = read_file(f"{change_dir}/design.md", transport) or ""
    tasks = read_file(f"{change_dir}/tasks.md", transport) or ""

    system_prompt = IMPLEMENTER_SYSTEM
    if venv_python:
        system_prompt += _venv_prompt_section(venv_python)

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

    return await agent.run(system_prompt, user_prompt,
                          **kwargs)


def _venv_prompt_section(venv_python: str) -> str:
    return f"""

## venv 配置（必须遵守）

项目使用 venv，所有命令 MUST 使用以下路径：
- Python: {venv_python}
- pip: {venv_python} -m pip
- pytest: {venv_python} -m pytest

规则：
- 绝对不要使用 python、python3、pip、pip3 — 必须使用上方完整路径
- 不要 pip install 项目已有依赖（venv 已包含所有依赖）
- 只有在 import 失败且确认 venv 中确实缺少该包时才安装"""


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
