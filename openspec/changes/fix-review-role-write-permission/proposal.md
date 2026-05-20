# Proposal: Fix Review Role — Sub-Agent Cannot Write review.md

## Summary

Review 阶段 100% 失败的根因是：review 子代理的角色配置为 read-only（`allowed_tools` 不含 `write_file`），但 `reviewer.py` 的 prompt 要求子代理将审查结果写入 `{change_dir}/review.md`。

子代理没有写文件的工具，因此 review.md 从未被创建。`parse_review_verdict` 读不到文件，永远返回 `("UNKNOWN", [])`，导致 31+ 次 review 全部失败。

## Evidence

1. `zsiga/agent/roles.py` 中 `Role.REVIEW` 的 `allowed_tools` 列表：
   ```
   ["bash", "read_file", "search", "list_files", "ast_search", "goto_definition", "find_references", "diagnostics"]
   ```
   不包含 `"write_file"` 或 `"edit_file"`

2. `zsiga/agent/reviewer.py` 的 `run_review()` 中 prompt 明确要求：
   > "将结果写入 {change_dir}/review.md"

3. `run_sub_agent()` 中 `_filter_tools_by_role()` 会过滤掉所有不在 `allowed_tools` 中的工具，所以子代理根本没有 `write_file` 可用。

4. 实际结果：`find openspec/changes/ -name "review.md"` 返回 0 个文件。31 次 review 全部 verdict=UNKNOWN。

## Root Cause

**`roles.py` Role.REVIEW 的 `allowed_tools` 缺少 `write_file`。**

子代理收到"写 review.md"的指令但没有写文件工具，无法完成任务。

## Requirements

1. **在 `Role.REVIEW` 的 `allowed_tools` 中添加 `"write_file"`**
   - 文件：`zsiga/agent/roles.py`
   - 只加 `write_file`，不加 `edit_file`（review 只需写新文件，不应修改已有实现文件）

2. **验证修复有效**
   - 修复后确认 review.md 能被正确创建
   - 确认 parse_review_verdict 能解析出 CLEAN 或 ISSUES_FOUND（而非 UNKNOWN）

3. **不要改动其他角色（EXPLORE/IMPLEMENT/DIAGNOSER）**
4. **不要改动 reviewer.py 的 prompt 逻辑**
5. **不要改动 metrics 记录逻辑**（已由上一个 proposal 修复）

## Constraints
- Scope: project=zsiga
- 关键文件：`zsiga/agent/roles.py`（一行修改）
- 运行 pytest 确认不破坏现有测试
