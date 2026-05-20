# Proposal: CLARIFY - 需求工程阶段改造

## Summary

改造现有 ENRICH 阶段，输出结构化需求契约文件 `clarify.md`，覆盖需求拆解、边界明确、目标对齐、约束梳理四个维度。替代当前 `design.md` + `tasks.md` 输出。

## Motivation

当前 ENRICH 阶段输出 `design.md` 和 `tasks.md`，但存在严重缺陷：
1. **需求拆解不评估可行性**：8 个 tasks 只有 2 个能完成
2. **没有边界定义**：compass-kline 是 DDL 操作不是代码修改，照样走 pipeline
3. **没有目标对齐**：VERIFY 只检查 pytest/ruff，不验证是否解决原始问题
4. **没有约束感知**：不知道 deploy_branch、不知道哪些文件不能动

## Implementation

### 1. 新输出文件 `clarify.md` 替代 `design.md` + `tasks.md`

```markdown
## 需求拆解
- 原始需求：[从 proposal.md 提取]
- 拆解后的子任务（每个可独立验证）：
  1. ... (预估复杂度：低/中/高, 预估 token：基于历史)

## 边界
- IN scope：[明确列出]
- OUT of scope：[明确列出]
- 依赖的外部条件：[数据库、API、手动操作等]

## 目标
- 成功标准：[怎样算完成？可验证的条件]
- 验收方式：[pytest 通过？手动验证？服务健康？]

## 约束
- 不能修改的文件：[配置、migration 等]
- 项目部署分支：[从 target config 读取]
- 已知风险：[基于历史教训]
- 预估 token 消耗：[基于相似任务的历史数据]
```

### 2. 修改 `orchestrator.py`

- `phase_enrich()` 重命名为 `phase_clarify()`
- 修改 enrich prompt：要求 LLM 输出四维度结构
- CLARIFY 输出 `clarify.md` 单文件
- 删除旧的 `design.md` + `tasks.md` 生成逻辑

### 3. 下游阶段引用 `clarify.md`

- IMPLEMENT：按 tasks 列表执行，受边界约束
- VERIFY：按成功标准验收
- DELIVER：按目标确认交付
- OPTIMIZE：按约束检查规范

### 4. 历史数据驱动

- 从 `zsiga.db` 读取相似任务的历史 token 消耗
- 用于"预估 token 消耗"字段
- 如果没有历史数据，标注"无历史参考"

## Constraints
- Scope: project=zsiga
- Files: orchestrator.py (主要修改)
- 向后兼容：旧 archive 中的 design.md/tasks.md 不受影响
- 新 proposal 只生成 clarify.md
