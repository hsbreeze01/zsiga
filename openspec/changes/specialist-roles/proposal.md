# Proposal: 专业子代理分化

## 背景
zsiga 的 `agent/sub_agent.py` 已有 `create_sub_agent()` + `run_parallel()` 基础设施，但所有子代理共用同一个通用 system prompt（"你是 zsiga 的子 agent"），没有角色区分。不同任务类型（探索、实现、验证）需要不同的权限、策略和工具集。

## 目标
创建 `agent/roles.py`，定义三种专业子代理角色（explore、implement、review），每种角色有专门的 system prompt、工具子集和行为约束。修改 `sub_agent.py` 支持 `create_with_role(role)` 工厂函数。

## 方案
1. `agent/roles.py`：
   - 定义 `Role` 枚举：EXPLORE、IMPLEMENT、REVIEW
   - 每个角色定义：
     - **explore**：只读，max_turns=5，system prompt 专注搜索/分析，工具集=[bash, read_file, search, list_files, ast_search]
     - **implement**：可写，max_turns=15，system prompt 专注实现/测试，工具集=[全部 8 个]
     - **review**：只读，max_turns=8，system prompt 专注验证/报告，工具集=[bash, read_file, search, list_files, ast_search]
   - `get_role_config(role: Role) -> RoleConfig` 返回角色配置
   - `get_role_system_prompt(role: Role) -> str` 返回角色 system prompt

2. 修改 `agent/sub_agent.py`：
   - 新增 `create_with_role(role: str, ...)` — 根据角色选择工具集和 system prompt
   - 保持 `create_sub_agent()` 不变（向后兼容）
   - `run_sub_agent()` 支持 role 参数，使用角色的 system prompt 替代默认的

3. 编写测试 `tests/test_roles.py`

## 预期行为
- `create_with_role("explore", ...)` 创建只读子代理，限制 5 轮
- `create_with_role("implement", ...)` 创建全能子代理，15 轮
- `create_with_role("review", ...)` 创建验证子代理，8 轮，输出 pass/fail 报告
- 旧的 `create_sub_agent()` 仍然工作，不受影响

## 范围
- 新增 `agent/roles.py`
- 修改 `agent/sub_agent.py`（新增 create_with_role，不改 create_sub_agent）
- 新增 `tests/test_roles.py`
- 不修改 `agent/loop.py`（AgentLoop 本身不关心角色）
- 不修改 pipeline 编排逻辑

## 约束
- 角色配置是纯数据（dataclass），不含复杂逻辑
- system prompt 用中文，与 zsiga 整体风格一致
- explore 角色必须不能有 write_file/edit_file（只读硬约束）
