# Clarify: validate-pipeline-fixes-20260520

## 需求拆解

### 原始需求
本次 proposal 是验证性任务，通过修改 dashboard 展示逻辑来触发完整 pipeline（CLARIFY → ENRICH → REFLECT → DELIVER），验证近期 pipeline 基础设施修复是否生效。具体修改两处：
1. `_phase_table` 函数确保 Phase 枚举所有值（含新增的 CLARIFY、ENRICH、OPTIMIZE）均出现在表格中，无数据时展示为 0
2. dashboard 页面标题下方加一行小字显示完整 pipeline 流程名称

### 拆解后的子任务
- [ ] 1. **Phase 表格全覆盖** — 修改 `zsiga/metrics/dashboard.py` 中 `_phase_table` 函数，使表格行覆盖 Phase 枚举的全部成员（含 CLARIFY / ENRICH / OPTIMIZE），无历史数据时展示计数为 0（预估复杂度：低, 预估 token：~3000 / 无历史参考）
- [ ] 2. **Dashboard 流程指示条** — 修改 `site/dashboard.html`，在标题 (`<h1>`) 下方添加一行小字 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`，用浅灰色渲染（预估复杂度：低, 预估 token：~1500 / 无历史参考）

## 边界

### IN scope
- 修改 `zsiga/metrics/dashboard.py` 中 `_phase_table` 函数，遍历 Phase 枚举而非仅展示有数据的 phase
- 修改 `site/dashboard.html`，在页面标题区域添加 pipeline 流程指示文字
- 通过这两处改动触发完整 pipeline 运行，验证各阶段 outcome

### OUT of scope
- 不修改 pipeline 核心逻辑（orchestrator、phase runner 等）
- 不修改 Phase 枚举定义本身
- 不新增 Phase 枚举成员（CLARIFY / ENRICH / OPTIMIZE 应已存在）
- 不修改 dashboard 数据采集 / 指标计算逻辑
- 不涉及数据库或持久化存储变更

### 依赖的外部条件
- Phase 枚举已包含 CLARIFY、ENRICH、OPTIMIZE 成员（需确认）
- `_phase_table` 函数当前仅展示有数据的 phase，需改为全量展示
- dashboard.html 已有标题 `<h1>` 区域可供追加文字

## 目标

### 成功标准
1. `_phase_table` 输出的表格包含 Phase 枚举的全部成员行，即使对应计数为 0 也正常渲染
2. dashboard 页面标题下方可见 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER` 文字
3. `pytest tests/test_dashboard_api.py` 全部通过
4. `ruff check zsiga/metrics/dashboard.py` 无错误
5. 完整 pipeline 运行后各阶段（CLARIFY / ENRICH / IMPLEMENT / REVIEW / VERIFY / OPTIMIZE / REFLECT / DELIVER）均有 outcome 记录

### 验收方式
- 运行 `pytest tests/test_dashboard_api.py` 确认无回归
- 运行 `ruff check zsiga/metrics/dashboard.py site/dashboard.html` 确认 lint 通过
- 检查 `_phase_table` 返回内容包含所有 Phase 枚举值
- 浏览器或 HTML 源码确认流程指示文字存在

## 约束

### 不能修改的文件
- pipeline 核心逻辑文件（orchestrator、phase runner 等）
- Phase 枚举定义文件（除非确认缺少成员才允许补充）
- 任何 `tests/` 目录下的文件
- `requirements.txt`、`pyproject.toml`

### 项目部署分支
main

### 已知风险
- Phase 枚举可能尚未包含 CLARIFY / ENRICH / OPTIMIZE 成员，若缺失需在枚举文件中补充（超出预期 scope）
- `_phase_table` 函数可能依赖外部数据结构（如 metrics dict），全量展示时需确保空值处理不会触发 KeyError
- dashboard.html 为静态 HTML，流程指示文字为硬编码字符串，后续 pipeline 阶段名变更需手动同步

### 预估 token 消耗
- prompt: ~5000
- completion: ~2000
- 数据来源: 无历史参考
