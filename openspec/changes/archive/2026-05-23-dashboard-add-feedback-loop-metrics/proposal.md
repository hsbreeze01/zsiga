# Proposal: dashboard-add-feedback-loop-metrics

## Summary
在 dashboard 新增 "Feedback Loop" 指标区域，展示学习闭环的关键健康指标，使反思→学习→反馈闭环的状态可观测。

## Motivation
当前 dashboard 有 Model Usage、Phase Timing、Change History 等指标，但完全没有反映"学习闭环是否有效"的指标。我们无法通过 dashboard 判断：
- Learnings 是否在被注入 prompt？
- Auto-proposal 的成功率是多少？
- Self-assessment 是否在正常记录？

没有可观测性 → 闭环断裂无法被发现。

## Expected Behavior

### Dashboard 新增 "Feedback Loop" section
在 dashboard 的 Metrics 区域新增一个 section，包含以下指标卡片：

#### 指标 1: Learnings Health
- Total learnings count
- Active learnings count（排除已清理的噪声）
- Top 5 pattern_key 分布（小型横向 bar chart 或列表）
- 上次 learning 写入时间

#### 指标 2: Learning Injection Rate
- IMPLEMENT 阶段被注入 learnings 的次数 / IMPLEMENT 总次数
- ENRICH 阶段被注入 learnings 的次数 / ENRICH 总次数
- 注入的 learnings 平均条数

#### 指标 3: Auto-Proposal Success Rate
- Auto-generated proposals 总数
- 成功数 / 失败数 / stuck 数（≥3次FAIL的）
- 成功率百分比
- 当前 stuck 的 proposal 列表（如有）

#### 指标 4: Self-Assessment Coverage
- 总 changes 数
- 有 self_assessment 记录的 changes 数
- 覆盖率百分比
- 上次 self-assessment 时间

### 数据来源
- 从 `memory/learnings.jsonl` 读取 learnings 数据
- 从 `data/zsiga.db` 的 changes、self_assessment、phase_records 表读取
- 新增一个 phase_record 或独立表来记录 learning injection 事件（在 IMPLEMENT/ENRICH 注入 learnings 时写入）

### 实现要求
- Python 端渲染（与现有 dashboard 一致），不用 JS
- 指标为空时显示 "No data yet" 而非报错
- Section 在 dashboard 底部（Change History 之前）

## Success Criteria
- Dashboard 页面出现 "Feedback Loop" section
- 4 个指标卡片均有数据或合理的 "No data" 状态
- 页面渲染无报错
- 全套 pytest 通过
