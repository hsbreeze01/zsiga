# Tasks: Self-Review Loop Module

## 1. Review Prompt Alignment & Dead Code Cleanup

- [x] 1.1 更新 `zsiga/agent/roles.py` 中 `_REVIEW_PROMPT`，使其输出格式为 `Verdict: CLEAN|ISSUES_FOUND` + Issues 列表（对齐 `parse_review_verdict()` 期望的格式），同时保持只读工具限制和 8 轮上限
- [x] 1.2 清理 `zsiga/agent/reviewer.py` 中未使用的 `REVIEW_SYSTEM` 常量（删除该常量定义）

## 2. Metrics Stats 补全

- [x] 2.1 在 `zsiga/metrics/collector.py` 的 `compute_stats()` 函数中，将 `phase_stats` 循环的 phase 列表从 `["enrich", "implement", "verify", "deliver"]` 扩展为 `["enrich", "implement", "review", "verify", "deliver"]`，使 review phase 的统计数据（count、pass_rate、avg_seconds、total_fixes）被正确计算

## 3. Review Lesson Recording

- [x] 3.1 在 `zsiga/pipeline/orchestrator.py` 的 Phase 2.5 REVIEW 块中，当 `review_result.had_critical` 为 `True` 时，调用 `record_lesson()` 记录审查发现的问题摘要（`pattern_key="pipeline.review.critical"`，takeaway 包含 CRITICAL issue 描述）

## 4. Reviewer Unit Tests

- [x] 4.1 创建 `tests/test_reviewer.py`，包含以下测试用例：`parse_review_verdict` 解析 CLEAN / ISSUES_FOUND / UNKNOWN 三种 verdict；解析带 CRITICAL 和 SUGGESTION 的混合 issues 列表；`_has_critical` 检测；`_build_fix_prompt` 输出格式验证；`ReviewLoopResult` dataclass 默认值验证
