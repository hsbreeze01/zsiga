import json
from pathlib import Path
from typing import Optional

from ..agent.loop import AgentLoop
from ..transport import Transport, LocalTransport
from .utils import read_file, dir_exists, list_files_recursive

CLARIFIER_SYSTEM = """你是 zsiga，一个基于 OpenSpec 的自动开发智能体。

你的任务：根据 proposal.md 和已提供的项目上下文，直接编写 OpenSpec artifacts。

必须遵循 OpenSpec 的 artifact 格式：

1. specs/ — Delta specs，描述行为变更
   - 用 ## ADDED Requirements / ## MODIFIED Requirements / ## REMOVED Requirements 区分
   - 每个 ### Requirement 必须有 #### Scenario（Given/When/Then 格式）
   - 用 SHALL/MUST/SHOULD 表达约束强度
   - spec 描述行为（what），不是实现（how）

2. clarify.md — 需求工程合同（替代 design.md + tasks.md）
   必须包含以下四个顶级 ## 节（按顺序）：

   ## 需求拆解
   ### 原始需求
   [从 proposal.md 提取的核心需求描述]
   ### 拆解后的子任务
   - [ ] 1. <description> (预估复杂度：低/中/高, 预估 token：~NNNN / 无历史参考)
   - [ ] 2. ...

   ## 边界
   ### IN scope
   - <item 1>
   ### OUT of scope
   - <item 1>
   ### 依赖的外部条件
   - <item 1>

   ## 目标
   ### 成功标准
   1. <criterion 1>
   ### 验收方式
   - <method 1>

   ## 约束
   ### 不能修改的文件
   - <file 1>
   ### 项目部署分支
   <branch_name>
   ### 已知风险
   - <risk 1>
   ### 预估 token 消耗
   - prompt: ~NNNN
   - completion: ~NNNN
   - 数据来源: historical / 无历史参考

规则：
- 项目代码和数据库结构已经提供在下方，不需要再用工具读文件或查询数据库
- specs 描述行为，不描述实现细节
- clarify.md 中的子任务必须可独立验证，每个子任务有明确的文件范围
- 直接开始写 artifacts，不要先做探索

## 任务粒度规则（关键）

任务必须按**功能模块**分组，不是按单个函数或文件分组：

### 后端任务（Python/路由/逻辑）
- 一个 - [ ] 对应一个完整的功能模块（如"添加技术指标计算层"包含所有calc函数）
- 每个 task 预估消耗 ≤ 3 轮（读1次+写1次+验证1次）
- 每组最多 4-6 个 task

### 前端任务（HTML/CSS/JS/模板）
- 如果项目包含前端模板（如 templates/index.html），在 clarify.md 中明确标注"前端任务需要人工完成"
- 前端 UI 渲染任务（图表、组件、样式）标记为 `scope: frontend` — zsiga 不执行这些
- 后端数据准备任务（API 路由、数据函数）正常生成
- 每个 - [ ] 应该是"一个页面区域"或"一个交互功能"，不是"一个函数"

### 反模式（不要这样做）
- ❌ `- [ ] 实现 calcMA 函数` — 太细，一个3行函数不值得一个任务
- ❌ `- [ ] 添加 MA 图表渲染` + `- [ ] 添加 MACD 图表渲染` — 应合并为一个"技术分析图表"
- ✅ `- [ ] 添加技术指标计算层（calcMA/calcEMA/calcMACD/calcKDJ/calcBOLL/calcRSI）`
- ✅ `- [ ] 添加 /api/stock/valuation 代理路由和估值数据接口`"""

MANDATORY_SECTIONS = ["## 需求拆解", "## 边界", "## 目标", "## 约束"]


def _validate_clarify(content: str) -> list[str]:
    """Validate clarify.md has all four mandatory sections.

    Returns list of missing section headings.
    """
    missing = []
    for heading in MANDATORY_SECTIONS:
        if heading not in content:
            missing.append(heading)
    return missing


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

    user_prompt = f"""## Change 目录: {change_dir}
## 目标项目: {target_path}
{ctx_section}{supp_section}{token_section}
## 已有 proposal.md:
{proposal}

直接开始写 artifacts：
1. 用 write_file 在 {change_dir}/specs/ 下创建 delta spec 文件（注意：必须在 specs/ 子目录里，不是 specs.md）
2. 用 write_file 创建 {change_dir}/clarify.md（四节结构：需求拆解、边界、目标、约束）

项目架构已在上方提供，直接开始写，不要用工具探索项目。"""

    result = await agent.run(CLARIFIER_SYSTEM, user_prompt, **kwargs)

    # Validate specs/ directory
    specs_dir = f"{change_dir}/specs"
    if not dir_exists(specs_dir, transport) or not list_files_recursive(specs_dir, "*.md", transport):
        print("  ⚠️ specs/ directory empty or missing, retrying...")
        transport.run_shell(f"mkdir -p '{specs_dir}'", timeout=5)
        retry_prompt = user_prompt + f"\n\n注意：上一次你没有在 specs/ 子目录下创建文件。必须用 write_file 创建 {change_dir}/specs/<name>.md，不要创建 specs.md。"
        result = await agent.run(CLARIFIER_SYSTEM, retry_prompt, **kwargs)

    # Validate clarify.md existence and sections
    clarify_path = f"{change_dir}/clarify.md"
    clarify_content = read_file(clarify_path, transport) or ""
    if not clarify_content.strip():
        print("  ⚠️ clarify.md missing or empty, retrying...")
        retry_prompt = user_prompt + f"\n\n注意：上一次你没有创建 clarify.md。必须用 write_file 创建 {change_dir}/clarify.md，包含四个 ## 节：需求拆解、边界、目标、约束。"
        result = await agent.run(CLARIFIER_SYSTEM, retry_prompt, **kwargs)
        clarify_content = read_file(clarify_path, transport) or ""

    # Validate mandatory sections
    if clarify_content.strip():
        missing = _validate_clarify(clarify_content)
        if missing:
            print(f"  ⚠️ clarify.md missing sections: {missing}, retrying...")
            retry_prompt = user_prompt + f"\n\n注意：clarify.md 缺少以下必要节：{', '.join(missing)}。请补充完整后重新 write_file {change_dir}/clarify.md。"
            result = await agent.run(CLARIFIER_SYSTEM, retry_prompt, **kwargs)

    return result


def derive_explore_tasks(proposal_text: str) -> list[str]:
    """Derive 2-5 focused explore instructions from proposal text.

    Pure function — no LLM calls, deterministic output based on keyword
    extraction from the proposal title / first line.
    """
    # Extract keywords from the first non-empty line (title)
    lines = [line.strip() for line in proposal_text.splitlines() if line.strip()]
    title = lines[0] if lines else ""
    # Use the first 6 meaningful characters as keyword hint
    keywords = title[:30] if len(title) >= 6 else title or "项目"

    # Fixed set of exploration templates covering different aspects
    templates = [
        "搜索项目中与「{kw}」相关的现有代码和模块",
        "查找项目的目录结构、入口文件、配置文件模式",
        "搜索项目中与「{kw}」相关的测试文件和测试模式",
        "查找项目的依赖管理和技术栈（requirements.txt, pyproject.toml, package.json 等）",
        "搜索项目中与「{kw}」相关的数据库模型和数据结构",
    ]

    tasks = [t.format(kw=keywords) for t in templates]

    # Always return at least 2, at most 5
    return tasks[:5]


def estimate_token_budget(change_name: str = "",
                          db_path: Optional[Path] = None) -> dict:
    """Estimate token budget based on historical IMPLEMENT phase records.

    Queries the metrics DB for recent IMPLEMENT phase token usage,
    returns average as estimate dict. Pure function — no side effects.

    Returns:
        {"estimated_prompt": int, "estimated_completion": int, "source": "historical"}
        or {"source": "none"} if no history exists.
    """
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
            if p.get("phase") in ("implement", "clarify", "enrich"):
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
