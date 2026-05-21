# Proposal: fix-self-assessment-and-reflector-loop

## Summary
修复 self_assessment 记录缺失问题（当前仅 1 条），确保 REFLECT 阶段每次执行后都写入自评记录；同时为 Reflector 增加 auto-proposal 失败分析能力，避免同一 proposal 反复 VERIFY FAIL。

## Motivation
两个问题：

1. **Self-assessment 几乎为空**：`self_assessment` 表仅 1 条记录。REFLECT 阶段应该每次 change 结束后记录一条自评（成功/失败原因、学到了什么、下次改进方向），但实际没有发生。没有自评数据 = 没有自省历史 = 无法形成"反思→改进"的循环。

2. **Auto-proposal 循环失败**：Reflector 生成的 proposal 在 VERIFY FAIL 后会反复生成几乎相同的 proposal（如 05-21 的 `auto-metric_degradation-*` 连续失败 5+ 次），不分析失败原因也不调整策略。

## Expected Behavior

### 1. Self-assessment 修复
检查 REFLECT 阶段的执行流程：
- 找到 `record_self_assessment()` 函数（或等价函数）
- 确认它是否被 `orchestrator.py` 的 REFLECT 阶段调用
- 如果没有被调用：在 REFLECT 阶段的末尾添加调用
- 如果被调用但没有写入：检查 DB schema 是否匹配、是否有异常被吞掉
- self_assessment 记录应包含：change_name, outcome, reflection_text, lessons_learned, timestamp

### 2. Auto-proposal 失败分析
修改 `reflector.py` 的 `_is_duplicate()` 或新增 `_is_stuck()` 方法：
- 在生成新 proposal 前，检查最近 3 次同名或同 pattern 的 auto-proposal 是否全部 VERIFY FAIL
- 如果是，不再重复生成该 proposal
- 而是在 `openspec/changes/auto-stuck-{pattern_key}-{date}/` 下生成一个 `diagnosis.md`，包含：
  - 失败的 proposal 名称列表
  - 每次 FAIL 的原因（从 changes 表的 phase_records 读取）
  - 建议的人工介入方向
- 该 diagnosis.md 不触发 pipeline 执行，仅供人工查看

### 3. Reflector 历史感知增强
修改 `generate_proposal()` 的 prompt 或模板：
- 在渲染 proposal 模板时，注入该 pattern_key 最近 3 次的 FAIL 原因
- 让生成的 proposal 能够参考历史失败，避免重复相同的策略

## Success Criteria
- REFLECT 阶段执行后，self_assessment 表新增一条记录
- 同一 auto-proposal VERIFY FAIL >=3 次后，不再重复生成
- 生成 `diagnosis.md` 替代重复 proposal
- 全套 pytest 通过
