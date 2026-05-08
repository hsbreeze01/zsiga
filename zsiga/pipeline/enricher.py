from ..agent.loop import AgentLoop
from ..agent.tools import register_tools
from ..transport import Transport, LocalTransport
from .utils import read_file, dir_exists, list_files_recursive

ENRICHER_SYSTEM = """你是 zsiga，一个基于 OpenSpec 的自动开发智能体。

你的任务：根据 proposal.md 和已提供的项目上下文，直接编写 OpenSpec artifacts。

必须遵循 OpenSpec 的 artifact 格式：

1. specs/ — Delta specs，描述行为变更
   - 用 ## ADDED Requirements / ## MODIFIED Requirements / ## REMOVED Requirements 区分
   - 每个 ### Requirement 必须有 #### Scenario（Given/When/Then 格式）
   - 用 SHALL/MUST/SHOULD 表达约束强度
   - spec 描述行为（what），不是实现（how）

2. design.md — 技术方案
   - 架构决策和理由
   - 数据流
   - 需要新增/修改的文件列表

3. tasks.md — 实现清单
   - 分组，层次编号（1.1, 1.2...）
   - 用 - [ ] 格式

规则：
- 项目代码已经提供在下方，不需要再用工具读文件
- specs 描述行为，不描述实现细节
- design 基于项目现有技术栈，遵循现有模式
- 直接开始写 artifacts，不要先做探索

## 任务粒度规则（关键）

任务必须按**功能模块**分组，不是按单个函数或文件分组：

### 后端任务（Python/路由/逻辑）
- 一个 - [ ] 对应一个完整的功能模块（如"添加技术指标计算层"包含所有calc函数）
- 每个 task 预估消耗 ≤ 3 轮（读1次+写1次+验证1次）
- 每组最多 4-6 个 task

### 前端任务（HTML/CSS/JS/模板）
- 如果项目包含前端模板（如 templates/index.html），在 design.md 中明确标注"前端任务需要人工完成"
- 前端 UI 渲染任务（图表、组件、样式）标记为 `scope: frontend` — zsiga 不执行这些
- 后端数据准备任务（API 路由、数据函数）正常生成
- 每个 - [ ] 应该是"一个页面区域"或"一个交互功能"，不是"一个函数"

### 反模式（不要这样做）
- ❌ `- [ ] 实现 calcMA 函数` — 太细，一个3行函数不值得一个任务
- ❌ `- [ ] 添加 MA 图表渲染` + `- [ ] 添加 MACD 图表渲染` — 应合并为一个"技术分析图表"
- ✅ `- [ ] 添加技术指标计算层（calcMA/calcEMA/calcMACD/calcKDJ/calcBOLL/calcRSI）`
- ✅ `- [ ] 添加 /api/stock/valuation 代理路由和估值数据接口`"""


async def enrich(agent: AgentLoop, change_dir: str, target_path: str,
                 transport: Transport = None, project_context: str = "", **kwargs):
    transport = transport or LocalTransport()
    proposal = read_file(f"{change_dir}/proposal.md", transport) or ""

    ctx_section = ""
    if project_context:
        ctx_section = f"\n## 项目代码上下文（已预读，不需要再用工具读取）\n{project_context}\n"

    user_prompt = f"""## Change 目录: {change_dir}
## 目标项目: {target_path}
{ctx_section}
## 已有 proposal.md:
{proposal}

直接开始写 artifacts：
1. 用 write_file 在 {change_dir}/specs/ 下创建 delta spec 文件（注意：必须在 specs/ 子目录里，不是 specs.md）
2. 用 write_file 创建 {change_dir}/design.md
3. 用 write_file 创建 {change_dir}/tasks.md

项目架构已在上方提供，直接开始写，不要用工具探索项目。"""

    result = await agent.run(ENRICHER_SYSTEM, user_prompt,
                          **kwargs)

    specs_dir = f"{change_dir}/specs"
    if not dir_exists(specs_dir, transport) or not list_files_recursive(specs_dir, "*.md", transport):
        print(f"  ⚠️ specs/ directory empty or missing, retrying enrich...")
        transport.run_shell(f"mkdir -p '{specs_dir}'", timeout=5)
        retry_prompt = user_prompt + "\n\n注意：上一次你没有在 specs/ 子目录下创建文件。必须用 write_file 创建 {change_dir}/specs/<name>.md，不要创建 specs.md。"
        result = await agent.run(ENRICHER_SYSTEM, retry_prompt, **kwargs)

    return result
