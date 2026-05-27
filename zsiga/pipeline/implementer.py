

import os
import re
from ..agent.loop import AgentLoop
from ..memory.pattern_miner import mine_patterns
from ..transport import Transport, LocalTransport
from .utils import read_file, dir_exists, list_files_recursive

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
- 如果 tasks.md 中包含不属于当前项目的任务（如引用了其他项目的路径或文件），跳过这些任务并标记 - [x]，只处理当前 target_path 下的文件

## Vertical Slice Rules

严格按垂直切片执行，每个 cycle 只处理一个 task：

1. **单 task 执行**：每次只取 tasks.md 中第一个未勾选的 task，读取相关代码（≤ 3 次文件读取），编辑完成后立即验证
2. **文件限制**：每个 task 最多编辑 2 个文件。如果确实需要编辑 3 个文件（如 model + service + route），必须在代码注释中说明原因，且每编辑 2 个文件就运行一次 lint
3. **增量验证**：每个 task 完成后立即对修改的文件运行 `ruff check`（只检查改动的文件），然后运行相关测试文件（不要全项目 pytest）
4. **逐步推进**：check-mark 当前 task 为 `- [x]` 后，再取下一个 task。不要并行处理多个 task
5. **禁止批量修改**：不要尝试一次性修改 3 个以上文件然后统一测试。每个 task 独立验证，失败立即修复

## Lint Prevention Rules

以下 lint 违规模式 MUST 在代码生成时主动避免，不要依赖事后检查：

### E701 — 单行多语句（冒号后不能跟语句体）

❌ 错误：
```python
if not x: x = {}
if flag: return result
```

✅ 正确：
```python
if not x:
    x = {}
if flag:
    return result
```

### E702 — 分号分隔多语句

❌ 错误：
```python
from dotenv import load_dotenv; load_dotenv()
x = 1; y = 2
```

✅ 正确：
```python
from dotenv import load_dotenv
load_dotenv()
x = 1
y = 2
```

### E401 — 单行多 import

❌ 错误：
```python
import json, requests, datetime
```

✅ 正确：
```python
import json
import requests
import datetime
```

### E741 — 歧义单字母变量名

❌ 错误：
```python
l = [1, 2, 3]
O = MyClass()
I = 42
```

✅ 正确：
```python
items = [1, 2, 3]
obj = MyClass()
idx = 42
```

### 通用规则
- 每个文件末尾必须有换行符
- 不要有行尾空格"""


async def implement(agent: AgentLoop, change_dir: str, target_path: str,
                    transport: Transport = None, project_context: str = "",
                    venv_python: str = None, **kwargs):
    transport = transport or LocalTransport()
    specs = _read_all_specs(change_dir, transport)
    design = read_file(f"{change_dir}/design.md", transport) or ""
    tasks = read_file(f"{change_dir}/tasks.md", transport) or ""

    kw_section = _build_spec_keywords_section(change_dir, transport)

    system_prompt = IMPLEMENTER_SYSTEM
    if venv_python:
        system_prompt += _venv_prompt_section(venv_python)

    ctx_section = ""
    if project_context:
        ctx_section = f"\n## 项目代码上下文（已预读）\n{project_context}\n"

    pattern_warnings = _build_pattern_warnings()
    must_section = _build_must_modify_section(specs, design, tasks, target_path=target_path)

    user_prompt = f"""## Change: {change_dir}
## 目标项目: {target_path}
{ctx_section}{must_section}{kw_section}
### specs:
{specs}

### design.md:
{design}

### tasks.md:
{tasks}

specs/design/tasks 已在上方提供。从第一个 - [ ] 开始实现，不需要再读取这些文件。{pattern_warnings}"""

    return await agent.run(system_prompt, user_prompt,
                          **kwargs)


def _build_spec_keywords_section(change_dir: str, transport: Transport) -> str:
    import json as _json

    kw_path = os.path.join(change_dir, "spec_keywords.json")
    raw = read_file(kw_path, transport)
    if not raw:
        return ""
    try:
        data = _json.loads(raw)
    except (ValueError, TypeError):
        return ""
    keywords = data.get("keywords", [])
    if not keywords:
        return ""
    items = ", ".join(f"`{k}`" for k in keywords[:15])
    return (
        f"\n## Spec Alignment Keywords (MUST appear in code/diff)\n"
        f"{items}\n"
        f"确保以上 spec 关键词在代码变更中有所体现，以提高 "
        f"spec_scenario_coverage 通过率。\n"
    )


def _build_pattern_warnings() -> str:
    """Build a markdown warning section from high-severity pipeline.fail.* patterns."""
    patterns = mine_patterns()
    high_fail = [
        p for p in patterns
        if p.severity == "high" and p.key.startswith("pipeline.fail.")
    ]
    if not high_fail:
        return ""
    top = high_fail[:3]
    lines = ["\n\n## Known Failure Patterns (AVOID)", ""]
    for p in top:
        lines.append(f"- **{p.key}** (occurred {p.count} times)")
        for tw in p.recent_takeaways[:2]:
            lines.append(f"  - {tw}")
    return "\n".join(lines)


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


_FILE_PATH_RE = re.compile(
    r"(?<![\w/-])"
    r"([A-Za-z_][\w./-]*?/[\w./-]+?\."
    r"(?:py|pyi|js|jsx|ts|tsx|html|css|md|markdown|"
    r"yaml|yml|json|toml|ini|cfg|sh|sql|rs|go|java|kt|swift|vue|c|cpp|h|hpp))"
    r"(?![\w/])"
)

# File paths that look real but are obvious placeholders / templates / examples.
_FILE_PATH_DENY_SUBSTR = (
    "path/to/",
    "your/",
    "<",
    ">",
    "...",
    "example.com",
    "/tmp/",
    "site-packages/",
    "node_modules/",
    "dist/",
    "build/",
    "__pycache__/",
)


def _extract_must_modify_files(
    *texts: str, target_path: str | None = None,
) -> list[str]:
    """Return ordered, deduped list of likely 'must-modify' file paths.

    Recognises paths that:
    - contain at least one '/' (so we don't match bare names like ``foo.py``);
    - end in a known source/asset extension;
    - are not obvious placeholders (``path/to/foo.py`` etc.).

    When *target_path* is provided, an additional disk-aware filter is
    applied: a path survives only if it currently exists under
    *target_path* OR it matches a sensible new-file pattern
    (``tests/test_*.py``).  This drops illustrative scenario paths like
    ``src/foo.py`` that specs commonly use as examples.
    """
    import os as _os

    seen: set[str] = set()
    ordered: list[str] = []
    for text in texts:
        if not text:
            continue
        for m in _FILE_PATH_RE.finditer(text):
            path = m.group(1).rstrip(".,;:)")
            lowered = path.lower()
            if any(bad in lowered for bad in _FILE_PATH_DENY_SUBSTR):
                continue
            if path in seen:
                continue
            seen.add(path)
            ordered.append(path)

    if target_path is None:
        return ordered

    # Disk-aware sanity filter.
    def _kept(p: str) -> bool:
        if _os.path.exists(_os.path.join(target_path, p)):
            return True
        # Allow new test files (very common spec pattern).
        base = _os.path.basename(p)
        if (
            p.startswith("tests/")
            and base.startswith("test_")
            and base.endswith(".py")
        ):
            return True
        return False

    return [p for p in ordered if _kept(p)]


def _build_must_modify_section(
    specs: str, design: str, tasks: str, target_path: str | None = None,
) -> str:
    """Render the MUST-MODIFY block injected into the IMPLEMENT user prompt."""
    files = _extract_must_modify_files(
        specs, design, tasks, target_path=target_path,
    )
    if not files:
        return ""
    bullet_list = "\n".join(f"- `{p}`" for p in files)
    return (
        "\n## MUST-MODIFY Files (extracted from specs/design/tasks)\n\n"
        "The files below are referenced by the specs. You **MUST** open and "
        "edit (or create) every one of them as part of this change. After "
        "IMPLEMENT, the diff will be checked: any file in this list that the "
        "diff does not touch counts as a spec violation in REVIEW/VERIFY.\n\n"
        f"{bullet_list}\n\n"
        "If a path looks wrong (typo, moved/renamed file), keep the closest "
        "matching real file and call out the discrepancy in your final "
        "summary, but still produce a diff that touches the corrected file.\n"
    )


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
