# Proposal: REFLECT - 自我评估阶段

## Summary

新增 REFLECT 阶段（DELIVER 之前），执行自我评估：任务复盘、能力评估、教训记录、能力建模更新。

## Motivation

当前 zsiga 无自我评估能力：
- 不知道自己擅长什么、不擅长什么
- 相同错误重复犯
- 无法基于历史数据预测任务难度和 token 消耗
- review 阶段 100% 失败率但无人关注

## Implementation

### 1. `orchestrator.py` 新增 `phase_reflect()`

位置：OPTIMIZE 之后、DELIVER 之前

### 2. 输出 `reflect.md`

```markdown
## 任务复盘
- 实际执行 vs 预估（token 消耗、时间、steps）
- fix_attempts 次数和原因

## 能力评估
- 本任务表现：优秀/良好/一般/差
- 擅长的部分：[列举]
- 不擅长的部分：[列举]

## 教训记录
- 失败原因（如有回滚）
- 关键决策点
- 可改进的地方

## 下次建议
- 相似任务的预估 token
- 需要特别注意的约束
```

### 3. 写入 metrics DB

在 `zsiga.db` 新增 `self_assessment` 表：

```sql
CREATE TABLE IF NOT EXISTS self_assessment (
    id INTEGER PRIMARY KEY,
    change_name TEXT,
    task_type TEXT,           -- fix/impl/refactor
    predicted_tokens INTEGER,
    actual_tokens INTEGER,
    predicted_steps INTEGER,
    actual_steps INTEGER,
    fix_attempts INTEGER,
    outcome TEXT,             -- success/reverted/partial
    self_rating TEXT,         -- excellent/good/average/poor
    strengths TEXT,           -- JSON array
    weaknesses TEXT,          -- JSON array
    lessons TEXT,             -- JSON array
    created_at TEXT
);
```

### 4. CLARIFY 阶段引用

CLARIFY 生成"预估 token 消耗"时，查询 `self_assessment` 表中相似 task_type 的历史数据。

### 5. 能力边界识别

如果某类任务连续 3 次评分为 poor：
- 在 CLARIFY 阶段标记为"超出当前能力"
- 建议"需要人工介入"

## Constraints
- Scope: project=zsiga
- Files: orchestrator.py, metrics/db.py
- 不影响现有 pipeline 的执行流程
- REFLECT 是只读评估，不修改任何代码
