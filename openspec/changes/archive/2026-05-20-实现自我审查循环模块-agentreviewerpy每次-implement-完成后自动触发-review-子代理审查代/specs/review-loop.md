# Self-Review Loop

## Overview

每次 implement 完成后，系统 SHALL 自动触发 review 子代理审查实现代码的质量和与 specs 的一致性。发现 CRITICAL 问题则修复后再审，最多 2 轮。review 结果记录到 metrics。

---

## ADDED Requirements

### Requirement: Review Sub-Agent Dispatch

每次 implement phase 成功完成后，系统 SHALL 自动调度一个 review-role 子代理。该子代理 SHALL：
- 使用只读工具（bash、read_file、search、list_files、ast_search、goto_definition、find_references、diagnostics）
- 接收完整的 specs、design.md、tasks.md 和 git diff 作为输入
- 逐条检查每条 spec 要求是否在 diff 中被覆盖
- 检查常见代码质量问题（死代码、缺失错误处理、命名规范）
- 将审查结果写入 `{change_dir}/review.md`

#### Scenario: Implement succeeds, review dispatched automatically

- **Given** 一个 change 的 implement phase 已成功完成（mechanical verification passed）
- **And** `pipeline.review_max_rounds` > 0
- **When** orchestrator 进入 Phase 2.5
- **Then** 系统 SHALL 调度一个 review-role 子代理
- **And** 子代理接收 specs、design、tasks、git diff 作为上下文
- **And** 子代理最多运行 `review_max_turns` 轮（默认 10）
- **And** 子代理超时为 `review_timeout` 秒（默认 180）

#### Scenario: Review disabled via config

- **Given** `pipeline.review_max_rounds` = 0
- **When** orchestrator 完成 implement phase
- **Then** 系统 SHALL 跳过 review phase，直接进入 verify phase

---

### Requirement: Review Verdict Format

review.md SHALL 使用固定格式输出审查结论，以便程序化解析。

#### Scenario: All specs covered, no quality issues

- **Given** review 子代理完成审查
- **And** 所有 spec 要求均被 diff 覆盖
- **And** 未发现代码质量问题
- **When** review.md 被写入
- **Then** review.md 的第一行有效 Verdict 行 SHALL 为 `Verdict: CLEAN`
- **And** 不包含任何 Issues 列表

#### Scenario: Issues found during review

- **Given** review 子代理完成审查
- **And** 发现未被覆盖的 spec 要求或代码质量问题
- **When** review.md 被写入
- **Then** review.md SHALL 包含 `Verdict: ISSUES_FOUND`
- **And** 每个 issue SHALL 标记严重程度 `[CRITICAL]` 或 `[SUGGESTION]`
- **And** 每个 issue SHALL 包含描述和代码证据

---

### Requirement: Verdict Parsing

系统 SHALL 能可靠解析 review.md 中的 verdict 和 issues 列表。

#### Scenario: Parse CLEAN verdict

- **Given** review.md 内容包含 `Verdict: CLEAN`
- **When** `parse_review_verdict` 被调用
- **Then** 返回 verdict = `"CLEAN"`, issues = `[]`

#### Scenario: Parse ISSUES_FOUND with mixed severities

- **Given** review.md 内容包含 `Verdict: ISSUES_FOUND` 及多条 issue
- **When** `parse_review_verdict` 被调用
- **Then** 返回 verdict = `"ISSUES_FOUND"`
- **And** issues 列表中每项 SHALL 包含 `severity` 和 `description` 字段
- **And** severity 值 SHALL 为 `"CRITICAL"` 或 `"SUGGESTION"`

#### Scenario: review.md missing or malformed

- **Given** review.md 不存在或未包含 `Verdict:` 行
- **When** `parse_review_verdict` 被调用
- **Then** 返回 verdict = `"UNKNOWN"`, issues = `[]`

---

### Requirement: Fix-and-Re-Review Loop

当 review 发现 CRITICAL 问题时，系统 SHALL 尝试修复后重新审查，最多 `review_max_rounds` 轮。

#### Scenario: CRITICAL issue triggers fix and re-review

- **Given** review 第一轮发现 CRITICAL issue
- **When** `run_review_loop` 执行
- **Then** 系统 SHALL 调用主 agent 执行修复
- **And** 修复 agent SHALL 只修改本次变更引入的文件
- **And** 修复 agent SHALL 只修复 CRITICAL 问题，不添加新功能
- **And** 修复完成后 SHALL 再次调度 review 子代理审查
- **And** 总轮数 SHALL 不超过 `review_max_rounds`（默认 2）

#### Scenario: SUGGESTION-only issues treated as pass

- **Given** review 发现仅 SUGGESTION 级别问题（无 CRITICAL）
- **When** `run_review_loop` 处理该轮结果
- **Then** 系统 SHALL 视为 CLEAN（不触发修复）

#### Scenario: Max rounds exhausted with remaining issues

- **Given** review loop 已执行 `review_max_rounds` 轮
- **And** 仍存在 CRITICAL issue
- **When** `run_review_loop` 返回
- **Then** `final_verdict` SHALL 为 `"ISSUES_FOUND"`
- **And** `had_critical` SHALL 为 `True`
- **And** pipeline SHALL 继续进入 verify phase（review 不 block 整个 pipeline）

---

### Requirement: Review Metrics Recording

review phase 的结果 SHALL 完整记录到 metrics 系统。

#### Scenario: Review phase recorded in ChangeRecord

- **Given** review phase 完成（无论 verdict 如何）
- **When** orchestrator 记录 phase 结果
- **Then** SHALL 添加一个 `PhaseRecord`，其中 `phase=Phase.REVIEW`
- **And** `outcome` SHALL 为 `Outcome.SUCCESS`（CLEAN）或 `Outcome.FAIL`（ISSUES_FOUND/UNKNOWN）
- **And** SHALL 记录 `seconds_used`、`fix_attempts`、`detail`（issues 摘要）

#### Scenario: Review stats computed alongside other phases

- **Given** metrics collector 计算统计数据
- **When** `compute_stats` 被调用
- **Then** `phase_stats` SHALL 包含 `"review"` key（与 enrich/implement/verify/delayed 并列）
- **And** review stats SHALL 包含 count、pass_rate、avg_seconds、total_fixes 等指标

---

### Requirement: Review Lesson Recording

review 发现的问题 SHALL 作为经验教训记录，供未来会话参考。

#### Scenario: Review found critical issues — lesson recorded

- **Given** review loop 完成
- **And** `had_critical` 为 `True`
- **When** orchestrator 完成该 change（无论最终成功或失败）
- **Then** 系统 SHALL 调用 `record_lesson` 记录 review 发现的问题
- **And** `pattern_key` SHALL 为 `"pipeline.review.critical"` 
- **And** takeaway SHALL 包含 CRITICAL issue 的描述摘要

---

### Requirement: Review System Prompt Consistency

review 子代理使用的 system prompt SHALL 与 `parse_review_verdict` 期望的输出格式一致。

#### Scenario: Review prompt and parser aligned

- **Given** review 子代理的 system prompt 指导输出格式
- **When** review.md 被写入并被解析
- **Then** system prompt SHALL 指示使用 `Verdict: CLEAN|ISSUES_FOUND` 格式
- **And** `REVIEW_SYSTEM` prompt（reviewer.py 中定义）SHALL 作为 review 子代理的实际 system prompt
- **And** roles.py 中的 `_REVIEW_PROMPT` SHALL 与 `REVIEW_SYSTEM` 保持格式一致
