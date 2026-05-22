# Clarify: dashboard-add-feedback-loop-metrics

## 需求拆解

### 原始需求
在 dashboard 新增 "Feedback Loop" 指标区域，展示学习闭环的 4 个关键健康指标（Learnings Health、Learning Injection Rate、Auto-Proposal Success Rate、Self-Assessment Coverage），使反思→学习→反馈闭环的状态可观测。所有渲染走 Python 端，空数据时显示 "No data yet"。

### 拆解后的子任务

- [ ] 1. **Feedback Loop 数据采集层** — 实现 Python 函数从 `memory/learnings.jsonl` 和 `data/zsiga.db` 读取 4 个指标所需的原始数据，聚合为结构化 dict。涵盖 learnings 计数/分布、injection 事件统计、auto-proposal 成败统计、self-assessment 覆盖率。空数据时返回安全的零值结构而非报错。 (预估复杂度：高, 预估 token：~6000 / 无历史参考)
- [ ] 2. **Learning Injection 事件记录机制** — 在 IMPLEMENT/ENRICH 阶段注入 learnings 时，写入一条 injection 事件记录（复用 phase_records 表或新建独立表），包含 change_id、phase、注入条数、时间戳。确保指标 2 的数据源存在。 (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 3. **Dashboard HTML 模板新增 Feedback Loop section** — 在 `site/dashboard.html` 的 Change History 之前插入 "Feedback Loop" section，包含 4 个指标卡片的 HTML 结构与样式，使用 Python 端模板变量填充数据。空数据时渲染 "No data yet"。 (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 4. **Dashboard 路由集成与端到端串联** — 在 dashboard 渲染入口调用数据采集函数，将结果注入模板上下文，使 Feedback Loop section 在访问 dashboard 时自动渲染。确保无数据场景不报错。 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 5. **测试覆盖** — 为数据采集函数、injection 事件记录、dashboard 渲染输出编写 pytest，覆盖正常数据与空数据两种路径。 (预估复杂度：中, 预估 token：~4000 / 无历史参考)

## 边界

### IN scope
- 4 个指标卡片的数据采集、聚合、渲染
- Learning injection 事件记录机制（写入 + 读取）
- Dashboard HTML 模板中新增 Feedback Loop section
- 空数据时 "No data yet" 降级显示
- 相关 pytest 测试

### OUT of scope
- 前端 JS 交互 / 异步刷新（保持 Python 端渲染模式）
- 指标历史趋势图 / 时间序列可视化
- 对现有 Model Usage / Phase Timing / Change History section 的修改
- learnings.jsonl 的数据清理逻辑
- API 端点变更（除非渲染流程需要）

### 依赖的外部条件
- `memory/learnings.jsonl` 文件可读（可能不存在，需降级）
- `data/zsiga.db` 中 changes / self_assessment / phase_records 表结构可查询
- 现有 dashboard 渲染入口可扩展（需确认具体渲染函数位置）

## 目标

### 成功标准
1. Dashboard 页面出现 "Feedback Loop" section，位于 Change History 之前
2. 4 个指标卡片（Learnings Health、Injection Rate、Auto-Proposal Success Rate、Self-Assessment Coverage）均有真实数据或合理的 "No data yet" 状态
3. 空数据场景下页面渲染无报错、无异常栈
4. 全套 `pytest` 通过（含新增测试 + 原有测试无回归）
5. `ruff check` 无 lint 错误

### 验收方式
- 手动或自动化访问 dashboard 页面，确认 Feedback Loop section 可见
- 删除 learnings.jsonl 后刷新 dashboard，确认显示 "No data yet" 而非报错
- `pytest tests/ -x` 全绿
- `ruff check site/ <相关Python文件>` 无错误

## 约束

### 不能修改的文件
- `tests/conftest_zsiga.py`（除非必须添加 fixture）
- `pyproject.toml`、`requirements.txt`（不引入新依赖）
- 现有 dashboard section 的 HTML 结构（Model Usage、Phase Timing、Change History）

### 项目部署分支
- zsiga-dashboard-add-feedback-loop-metrics

### 已知风险
- `data/zsiga.db` 表结构可能不完全匹配 proposal 假设（如无 self_assessment 表），需运行时探测并降级
- `memory/learnings.jsonl` 文件可能不存在或为空，数据采集函数必须安全处理
- Learning injection 事件若无历史数据，指标 2 在初始状态下仅显示 "No data yet"，直到新的注入事件产生记录
- Dashboard 渲染入口的具体实现位置尚未确认（可能在 Python 脚本或简单 HTTP handler 中），需先定位

### 预估 token 消耗
- prompt: ~8000
- completion: ~12000
- 数据来源: 无历史参考
