# clarify.md — 启用 Proposal Gate 和 Design Gate

## 需求拆解

### 原始需求

zsiga 已完成 9 角色 sub-agent 能力体系（commit 7757229），包括 Steward（管家）、Judge（裁判）等角色，但 proposal_gate 和 design_gate 目前处于 disabled 状态。需要在 zsiga.yaml 的 pipeline 节中启用这两个 Gate，使 Steward 和 Judge 正式参与 pipeline 流程。

### 拆解后的子任务

- [ ] 1. 在 zsiga.yaml pipeline 节中添加 proposal_gate 配置块（enabled: true, max_retries: 1, steward_max_turns: 3, steward_timeout: 90, score_accept: 6, score_pushback: 3, learning_weight_days: 90）并添加 design_gate 配置块（enabled: true, max_retries: 2, max_turns: 4, timeout: 120）（预估复杂度：低, 预估 token：~1500 / 无历史参考）
- [ ] 2. 验证 YAML 语法正确性，确认 config.py 能正确解析新增字段，且 daemon status API 正常响应（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 3. 运行现有测试 `tests/test_spec_enable_sub_agent_gates__pipeline_gates_config.py` 确认无回归（预估复杂度：低, 预估 token：~1500 / 无历史参考）

## 边界

### IN scope

- 修改 zsiga.yaml 中 pipeline 节，添加 proposal_gate 和 design_gate 两个配置块
- 确认 YAML 语法有效，config.py 解析无报错
- 确认现有测试通过

### OUT of scope

- 修改任何 Python 代码（config.py、daemon.py、pipeline 模块等）
- 修改 pipeline 的 phase 顺序
- 影响 FIX intent 的快速 pipeline（跳过 CLARIFY/ENRICH）
- 修改或新增测试用例
- 修改 archive 中已有 proposal 的状态

### 依赖的外部条件

- config.py 中已实现 proposal_gate 和 design_gate 配置字段的解析逻辑（`.get()` 读取）
- daemon.py 中已有 Gate 相关的条件分支逻辑，仅依赖 enabled 标志控制
- commit 7757229 已完成 Steward/Judge 角色的代码实现
- zsiga.yaml 文件存在于项目根目录

## 目标

### 成功标准

1. zsiga.yaml 中 `proposal_gate.enabled: true` 且 `design_gate.enabled: true`
2. YAML 语法合法，`python -c "import yaml; yaml.safe_load(open('zsiga.yaml'))"` 无报错
3. 现有测试套件全部通过（pytest + ruff check）
4. 回滚路径可行：将 enabled 改回 false 即可恢复原状态

### 验收方式

- 读取 zsiga.yaml 确认两个 Gate 配置块存在且值正确
- 执行 `ruff check` 确认无 YAML 相关告警
- 执行 `pytest tests/test_spec_enable_sub_agent_gates__pipeline_gates_config.py` 确认通过
- 执行全量 `pytest` 确认无回归

## 约束

### 不能修改的文件

- zsiga/config.py
- zsiga/daemon.py
- zsiga/pipeline/ 目录下所有文件
- tests/ 目录下所有文件
- pyproject.toml、requirements.txt

### 项目部署分支

- main（默认分支）

### 已知风险

- **前序失败风险**：同名 proposal `enable-sub-agent-gates` 曾于 2026-05-25 在 verify 阶段失败（模式 code.unknown），失败根因未被清晰归因。本变更内容与前次高度重叠，存在重蹈覆辙的可能
- **配置消费链路未验证**：config.py 中的配置解析逻辑存在，但 `proposal_gate_enabled` 和 `design_gate_enabled` 作为符号在代码中未被验证工具确认有下游消费方。如果 daemon/pipeline 中缺少对应的 `if config.proposal_gate_enabled` 条件分支，启用配置不会产生实际运行时效果
- **两个 Gate 同时启用**：Proposal Gate（Steward）和 Design Gate（Judge）同时启用，任一出问题均可能阻塞后续 pipeline。建议如遇 verify 失败，优先回退为仅启用 proposal_gate
- **参数值与代码默认值可能不一致**：proposal 中 `score_accept: 6`（整数）与历史教训中提到的代码默认值 `0.85`（浮点）存在量级差异，需确认 config.py 实际期望的类型

### 预估 token 消耗

- prompt: ~3000
- completion: ~1500
- 数据来源: 无历史参考（前序同名任务失败，无可用的 token 消耗数据）
