# Proposal: Fix Review Sub-Agent Not Calling write_file Tool

## Summary

Review 子代理虽然已有 `write_file` 工具（已在上一轮修复），但 **不调用它**。LLM 将 review 内容直接输出在回复文本中，没有调用 `write_file` 工具写入 `{change_dir}/review.md`。导致 `parse_review_verdict` 读不到文件，永远返回 UNKNOWN。

## Evidence

1. `roles.py` 已正确配置：`Role.REVIEW` 的 `allowed_tools` 包含 `"write_file"` ✅
2. 但 `find openspec/changes/archive/ -name "review.md"` 返回 **0 个文件** ❌
3. 最近 3 次 review（ID=160, 161, 162）全部 verdict=UNKNOWN，seconds 在 9-13s
4. sub-agent 的 `SubAgentResult.content` 中确实包含 review 文本，但没有落盘

## Root Cause

`reviewer.py` 的 `run_review()` 中 prompt 说了"将结果写入 {change_dir}/review.md"，但 LLM 选择在回复文本中直接输出内容，**没有调用 write_file 工具**。这是 prompt 引导不足的问题。

## Requirements

### 1. 优化 review prompt（主要修复）
- 文件：`zsiga/agent/reviewer.py`
- 当前 prompt 说"将结果写入 {change_dir}/review.md"
- 改为明确要求 **必须调用 write_file 工具** 来写入文件，例如：
  > "你必须调用 write_file 工具将 review.md 写入 {change_dir}/review.md。不要只在回复文本中输出内容。"
- 参考 `_REVIEW_PROMPT`（在 `roles.py` 中）和 `run_review()` 的 `user_prompt`，两处都需要确保指令一致

### 2. 添加防御性兜底（次要修复）
- 文件：`zsiga/agent/reviewer.py`
- 在 `run_review()` 返回 `SubAgentResult` 后，检查 review.md 是否存在
- 如果文件不存在但 `SubAgentResult.content` 中包含 `Verdict:` 格式的文本，自动将内容写入 `{change_dir}/review.md`
- 这不是默认路径，只是防御性编程——理想情况下 sub-agent 应该自己完成写入

### 3. 验证
- 修复后 review.md 能被正确创建
- `parse_review_verdict` 能解析出 CLEAN 或 ISSUES_FOUND

### 4. 不要改动
- 不要修改 `roles.py` 的 `allowed_tools`（已正确）
- 不要修改 `parse_review_verdict` 的逻辑
- 不要修改 metrics 记录逻辑

## Constraints
- Scope: project=zsiga
- 关键文件：`zsiga/agent/reviewer.py`（prompt 优化 + 兜底写入）
- 运行 pytest 确认不破坏现有测试
