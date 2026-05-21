# Clarify: Investigate Metric Degradation — verify_pass_rate

## 需求拆解

### 原始需求
`verify_pass_rate` 指标当前为 49.2%，低于可接受阈值。需要定位 verify 阶段失败的根因，并修复导致 pass rate 低的关键问题，使指标恢复到健康水平。

### 拆解后的子任务

- [ ] 1. **数据采集与失败分类** — 读取 `metrics/changes.jsonl` 和相关日志，提取所有 verify 阶段失败记录，按失败原因分类（lint 错误、测试失败、daemon.cycle_error、无实现变更等），输出分类报告。（预估复杂度：中, 预估 token：~4000）
- [ ] 2. **Verify 阶段逻辑审查** — 阅读 `zsiga/pipeline/` 下 verify 相关代码，确认 verify_pass_rate 的计算逻辑、通过条件、以及与上游 review 阶段的衔接，识别是否存在误判或过于严格的检查。（预估复杂度：中, 预估 token：~5000）
- [ ] 3. **修复高频失败根因** — 根据任务 1 的分类结果，修复 top-2 高频失败类型（预计为 daemon.cycle_error 导致的分支冲突 和 lint/format 未预检），在 implement 阶段增加防护措施。（预估复杂度：高, 预估 token：~8000）
- [ ] 4. **验证修复效果** — 运行 `pytest` + `ruff` 确认所有修改通过，并构造测试用例验证新增防护逻辑的正确性。（预估复杂度：低, 预估 token：~3000）

## 边界

### IN scope
- 分析 verify_pass_rate 低于阈值的原因
- 审查 verify 阶段的代码逻辑与判定标准
- 修复可复现的高频失败根因（daemon.cycle_error、lint 未预检等）
- 在 implement 阶段增加前置检查以防止常见失败
- 为新增防护逻辑编写单元测试

### OUT of scope
- 重构整个 pipeline 架构
- 修改 dashboard 前端展示
- 处理一次性/偶发的失败（如网络超时、LLM API 异常）
- 修改 `memory/learnings.jsonl` 或 `data/zsiga.db` 的存储格式
- 解决 cross_project 类型的问题（需独立 change 处理）

### 依赖的外部条件
- `metrics/changes.jsonl` 中有足够的 verify 失败记录可供分析
- `zsiga/pipeline/` 目录下 verify 相关代码可被正常读取和修改
- 测试环境可正常执行 `pytest` 和 `ruff`

## 目标

### 成功标准
1. 识别出至少 2 个导致 verify_pass_rate < 50% 的高频根因，并有明确的分类统计
2. 针对每个识别出的根因，在代码中实现对应的防护/修复
3. 新增/修改的代码通过 `pytest` 和 `ruff check`
4. 新增的防护逻辑有对应的单元测试覆盖

### 验收方式
- `pytest` 全部通过（含新增测试用例）
- `ruff check` 无错误
- 分类报告中各类失败有明确的计数和占比
- 代码 diff 可明确对应到某个根因的修复

## 约束

### 不能修改的文件
- `data/zsiga.db`（运行时数据，不可手动修改）
- `memory/learnings.jsonl`（记忆数据，不可手动修改）
- `venv2/`（第三方依赖）
- `site/dashboard.html`（前端不在本次范围内）

### 项目部署分支
main

### 已知风险
- `daemon.cycle_error` 涉及 git checkout 冲突，修复可能需要调整 daemon 循环的 git 操作策略，影响面较广
- 历史失败数据可能不够完整（部分失败未被记录到 metrics），导致分类结果有偏差
- 修复 implement 阶段的前置检查可能引入新的边缘情况

### 预估 token 消耗
- prompt: ~15000
- completion: ~8000
- 数据来源: 无历史参考（首次处理 verify_pass_rate 退化的 change）
