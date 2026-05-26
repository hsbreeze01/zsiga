# clarify.md — add-phase-token-cap

## 需求拆解

### 原始需求
为 pipeline 各阶段添加独立的 token 预算上限（phase cap），防止单个阶段消耗过多 token。当前各阶段共享 1.2M 总预算且无阶段级限制，导致 implement 阶段峰值可达 1.85M、enrich 峰值 1.16M。需要一种机制让每个阶段在超出各自配额时优雅终止，而非硬失败。

### 拆解后的子任务

- [ ] 1. **TokenBudget 增加 phase_cap 属性与检测逻辑** — 在 `zsiga/agent/token_budget.py` 的 `TokenBudget.__init__` 中新增 `phase_cap: int = 0` 参数，在 `record()` 方法中计算 `cap_exceeded` 标志并写入返回结果；默认值 0 表示不启用（向后兼容）。（预估复杂度：低, 预估 token：~3000 / 无历史参考）
- [ ] 2. **PipelineConfig 添加 phase_token_caps 配置** — 在 `zsiga/config.py` 的 `PipelineConfig`（或相关配置结构）中新增 `PHASE_TOKEN_CAPS` 字典常量，包含 clarify/enrich/implement/review/verify/optimize/reflect/deliver 八个阶段的默认 cap 值。（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 3. **Agent loop 中检测并返回 CAP_EXCEEDED** — 在 `zsiga/agent/loop.py` 中，当 `budget.record()` 返回 `cap_exceeded=True` 时，提前终止当前 loop 迭代并返回内容为 `"CAP_EXCEEDED"` 的结果（类似现有 `"BUDGET_EXCEEDED"` 的处理路径，但非硬失败）。（预估复杂度：中, 预估 token：~4000 / 无历史参考）
- [ ] 4. **Orchestrator 阶段前置 cap 设置与 CAP_EXCEEDED 处理** — 在 `zsiga/pipeline/orchestrator.py` 中：(a) 每个阶段启动前将 `PHASE_TOKEN_CAPS[phase_name]` 赋值给 `self.agent.budget.phase_cap`；(b) 阶段返回 `"CAP_EXCEEDED"` 时记录 WARNING 日志并正常推进到下一阶段（不 revert、不 retry）。需确保每阶段开始时重置 phase 已用量（区别于 session 级累计用量）。（预估复杂度：中, 预估 token：~5000 / 无历史参考）
- [ ] 5. **补充 phase_cap 相关测试** — 在 `tests/test_token_budget.py` 中新增：phase_cap=0 时不触发、phase_cap 超限时 cap_exceeded=True、cap_exceeded 不影响 session_exceeded 行为；可选新增 orchestrator 级集成测试验证 CAP_EXCEEDED 后阶段正常推进。（预估复杂度：中, 预估 token：~4000 / 无历史参考）

## 边界

### IN scope
- `zsiga/agent/token_budget.py`：新增 `phase_cap` 属性与 `cap_exceeded` 检测
- `zsiga/config.py`：新增 `PHASE_TOKEN_CAPS` 配置常量
- `zsiga/agent/loop.py`：`CAP_EXCEEDED` 检测与返回
- `zsiga/pipeline/orchestrator.py`：阶段前置 cap 设置 + `CAP_EXCEEDED` 优雅处理
- `tests/test_token_budget.py`：phase_cap 单元测试
- 现有 `total_budget` / `session_exceeded` 行为保持不变（向后兼容）

### OUT of scope
- 基于超时的预算控制（timeout-based budgets）
- 上下文压缩（compaction）策略变更
- Langfuse / 可观测性集成变更
- Dashboard 指标展示（phase cap 使用率可视化）
- 动态 cap 调整（如根据历史消耗自适应）

### 依赖的外部条件
- `zsiga/agent/token_budget.py` 中 `TokenBudget` 类的 `record()` 方法签名需保持兼容
- `zsiga/agent/loop.py` 中现有的 `BUDGET_EXCEEDED` 处理路径作为参考实现
- `zsiga/pipeline/orchestrator.py` 中阶段调度逻辑需有明确的 phase name 可映射到 `PHASE_TOKEN_CAPS` 字典
- `tests/test_token_budget.py` 已有测试用例不因新增属性而失败

## 目标

### 成功标准
1. `TokenBudget` 具有 `phase_cap` 属性，默认值为 0（不启用），向后兼容
2. `PipelineConfig`（或等效配置）包含 `PHASE_TOKEN_CAPS` 字典，涵盖全部 8 个阶段
3. 每个阶段启动前 orchestrator 正确设置 `budget.phase_cap` 为该阶段的配额值
4. 当 `phase_cap > 0` 且阶段已用量超过 cap 时，`record()` 返回 `cap_exceeded=True`
5. `CAP_EXCEEDED` 触发阶段提前终止 + WARNING 日志，下一阶段正常启动，不 revert
6. 现有 `total_budget` 和 `session_exceeded` 行为不受影响
7. `ruff check` 在所有修改文件上通过
8. `pytest tests/test_token_budget.py` 全部通过

### 验收方式
- 单元测试验证 `phase_cap=0` 不触发、`phase_cap` 超限时正确返回 `cap_exceeded`
- 单元测试验证 `cap_exceeded` 与 `session_exceeded` 独立互不干扰
- 集成/手动验证：设置极低 cap（如 1000）后，阶段应在 `CAP_EXCEEDED` 后优雅退出并继续下一阶段
- `ruff check` + `pytest` 无回归

## 约束

### 不能修改的文件
- `zsiga/agent/compaction.py`（压缩策略不在 scope 内）
- `site/dashboard.html`（前端不在 scope 内）
- `zsiga/daemon.py`（守护进程逻辑不在 scope 内）
- `venv2/` 下所有文件（第三方依赖）

### 项目部署分支
- main（通过 proposal 管道自动合并）

### 已知风险
- **阶段间累计用量 vs 阶段内用量混淆**：`TokenBudget` 的 `_used` 可能是 session 级累计，phase cap 需基于阶段内用量。需确认 `record()` 是否需要在每次阶段切换时重置阶段内计数器，或引入独立的 `_phase_used` 字段
- **orchestrator 阶段名称映射**：如果 orchestrator 内部使用的 phase name 与 `PHASE_TOKEN_CAPS` 字典 key 不完全一致，可能导致 KeyError。需验证阶段名称枚举
- **loop.py 中 CAP_EXCEEDED 与 BUDGET_EXCEEDED 的区分**：两者处理路径相似但语义不同（soft vs hard），需确保 `loop.py` 中不会将 `CAP_EXCEEDED` 误判为硬失败
- **默认值 0 的安全性**：`phase_cap=0` 必须保证"不启用"语义，避免 0 被误解析为"立即超额"

### 预估 token 消耗
- prompt: ~12000
- completion: ~4000
- 数据来源: 无历史参考（基于 4 文件中等变更 + 测试的估算）
