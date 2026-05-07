---
name: enrich
description: 补全OpenSpec change的artifacts
---

# Artifact 补全规则

你的任务：根据 proposal.md 补全 specs、design、tasks。

## specs/ 格式（Delta Spec）
```
## ADDED Requirements
### Requirement: <名称>
<行为描述，用 SHALL/MUST/SHOULD>

#### Scenario: <场景名>
- GIVEN <前提>
- WHEN <动作>
- THEN <预期结果>

## MODIFIED Requirements
### Requirement: <已有需求名>
<变更描述>

## REMOVED Requirements
### Requirement: <需求名>
<移除原因>
```

## design.md 格式
- 技术方案（怎么实现）
- 架构决策 + 理由
- 数据流
- 文件变更列表

## tasks.md 格式
```markdown
# Tasks
## 1. <分组名>
- [ ] 1.1 <具体任务>
- [ ] 1.2 <具体任务>
```
每个 - [ ] 必须足够小：一个 session 能完成，最多改 3 个文件。

## 规则
- 先读目标项目代码（list_files, read_file, search）
- specs 描述行为（what），不描述实现（how）
- design 基于项目现有技术栈
- 不要创建 proposal.md（已存在）
