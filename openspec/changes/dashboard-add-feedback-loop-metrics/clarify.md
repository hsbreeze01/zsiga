# Clarify: dashboard-add-feedback-loop-metrics

## 需求拆解

### 原始需求
在 dashboard 新增 "Feedback Loop" 指标区域，包含 4 个指标卡片（Learnings Health、Learning Injection Rate、Auto-Proposal Success Rate、Self-Assessment Coverage），展示学习闭环的关键健康指标，使反思→学习→反馈闭环的状态可观测。Python 端渲染，与现有 dashboard 一致。

### 拆解后的子任务

- [x] 1. **Feedback Loop 指标计算层** — 新增 Python 函数，从 `memory/learnings.jsonl`、`metrics/changes.jsonl` 等数据源计算 4 组指标（Learnings Health：total/active count、top-5 pattern_key 分布、上次写入时间；Injection Rate：IMPLEMENT/ENRICH 阶段注入次数及比率、平均注入条数；Auto-Proposal Success Rate：总数/成功/失败/stuck 数、成功率；Self-Assessment Coverage：总 changes 数、有记录数、覆盖率、上次时间）。空数据时返回 "No data yet" 安全默认值。涉及文件：dashboard 渲染后端模块（新增或扩展 metrics 函数）。(预估复杂度：高, 预估 token：~8000 / 无历史参考)

- [x] 2. **Dashboard HTML 模板更新** — 在 `site/dashboard.html` 的 Metrics 区域、Change History section 之前，新增 "Feedback Loop" section，包含 4 个指标卡片的 HTML/CSS 结构。卡片样式复用现有 `.card` / `.section` 样式，支持 good/warn/bad 颜色分级。指标为空时显示 "No data yet"。(预估复杂度：中, 预估 token：~4000 / 无历史参考)

- [x] 3. **渲染集成：将指标注入 dashboard 输出** — 修改 dashboard 渲染管线，调用新增的计算函数获取 4 组指标，将结果填入 HTML 模板对应占位符。确保与现有 metrics 卡片渲染流程一致（Python 端渲染，无 JS）。涉及文件：dashboard 渲染主逻辑文件。(预估复杂度：中, 预估 token：~4000 / 无历史参考)

- [x] 4. **测试覆盖** — 新增 pytest 测试文件，覆盖：4 组指标在正常数据下的计算正确性、空数据时返回 "No data yet" 安全默认值、dashboard HTML 输出包含 "Feedback Loop" section、页面渲染不报错。遵循项目现有测试模式（参考 `tests/test_dashboard_api.py`）。(预估复杂度：中, 预估 token：~5000 / 无历史参考)

## 边界

### IN scope
- 4 个 Feedback Loop 指标的计算逻辑（Learnings Health、Injection Rate、Auto-Proposal Success Rate、Self-Assessment Coverage）
- dashboard.html 新增 Feedback Loop section（HTML + CSS）
- 渲染管线集成（Python 端填充数据到模板）
- 空数据的优雅降级（显示 "No data yet"）
- 对应的 pytest 测试

### OUT of scope
- 现有 dashboard 指标（Model Usage、Phase Timing、Change History）的修改
- 新增 API endpoint（除非渲染管线需要）
- JS 前端逻辑（全部 Python 端渲染）
- learnings/changes 数据采集逻辑的修改（只读取已有数据）
- 移动端响应式适配（不在 proposal 范围内）

### 依赖的外部条件
- `memory/learnings.jsonl` 文件格式稳定（字段包含 pattern_key、timestamp 等）
- `metrics/changes.jsonl` 文件格式稳定（字段包含 phase、learnings_injected、self_assessment、auto_generated 等）
- 现有 dashboard 渲染管线的入口函数可被扩展
- 现有 CSS 类（`.card`、`.section`、`.value`）可复用

## 目标

### 成功标准
1. Dashboard 页面出现 "Feedback Loop" section，位于 Change History 之前
2. 4 个指标卡片（Learnings Health、Injection Rate、Auto-Proposal Success Rate、Self-Assessment Coverage）均有数据或合理 "No data yet" 状态
3. 有数据时指标值正确反映 learnings.jsonl / changes.jsonl 中的实际状态
4. 页面渲染无报错（无论数据是否存在）
5. 全套 pytest 通过，新增测试覆盖 4 组指标的计算与空数据降级

### 验收方式
- 手动检查 dashboard HTML 输出包含 "Feedback Loop" section 及 4 个卡片
- 运行 `pytest tests/ -x` 全套通过
- 运行 `ruff check` 无 lint 错误
- 在无 learnings/changes 数据时，dashboard 仍能正常渲染（不抛异常）

## 约束

### 不能修改的文件
- `tests/test_dashboard_api.py`（已有测试，不应改动）
- `tests/test_dashboard_queue.py`（已有测试，不应改动）
- `pyproject.toml`（无新依赖）
- `requirements.txt`（无新依赖）
- `venv2/` 目录下所有文件

### 项目部署分支
- main

### 已知风险
- `memory/learnings.jsonl` 和 `metrics/changes.jsonl` 的字段格式未在 proposal 中严格定义，需在实现时确认实际字段名（如 `learnings_injected`、`self_assessment`、`auto_generated` 等）
- learnings.jsonl 可能为空或不存在，需防御性处理
- 现有 dashboard 渲染管线的入口函数位置需在实现时定位确认
- 自增指标中 "stuck" 定义（>=3 次 FAIL）需从 changes 历史中推断，可能依赖 `metrics/changes.jsonl` 中未记录的字段

### 预估 token 消耗
- prompt: ~20000
- completion: ~12000
- 数据来源: 无历史参考
