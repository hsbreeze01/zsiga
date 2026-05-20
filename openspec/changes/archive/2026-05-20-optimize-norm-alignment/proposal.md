# Proposal: OPTIMIZE - 规范对齐阶段

## Summary

新增可选 OPTIMIZE 阶段（VERIFY 之后、DELIVER 之前），执行规范对齐检查：模式对齐、冗余剔除、可读性、性能。

## Motivation

当前 agent 代码"能跑就行"：
- 项目有 BaseDB 类但 agent 直接写原生 SQL
- 函数超过 50 行无拆分
- 新增代码与已有模式不一致
- VERIFY 只检查 pytest/ruff，不检查工程规范

## Implementation

### 1. `orchestrator.py` 新增 `phase_optimize()`

位置：VERIFY 通过后、DELIVER 之前

### 2. 触发条件（满足任一即触发）

通过 LLM 评审代码变更，检查：
- 模式一致性：项目有 BaseModel/BaseDB/BaseService 但新代码未使用
- 冗余代码：新增代码与已有代码重复
- 可读性：函数超过 50 行、命名不一致
- 性能：N+1 查询、不必要的全量加载

### 3. 检查方式

```python
async def phase_optimize(self, change_path):
    # 读取 clarify.md 中的约束
    # 收集 IMPLEMENT 阶段变更的文件
    # 用 LLM_fast 评审：是否满足项目既有模式？
    # 如果发现问题，生成修复 task 并执行
    # 修复后自动 re-verify
```

### 4. 配置

```yaml
pipeline:
  optimize:
    enabled: true  # 可通过 proposal 级别 skip_optimize: true 跳过
    max_function_lines: 50
    re_verify: true
```

### 5. 跳过机制

proposal.md 中可标注 `skip_optimize: true` 跳过此阶段（如紧急 bug fix）。

## Constraints
- Scope: project=zsiga
- Files: orchestrator.py (主要修改)
- 可选阶段，不影响现有 pipeline
- OPTIMIZE 后必须 re-verify
