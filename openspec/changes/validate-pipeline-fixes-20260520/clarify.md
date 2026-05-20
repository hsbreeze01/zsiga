# Clarify: validate-pipeline-fixes-20260520

## 需求拆解

### 原始需求
本次是一个验证性任务，通过修改一个简单的功能点来触发完整 pipeline 运行（CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER），验证近期 pipeline 基础设施修复是否生效。具体修改两个文件：`zsiga/metrics/dashboard.py` 和 `site/dashboard.html`。

### 拆解后的子任务
- [ ] 1. **_phase_table 补全 Phase 枚举展示**：修改 `zsiga/metrics/dashboard.py` 中 `_phase_table` 函数，确保 Phase 枚举的所有值都能出现在表格行中，即使该阶段无历史数据也展示为 0。需先确认 Phase 枚举定义及其与现有数据的交互方式。（预估复杂度：低, 预估 token：~3000 / 无历史参考）
- [ ] 2. **dashboard.html 新增 pipeline 流程指示行**：在 `site/dashboard.html` 页面标题（`<h1>`）下方加一行小字，显示完整 pipeline 流程 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`，使用灰色小字体，不破坏现有布局。（预估复杂度：低, 预估 token：~1500 / 无历史参考）
- [ ] 3. **验证 pipeline 全阶段贯通**：确认修改后项目所有测试通过（pytest + ruff），确保改动未引入回归。（预估复杂度：低, 预估 token：~1000 / 无历史参考）

## 边界

### IN scope
- 修改 `zsiga/metrics/dashboard.py` 中 `_phase_table` 函数，使其展示所有 Phase 枚举值
- 修改 `site/dashboard.html`，在标题下方添加 pipeline 流程指示文字
- 运行测试和 lint 验证

### OUT of scope
- 不修改 pipeline 核心逻辑（daemon、phase 执行引擎等）
- 不新增 Phase 枚举值（只确保已有枚举全部展示）
- 不修改 dashboard 的其他 UI 组件或数据采集逻辑
- 不涉及 metrics 数据存储或采集方式变更

### 依赖的外部条件
- Phase 枚举已包含 CLARIFY、ENRICH、OPTIMIZE 等新阶段值（需在实现时确认）
- 现有测试套件可正常运行

## 目标

### 成功标准
1. `_phase_table` 输出的表格包含 Phase 枚举的全部值，无数据阶段显示为 0
2. dashboard.html 标题下方出现 pipeline 完整流程指示行：`CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`
3. 全部测试通过（pytest），无 ruff lint 错误
4. pipeline 全阶段成功走完（本次变更本身即作为 pipeline 验证的载体）

### 验收方式
- `pytest tests/` 全绿
- `ruff check zsiga/metrics/dashboard.py` 无错误
- `ruff check site/` 无错误（如适用）
- 浏览器打开 dashboard.html 可见新增的 pipeline 流程行

## 约束

### 不能修改的文件
- pipeline 核心逻辑文件（daemon、phase engine、scheduler 等）
- 除 `zsiga/metrics/dashboard.py` 和 `site/dashboard.html` 外的任何文件

### 项目部署分支
- main

### 已知风险
- Phase 枚举可能尚未包含 CLARIFY、ENRICH、OPTIMIZE 等阶段值，需实现时确认；若缺失则需扩展枚举定义（仍属于 dashboard.py 范围内的上游依赖）
- dashboard.html 可能被其他测试引用，修改需确保不破坏现有测试

### 预估 token 消耗
- prompt: ~8000
- completion: ~3000
- 数据来源: 无历史参考
