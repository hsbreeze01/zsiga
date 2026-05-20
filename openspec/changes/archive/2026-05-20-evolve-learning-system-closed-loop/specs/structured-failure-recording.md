# Spec: 结构化失败记录

## ADDED Requirements

### Requirement: 两层错误分类学（Error Taxonomy）

学习系统 SHALL 将失败记录分为两层：**故障域（WHERE）** 和 **根因（WHY）**。

故障域包括：
- `code` — 生成的代码有问题（lint/test 错误）
- `pipeline` — zsiga 自身 pipeline 逻辑有缺陷
- `infrastructure` — 外部环境问题（SSH超时、磁盘满、API限流）
- `spec` — proposal/specs 本身有歧义或不完整

根因格式为 `{domain}.{specific}`，例如：
- `code.lint.e401`, `code.lint.e702`, `code.lint.e701`
- `code.test.assertion`, `code.test.import`
- `pipeline.decompose.false_positive`, `pipeline.proposal.empty`
- `infrastructure.ssh.timeout`, `infrastructure.api.rate_limit`

#### Scenario: lint 错误自动分类到 code 域
- GIVEN 一条包含 "E701 Multiple statements on one line" 的失败详情
- WHEN `record_outcome()` 被调用且未指定 `error_domain`
- THEN 系统 SHALL 自动将 `error_domain` 设为 `code`
- AND `pattern_key` SHALL 为 `code.lint.e701`

#### Scenario: pipeline 故障由调用方显式标记
- GIVEN orchestrator 检测到 decompose 的跨项目误判
- WHEN `record_outcome()` 被调用且 `error_domain="pipeline"`
- THEN 系统 SHALL 使用调用方提供的 `error_domain`
- AND `pattern_key` SHALL 为 `pipeline.decompose.false_positive`

### Requirement: 扩展的 record_outcome 签名

`record_outcome()` SHALL 接受以下新参数（均带默认值以保持向后兼容）：

- `error_domain: str = None` — 故障域分类
- `root_cause: str = None` — 根因分析（"我假设了 X，实际是 Y"）
- `prevention: str = None` — 具体的预防措施

当 `error_domain` 为 None 时，系统 MUST 根据已有 `detail` 参数自动推断。

#### Scenario: 向后兼容的调用
- GIVEN 旧代码调用 `record_outcome("change-1", "proj", False, "implement", detail="E401 ...")`
- WHEN 未提供 `error_domain`/`root_cause`/`prevention`
- THEN 系统 SHALL 自动推断 `error_domain` 和根因，并生成默认的 prevention 建议
- AND 学习记录 SHALL 写入 learnings.jsonl 且包含新字段

#### Scenario: 完整参数的调用
- GIVEN orchestrator 调用 `record_outcome(..., error_domain="pipeline", root_cause="...", prevention="...")`
- WHEN 所有新参数均提供
- THEN 系统 SHALL 直接使用这些值，不做覆盖推断

### Requirement: 结构化 lesson 记录格式

每条写入 `learnings.jsonl` 的 lesson 记录 SHALL 包含以下字段（原有字段保留）：

- `error_domain: str` — 故障域
- `root_cause: str` — 根因描述
- `prevention: str` — 预防措施
- `what_happened: str` — 现象描述（从 title/context 推导）

#### Scenario: lesson 包含结构化根因
- GIVEN 一条失败被记录
- WHEN 写入 learnings.jsonl
- THEN 该条记录 MUST 包含 `error_domain`、`root_cause`、`prevention` 三个非空字段
- AND 这三个字段 SHALL 在后续 skill 结晶时被读取使用

### Requirement: 增强的 _classify_failure 函数

`_classify_error()` SHALL 被重命名为 `_classify_failure()` 并扩展为：

1. 支持所有现有 lint 错误码（E401/E702/E701/E722/E501/E741）
2. 支持 test 失败的细分：`assertion`、`import`、`timeout`
3. 支持 pipeline 级故障的识别
4. 返回值 SHALL 包含 `error_domain`、`root_cause_key`、`prevention` 三个字段

#### Scenario: 未知错误类型
- GIVEN 一条不匹配任何已知模式的 detail
- WHEN `_classify_failure()` 被调用
- THEN `error_domain` SHALL 为 `code`，`root_cause_key` SHALL 为 `unknown`
- AND `prevention` SHALL 为通用建议 "review error and adjust approach"

## MODIFIED Requirements

### Requirement: pattern_key 格式迁移

`pattern_key` 的格式 SHALL 从 `pipeline.fail.{phase}.{error_type}` 迁移为 `{domain}.{root_cause}`。

旧格式的 pattern_key SHALL 通过一次性迁移脚本映射到新格式：
- `pipeline.fail.implement.lint_e401_multi_import` → `code.lint.e401`
- `pipeline.fail.implement.lint_e701_one_line` → `code.lint.e701`
- `pipeline.fail.verify.test_failure` → `code.test.assertion`
- `pipeline.fail.verify.unknown` → `code.test.unknown`
- `pipeline.cross_project` → `pipeline.decompose.false_positive`

迁移后旧的 pattern_key SHALL 不再生成。
