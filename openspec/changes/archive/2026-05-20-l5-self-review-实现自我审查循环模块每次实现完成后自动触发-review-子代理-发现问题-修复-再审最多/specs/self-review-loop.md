# Self-Review Loop

## ADDED Requirements

### REQ-SR-01: Post-Implementation Review Loop

系统 SHALL 在 IMPLEMENT 阶段完成后、VERIFY 阶段之前，自动触发自我审查循环。

审查循环的流程为：
1. 派发 review-role 子代理，审查实现代码与 specs/design/tasks 的一致性
2. 解析 review.md 获取 Verdict 和 Issues 列表
3. 若 Verdict 为 CLEAN，审查循环结束
4. 若 Verdict 为 ISSUES_FOUND 且存在 CRITICAL 级别问题，系统 SHALL 尝试自动修复
5. 修复完成后重新触发审查（回到步骤 1）
6. 最多执行 N 轮（由 `pipeline.review_max_rounds` 配置，默认 2）

#### Scenario: Clean implementation passes review immediately

```
Given 一个 change 已通过 IMPLEMENT 阶段
  And specs 包含 3 条 requirement
  And 实现代码正确覆盖所有 3 条 requirement
When 系统触发自我审查循环
Then review 子代理 SHALL 生成 review.md，内容包含 "Verdict: CLEAN"
  And 审查循环 SHALL 在第 1 轮结束
  And 系统继续进入 VERIFY 阶段
```

#### Scenario: Critical issue found and auto-fixed in first round

```
Given 一个 change 已通过 IMPLEMENT 阶段
  And 实现代码存在一处 CRITICAL 级别质量问题（如缺失错误处理）
When 系统触发自我审查循环
Then review 子代理 SHALL 生成 review.md，内容包含 "Verdict: ISSUES_FOUND"
  And issues 列表中包含至少 1 条 CRITICAL 问题描述
  And 系统 SHALL 派发 fix agent 自动修复 CRITICAL 问题
  And 修复后 SHALL 重新触发审查（第 2 轮）
When 第 2 轮审查结果为 CLEAN
Then 审查循环 SHALL 在第 2 轮结束
  And 系统继续进入 VERIFY 阶段
```

#### Scenario: Issues persist after max rounds

```
Given 一个 change 已通过 IMPLEMENT 阶段
  And 实现代码存在持续性问题
  And pipeline.review_max_rounds 配置为 2
When 审查循环执行 2 轮后 Verdict 仍为 ISSUES_FOUND
Then 审查循环 SHALL 停止
  And 系统 SHALL 记录审查结果到 metrics（PhaseRecord phase=REVIEW）
  And 系统 SHALL 继续进入 VERIFY 阶段（不因 review 问题而 revert）
```

#### Scenario: SUGGESTION-only issues do not trigger fix

```
Given 一个 change 已通过 IMPLEMENT 阶段
  And review 子代理返回 Verdict: ISSUES_FOUND
  And 所有 issues 均为 SUGGESTION 级别（无 CRITICAL）
When 系统解析审查结果
Then 系统 SHALL 视为审查通过（等同于 CLEAN）
  And 审查循环 SHALL 在当前轮结束
  And 系统 SHALL 在 metrics 中记录存在 SUGGESTION 级别建议
  And 系统继续进入 VERIFY 阶段
```

### REQ-SR-02: Review Fix Agent

当审查发现 CRITICAL 级别问题时，系统 SHALL 派发修复代理自动修复。

修复代理 SHALL 遵循以下约束：
- 只修改本次变更引入的文件（与 _fix_loop 相同的 changed_files 约束）
- 不添加新路由、新端点、新功能
- 修复后 SHALL 运行 ruff check 确认无 lint 错误
- 每轮修复最多使用 `pipeline.review_fix_max_turns` 轮（默认 6）

#### Scenario: Fix agent resolves critical issue

```
Given 审查返回 1 个 CRITICAL issue: "函数 foo() 缺少 None 检查"
  And pipeline.review_fix_max_turns 配置为 6
When 系统派发修复代理
Then 修复代理 SHALL 只修改包含 foo() 的文件
  And 修复代理 SHALL 添加 None 检查
  And 修复完成后 ruff check SHALL 通过
  And 系统触发重新审查
```

#### Scenario: Fix agent fails but review loop continues gracefully

```
Given 审查返回 1 个 CRITICAL issue
  And 修复代理执行后 ruff check 仍然失败
When 修复代理耗尽 max_turns
Then 系统 SHALL 记录修复失败
  And 审查循环 SHALL 继续计为当前轮次
  And 若未达到 max_rounds，SHALL 进入下一轮审查
  And 若已达到 max_rounds，SHALL 结束审查循环并继续 VERIFY
```

### REQ-SR-03: Review Metrics Recording

系统 SHALL 在 metrics 中记录审查阶段的执行情况。

每次审查循环完成时，系统 SHALL 生成一个 PhaseRecord：
- `phase` SHALL 为 `Phase.REVIEW`
- `outcome` SHALL 为 `Outcome.SUCCESS`（当最终 Verdict 为 CLEAN 或仅 SUGGESTION）
- `outcome` SHALL 为 `Outcome.FAIL`（当达到 max_rounds 仍有 CRITICAL 问题）
- `seconds_used` SHALL 记录审查循环总耗时
- `fix_attempts` SHALL 记录修复尝试次数
- `detail` SHALL 包含审查发现的问题摘要（最多 200 字符）

#### Scenario: Metrics recorded for successful review

```
Given 审查循环在第 1 轮返回 CLEAN
When 系统记录 metrics
Then PhaseRecord.phase SHALL 为 "review"
  And PhaseRecord.outcome SHALL 为 "success"
  And PhaseRecord.fix_attempts SHALL 为 0
```

#### Scenario: Metrics recorded for multi-round review with fixes

```
Given 审查循环执行 2 轮
  And 第 1 轮发现 CRITICAL issue 并成功修复
  And 第 2 轮返回 CLEAN
When 系统记录 metrics
Then PhaseRecord.phase SHALL 为 "review"
  And PhaseRecord.outcome SHALL 为 "success"
  And PhaseRecord.fix_attempts SHALL 为 1
```

### REQ-SR-04: Review Configuration

审查行为 SHALL 通过 `zsiga.yaml` 的 `pipeline` 段配置。

配置项 SHALL 包括：
- `review_max_rounds`: 审查循环最大轮数（默认 2，最小 1，最大 5）
- `review_max_turns`: 每轮审查子代理最大 tool 调用轮数（默认 10）
- `review_timeout`: 每轮审查超时秒数（默认 180）
- `review_fix_max_turns`: 修复代理每轮最大 tool 调用轮数（默认 6）

系统 SHALL 在 `review_max_rounds` 超出 [1, 5] 范围时发出 config warning。

#### Scenario: Default configuration values

```
Given zsiga.yaml 未配置 review 相关参数
When 系统加载配置
Then pipeline.review_max_rounds SHALL 为 2
  And pipeline.review_max_turns SHALL 为 10
  And pipeline.review_timeout SHALL 为 180
  And pipeline.review_fix_max_turns SHALL 为 6
```

#### Scenario: Out-of-range review_max_rounds triggers warning

```
Given zsiga.yaml 配置 pipeline.review_max_rounds 为 10
When 系统加载配置
Then config validation SHALL 产生 warning
  And warning 信息 SHALL 包含 "review_max_rounds"
```
