# Clarify: Investigate Metric Degradation — verify_pass_rate

## 需求拆解

### 原始需求
`verify_pass_rate` 指标当前值为 49.2%，低于可接受阈值。需要定位根因并修复，使该指标恢复到健康水平。该指标反映 daemon pipeline 中 verify 阶段（`pytest` + `ruff` 检查）通过率持续偏低的问题。

### 拆解后的子任务

- [ ] 1. **建立 verify_pass_rate 指标度量基线与采集链路** — 确认指标的计算方式（分子/分母来源）、历史趋势数据是否完整，若无则补建度量脚本，输出最近 N 个 change 的 verify 结果汇总 (预估复杂度：低, 预估 token：~1500)
- [ ] 2. **根因分析：分类 verify 失败原因** — 扫描 `metrics/changes.jsonl` 或 `data/zsiga.db` 中已记录的 verify 失败记录，按失败类别（lint / test / must-modify-gate / phase-wal 等）聚类，定位 top-3 失败类别及其典型模式 (预估复杂度：中, 预估 token：~2500)
- [ ] 3. **修复高频失败类别** — 针对根因分析中识别的 top 失败类别，在 reviewer / implementer / verify 层增加防御逻辑（如：implement 后自动 lint-and-fix、reviewer 增加 must-modify-gate 预检、verify 阶段增加重试与部分回退） (预估复杂度：高, 预估 token：~4000)
- [ ] 4. **回归验证与指标回归测试** — 编写针对 verify pass rate 提升的回归测试，确保修复后 `pytest` 和 `ruff` 全量通过，并在模拟 pipeline 端到端场景下验证 pass rate 改善 (预估复杂度：中, 预估 token：~2000)

## 边界

### IN scope
- 分析 `verify_pass_rate` 指标退化根因
- 修复导致 verify 阶段高频失败的代码路径
- 补充必要的防御性检查与自动修复逻辑
- 编写回归测试确保指标改善可度量

### OUT of scope
- 修改 dashboard 前端展示逻辑
- 修改 daemon 调度策略（rest/work cycle）
- 重构整个 pipeline 状态机架构
- 修改 `data/zsiga.db` schema

### 依赖的外部条件
- `metrics/changes.jsonl` 或 `data/zsiga.db` 中存在足够的 change 历史数据用于分析
- `pytest` 和 `ruff` 工具链可正常运行
- 现有测试套件在修改前基线状态可运行

## 目标

### 成功标准
1. `verify_pass_rate` 从当前 49.2% 提升至 ≥ 70%（或证明指标计算本身有误并修正计算逻辑）
2. 识别并文档化至少 3 个 verify 失败根因类别及其占比
3. 新增/修改的防御逻辑全部通过 `pytest` + `ruff`
4. 无回归：现有测试套件全量通过

### 验收方式
- 运行 `pytest` 全量通过，`ruff check` 无错误
- `verify_pass_rate` 指标数值可度量改善（通过度量脚本或 dashboard 确认）
- 根因分析文档化（记录在 clarify.md 或 spec 中）

## 约束

### 不能修改的文件
- `site/dashboard.html` — 前端不在本次 scope
- `venv2/` 目录下所有文件 — 第三方依赖
- `data/zsiga.db` schema 结构

### 项目部署分支
- `main`

### 已知风险
- 历史数据可能不足，导致无法精确计算 `verify_pass_rate` 基线
- 部分 verify 失败可能与 LLM 输出质量相关，非代码修复能完全解决
- 修复可能引入新的 pipeline 行为变化，需要充分的回归测试覆盖

### 预估 token 消耗
- prompt: ~8000
- completion: ~4000
- 数据来源: 无历史参考
