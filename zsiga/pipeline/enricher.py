import json
from pathlib import Path
from typing import Optional

from ..agent.loop import AgentLoop
from ..memory.learn import fetch_relevant_learnings
from ..transport import Transport, LocalTransport
from .utils import read_file, dir_exists, list_files_recursive
from .spec_pytest_check import validate_testable_artifacts

ENRICHER_SYSTEM = """你是 zsiga 的技术规格设计师。clarify.md（需求契约）已由 CLARIFY 阶段生成。

你的任务：基于 clarify.md 中的需求拆解和边界定义，生成 OpenSpec delta specs。

必须遵循 OpenSpec 的 artifact 格式：

specs/ — Delta specs，描述行为变更
- 用 ## ADDED Requirements / ## MODIFIED Requirements / ## REMOVED Requirements 区分
- 每个 ### Requirement 必须有 #### Scenario（Given/When/Then 格式）
- 用 SHALL/MUST/SHOULD 表达约束强度
- spec 描述行为（what），不是实现（how）

## Testable Scenarios（机械可验场景，新增）

对每个 Scenario 决定它是否机械可验：
- **接口契约**（输入 → 输出确定）→ testable: true
- **错误处理**（raises 某异常）→ testable: true
- **文件存在/内容**（path.exists / read_text 比较）→ testable: true
- **状态不变量**（git status / 数据库行 / 字典 key）→ testable: true
- **性能 / 风格 / 主观体验** → testable: false

格式约定（**必须严格遵守**）：

```
#### Scenario: <name>

- **testable**: true        ← 仅在机械可验时为 true，否则不写或写 false
- **target**: <file>.py::<symbol>   ← testable=true 时必填，例如 src/email.py::validate_email 或 src/foo.py::Bar.baz
- **Given** ...
- **When** ...
- **Then** ...
```

当 Scenario 标记 testable=true 时，**额外**用 write_file 写一个 pytest 测试文件：

- 路径: <target_path>/tests/test_spec_<change_id_slug>__<spec_filename_slug>.py
  - change_id_slug = 当前 change 目录名，把所有 - 替换为 _
  - spec_filename_slug = spec 文件名（去掉 .md），把所有 - 替换为 _
  - 例: change_dir 是 .../changes/dashboard-foo/，spec 是 phase-progress.md
        → tests/test_spec_dashboard_foo__phase_progress.py
- 文件中每个 testable scenario 一个 def test_<scenario_slug>(...): 函数
- 函数体必须含**真实断言**，禁止 `assert True` / `pass` / `# TODO` 占位
- 接口契约: from <module> import <func>; assert <func>(<input>) == <expected>
- 错误处理: import pytest; with pytest.raises(<Exc>): <func>(<input>)
- 文件存在: from pathlib import Path; assert Path("<expected>").exists()
- 状态不变量: 用 conftest_zsiga.py 提供的 tmp_repo / mock_transport fixture

如果你写不出真断言（例如行为太抽象），就不要标 testable: true，让它走 LLM judge 兜底。

规则：
- 项目代码和数据库结构已提供在下方，不需要再用工具读文件
- specs 描述行为，不描述实现细节
- 直接开始写 specs，不要先做探索
- 不要生成 clarify.md（已由前置阶段生成）
- testable 字段缺省为 false，老 spec 不需要改"""


async def enrich(agent: AgentLoop, change_dir: str, target_path: str,
                 transport: Transport = None, project_context: str = "", **kwargs):
    transport = transport or LocalTransport()
    proposal = read_file(f"{change_dir}/proposal.md", transport) or ""

    # Optional parallel explore pool (REQ-PP-04)
    supplementary_context = kwargs.pop("supplementary_context", "")

    ctx_section = ""
    if project_context:
        ctx_section = f"\n## 项目代码上下文（已预读，不需要再用工具读取）\n{project_context}\n"

    supp_section = ""
    if supplementary_context:
        supp_section = (
            "\n## 并行探索结果（explore agents 已预先搜索）\n"
            f"{supplementary_context}\n"
        )

    # Build token estimation section if provided
    token_estimation = kwargs.pop("token_estimation", "")
    token_section = ""
    if token_estimation:
        token_section = f"\n## Token 预估参考数据\n{token_estimation}\n"

    # Read clarify.md produced by CLARIFY phase
    clarify_content = read_file(f"{change_dir}/clarify.md", transport) or ""
    clarify_section = ""
    if clarify_content:
        clarify_section = (
            f"\n## 需求契约 clarify.md（已由 CLARIFY 阶段生成，遵循其边界和约束）:\n"
            f"{clarify_content}\n"
        )

    user_prompt = f"""## Change 目录: {change_dir}
## 目标项目: {target_path}
{ctx_section}{supp_section}{token_section}{clarify_section}
## 已有 proposal.md:
{proposal}

基于 clarify.md 中的需求拆解和边界，直接开始写 specs：
1. 用 write_file 在 {change_dir}/specs/ 下创建 delta spec 文件（注意：必须在 specs/ 子目录里，不是 specs.md）
2. 不要重新生成 clarify.md（已存在）

项目架构已在上方提供，直接开始写，不要用工具探索项目。"""

    # Build system prompt with learnings injection
    change_name = Path(change_dir).name
    system_prompt = ENRICHER_SYSTEM
    learnings_text = fetch_relevant_learnings(change_name, max_count=3)
    if learnings_text:
        system_prompt += f"\n\n## Relevant Past Experience\n{learnings_text}"

    result = await agent.run(system_prompt, user_prompt, **kwargs)

    # Validate specs/ directory
    specs_dir = f"{change_dir}/specs"
    if not dir_exists(specs_dir, transport) or not list_files_recursive(specs_dir, "*.md", transport):
        print("  ⚠️ specs/ directory empty or missing, retrying...")
        transport.run_shell(f"mkdir -p \'{specs_dir}\'", timeout=5)
        retry_prompt = user_prompt + f"\n\n注意：上一次你没有在 specs/ 子目录下创建文件。必须用 write_file 创建 {change_dir}/specs/<name>.md，不要创建 specs.md。"
        result = await agent.run(system_prompt, retry_prompt, **kwargs)

    # clarify.md validation is handled by CLARIFY phase

    # P1-5 Phase 2: validate companion pytest artifacts for testable
    # scenarios. Demotes scenarios whose test file is missing or fails
    # py_compile, ensures conftest_zsiga.py exists in <target>/tests/.
    try:
        report = validate_testable_artifacts(change_dir, target_path, transport)
        print(f"  {report.summary_line()}", flush=True)
    except Exception as exc:  # pragma: no cover - defensive
        print(f"  ⚠ spec→pytest validation error: {exc}", flush=True)

    return result


def derive_explore_tasks(proposal_text: str) -> list[str]:
    """Derive 2-5 focused explore instructions from proposal text."""
    lines = [line.strip() for line in proposal_text.splitlines() if line.strip()]
    title = lines[0] if lines else ""
    keywords = title[:30] if len(title) >= 6 else title or "项目"

    templates = [
        "搜索项目中与「{kw}」相关的现有代码和模块",
        "查找项目的目录结构、入口文件、配置文件模式",
        "搜索项目中与「{kw}」相关的测试文件和测试模式",
        "查找项目的依赖管理和技术栈（requirements.txt, pyproject.toml, package.json 等）",
        "搜索项目中与「{kw}」相关的数据库模型和数据结构",
    ]
    return [t.format(kw=keywords) for t in templates][:5]


def estimate_token_budget(change_name: str = "",
                          db_path: Optional[Path] = None) -> dict:
    """Estimate token budget based on historical IMPLEMENT phase records."""
    from ..metrics.db import _get_conn
    try:
        conn = _get_conn(db_path)
        try:
            rows = conn.execute(
                "SELECT phases_json FROM changes ORDER BY id DESC LIMIT 20"
            ).fetchall()
        finally:
            conn.close()
    except Exception:
        return {"source": "none"}

    prompt_tokens = []
    completion_tokens = []
    for row in rows:
        phases = json.loads(row["phases_json"]) if row["phases_json"] else []
        for p in phases:
            if p.get("phase") in ("implement", "enrich"):
                pt = p.get("prompt_tokens", 0)
                ct = p.get("completion_tokens", 0)
                if pt > 0 or ct > 0:
                    prompt_tokens.append(pt)
                    completion_tokens.append(ct)

    if not prompt_tokens:
        return {"source": "none"}

    return {
        "estimated_prompt": int(sum(prompt_tokens) / len(prompt_tokens)),
        "estimated_completion": int(sum(completion_tokens) / len(completion_tokens)),
        "source": "historical",
    }
