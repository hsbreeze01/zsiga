# Clarify: validate-pipeline-fixes-20260520

## 需求拆解

### 原始需求
本次为验证性任务：通过修改一个小功能点，触发完整 pipeline（CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER），验证近期多项 pipeline 基础设施修复是否生效。具体改动两处：1) `_phase_table` 展示所有 Phase 枚举值（含无数据阶段）；2) dashboard 页面标题下方加 pipeline 完整流程指示文字。

### 拆解后的子任务
- [ ] 1. **Phase 表格全量展示** — 修改 `zsiga/metrics/dashboard.py` 中 `_phase_table` 函数，使其遍历 Phase 枚举所有值输出行，无数据阶段显示为 0（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 2. **Dashboard pipeline 流程指示器** — 在 `site/dashboard.html` 页面 `<h1>` 标题下方增加一行小字，展示完整 pipeline 流程 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`，使用合适的样式（预估复杂度：低, 预估 token：~1500 / 无历史参考）

## 边界

### IN scope
- `_phase_table` 函数改为枚举驱动展示，确保所有 Phase 行均出现
- `site/dashboard.html` 标题区新增 pipeline 流程指示文字
- 通过本次实际改动触发完整 8 阶段 pipeline 以验证修复

### OUT of scope
- 不修改 pipeline 核心逻辑（engine、phase 调度等）
- 不修改 Phase 枚举定义本身
- 不添加新的 Phase 阶段
- 不修改 dashboard API 端点逻辑（仅前端展示 + 后端表格渲染）
- 不涉及 metrics 数据采集逻辑

### 依赖的外部条件
- Phase 枚举已包含 CLARIFY / ENRICH / OPTIMIZE 等新阶段值
- `_phase_table` 函数当前已存在并可正常工作
- dashboard.html 已有基础结构和样式体系

## 目标

### 成功标准
1. `_phase_table` 输出包含 Phase 枚举的所有值，无数据阶段显示计数为 0
2. dashboard.html 标题下方可见一行 pipeline 流程文字：`CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`
3. 改动能通过完整 pipeline 的 8 个阶段而不中断
4. 所有现有测试仍通过（`pytest` + `ruff check`）

### 验收方式
- `pytest` 全量通过，无回归
- `ruff check` 无 lint 错误
- 手动或自动化确认 pipeline 8 阶段均被执行并记录 outcome
- 确认 dashboard 页面渲染包含新流程指示器和全量 phase 行

## 约束

### 不能修改的文件
- pipeline 引擎代码（phase 调度、daemon cycle 等）
- Phase 枚举定义文件
- 现有测试用例（可新增但不改已有断言）
- `requirements.txt` / `pyproject.toml`

### 项目部署分支
- main

### 已知风险
- `_phase_table` 函数签名或返回格式变更可能影响 dashboard API 端点的 JSON 输出，需确认兼容性
- dashboard.html 中新增 HTML/CSS 可能影响移动端布局，但范围极小风险可控
- pipeline 验证依赖 daemon 状态干净（无残留 stale lock），若 daemon 未重启可能影响验证结果

### 预估 token 消耗
- prompt: ~4000
- completion: ~2000
- 数据来源: 无历史参考
