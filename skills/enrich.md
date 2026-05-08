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
- [ ] 1.1 <具体任务，按功能模块而非按函数>
- [ ] 1.2 <具体任务>
```

### 任务粒度规则
- 每个 - [ ] 对应一个**功能模块**，不是单个函数
- 一个 task 可以包含多个相关函数（如"技术指标计算层"包含 calcMA/calcEMA/calcMACD 等）
- 每个 task 预估消耗 ≤ 3 轮（读1次+写1次+验证1次）
- 前端 UI 渲染任务标记为 `scope: frontend`

### 粒度示例
- ❌ `- [ ] 实现 calcMA 函数` — 太细
- ✅ `- [ ] 添加技术指标计算层（calcMA/calcEMA/calcMACD/calcKDJ/calcBOLL/calcRSI）`
- ✅ `- [ ] 添加 /api/stock/valuation 代理路由和估值数据接口`

## 规则
- 先读目标项目代码（list_files, read_file, search）
- specs 描述行为（what），不描述实现（how）
- design 基于项目现有技术栈
- 如果项目包含前端模板（templates/*.html），在 design.md 中标注前端任务
- 不要创建 proposal.md（已存在）
