# Clarify: dashboard-add-feedback-loop-metrics

## 需求拆解

### 原始需求
在 dashboard 新增 "Feedback Loop" 指标区域，展示学习闭环的 4 个关键健康指标（Learnings Health、Learning Injection Rate、Auto-Proposal Success Rate、Self-Assessment Coverage），使反思→学习→反馈闭环的状态可观测。数据来源为 `memory/learnings.jsonl` 和 `data/zsiga.db`，需新增 injection event 记录机制。Python 端渲染，空数据时显示 "No data yet"，section 置于 Change History 之前。

### 拆解后的子任务
- [ ] 1. **Feedback Loop 指标计算层** — 新建 Python 模块，包含 4 组指标的采集与计算函数：Learnings Health（total/active/top5/last_write）、Injection Rate（IMPLEMENT/ENRICH 注入比率与平均条数）、Auto-Proposal Success Rate（总数/成功/失败/stuck/成功率/stuck列表）、Self-Assessment Coverage（总数/有记录数/覆盖率/上次时间）。数据源：`memory/learnings.jsonl` + `data/zsiga.db` 已有表。空数据时返回安全的零值/None 结构。 (预估复杂度：高, 预估 token：~8000 / 无历史参考)
- [ ] 2. **Learning Injection 事件追踪机制** — 在 `data/zsiga.db` 中新增 `learning_injections` 表（字段：id, change_id, phase, injected_count, timestamp），并在 IMPLEMENT/ENRICH 阶段注入 learnings 时写入记录。提供写入函数供现有注入逻辑调用。 (预估复杂度：中, 预估 token：~5000 / 无历史参考)
- [ ] 3. **Dashboard HTML 模板与渲染集成** — 在 `site/dashboard.html` 的 Change History section 之前插入 "Feedback Loop" section HTML（4 个卡片：Learnings Health / Injection Rate / Auto-Proposal Success / Self-Assessment Coverage），Python 端渲染数据注入。空数据卡片显示 "No data yet"。样式复用现有 `.card` / `.section` CSS。在 dashboard 渲染流程中调用指标计算层并传入模板。 (预估复杂度：中, 预估 token：~6000 / 无历史参考)
- [ ] 4. **测试套件** — 覆盖：指标计算层（mock 数据源、空数据边界）、injection 追踪写入、dashboard 渲染输出包含 Feedback Loop section、空数据时 "No data yet" 文本出现。文件范围：`tests/test_feedback_loop_metrics.py`。 (预估复杂度：中, 预估 token：~5000 / 无历史参考)

## 边界

### IN scope
- 新增 feedback loop 指标计算模块
- 新增 `learning_injections` DB 表及写入逻辑
- Dashboard HTML 模板新增 "Feedback Loop" section
- Python 端渲染集成（将指标数据注入模板）
- 空数据 "No data yet" fallback
- 对应测试

### OUT of scope
- 修改现有 dashboard 已有 section（Model Usage / Phase Timing / Change History 等）
- 前端 JS 交互或实时刷新
- 新的 API endpoint
- Learnings 噪声清理逻辑的修改
- Auto-proposal 生成逻辑的修改
- Self-assessment 记录逻辑的修改

### 依赖的外部条件
- `memory/learnings.jsonl` 文件格式稳定（JSONL，每行一个 learning 对象含 pattern_key、timestamp 等字段）
- `data/zsiga.db` 中 changes / self_assessment / phase_records 表结构稳定
- 现有 dashboard 渲染管线可扩展（可在渲染流程中插入新 section 数据）
- Python 可使用 `sqlite3` 标准库访问 zsiga.db

## 目标

### 成功标准
1. Dashboard 页面出现 "Feedback Loop" section，位于 Change History 之前
2. 4 个指标卡片（Learnings Health / Injection Rate / Auto-Proposal Success / Self-Assessment Coverage）均有数据或显示 "No data yet"
3. 数据源为空或缺失时页面渲染无报错
4. 全套 pytest（含新增测试）通过，ruff check 无错误

### 验收方式
- 运行 dashboard 渲染，检查输出 HTML 包含 "Feedback Loop" section 及 4 个卡片标题
- 清空 learnings.jsonl 和 zsiga.db 后渲染，确认显示 "No data yet" 而非报错
- `pytest tests/test_feedback_loop_metrics.py -v` 全绿
- `ruff check` 无新增错误

## 约束

### 不能修改的文件
- 现有 dashboard 已有 section 的渲染逻辑（不可破坏已有指标）
- `tests/conftest_zsiga.py`（共享 fixture 不可改）
- `skills/` 目录（不涉及 skill 逻辑）
- `venv2/` 下任何文件

### 项目部署分支
- 工作分支：`zsiga-dashboard-add-feedback-loop-metrics`

### 已知风险
- `data/zsiga.db` 和 `memory/learnings.jsonl` 的 schema 可能在不同环境有差异，需做防御性读取
- 现有 dashboard 渲染管线的扩展点位置需精确定位，避免 section 顺序错误
- `learning_injections` 表为新增，需处理首次部署时表不存在的情况（CREATE TABLE IF NOT EXISTS）
- 历史数据中没有 injection event 记录，Injection Rate 指标在旧数据上会显示 "No data yet"，属预期行为

### 预估 token 消耗
- prompt: ~14000
- completion: ~12000
- 数据来源: 无历史参考
