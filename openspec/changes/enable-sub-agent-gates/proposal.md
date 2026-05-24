# 启用 Proposal Gate 和 Design Gate

## 背景

zsiga 刚完成了 9 角色 sub-agent 能力体系的代码实现（commit 7757229），包括：
- Steward (管家) 角色：pipeline 前置评审，综合历史经验和代码库事实判断 proposal 是否值得执行
- Judge (裁判) 角色：ENRICH 后的 design/spec 质量门禁
- Analyst (分析师) 角色：依赖分析和影响评估
- Scout (侦察兵) 角色：快速代码搜索
- SRE 意图路由和 Operator 角色

这些功能目前全部处于 disabled 状态（proposal_gate_enabled: false, design_gate_enabled: false）。

## 目标

在 zsiga.yaml 中启用 Proposal Gate 和 Design Gate，让 Steward 和 Judge 角色正式参与 pipeline。

## 具体变更

### 文件：zsiga.yaml（pipeline 节）

在 pipeline 配置中添加以下字段：

    proposal_gate:
      enabled: true
      max_retries: 1
      steward_max_turns: 3
      steward_timeout: 90
      score_accept: 6
      score_pushback: 3
      learning_weight_days: 90

    design_gate:
      enabled: true
      max_retries: 2
      max_turns: 4
      timeout: 120

## 约束

- 只修改 zsiga.yaml，不修改任何 Python 代码
- 不改变现有 pipeline 的 phase 顺序
- 不影响 FIX intent 的快速 pipeline（跳过 CLARIFY/ENRICH）
- 新功能启用后，下一个 proposal 应该首先经过 Steward 评审
- 如果 Steward 或 Judge 导致问题，可以通过改回 enabled: false 立即回滚

## 验收标准

1. zsiga.yaml 中 proposal_gate.enabled 和 design_gate.enabled 均为 true
2. 重启 daemon 后，新 proposal 会先经过 Proposal Gate (Steward)
3. ENRICH 完成后会经过 Design Gate (Judge)
4. 现有 archive 中的 proposal 不受影响
5. daemon status API 能正常响应
