# clarify.md — optimize-prompt-token-usage

## 需求拆解

### 原始需求
降低 enrich、implement、verify 三个阶段的 prompt token 浪费。核心问题：(1) `project_context`（~25K chars）在多轮对话的消息历史中被重复发送；(2) Verify Layer 2 的 prompt 包含过多不必要内容（15K diff、全量 specs/design/tasks）；(3) enrich 并行探索池中多个 agent 各自独立接收完整 project_context，造成冗余。目标是将每个成功 proposal 的平均 prompt token 下降 ≥20%。

### 拆解后的子任务

- [ ] 1. **多轮消息历史中的 context 压缩** — 在 `zsiga/agent/loop.py` 中实现 `_compact_context_in_history(messages, turn_count)` 辅助函数：当轮次 > 3 时，将早期消息中的 `## 项目代码上下文` 完整块替换为紧凑引用 `[project_context: {len(ctx)} chars, see turn 0]`。需确保替换不影响当前轮对上下文的引用。 (预估复杂度：中, 预估 token：~8000 / 无历史参考)
- [ ] 2. **Verify Layer 2 prompt 裁剪** — 在 `zsiga/pipeline/verifier.py` 中：(a) 将 diff 上限从 15000 chars 降至 5000 chars；(b) 仅为 `testable=false` 的场景包含 specs，而非全量；(c) 当 design.md 或 tasks.md 长度 > 3000 chars 时，替换为一行摘要。添加 Layer 2 prompt 大小日志以供观测。 (预估复杂度：中, 预估 token：~6000 / 无历史参考)
- [ ] 3. **Enrich 并行池 context 去重** — 在 `zsiga/pipeline/enricher.py`（或 `zsiga/intake/scanner.py`）中：对于并行 explore pool，仅向首个 scout agent 传递完整 `project_context`，其余 agent 接收 500 chars 摘要。确保并行 agent 的任务分配逻辑不受影响。 (预估复杂度：中, 预估 token：~5000 / 无历史参考)
- [ ] 4. **验证与回归测试** — 确认现有测试通过（ruff + pytest），补充或更新与 loop.py / verifier.py / enricher.py 相关的单元测试，覆盖压缩逻辑、裁剪阈值、去重分配。 (预估复杂度：低, 预估 token：~4000 / 无历史参考)

## 边界

### IN scope
- `zsiga/agent/loop.py` 中多轮消息历史的 context 压缩逻辑
- `zsiga/pipeline/verifier.py` 中 Verify Layer 2 prompt 大小裁剪
- `zsiga/pipeline/enricher.py` 或 `zsiga/intake/scanner.py` 中并行池 context 去重
- 相关单元测试的补充/更新
- Layer 2 prompt 大小的可观测性日志

### OUT of scope
- 修改 LLM 模型选择（llm_router 等）
- 修改 review / optimize / deliver 阶段的 prompt
- 修改 `build_project_context()` 函数本身的构建逻辑
- 修改 completion token 相关逻辑
- 修改 daemon 调度或 proposal 生命周期管理

### 依赖的外部条件
- `zsiga/agent/loop.py`、`zsiga/pipeline/verifier.py`、`zsiga/pipeline/enricher.py`（或 `zsiga/intake/scanner.py`）文件存在且结构可修改
- 现有 pytest 测试套件可作为回归基线
- `build_project_context()` 返回值格式稳定（包含 `## 项目代码上下文` 标记段）

## 目标

### 成功标准
1. 平均 prompt tokens per successful proposal 下降 ≥ 20%（对比变更前后各若干 proposal 的指标）
2. Verify Layer 2 单次 prompt 大小 ≤ 10K tokens（通过日志可观测）
3. Verify pass rate 保持 ≥ 50%（无回归）
4. Implement pass rate 保持 ≥ 95%（无回归）
5. `build_project_context()` 仍只调用一次并共享，无重复构建

### 验收方式
- 运行 `pytest` + `ruff check` 全部通过
- 检查 `_compact_context_in_history` 在 turn > 3 时正确替换历史消息中的 context 块
- 检查 Verify Layer 2 prompt 中 diff ≤ 5000 chars，长 design/tasks 被摘要替换
- 检查 enrich 并行池中只有首个 agent 接收完整 context
- 通过日志或 debug 输出确认 prompt token 使用量下降

## 约束

### 不能修改的文件
- `zsiga/__main__.py`（入口文件）
- `zsiga/daemon.py`（调度逻辑）
- `zsiga/pipeline/proposal_gate.py`（审批逻辑）
- `build_project_context()` 所在文件的构建逻辑本身
- `site/dashboard.html`（前端）

### 项目部署分支
main

### 已知风险
- **Context 压缩可能破坏消息解析**：如果 LLM 依赖历史消息中的完整 `## 项目代码上下文` 段落来理解后续指令，替换为引用后可能导致幻觉或指令跟随失败。缓解：仅在 turn > 3 后压缩，且保留最新轮的完整上下文。
- **Verify Layer 2 裁剪过度**：diff 从 15K 降至 5K 可能丢失关键变更细节，导致 verify 误判。缓解：Layer 1 已机械验证 testable 场景，Layer 2 仅需判断 completeness。
- **并行池去重影响探索质量**：非首 agent 仅获 500 chars 摘要，可能降低探索覆盖度。缓解：按 proposal 逐一观察 enrich 质量，必要时调整摘要长度。
- **三个变更耦合风险**：同时上线三项优化，若出现回归难以定位。缓解：按 Change 1 → Change 2 → Change 3 顺序逐步上线，每步验证。

### 预估 token 消耗
- prompt: ~12000
- completion: ~6000
- 数据来源: 无历史参考（基于 3 个中等复杂度变更 + 测试的估算）
