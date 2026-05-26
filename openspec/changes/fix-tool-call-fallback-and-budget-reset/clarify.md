# clarify.md — fix-tool-call-fallback-and-budget-reset

## 需求拆解

### 原始需求
修复两个关键 pipeline bug：(1) LLM 偶尔输出 XML 格式 tool call 而非 JSON，导致 sub-agent 静默失败（Judge 无法读取 spec → 虚假 FAIL verdict → ENRICH 浪费多轮重试）；(2) TokenBudget 跨 phase 不重置，ENRICH 超预算后所有后续 phase 立即返回 BUDGET_EXCEEDED，级联失败浪费 ~30 分钟。

### 拆解后的子任务

- [ ] 1. **XML/inline tool call 回退解析器** — 在 `zsiga/agent/loop.py` 新增 `_extract_tool_calls_from_content()` 函数，解析三种非标准 tool call 格式（XML `<invoke>` 标签、内联 JSON 对象、markdown code block JSON），并在 `msg.tool_calls` 为空时尝试从 content 提取并执行已注册的工具，记录 warning 日志 (预估复杂度：高, 预估 token：~8000 / 无历史参考)
- [ ] 2. **回退解析器集成到 AgentLoop 转循环** — 修改 `loop.py` ~L223 的早返回逻辑：当 `msg.tool_calls` 为空且 fallback 提取成功时，执行提取的工具调用并继续 turn loop 而非直接 return RunResult；提取失败才视为最终响应返回 (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 3. **Phase 级 budget 重置** — 在 `zsiga/pipeline/orchestrator.py` 的 ENRICH（~L689）、ENRICH retry（~L759）、IMPLEMENT（~L897）、VERIFY（~L1128）四处 `agent.run()` 调用前，重置 `TokenBudget` 为全新实例，确保每个 phase 从零开始计数 (预估复杂度：低, 预估 token：~3000 / 无历史参考)
- [ ] 4. **BUDGET_EXCEEDED 结果正确记录** — 在 orchestrator 各 phase 调用后检查 `result.content == "BUDGET_EXCEEDED"`，将 outcome 从 `Outcome.SUCCESS` 修正为 `Outcome.FAIL`，并记录明确的 warning 日志 (预估复杂度：低, 预估 token：~3000 / 无历史参考)
- [ ] 5. **测试覆盖** — 为两个修复分别编写测试：XML fallback 解析器单元测试（覆盖三种格式 + 安全边界：只执行已注册工具）、budget 重置集成测试（验证 phase 间计数器归零）、BUDGET_EXCEEDED outcome 记录测试 (预估复杂度：中, 预估 token：~6000 / 无历史参考)

## 边界

### IN scope
- `zsiga/agent/loop.py` 中新增 fallback parser 函数及 turn loop 分支逻辑修改
- `zsiga/pipeline/orchestrator.py` 中四处 phase 调用前 budget 重置 + 结果 outcome 修正
- 对应的测试文件（新建或追加）
- Fallback parser 安全约束：只执行 `self.tool_funcs` 中已注册的工具

### OUT of scope
- 更换 LLM 模型或修改 LLM 调用参数（如 temperature、max_tokens）
- 修改工具定义（tool schema / function signature）
- 调整 budget 阈值数值
- 修改 `TokenBudget` 类本身的实现（如改变计数逻辑）
- 改动 `RunResult` 数据结构

### 依赖的外部条件
- `zsiga/agent/loop.py` 和 `zsiga/pipeline/orchestrator.py` 文件存在且结构与 proposal 描述一致（行号 ~L223, ~L689, ~L759, ~L897, ~L1128 需实际验证）
- `TokenBudget` 类具有可重置的接口（如重新构造或 `reset()` 方法）
- `msg.tool_calls` 字段的类型和行为与 OpenAI API `tool_calls` 兼容
- `self.tool_funcs` 在 AgentLoop 实例上可访问，用于 fallback 安全校验

## 目标

### 成功标准
1. LLM 输出 XML 格式 tool call 时，工具仍被执行（日志出现 "fallback tool call parsed" warning）
2. LLM 输出 XML 格式 tool call 时，turn loop 继续（不提前 return）
3. 每个 phase 启动时 token budget 计数器归零（无跨 phase 累积）
4. `BUDGET_EXCEEDED` 在 PhaseRecord 中记录为 `Outcome.FAIL` 而非 `Outcome.SUCCESS`
5. `BUDGET_EXCEEDED` 后 pipeline 记录明确 warning 而非静默继续
6. 现有测试套件全部通过（正常 JSON tool call 路径无回归）
7. Judge sub-agent 使用 XML tool call 时仍能产出基于实际 spec 的有效 verdict

### 验收方式
- `pytest tests/` 全绿，含新增 fallback parser 和 budget reset 测试
- `ruff check zsiga/agent/loop.py zsiga/pipeline/orchestrator.py` 无 error
- 手动构造 XML tool call 输入，验证工具被正确提取执行且日志有 warning
- 模拟跨 phase budget 累积场景，验证 ENRICH 后 IMPLEMENT phase budget 归零

## 约束

### 不能修改的文件
- `zsiga/agent/` 目录下除 `loop.py` 外的文件（budget.py 除外，如需新增 reset 方法）
- `zsiga/pipeline/` 目录下除 `orchestrator.py` 外的文件
- 任何 `test_spec_*` 测试文件（历史生成，不可触碰）

### 项目部署分支
- 主开发分支（由 git 当前 HEAD 确定）

### 已知风险
- **行号漂移**：proposal 引用的行号（L223, L689 等）可能已过时，需在实施时用 AST 搜索精确定位插入点
- **XML 格式多样性**：LLM 输出的 XML tool call 格式可能不只 proposal 描述的 `<tool_call_layout>` 一种，fallback parser 需要足够宽松但又不误匹配普通 XML 内容
- **TokenBudget 接口不确定性**：proposal 假设可通过重新构造或 `reset()` 方法重置，但实际类可能需要新增方法
- **高影响范围**：修改 `loop.py` 的 turn loop 核心逻辑，影响所有使用 AgentLoop 的 phase（enrich, implement, verify, review, judge），回归风险高
- **fallback 解析安全**：需严格限制只执行已注册工具，防止解析恶意/误匹配内容执行未授权操作

### 预估 token 消耗
- prompt: ~22000
- completion: ~8000
- 数据来源: 无历史参考（基于 5 个子任务复杂度估算：高 + 中 + 低 + 低 + 中，含测试编写）
