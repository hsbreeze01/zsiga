# Spec: 闭环验证

## ADDED Requirements

### Requirement: Skill 有效性验证

`skill_evolver.py` SHALL 在生成新 skill 后验证其有效性：检查过去 10 条同 pattern_key 的 lesson，确认根因是否不再出现。

#### Scenario: 根因消失确认 skill 生效
- GIVEN skill `pipeline-decompose.md` 已生成
- WHEN `evolve_skills()` 检查最近 10 条 `pipeline.decompose` 相关 lesson
- AND 没有新的相同 root_cause 出现
- THEN skill 的 frontmatter SHALL 标记 `verified: true`
- AND 日志 SHALL 输出 "Skill pipeline-decompose.md verified: root cause not recurring"

#### Scenario: 根因持续出现标记 skill 需迭代
- GIVEN skill `pipeline-decompose.md` 已生成
- WHEN `evolve_skills()` 检查最近 10 条 lesson
- AND 发现新的相同 root_cause 出现
- THEN skill 的 frontmatter SHALL 标记 `verified: false`
- AND 日志 SHALL 输出 "Skill pipeline-decompose.md needs iteration: root cause still recurring"

### Requirement: 自动 context 注入

`_update_memory()` SHALL 将新生成的 skill 文件内容注入到 `active_context.md`，使得下次 agent 运行时自动获得最新的行为规则。

#### Scenario: 新 skill 被注入 active_context
- GIVEN `evolve_skills()` 生成了 `skills/pipeline-decompose.md`
- WHEN `_update_memory()` 被调用
- THEN `active_context.md` SHALL 包含该 skill 的 Rules 部分
- AND 注入格式 SHALL 为 `## Active Skill: {skill_name}` + 规则内容

#### Scenario: 无新 skill 时不注入
- GIVEN `evolve_skills()` 未生成新 skill
- WHEN `_update_memory()` 被调用
- THEN `active_context.md` SHALL 不包含额外的 skill section

### Requirement: 旧 pattern_key 数据迁移

系统 SHALL 提供一次性迁移脚本 `scripts/migrate_pattern_keys.py`，将 `learnings.jsonl` 中旧格式的 pattern_key 转换为新格式。

#### Scenario: 迁移脚本转换旧格式
- GIVEN learnings.jsonl 中包含 `"pattern_key": "pipeline.fail.implement"`
- WHEN 迁移脚本执行
- THEN 该条记录的 pattern_key SHALL 被替换为对应的新格式（如 `code.lint.e701`）
- AND 脚本 SHALL 同时为该条记录补充 `error_domain` 和 `root_cause` 字段

#### Scenario: 幂等执行
- GIVEN learnings.jsonl 已被迁移过一次
- WHEN 迁移脚本再次执行
- THEN 所有记录 SHALL 保持不变
