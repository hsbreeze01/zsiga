# Spec: Pipeline 自诊断钩子

## ADDED Requirements

### Requirement: Decompose 后置验证

当 `decompose()` 返回多于 1 个 subtask 时，orchestrator SHALL 验证每个 subtask 的 `change_dir` 是否在目标项目上存在。验证失败时 SHALL 记录 lesson 并降级为单项目处理。

#### Scenario: change_dir 在目标项目不存在时降级
- GIVEN `decompose()` 返回 2 个 subtask，分别为 project=A 和 project=B
- WHEN project=B 的 transport 上 `change_dir` 不存在（`test -d` 返回非零）
- THEN 系统 SHALL 调用 `record_outcome()` 记录一条 `error_domain="pipeline"`, `root_cause_key="pipeline.decompose.false_positive"` 的 lesson
- AND 系统 SHALL 降级为仅处理 originating_project 的单 subtask
- AND 该 change 的执行 SHALL 继续而非中止

#### Scenario: 所有 subtask 的 change_dir 均存在
- GIVEN `decompose()` 返回 2 个 subtask
- WHEN 两个 subtask 的 `change_dir` 在各自 transport 上均存在
- THEN 系统 SHALL 正常执行跨项目分解流程，不记录额外 lesson

### Requirement: Proposal 读取验证

当 `_process_change()` 读取 proposal 后，若内容为空，系统 SHALL 记录一条 pipeline 级 lesson 并跳过该 change。

#### Scenario: 空 proposal 文件
- GIVEN proposal.md 文件存在但内容为空
- WHEN `_process_change()` 读取并检测到 `not proposal_text.strip()`
- THEN 系统 SHALL 调用 `record_outcome()` 记录 `error_domain="pipeline"`, `root_cause_key="pipeline.proposal.empty"`
- AND 该 change SHALL 被跳过（返回 False）

#### Scenario: proposal 正常
- GIVEN proposal.md 内容非空
- WHEN `_process_change()` 读取 proposal
- THEN 系统 SHALL 正常进行 intent 分类和后续流程

### Requirement: Intent 分类后记录

当 intent classify 路由到 `ask_user` 时（daemon 模式下意味着跳过），系统 SHALL 记录一条 lesson 说明为什么被跳过。

#### Scenario: open-ended intent 在 daemon 模式下被跳过
- GIVEN `classify()` 返回 `IntentType.OPEN_ENDED` 且 `route()` 返回 `"ask_user"`
- WHEN `_process_change()` 检测到该路由结果
- THEN 系统 SHALL 调用 `record_outcome()` 记录 `error_domain="pipeline"`, `root_cause_key="pipeline.intent.misclassify"`
- AND `prevention` 字段 SHALL 包含 "fallback to implementation for proposals with clear action verbs"

#### Scenario: implementation intent 正常路由
- GIVEN `classify()` 返回 `IntentType.IMPLEMENTATION`
- WHEN `_process_change()` 获得路由结果
- THEN 系统 SHALL 正常进入 pipeline 流程，不记录额外 lesson

### Requirement: 成功交付后记录

当 change 成功完成全部 phase 后，orchestrator SHALL 调用 `record_success()` 记录成功模式。

#### Scenario: change 成功完成
- GIVEN 一个 change 完成了 ENRICH → IMPLEMENT → VERIFY → DELIVER 全部 phase
- WHEN 交付成功
- THEN 系统 SHALL 调用 `record_success()` 记录成功模式
- AND 成功记录 SHALL 包含 `type="success_pattern"`、`first_pass` 标记、总轮次、总耗时

#### Scenario: change 成功但走了 fix loop
- GIVEN 一个 change 经过了 fix loop 后成功交付
- WHEN 交付成功
- THEN 系统 SHALL 调用 `record_success()` 且 `first_pass=False`
