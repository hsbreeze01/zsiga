import subprocess
from pathlib import Path

from ..agent.loop import AgentLoop
from ..agent.tools import register_tools

ENRICHER_SYSTEM = """你是 zsiga，一个基于 OpenSpec 的自动开发智能体。

你的任务：根据 proposal.md 补全 OpenSpec change 的其余 artifacts。

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
   - 每个任务足够小，一个 session 能完成
   - 用 - [ ] 格式

规则：
- 先读目标项目代码，理解现有架构和模式
- specs 描述行为，不描述实现细节
- design 基于项目现有技术栈
- tasks 每个 - [ ] 最多改 3 个文件"""


async def enrich(agent: AgentLoop, change_dir: str, target_path: str,
                 max_turns: int = 25, timeout_seconds: int = 600):
    proposal = Path(change_dir, "proposal.md").read_text()

    user_prompt = f"""## Change 目录: {change_dir}
## 目标项目: {target_path}

## 已有 proposal.md:
{proposal}

## 你的任务:
1. 读取目标项目代码，理解现有架构（list_files, read_file, search）
2. 在 {change_dir}/specs/ 下创建 delta spec
3. 创建 {change_dir}/design.md
4. 创建 {change_dir}/tasks.md

先读代码再写 artifacts。"""

    return await agent.run(ENRICHER_SYSTEM, user_prompt,
                          max_turns=max_turns, timeout_seconds=timeout_seconds)
