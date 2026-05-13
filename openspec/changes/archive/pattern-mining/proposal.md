# Proposal: 跨会话模式挖掘

## 背景
zsiga 的记忆系统（`memory/learnings.jsonl`）已积累 28 条经验，7 个 pattern_key。其中 `pipeline.pass.deliver` 17 次、`pipeline.fail.implement` 6 次。但当前 `memory/context.py` 只做简单的全文拼接，没有从历史数据中自动提取重复模式并生成避坑建议的能力。

## 目标
创建 `memory/pattern_miner.py`，从 `learnings.jsonl` 中提取出现 ≥3 次的 pattern_key，生成结构化的避坑建议，并自动注入到 `active_context.md` 中。让 zsiga 在每次 pipeline 运行前自动看到自己的历史模式。

## 方案
1. `memory/pattern_miner.py`：
   - `mine_patterns(min_occurrences=3)` — 读取 learnings.jsonl，按 pattern_key 分组统计，返回出现次数 ≥ min_occurrences 的模式列表
   - 每个模式包含：key、count、最近 3 条 lesson 的 takeaway、严重程度（pass→低、fail→高）
   - `generate_warnings(patterns)` — 将模式列表转换为 `active_warnings` 文本块
2. 修改 `memory/context.py` 的 `build_active_context()` — 调用 pattern_miner，将 warnings 注入到 active_context 末尾
3. 编写测试 `tests/test_pattern_miner.py`

## 预期行为
- `mine_patterns()` 返回 `pipeline.pass.deliver`（17次，低严重度）和 `pipeline.fail.implement`（6次，高严重度）
- `build_active_context()` 生成的文本中包含类似 "⚠️ pipeline.fail.implement 出现 6 次：注意实现阶段的常见陷阱" 的警告
- 不破坏现有 active_context 注入逻辑

## 范围
- 新增 `memory/pattern_miner.py`
- 修改 `memory/context.py`（追加 warnings 段）
- 新增 `tests/test_pattern_miner.py`
- 不修改 `memory/learn.py`（记录端不变）
- 不修改任何 pipeline 逻辑

## 约束
- 使用标准库（json、collections.Counter），不引入新依赖
- pattern_miner 的输出是纯文本，便于注入到 system prompt
- 严重度判断：pattern_key 包含 "fail" → high，"pass" → low，其他 → medium
