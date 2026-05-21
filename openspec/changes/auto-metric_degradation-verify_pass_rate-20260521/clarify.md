# Clarify: Investigate Metric Degradation — verify_pass_rate

## 需求拆解

### 原始需求
`verify_pass_rate` 指标当前为 49.2%，低于可接受阈值。需要定位 verify 阶段失败的根因，并针对性修复以将通过率提升到可接受水平。

### 拆解后的子任务

- [ ] 1. **构建 verify 通过率度量脚本**：创建独立脚本或工具函数，从 `metrics/changes.jsonl`（或等效数据源）中提取最近 N 次 change 的 verify 结果，计算通过率并输出结构化报告（总次数、通过、失败、按失败类别统计）。(预估复杂度：中, 预估 token：~3000)

- [ ] 2. **实现 verify 失败分类机制**：在 verify 阶段失败时，自动将失败归类为已知类别（如 `lint_error`、`test_failure`、`git_conflict`、`review_rejection`、`missing_implementation` 等），写入结构化日志，为后续根因分析提供数据基础。(预估复杂度：中, 预估 token：~4000)

- [ ] 3. **增强 verify 失败可观测性**：在 dashboard 或日志中暴露 verify 失败的分类统计与趋势，使 `verify_pass_rate` 退化可被及时发现；包含失败类别分布、近期失败历史等。(预估复杂度：中, 预估 token：~3000)

- [ ] 4. **实现 post-implement lint 自动修复**：针对 pattern mining 发现的高频 lint 失败（如 E701 多语句一行），在 implement 阶段结束后、verify 前插入自动 lint-fix 步骤，减少因 trivial lint 错误导致的 verify 失败。(预估复杂度：高, 预估 token：~5000)

## 边界

### IN scope
- verify 失败的根因分析与分类
- verify 通过率的度量计算与趋势可视化
- post-implement lint 自动修复（仅限 ruff 可自动修复的规则）
- 已有测试文件中定义的 spec 验证场景通过

### OUT of scope
- 修改 verify 阶段的核心判定逻辑（通过/失败标准）
- 修改 daemon 主循环的调度策略
- 新增 LLM 调用或模型配置变更
- 前端 dashboard 大规模重构（仅新增指标展示区域）

### 依赖的外部条件
- `metrics/changes.jsonl` 或等效 change 历史数据可用
- `ruff` 已安装且可通过 CLI 调用
- 现有 test suite 可正常运行（不因外部环境问题失败）

## 目标

### 成功标准
1. verify 通过率度量脚本可正确计算并输出 `verify_pass_rate`
2. verify 失败能被自动归类到至少 5 种已知失败类别
3. post-implement lint 自动修复覆盖 ruff 可自动修复的 lint 错误，减少 `pipeline.fail.implement` 类型的失败
4. 所有新增/修改代码通过 `pytest` 和 `ruff check`
5. 已存在的 4 个 spec 测试文件全部通过

### 验收方式
- 运行 `pytest tests/test_spec_auto_metric_degradation_verify_pass_rate_20260521__*.py -v` 全部通过
- 运行 `ruff check <modified_files>` 无错误
- 度量脚本输出结构化 JSON，包含 `total`、`passed`、`failed`、`rate`、`breakdown_by_category` 字段

## 约束

### 不能修改的文件
- `venv2/` 目录下所有文件（第三方依赖）
- `tests/conftest_zsiga.py`（共享 conftest，非本 change 范围）
- `skills/skill_evolver.py`（非本 change 范围）

### 项目部署分支
- `main`

### 已知风险
- `metrics/changes.jsonl` 数据格式可能不稳定，需要做防御性解析
- post-implement lint-fix 可能引入意外的代码变更，需要在 fix 后做 diff 校验
- pattern warnings 中的 `daemon.cycle_error`（git conflict）是 verify 失败的另一主因，但修复需要改变 git 工作流，本 change 仅做分类不修复

### 预估 token 消耗
- prompt: ~12000
- completion: ~8000
- 数据来源: historical（基于同类 pipeline improvement change 的历史消耗）
