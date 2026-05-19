# Spec: Skill 结晶器增强

## MODIFIED Requirements

### Requirement: 增强的 skill markdown 格式

`skill_evolver.py` 生成的 skill 文件 SHALL 包含以下结构化部分（取代当前的 Patterns Observed + Guidelines）：

1. **`## When to Apply`** — 触发条件（来自 pattern_key 语义和出现场景）
2. **`## Rules`** — 具体的行为规则（来自 lesson 的 `prevention` 字段）
3. **`## Anti-Patterns`** — 禁止行为（来自 lesson 的 `root_cause` 字段）
4. **`## Examples`** — 真实案例（来自 lesson 的 `what_happened` / `context` 字段）

原有的 `## Patterns Observed` 表格 SHALL 保留作为元数据参考。

#### Scenario: 含 prevention 字段的 lesson 生成 Rules
- GIVEN 一个 cluster 包含 3 条 lesson，每条均有 `prevention` 字段
- WHEN `_generate_skill_markdown()` 被调用
- THEN `## Rules` 部分 SHALL 列出去重后的 prevention 条目，每条以编号列表形式呈现
- AND 条目数 SHALL 不超过 5 条

#### Scenario: 无 prevention 字段的 lesson 回退到 takeaway
- GIVEN 一个 cluster 包含 3 条 lesson，但没有 `prevention` 字段
- WHEN `_generate_skill_markdown()` 被调用
- THEN `## Rules` 部分 SHALL 使用 `takeaway` 字段作为回退
- AND 每条 SHALL 以编号列表形式呈现

#### Scenario: root_cause 字段生成 Anti-Patterns
- GIVEN 一个 cluster 包含 lesson 且有 `root_cause` 字段
- WHEN `_generate_skill_markdown()` 被调用
- THEN `## Anti-Patterns` 部分 SHALL 列出去重后的 root_cause 条目
- AND 每条 SHALL 前缀 "Do NOT" 或类似否定措辞

#### Scenario: 生成 When to Apply 触发条件
- GIVEN 一个 cluster 的 prefix 为 `pipeline.decompose`
- WHEN `_generate_skill_markdown()` 被调用
- THEN `## When to Apply` 部分 SHALL 描述 "When decompose() returns >1 subtasks for a change"

### Requirement: 结晶触发条件

`evolve_skills()` SHALL 在以下任一条件满足时触发 skill 生成（取代当前的固定 `min_cluster_occurrences=3`）：

1. 同一个 pattern_key 出现 >= 3 次（现有条件）
2. 同一个 `error_domain` 出现 >= 2 次（新增）
3. 一次 `error_domain="pipeline"` 的故障（severity=high，立即触发）

#### Scenario: pipeline 故障立即触发
- GIVEN 一条 `error_domain="pipeline"`, `severity="high"` 的 lesson
- WHEN `evolve_skills()` 运行
- THEN 即使该 pattern_key 只出现 1 次，SHALL 仍生成对应的 skill 文件

#### Scenario: 同 error_domain 两次触发
- GIVEN 2 条不同 pattern_key 但相同 `error_domain="code.lint"` 的 lesson
- WHEN `evolve_skills()` 运行
- THEN SHALL 生成一个按 error_domain 聚合的 skill 文件

### Requirement: skill 文件名包含域信息

生成的 skill 文件名 SHALL 从 cluster prefix 推导，格式保持 `{prefix-with-dots-replaced-by-hyphens}.md`。文件名 SHALL 足以识别故障域。

#### Scenario: pipeline.decompose.false_positive 生成文件名
- GIVEN cluster prefix 为 `pipeline.decompose`
- WHEN 生成 skill 文件
- THEN 文件名 SHALL 为 `pipeline-decompose.md`
