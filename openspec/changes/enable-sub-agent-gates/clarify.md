# Clarify: 启用 Proposal Gate 和 Design Gate

## 需求拆解

### 原始需求
zsiga 已完成 9 角色 sub-agent 能力体系代码实现（commit 7757229），包括 Steward（proposal 前置评审）和 Judge（design/spec 质量门禁）等角色。这些功能目前全部处于 disabled 状态。需要在 zsiga.yaml 的 pipeline 节中添加 `proposal_gate` 和 `design_gate` 配置块并设为 enabled: true，使 Steward 和 Judge 正式参与 pipeline。

### 拆解后的子任务
- [ ] 1. 在 zsiga.yaml pipeline 节中添加 proposal_gate 和 design_gate 配置块 (预估复杂度：低, 预估 token：~1500 / 无历史参考)
  - proposal_gate: enabled, max_retries, steward_max_turns, steward_timeout, score_accept, score_pushback, learning_weight_days
  - design_gate: enabled, max_retries, max_turns, timeout

## 边界

### IN scope
- 在 zsiga.yaml 的 pipeline 节中添加 proposal_gate 配置块（含 7 个字段）
- 在 zsiga.yaml 的 pipeline 节中添加 design_gate 配置块（含 4 个字段）
- 确保配置格式符合 YAML 规范，不破坏现有配置结构

### OUT of scope
- 修改任何 Python 代码（Steward / Judge 角色逻辑已在 commit 7757229 中实现）
- 修改 pipeline 的 phase 执行顺序
- 修改 FIX intent 的快速 pipeline 路径
- 修改 daemon status API 逻辑
- 修改 archive 中已有 proposal 的处理逻辑

### 依赖的外部条件
- zsiga.yaml 已有 pipeline 节（配置项插入位置存在）
- Steward 和 Judge 角色的 Python 实现已就绪（commit 7757229）
- 现有代码已支持读取 proposal_gate.enabled 和 design_gate.enabled 字段

## 目标

### 成功标准
1. zsiga.yaml 中 proposal_gate.enabled 值为 true
2. zsiga.yaml 中 design_gate.enabled 值为 true
3. proposal_gate 包含全部 7 个字段：enabled, max_retries, steward_max_turns, steward_timeout, score_accept, score_pushback, learning_weight_days
4. design_gate 包含全部 4 个字段：enabled, max_retries, max_turns, timeout
5. YAML 文件语法正确，不破坏现有配置项
6. 现有 pipeline phase 顺序不受影响
7. 可通过将 enabled 改回 false 立即回滚

### 验收方式
- `python -c "import yaml; c=yaml.safe_load(open('zsiga.yaml')); assert c['pipeline']['proposal_gate']['enabled'] is True; assert c['pipeline']['design_gate']['enabled'] is True"` 通过
- `ruff check` 无新增错误
- 人工确认 proposal_gate 和 design_gate 字段值与 proposal.md 中指定的数值一致

## 约束

### 不能修改的文件
- 所有 .py 文件（zsiga/pipeline/ 下的所有模块）
- site/dashboard.html
- tests/ 下所有文件
- requirements.txt / pyproject.toml

### 项目部署分支
- main

### 已知风险
- 若现有 Python 代码中读取 proposal_gate / design_gate 的字段名与本次配置的 key 不完全一致，启用后可能触发 KeyError 或使用默认值而非配置值
- 若 Steward/Judge 角色实现中存在 bug，启用后可能导致 pipeline 阻塞——但可通过改回 enabled: false 立即回滚
- learning_weight_days: 90 是首次设定值，缺乏历史数据校准

### 预估 token 消耗
- prompt: ~800
- completion: ~300
- 数据来源: 无历史参考（纯配置变更，单文件单次编辑）
