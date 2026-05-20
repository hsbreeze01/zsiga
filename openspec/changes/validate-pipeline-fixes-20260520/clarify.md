# Clarify: validate-pipeline-fixes-20260520

## 需求拆解

### 原始需求
验证近期 pipeline 基础设施修复是否生效。通过修改 dashboard 的 Phase Performance 表格和页面标题，确保新增的 CLARIFY、ENRICH、OPTIMIZE 等阶段能在 dashboard 中正确展示，同时作为一次真实 pipeline 端到端运行的验证。

### 拆解后的子任务
- [ ] 1. 修复 `_phase_table` 函数确保 Phase 枚举全量展示 (预估复杂度：低, 预估 token：~3000 / 无历史参考)
  - 文件范围：`zsiga/metrics/dashboard.py`（或 `metrics/dashboard.py`）
  - 当前 `_phase_table` 只展示有数据的 phase，需改为遍历 Phase 枚举所有值，无数据的阶段展示为 0
- [ ] 2. 在 dashboard 页面标题下方添加 pipeline 流程指示器 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
  - 文件范围：`site/dashboard.html`
  - 在页面标题 `<h1>` 下方新增一行小字，显示完整 pipeline 流程：`CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`
  - 需使用 HTML 实体或 CSS 样式使其与现有页面风格一致

## 边界

### IN scope
- 修改 `_phase_table` 函数以展示所有 Phase 枚举值（含无数据阶段）
- 在 `dashboard.html` 标题下方添加 pipeline 流程指示器文本
- 通过完整 pipeline 运行验证修复效果

### OUT of scope
- 不修改 pipeline 核心逻辑（daemon、reviewer、verifier 等角色代码）
- 不修改 Phase 枚举定义本身
- 不添加新的 pipeline 阶段
- 不修改 dashboard 的其他表格或卡片组件
- 不修改 API 端点

### 依赖的外部条件
- Phase 枚举已包含 CLARIFY、ENRICH、OPTIMIZE 等值
- `metrics/dashboard.py` 中的 `_phase_table` 函数存在且可定位
- dashboard 前端通过 JS 动态加载 phase table 数据

## 目标

### 成功标准
1. `_phase_table` 返回的表格包含 Phase 枚举中所有阶段，无数据的阶段行显示为 0 而非被省略
2. dashboard.html 页面标题下方可见一行 pipeline 流程文字：`CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`
3. 整个 change 能成功走完完整 pipeline（CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER），无阶段报错
4. 所有修改通过 ruff lint 检查
5. 相关测试通过

### 验收方式
- 检查 `_phase_table` 输出是否包含所有 Phase 枚举值
- 浏览器或 HTML 检查 dashboard 标题下方的流程指示器文本存在且样式正确
- pipeline 端到端运行无报错，每个阶段 outcome 为 success
- `ruff check` 和 `pytest` 通过

## 约束

### 不能修改的文件
- pipeline 核心逻辑文件（daemon、reviewer、verifier、implementer 等角色模块）
- Phase 枚举定义文件
- `pyproject.toml`、`requirements.txt`
- `venv2/` 下任何文件

### 项目部署分支
main

### 已知风险
- `_phase_table` 函数的实际路径可能与 `metrics/dashboard.py` 不完全一致，需在实施时确认确切文件位置
- dashboard.html 中动态渲染 phase table 的 JS 可能会覆盖后端返回的空数据行，需确认前后端数据流
- pipeline 首次运行新阶段时 metrics 数据可能为空，需确保空数据展示逻辑正确

### 预估 token 消耗
- prompt: ~8000
- completion: ~3000
- 数据来源: 无历史参考
