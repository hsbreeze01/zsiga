# Clarify: validate-pipeline-fixes-20260520

## 需求拆解

### 原始需求
验证近期 pipeline 基础设施修复是否生效。通过修改一个简单功能点（dashboard phase 展示），触发完整 pipeline 流程，观察各阶段 outcome。具体修改两处：1) `_phase_table` 确保展示所有 Phase 枚举值（含无数据的新阶段）；2) dashboard 页面标题下新增 pipeline 完整流程标注行。

### 拆解后的子任务
- [ ] 1. **_phase_table 全阶段展示**：修改 `zsiga/metrics/dashboard.py` 中 `_phase_table` 函数，使其遍历 Phase 枚举所有值渲染表格行，无数据时显示 0 而非跳过。需确认 Phase 枚举定义包含 CLARIFY / ENRICH / OPTIMIZE 等新阶段。(预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 2. **Dashboard 标题下新增 pipeline 流程行**：在 `site/dashboard.html` 的 `<h1>` 标题元素下方插入一行小字，内容为 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`，样式与现有 `.meta` 一致。(预估复杂度：低, 预估 token：~800 / 无历史参考)

## 边界

### IN scope
- 修改 `zsiga/metrics/dashboard.py` 中 `_phase_table` 函数
- 修改 `site/dashboard.html` 页面标题区域
- 确认 Phase 枚举定义覆盖所有 8 个阶段

### OUT of scope
- 不修改 pipeline 核心逻辑（daemon、roles、config 等）
- 不新增 Phase 枚举成员（如已有则只读取）
- 不修改 dashboard API 端点
- 不修改前端 JS 逻辑

### 依赖的外部条件
- Phase 枚举已包含 CLARIFY、ENRICH、OPTIMIZE 等阶段值（需验证）
- dashboard.html 已有标题 `<h1>` 元素可作为插入锚点

## 目标

### 成功标准
1. `_phase_table` 输出包含 Phase 枚举中所有阶段，无数据阶段显示为 0
2. dashboard.html 标题下方出现 pipeline 完整流程文字 `CLARIFY → ENRICH → ... → DELIVER`
3. 现有测试全部通过（`pytest` + `ruff check`）
4. 触发完整 pipeline 流程并成功走完全部 8 个阶段

### 验收方式
- `ruff check` 无错误
- `pytest` 全部通过
- 手动或自动化触发 pipeline，观察 `.phase_state` 文件确认各阶段正确流转

## 约束

### 不能修改的文件
- `zsiga/daemon.py`（pipeline 核心）
- `zsiga/roles.py`（角色调度）
- `zsiga/config.py`（配置）
- 任何 `tests/` 文件

### 项目部署分支
- main

### 已知风险
- Phase 枚举可能尚未包含 CLARIFY / ENRICH / OPTIMIZE，需先确认枚举定义再决定实现策略
- dashboard.html 已被多次修改，需注意插入位置不破坏现有结构

### 预估 token 消耗
- prompt: ~4000
- completion: ~1500
- 数据来源: 无历史参考
