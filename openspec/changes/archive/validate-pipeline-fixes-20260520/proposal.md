# Proposal: validate-pipeline-fixes-20260520

## Summary
本次 proposal 是一个验证性任务，用于验证近期 pipeline 基础设施修复是否生效。需修改一个简单的功能点，触发完整 pipeline（CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER），观察每个阶段的 outcome。

## Motivation
近期修复了多个 pipeline bug：
1. Review 兜底写入（移除 regex gate）
2. Verify STALE_LIMIT（prompt 强制 write_file + stale_limit 5→10）
3. CLARIFY 独立阶段（需求工程）
4. OPTIMIZE 独立阶段（规范对齐）
5. REFLECT 阶段（daemon 重启后生效）

需要一次真实运行来验证所有修复。

## Expected Behavior
在 dashboard 的 Phase Performance 表格中，新增 CLARIFY、ENRICH、OPTIMIZE 三行统计数据。当前 dashboard 只展示已有数据的 phase，需要确保 `_phase_table` 能正确展示新阶段。

具体任务：
1. 在 `metrics/dashboard.py` 的 `_phase_table` 函数中，确认 Phase 枚举的所有值都能出现在表格中（即使没有数据也展示为 0）
2. 在 dashboard 页面标题下方加一行小字显示 pipeline 完整流程：`CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`

## Constraints
- Scope: project=zsiga
- 只修改 `zsiga/metrics/dashboard.py` 和 `site/dashboard.html`
- 不要改动 pipeline 核心逻辑
