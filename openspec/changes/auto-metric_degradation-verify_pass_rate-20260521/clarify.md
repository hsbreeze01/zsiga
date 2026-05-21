# Clarify: Investigate Metric Degradation — verify_pass_rate

## 需求拆解

### 原始需求
`verify_pass_rate` 指标当前为 49.2%，低于可接受阈值。需要定位 verify 阶段失败的根因，并从 分类可观测性、lint 自动修复、指标度量脚本 三个维度进行改善，使 pass rate 回到健康水平。

### 拆解后的子任务

- [ ] 1. **Verify 失败分类体系** — 建立失败分类模型（lint / test / import / runtime / config），在 verify 流程中为每次失败打上结构化标签，写入 metrics 变更日志 (预估复杂度：中, 预估 token：~4000)
- [ ] 2. **Verify 失败可观测性增强** — 在 dashboard 或 metrics 层暴露失败分类分布、历史趋势，使 degradation 可被快速定位 (预估复杂度：中, 预估 token：~3500)
- [ ] 3. **Post-implement Lint 自动修复** — 在 implement 阶段完成后、verify 之前，自动运行 ruff fix 处理可自动修复的 lint 问题（E701、trailing whitespace、unused import 等高频错误），减少因 lint 导致的 verify 失败 (预估复杂度：中, 预估 token：~4000)
- [ ] 4. **Verify pass rate 指标脚本** — 提供独立脚本或函数，从 metrics/changes.jsonl 计算 verify_pass_rate，支持按时间窗口、失败类别过滤，输出当前值及趋势 (预估复杂度：低, 预估 token：~2500)

## 边界

### IN scope
- 对 verify 阶段失败进行结构化分类与记录
- 自动修复高频 lint 错误以提升 pass rate
- 提供 verify_pass_rate 的计算/查询能力
- 失败分类在 dashboard/metrics 中的可观测性展示
- 为上述功能编写对应的 pytest 测试

### OUT of scope
- 修改 LLM prompt 策略或模型选择逻辑
- 重构 verify 阶段的核心架构
- 修改 dashboard.html 前端布局（仅限 metrics 数据接入）
- 跨项目指标对比分析
- daemon 循环调度的修改

### 依赖的外部条件
- metrics/changes.jsonl 中需有足够的 verify 阶段历史数据用于分析
- ruff 已在项目依赖中（requirements.txt: ruff>=0.4）
- 现有 verify 流程入口可被 hook/扩展

## 目标

### 成功标准
1. verify_pass_rate 指标可通过脚本/函数直接查询，输出含分类明细的统计结果
2. 常见 lint 错误（E701、unused import 等）在 post-implement 阶段被自动修复
3. 每次 verify 失败携带结构化分类标签，写入 metrics 日志
4. 所有新增/修改代码通过 `pytest` 和 `ruff check`
5. 已有测试（test_spec_auto_metric_degradation_verify_pass_rate_20260521__* 系列）全部通过

### 验收方式
- 运行 `pytest tests/test_spec_auto_metric_degradation_verify_pass_rate_20260521__*.py` 全部通过
- 运行 `ruff check` 零错误
- 手动触发 verify 场景，确认失败日志包含分类标签
- 执行指标脚本，确认输出 verify_pass_rate 数值及分类明细

## 约束

### 不能修改的文件
- venv2/ 目录下的任何文件
- pyproject.toml（除非仅添加 entry point）
- tests/conftest_zsiga.py（除非必要且不影响现有测试）
- skills/skill_evolver.py

### 项目部署分支
main

### 已知风险
- metrics/changes.jsonl 数据格式可能不一致，解析需防御性处理
- post-implement lint autofix 可能引入语义变化（如移除看似 unused 但被 eval 使用的 import），需白名单机制
- verify 失败分类可能存在灰色地带（如 lint + test 同时失败），需定义优先级

### 预估 token 消耗
- prompt: ~14000
- completion: ~6000
- 数据来源: 无历史参考
