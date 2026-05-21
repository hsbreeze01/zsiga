# Clarify: Investigate Metric Degradation — verify_pass_rate

## 需求拆解

### 原始需求
`verify_pass_rate` 当前为 49.2%，低于可接受阈值。需要定位 verify 阶段失败的根因并修复，使通过率回升到健康水平。

### 拆解后的子任务

- [ ] 1. **诊断 verify 失败模式** — 分析 `metrics/changes.jsonl`、`memory/learnings.jsonl` 及近期 verify 阶段日志，归类 TOP-N 失败原因（回归引入、依赖缺失、lint 错误、测试基础设施等），输出结构化诊断报告到 clarify.md 补充节。 (预估复杂度：中, 预估 token：~3000 / 无历史参考)
- [ ] 2. **修复 verify 阶段高频失败根因** — 针对任务 1 排名前三的失败模式，在 `zsiga/pipeline/` 相关模块（orchestrator、verifier、reviewer）中实施防御性修复：包括但不限于 verify 前自动 lint 预检、回归快照比对、依赖完整性校验。 (预估复杂度：高, 预估 token：~6000 / 无历史参考)
- [ ] 3. **强化 verify_pass_rate 指标采集与告警** — 在 metrics 模块中确保 `verify_pass_rate` 计算逻辑正确，增加按失败类型的细分统计（`verify_fail_lint`、`verify_fail_test`、`verify_fail_regression`），为后续自省循环提供可追溯数据。 (预估复杂度：低, 预估 token：~2500 / 无历史参考)

## 边界

### IN scope
- 分析 verify 阶段失败的历史数据与日志
- 修复 `zsiga/pipeline/` 下 verify 相关代码中的缺陷与防御性不足
- 改进 metrics 模块中 `verify_pass_rate` 的采集粒度
- 为修复项编写/更新对应 pytest 测试

### OUT of scope
- 不改动 `site/dashboard.html` 仪表盘展示逻辑（本次聚焦后端指标）
- 不重构 pipeline 整体架构（仅针对 verify 阶段做增量修复）
- 不处理 `daemon.cycle_error`（属于独立问题，已有多条 learnings）
- 不修改 `venv2/` 下任何文件

### 依赖的外部条件
- `metrics/changes.jsonl` 和 `memory/learnings.jsonl` 中存在可分析的 verify 失败记录
- 现有 `zsiga/pipeline/` 模块结构稳定，可增量修改
- `ruff` 和 `pytest` 作为质量门禁可用

## 目标

### 成功标准
1. `verify_pass_rate` 指标在自省循环下次采集时 ≥ 70%
2. TOP-3 失败模式各有对应的防御性修复且覆盖测试通过
3. metrics 模块输出 `verify_pass_rate` 时附带失败类型细分（`lint`/`test`/`regression`）
4. 所有变更通过 `ruff check` 和 `pytest` 全量测试

### 验收方式
- 执行 `pytest tests/` 全部通过（含新增测试）
- 执行 `ruff check zsiga/` 零错误
- `metrics/changes.jsonl` 中最近 N 条 verify 记录的 pass 占比可视化提升
- 代码 diff 仅涉及 `zsiga/pipeline/`、`zsiga/metrics/`、`tests/` 目录

## 约束

### 不能修改的文件
- `site/dashboard.html`
- `venv2/` 下所有文件
- `pyproject.toml`、`requirements.txt`（不引入新依赖）
- `skills/` 目录

### 项目部署分支
main

### 已知风险
- verify 失败可能与其他阶段（implement、review）的输出质量耦合，单点修复未必能完全解决
- 历史日志数据可能不完整，影响诊断准确性
- `daemon.cycle_error` 持续出现可能导致 verify 修复无法被正确度量

### 预估 token 消耗
- prompt: ~8000
- completion: ~5000
- 数据来源: 无历史参考
