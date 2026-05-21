# clarify.md — dashboard-add-feedback-loop-metrics

## 需求拆解

### 原始需求
在 dashboard 新增 "Feedback Loop" 指标区域，展示学习闭环的 4 项关键健康指标（Learnings Health、Learning Injection Rate、Auto-Proposal Success Rate、Self-Assessment Coverage），使反思→学习→反馈闭环的状态可观测。Python 端渲染，空数据优雅降级。

### 拆解后的子任务
- [ ] 1. **后端数据聚合层** — 新增 feedback loop 指标的数据查询与聚合函数，从 learnings、changes、proposals 等数据源计算 4 项指标（Learnings Health / Injection Rate / Auto-Proposal Success / Self-Assessment Coverage），返回结构化 dict，空数据时返回安全的默认值 (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 2. **Dashboard API 端点** — 新增或扩展 dashboard API 路由，暴露 feedback loop 指标数据供页面渲染调用 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 3. **Dashboard HTML 渲染** — 在 `site/dashboard.html` 的 Change History section 之前插入 "Feedback Loop" section，包含 4 个指标卡片的 HTML 结构（card 布局复用现有 `.card` / `.section` 样式），空数据时显示 "No data yet" (预估复杂度：中, 预估 token：~3500 / 无历史参考)
- [ ] 4. **测试覆盖** — 为新增的数据聚合函数、API 端点和页面渲染编写 pytest，覆盖正常数据、空数据、边界情况 (预估复杂度：中, 预估 token：~3000 / 无历史参考)

## 边界

### IN scope
- 在 dashboard 页面新增 "Feedback Loop" section（含 4 个指标卡片）
- 后端数据查询/聚合逻辑（learnings、changes、proposals 统计）
- 空数据时 "No data yet" 优雅降级
- 相关 pytest 测试

### OUT of scope
- 修改 learnings 写入逻辑或数据结构
- 修改 auto-proposal 生成逻辑
- 修改 self-assessment 记录逻辑
- JS 交互或动态刷新
- 新增独立 API 服务（复用现有 dashboard 渲染链路）

### 依赖的外部条件
- 现有 `memory/learnings.jsonl` 文件格式保持不变
- 现有 `metrics/changes.jsonl` 文件格式保持不变
- 现有 dashboard 渲染管线（Python 端）可扩展
- proposals 数据可从已有数据源（changes 目录 / DB）查询

## 目标

### 成功标准
1. Dashboard 页面出现 "Feedback Loop" section，位于 Change History 之前
2. 4 个指标卡片（Learnings Health、Injection Rate、Auto-Proposal Success、Self-Assessment Coverage）均有真实数据或合理的 "No data yet" 状态
3. 页面渲染无报错，无 500 错误
4. 全套 pytest（含新增测试）通过，ruff lint 通过

### 验收方式
- 手动或脚本访问 dashboard HTML，确认 Feedback Loop section 存在且结构正确
- `pytest tests/ -x` 全绿
- `ruff check` 无新增错误

## 约束

### 不能修改的文件
- `memory/learnings.jsonl`（只读）
- `metrics/changes.jsonl`（只读）
- 现有 dashboard 已有 section 的核心逻辑（不破坏现有功能）

### 项目部署分支
main

### 已知风险
- learnings.jsonl 和 changes.jsonl 格式可能存在历史不一致，聚合函数需做防御性解析
- dashboard.html 已有大量内联样式，新增 HTML 需注意不引入样式冲突
- 数据量较大时聚合查询可能有性能影响，建议限制查询范围或添加简单缓存

### 预估 token 消耗
- prompt: ~8000
- completion: ~6000
- 数据来源: 无历史参考
