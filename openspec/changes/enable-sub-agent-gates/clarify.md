## 需求拆解

### 原始需求

在 zsiga.yaml 中启用 Proposal Gate 和 Design Gate 配置，使 Steward（前置评审）和 Judge（ENRICH 后门禁）角色正式参与 pipeline。当前这两个功能处于 disabled 状态，需要将 `proposal_gate_enabled` 和 `design_gate_enabled` 翻转为 enabled，并配置相关参数（max_retries、steward_max_turns、score_accept 等）。

### 拆解后的子任务

- [ ] 1. 在 zsiga.yaml 的 pipeline 节中添加 proposal_gate 和 design_gate 配置块 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 2. 验证 YAML 配置结构与 Python 消费代码的 schema 兼容性 (预估复杂度：中, 预估 token：~3000 / 无历史参考)

## 边界

### IN scope
- 修改 zsiga.yaml 中 pipeline 节的配置，添加 proposal_gate 和 design_gate 参数
- 配置项包括：enabled、max_retries、steward_max_turns、steward_timeout、score_accept、score_pushback、learning_weight_days（proposal_gate）；enabled、max_retries、max_turns、timeout（design_gate）

### OUT of scope
- 修改任何 Python 源码文件
- 改变现有 pipeline 的 phase 顺序
- 影响 FIX intent 的快速 pipeline（跳过 CLARIFY/ENRICH 的行为不变）
- 修改 archive 中的已有 proposal

### 依赖的外部条件
- ⚠️ **关键依赖**：Python 代码中必须存在消费 `proposal_gate` / `design_gate` 配置的逻辑。并行探索结果（5 个 Explore Agent）一致确认：项目中零匹配 `proposal_gate`、`design_gate`、`gate`、`ProposalGate`、`DesignGate`。若代码中无对应消费逻辑，启用配置不会产生任何运行时效果
- ⚠️ **配置 schema 兼容性**：proposal 描述的嵌套结构（`proposal_gate.enabled: true`）与可能的扁平 key 读取方式（`config.get("proposal_gate_enabled")`）需确认一致
- ⚠️ **score_accept 阈值范围**：proposal 中 `score_accept: 6` 为整数，需确认代码中评分是 0.0–1.0 浮点还是 0–10 整数范围，否则可能所有 proposal 永远被拒

## 目标

### 成功标准
1. zsiga.yaml 中 proposal_gate 配置块存在且 enabled 为 true
2. zsiga.yaml 中 design_gate 配置块存在且 enabled 为 true
3. YAML 语法合法，daemon 启动时不报配置解析错误
4. daemon status API 能正常响应（配置变更不破坏现有功能）

### 验收方式
- 读取 zsiga.yaml 确认两个 gate 的 enabled 字段为 true
- 验证 YAML 可被 `yaml.safe_load()` 正常解析，无重复 key 等问题
- 确认 daemon 启动后 status API 正常返回

## 约束

### 不能修改的文件
- 所有 `.py` 文件（proposal 明确约束"只修改 zsiga.yaml，不修改任何 Python 代码"）
- 现有 pipeline phase 顺序
- FIX intent 快速 pipeline 路径

### 项目部署分支
- 未在 proposal 中指定（需确认）

### 已知风险
- **配置幽灵风险（高）**：5 个 Explore Agent 均未在项目中找到 `gate` 相关代码。若 Python 代码不读取这些配置项，则本次变更为纯 placebo 操作——配置写了但无任何行为变化。验收标准中"新 proposal 会先经过 Proposal Gate (Steward)"和"ENRICH 完成后会经过 Design Gate (Judge)"在纯配置变更下无法达成
- **配置结构不匹配风险（高）**：proposal 描述的嵌套 YAML 结构（`proposal_gate: { enabled: true, ... }`）可能不匹配代码实际消费的扁平 key 模式（`proposal_gate_enabled: true`）。如果代码读的是扁平 key，嵌套结构将永远不会被命中
- **score_accept 类型风险（中）**：`score_accept: 6` 作为整数，若代码期望 0.0–1.0 浮点阈值，则所有 proposal/design 将永远被拒绝
- **历史重复失败模式（高）**：历史 lessons 中 `sre-subagent-design` 连续 3 次 verify 失败，`proposal_gate.reject/pushback` 出现 9+ 次，核心原因均为"声称功能已实现但代码中不存在"。本次 proposal 与历史失败模式高度相似
- **可回滚性**：proposal 声称可通过改回 `enabled: false` 回滚，但前提是代码确实消费了该字段

### 预估 token 消耗
- prompt: ~3000
- completion: ~1500
- 数据来源: 无历史参考（同类任务历史均为 reject/pushback，无成功交付记录）
