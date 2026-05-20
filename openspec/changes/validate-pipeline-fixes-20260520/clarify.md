# clarify.md — validate-pipeline-fixes-20260520

## 需求拆解

### 原始需求
本次 proposal 是一个验证性任务，通过修改 dashboard 展示层的小功能点，触发完整 pipeline（CLARIFY → ENRICH → OPTIMIZE → REFLECT 等新阶段），验证近期 pipeline 基础设施修复是否生效。具体修改两处：确保 `_phase_table` 展示所有 Phase 枚举值（含空数据行）；在 dashboard 标题下方加一行 pipeline 流程示意。

### 拆解后的子任务
- [ ] 1. **Phase 表格完整展示**：修改 `zsiga/metrics/dashboard.py` 的 `_phase_table` 函数，使其遍历 Phase 枚举的所有值生成表格行，无数据时展示为 0（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 2. **Dashboard 标题下方新增 pipeline 流程行**：修改 `site/dashboard.html`，在页面标题 `<h1>` 下方添加一行小字，内容为 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`，使用合适的灰色小号字体样式（预估复杂度：低, 预估 token：~1500 / 无历史参考）

## 边界

### IN scope
- 修改 `zsiga/metrics/dashboard.py` 中 `_phase_table` 函数，遍历 Phase 枚举全量输出行
- 修改 `site/dashboard.html` 标题区域，增加 pipeline 流程文字行
- 确保无数据阶段显示为 0 而非被隐藏

### OUT of scope
- 不修改 pipeline 核心逻辑（phases 定义、调度、状态机等）
- 不修改任何 Phase 枚举定义本身
- 不涉及 dashboard 的 API 端点或数据采集逻辑
- 不增加新的 CSS 动画或交互功能

### 依赖的外部条件
- Phase 枚举已包含 CLARIFY、ENRICH、OPTIMIZE、REFLECT 等值
- `_phase_table` 函数当前能正确展示已有数据的 phase
- `site/dashboard.html` 已有标题区域 `<h1>` 元素

## 目标

### 成功标准
1. `_phase_table` 输出包含 Phase 枚举的每一个值，无数据阶段显示为 0
2. dashboard 页面标题下方可见 pipeline 完整流程文字：`CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`
3. 修改通过 `ruff check` 和 `pytest` 无报错
4. 完整 pipeline 8 个阶段均被触发并正常完成

### 验收方式
- 运行 `ruff check zsiga/metrics/dashboard.py` 无 lint 错误
- 运行 `pytest tests/ -x -q` 全部通过
- 在 dashboard.html 中可目视确认新增流程行存在
- 检查 `_phase_table` 输出覆盖所有 Phase 枚举成员

## 约束

### 不能修改的文件
- pipeline 核心调度逻辑文件（任何 phases/ 目录或 pipeline 引擎文件）
- Phase 枚举定义文件
- dashboard API 端点代码（如存在）

### 项目部署分支
main

### 已知风险
- Phase 枚举的成员名称可能与 dashboard 现有硬编码字符串不完全一致，需确认枚举值
- dashboard.html 可能在后续版本被模板引擎替代，静态修改可能需要适配
- 这是一个验证性任务，主要目的是触发完整 pipeline 流程，功能修改本身较小

### 预估 token 消耗
- prompt: ~6000
- completion: ~3000
- 数据来源: 无历史参考
