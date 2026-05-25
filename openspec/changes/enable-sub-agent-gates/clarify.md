## 需求拆解

### 原始需求

在 zsiga.yaml 中启用 Proposal Gate 和 Design Gate 两个子代理门控机制，使 Steward（管家）和 Judge（裁判）角色正式参与 pipeline 流程。Proposal Gate 在新 proposal 提交时由 Steward 进行前置评审，Design Gate 在 ENRICH 完成后由 Judge 进行 design/spec 质量门禁。仅修改 YAML 配置，不涉及 Python 代码变更。

### 拆解后的子任务

- [ ] 1. 在 zsiga.yaml 的 pipeline 节中添加/更新 proposal_gate 配置块，设置 enabled: true 及 max_retries、steward_max_turns、steward_timeout、score_accept、score_pushback、learning_weight_days 六个参数 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 2. 在 zsiga.yaml 的 pipeline 节中添加/更新 design_gate 配置块，设置 enabled: true 及 max_retries、max_turns、timeout 三个参数 (预估复杂度：低, 预估 token：~1500 / 无历史参考)
- [ ] 3. 验证 YAML 配置格式正确且可被 config.py 正常解析（proposal_gate_* 和 design_gate_* 字段被 PipelineConfig 正确读取） (预估复杂度：低, 预估 token：~1500 / 无历史参考)
- [ ] 4. 确认已有测试 `test_spec_enable_sub_agent_gates__pipeline_gates_config.py` 通过，覆盖 gates 配置读取和启用的核心路径 (预估复杂度：低, 预估 token：~1000 / 无历史参考)

## 边界

### IN scope
- 修改 zsiga.yaml 中 pipeline 节的 proposal_gate 和 design_gate 配置块
- 确保配置字段名与 config.py 中 PipelineConfig 的解析逻辑匹配
- 确保已有测试通过
- 回滚方案：将 enabled 改回 false 即可禁用

### OUT of scope
- 不修改任何 Python 源代码文件（config.py、daemon.py、pipeline/*.py 等）
- 不修改 pipeline phase 顺序或 phase 定义
- 不影响 FIX intent 的快速 pipeline（跳过 CLARIFY/ENRICH 的路径）
- 不新增测试文件
- 不修改 archive 中已有 proposal 的状态
- 不调整 Steward/Judge 角色的 prompt 或行为逻辑

### 依赖的外部条件
- commit 7757229 已完成 9 角色 sub-agent 代码实现，gate 执行逻辑（Steward/Judge 调用链）已存在于代码库
- config.py:407-418 的 PipelineConfig 解析链路已能正确读取 proposal_gate 和 design_gate 的所有子字段
- daemon.py 或 pipeline runner 中存在 `proposal_gate_enabled`/`design_gate_enabled` 的条件分支，能够在 enabled=true 时触发 gate 流程
- score_accept/score_pushback 的值域（整数 0-8 vs 浮点 0-1）与 gate 评分函数的输出范围兼容

## 目标

### 成功标准
1. zsiga.yaml 中 proposal_gate.enabled 为 true 且包含全部 6 个子参数（max_retries、steward_max_turns、steward_timeout、score_accept、score_pushback、learning_weight_days）
2. zsiga.yaml 中 design_gate.enabled 为 true 且包含全部 3 个子参数（max_retries、max_turns、timeout）
3. YAML 语法合法，config.py 能无报错解析新配置
4. 已有测试 `test_spec_enable_sub_agent_gates__pipeline_gates_config` 通过
5. daemon 重启后 status API 正常响应，不因 gate 启用而崩溃

### 验收方式
- `ruff check` 无 lint 错误（YAML 文件无 Python lint 影响）
- `pytest tests/test_spec_enable_sub_agent_gates__pipeline_gates_config.py` 通过
- 手动确认 zsiga.yaml 的 proposal_gate 和 design_gate 字段值与 proposal 一致
- 确认回滚路径可行：将 enabled 改回 false 后功能可立即禁用

## 约束

### 不能修改的文件
- zsiga/config.py
- zsiga/daemon.py
- zsiga/pipeline/*.py
- zsiga/gate/*.py
- tests/ 下所有测试文件
- pyproject.toml、requirements.txt

### 项目部署分支
main

### 已知风险
- **score_accept/score_pushback 值域兼容性**：proposal 设置 score_accept=6、score_pushback=3（整数），而 config.py 默认值为 0.8/0.5（浮点）。如果 gate 评分函数输出 0-1 范围的浮点数，score_accept=6 将导致所有 proposal 永远无法通过 accept 阈值，pipeline 被永久阻塞
- **历史失败**：同名/同目标的 proposal `enable-sub-agent-gates` 多次在 verify 阶段失败，失败模式为 `code.unknown`，根因未明确。本次 proposal 未分析前序失败原因
- **gate 执行路径可能不完整**：并行探索 Agent 在整个代码库中搜索 `proposal_gate`、`design_gate`、`gate` 等关键词均未找到结果。如果 config.py 虽然能解析配置但 daemon/pipeline 中不存在消费这些配置的条件分支，enabled=true 将是空操作
- **零测试覆盖**：除 `test_spec_enable_sub_agent_gates__pipeline_gates_config.py` 外，无其他 gate 相关测试。gate 启用后的运行时行为无自动化验证
- **双 gate 同时启用的叠加风险**：proposal 同时启用两个 gate，任一出问题都可能阻塞 pipeline，无分阶段灰度策略

### 预估 token 消耗
- prompt: ~4000
- completion: ~1500
- 数据来源: 无历史参考（同类任务历史上均在 verify 阶段失败，无成功基线）
