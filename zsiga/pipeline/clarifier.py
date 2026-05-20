"""CLARIFY phase: requirement engineering — decompose, bound, align, constrain.

Produces clarify.md with four mandatory sections before ENRICH runs.
Lightweight: 1-3 turns, reads proposal + project context, writes clarify.md.
"""

import logging

from ..agent.loop import AgentLoop, RunResult
from ..transport import Transport, LocalTransport
from .utils import read_file

log = logging.getLogger(__name__)

CLARIFY_SYSTEM = """你是 zsiga 的需求工程师。你的唯一任务是分析 proposal.md，输出结构化需求契约 clarify.md。

必须用 write_file 工具写入 clarify.md，包含以下四个 ## 节（按顺序）：

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

关键规则：
- 不要读文件，所有信息已在 prompt 中提供
- 不要生成 specs/ 或代码，只写 clarify.md
- 子任务必须可独立验证，每个有明确文件范围
- 任务按功能模块分组（不要一个函数一个 task）
- 直接用 write_file 写入，不要先输出再写

## 任务粒度规则
- 一个 - [ ] 对应一个完整功能模块
- 每个 task 预估消耗 ≤ 3 轮
- ✅ 添加技术指标计算层（calcMA/calcEMA/calcMACD）
- ❌ 实现 calcMA 函数（太细）"""


MANDATORY_SECTIONS = ["## 需求拆解", "## 边界", "## 目标", "## 约束"]


def _validate_clarify(content: str) -> list[str]:
    """Return missing mandatory section headings."""
    return [h for h in MANDATORY_SECTIONS if h not in content]


async def clarify(
    agent: AgentLoop,
    change_dir: str,
    target_path: str,
    transport: Transport = None,
    project_context: str = "",
    max_turns: int = 3,
    timeout_seconds: int = 120,
) -> RunResult:
    """CLARIFY phase: generate clarify.md from proposal + context.

    Lightweight pre-step before ENRICH.  Produces the structured requirement
    contract so that ENRICH can focus on specs generation.
    """
    transport = transport or LocalTransport()
    proposal = read_file(f"{change_dir}/proposal.md", transport) or ""

    ctx_section = ""
    if project_context:
        ctx_section = (
            f"\n## 项目代码上下文（已预读，不需要再用工具读取）\n"
            f"{project_context}\n"
        )

    user_prompt = f"""## Change 目录: {change_dir}
## 目标项目: {target_path}
{ctx_section}
## proposal.md:
{proposal}

直接用 write_file 写入 {change_dir}/clarify.md，包含四节：需求拆解、边界、目标、约束。"""

    result = await agent.run(
        CLARIFY_SYSTEM, user_prompt,
        max_turns=max_turns, timeout_seconds=timeout_seconds,
    )

    # Validate clarify.md
    clarify_path = f"{change_dir}/clarify.md"
    clarify_content = read_file(clarify_path, transport) or ""
    if not clarify_content.strip():
        log.warning("clarify.md missing after first attempt, retrying...")
        retry_prompt = (
            user_prompt
            + f"\n\n注意：你上一次没有创建 clarify.md。必须用 write_file 创建 "
            f"{change_dir}/clarify.md，包含四个 ## 节。"
        )
        result = await agent.run(
            CLARIFY_SYSTEM, retry_prompt,
            max_turns=max_turns, timeout_seconds=timeout_seconds,
        )
        clarify_content = read_file(clarify_path, transport) or ""

    # Validate mandatory sections
    if clarify_content.strip():
        missing = _validate_clarify(clarify_content)
        if missing:
            log.warning("clarify.md missing sections: %s, retrying...", missing)
            retry_prompt = (
                user_prompt
                + f"\n\n注意：clarify.md 缺少以下节：{', '.join(missing)}。"
                f"请补充完整后重新 write_file {change_dir}/clarify.md。"
            )
            result = await agent.run(
                CLARIFY_SYSTEM, retry_prompt,
                max_turns=max_turns, timeout_seconds=timeout_seconds,
            )

    return result
