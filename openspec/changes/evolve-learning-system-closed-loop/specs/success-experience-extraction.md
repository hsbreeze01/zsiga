# Spec: 成功经验提炼

## ADDED Requirements

### Requirement: record_success 函数

`zsiga/memory/learn.py` SHALL 提供 `record_success()` 函数，在 change 成功完成时提取关键知识并写入 `learnings.jsonl`。

函数签名：
```python
def record_success(
    change_name: str,
    project: str,
    phase_records: list[dict] = None,
    total_turns: int = 0,
    total_seconds: float = 0.0,
)
```

#### Scenario: 一次性通过的成功
- GIVEN 一个 change 的所有 phase 均无 fix_attempts
- WHEN `record_success()` 被调用
- THEN 记录 SHALL 包含 `first_pass=True`
- AND `type` SHALL 为 `"success_pattern"`

#### Scenario: 经修复后通过的成功
- GIVEN 一个 change 的 implement phase 有 fix_attempts=2
- WHEN `record_success()` 被调用
- THEN 记录 SHALL 包含 `first_pass=False`
- AND `fix_attempts` SHALL 为总修复次数

#### Scenario: 记录写入 learnings.jsonl
- GIVEN `record_success()` 被调用
- WHEN 函数执行
- THEN 一条包含 `type="success_pattern"` 的 JSON 记录 SHALL 被追加到 `learnings.jsonl`
- AND 该记录 SHALL 包含 `ts`、`change_name`、`project`、`first_pass`、`total_turns`、`total_seconds` 字段

### Requirement: 成功记录包含 pattern_key

成功记录 SHALL 包含 `pattern_key="pipeline.pass.deliver"` 以与现有数据兼容，并新增 `error_domain="success"` 标记用于区分成功与失败模式。

#### Scenario: pattern_key 兼容性
- GIVEN 成功记录被写入
- WHEN `pattern_miner` 读取 learnings.jsonl
- THEN 成功记录 SHALL 可被 pattern_key="pipeline.pass.deliver" 正常分组
- AND 成功记录的 severity SHALL 为 "low"

### Requirement: 成功经验可被 skill_evolver 使用

`skill_evolver` SHALL 能区分 `success_pattern` 和 `lesson` 类型的记录，并将成功经验提炼为正向规则。

#### Scenario: 成功模式的提炼
- GIVEN `pipeline.pass.deliver` 出现 >= 3 次
- WHEN `skill_evolver` 处理该 pattern
- THEN 生成的 skill 文件 SHALL 包含成功模式总结
- AND `Guidelines` 部分 SHALL 包含从成功案例中提炼的最佳实践
