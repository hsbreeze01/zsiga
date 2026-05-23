# Proposal: fix-learnings-noise-and-inject

## Summary
清理 learnings 噪声（空文本记录），加校验防止未来噪声，并将有效 learnings 注入到 IMPLEMENT 和 ENRICH 阶段的 prompt 中，接通"学习→反馈"闭环。

## Motivation
当前 learnings.jsonl 有 81 条记录，其中 30% 是 `daemon.cycle_error` 空文本噪声。更关键的是，即使有效 learnings 也从未被注入到任何 agent 的 prompt 中——zsiga "会学但不会用"。

这导致：
1. 反复犯相同类型的错误（如 `pipeline.fail.implement` 出现 6 次）
2. 成功经验（如 `pipeline.pass.deliver: 17` 条）无法复用
3. 反思→学习闭环断裂在最后一步

## Expected Behavior

### 1. Learnings 写入校验
修改 `reflector.py` 或相关的 learnings 写入函数，在 `record_lesson()` / 写入 learnings.jsonl 时：
- 如果 `text` 字段为空或长度 < 10 字符，跳过不记录
- 如果 `pattern_key` 以 `daemon.cycle_error` 开头，跳过不记录（这些是 daemon 崩溃信号，不是可学习经验）
- 记录被跳过的条目数到日志（DEBUG 级别）

### 2. 一次性清理现有噪声
新增函数或脚本，扫描 `memory/learnings.jsonl`：
- 删除 text 为空的记录
- 删除 pattern_key 为 `daemon.cycle_error` 或 `code.unknown` 的记录
- 保留其余所有记录
- 写回 learnings.jsonl
- 同时清理 DB lessons 表中的对应记录（按 pattern_key 匹配）

### 3. Learnings 注入 IMPLEMENT prompt
修改 `implementer.py`（或其 system prompt 构建函数）：
- 在构建 system prompt 时，从 learnings.jsonl 读取最近 5 条与当前 change 相关的 learnings
- "相关"定义：pattern_key 包含当前 change_name 的关键词，或属于通用的 `pipeline.fail.*` / `pipeline.pass.*` 类别
- 以 `## Previous Learnings (avoid repeating mistakes)` 为 section header 注入
- 每条 learning 格式：`- [{pattern_key}] {text}`
- 如果无相关 learnings，不注入任何内容（不浪费 context window）

### 4. Learnings 注入 ENRICH prompt
修改 `enricher.py`（或其 system prompt 构建函数）：
- 与 IMPLEMENT 相同的注入逻辑
- Section header: `## Relevant Past Experience`
- 最多注入 3 条（ENRICH 的 context 更紧凑）

## Success Criteria
- `daemon.cycle_error` 类型的 learnings 不再被记录
- 现有 learnings.jsonl 中空文本记录被清除
- IMPLEMENT 阶段的 system prompt 中出现 `## Previous Learnings` section（当有相关 learnings 时）
- ENRICH 阶段的 system prompt 中出现 `## Relevant Past Experience` section（当有相关 learnings 时）
- 全套 pytest 通过（无新增失败）
