## Verdict: PUSHBACK

## 我的判断

这个 proposal 描述的两个 bug 在概念上是合理的——LLM 确实可能输出非标准格式的 tool call，预算跨阶段累积也确实会造成级联失败。**但问题在于：proposal 描述的代码结构与实际代码库严重不符。** `TokenBudget._used`、`self.tool_funcs`、`reset_budget`、`design_gate_max_retries`——这些核心符号在代码库中全部不存在。proposal 中引用的行号（223、689、759 等）也无法验证。我无法批准一个基于对代码错误理解的变更。在动手之前，proposal 必须先证明这些 bug 真实存在于当前代码中，而不是基于想象中的代码结构。

## 评分详情
- **可行性: 1/2** — 目标文件 `zsiga/agent/loop.py`(305行) 和 `zsiga/pipeline/orchestrator.py`(2188行) 确实存在。但 proposal 引用的核心符号 `TokenBudget._used`、`self.tool_funcs`、`reset_budget`、`design_gate_max_retries` 在确定性事实中均标记为 ❌ 不存在。实际存在的只有 `budget.try_extend("productive")`(loop.py:208) 和 `_extract_calls`/`_extract_tokens`(orchestrator.py)。代码结构认知与实际不符。
- **可执行性: 1/2** — 提供了具体的文件名、函数名设计（`_extract_tool_calls_from_content`）和代码片段，方向明确。但实现路径依赖多个不存在的符号（如 `self.tool_funcs` 用于安全校验、`TokenBudget._used` 用于计数器重置），实际落地时需要在代码中重新定位对应逻辑。行号引用无法验证。
- **能力匹配: 1/2** — 无近期同类任务（tool call 解析、预算管理）的成功或失败记录。唯一的历史教训是 daemon cycle 的 duplicate column 错误，与此无关。
- **历史风险: 2/2** — 无相关失败记录。历史教训中的 `daemon cycle #1` 是数据库 schema 问题，与 tool call 解析和预算管理完全无关。
- **范围合理性: 1/2** — Scope 声明清晰（两个独立 fix），in/out of scope 边界明确。但修改的是 `zsiga/agent/loop.py` 和 `zsiga/pipeline/orchestrator.py`——这是 pipeline/agent 自身核心代码，按特殊规则上限为 1。此外，核心改动路径（loop.py 的 agent 循环）**没有任何测试覆盖**（Scout #2 确认不存在 test_loop.py），对如此高影响模块做改动风险极大。
- **总分: 6/10**

## 疑虑
1. **核心符号不存在，bug 可能是虚构的。** Proposal 的 Bug 2 核心依赖 `TokenBudget._used` 累积计数——但确定性事实显示 `_used` ❌ 不存在。Bug 1 的安全校验依赖 `self.tool_funcs`——同样 ❌ 不存在。proposal 描述的可能是一个想象中的代码架构，而非当前代码库的真实问题。在不确定 bug 是否真实存在的情况下贸然修改 agent loop，后果可能是引入真正的 bug。
2. **零测试覆盖 + 核心模块 = 高回归风险。** Scout #2 确认 `zsiga/agent/loop.py` 没有对应的测试文件，tool call fallback 和 budget reset 均无测试覆盖。Analyst 也指出所有相关测试覆盖为 ❌。对 305 行的 agent 主循环做改动，没有安全网。
3. **行号引用不可验证。** Proposal 精确引用了 loop.py:223、orchestrator.py:689/759/897/1128 等行号，但确定性事实中没有提供这些行的内容验证。如果行号与实际代码不对应，实现指导就是误导。

## 建议
1. **先验证 bug 是否真实存在。** 读取 `zsiga/agent/loop.py` 完整代码，确认：(a) tool call 解析的确切逻辑——当 `msg.tool_calls` 为空时实际发生了什么；(b) 预算管理的真实数据结构——`budget` 对象的真实属性和方法（不是假想的 `_used`）。基于实际代码重新描述 bug。
2. **补充测试后再改动。** 在修改 loop.py 之前，先为当前行为写测试：(a) 正常 JSON tool call 路径的 baseline 测试；(b) 空 tool_calls + 内容中包含 XML 的场景测试（确认当前行为是返回 content 还是报错）；(c) budget 跨 phase 传递的集成测试。有测试保护后再做变更。
3. **用确定性事实中的真实符号重写 Technical Design。** 将 `_used` 替换为实际的预算追踪属性（需从代码中确认）；将 `self.tool_funcs` 替换为实际的工具注册机制（需从代码中确认）；将 `reset_budget()` 替换为基于实际 budget 类 API 的 reset 方案。

## 历史参考
- （无直接相关的失败记录。daemon cycle #1 的 duplicate column 问题是 schema 层面的，与此 proposal 无关。）
