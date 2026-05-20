# Clarify: validate-pipeline-fixes-20260520

## 需求拆解
### 原始需求
验证近期 pipeline 基础设施修复是否生效。通过修改两个文件触发完整 pipeline 流程，同时为 dashboard 补充新阶段（CLARIFY、ENRICH、OPTIMIZE）的展示能力：1) `_phase_table` 函数确保 Phase 枚举所有值都出现在表格中（无数据时展示为 0）；2) dashboard 页面标题下方添加 pipeline 流程指示条。

### 拆解后的子任务
- [ ] 1. `_phase_table` 函数补全阶段展示：修改 `zsiga/metrics/dashboard.py` 中 `_phase_table`，遍历 Phase 枚举所有成员，对无数据阶段填充零值行，确保 CLARIFY/ENRICH/OPTIMIZE 等新阶段始终可见 (预估复杂度：低, 预估 token：~1500 / 无历史参考)
- [ ] 2. Dashboard 流程指示条：在 `site/dashboard.html` 页面标题（h1）下方新增一行小字，显示完整 pipeline 流程 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`，使用浅灰色小字体 (预估复杂度：低, 预估 token：~800 / 无历史参考)

## 边界
### IN scope
- `_phase_table` 函数修改，使所有 Phase 枚举值始终展示
- dashboard.html 标题下方新增 pipeline 流程指示条
- 触发完整 pipeline 验证各阶段是否正常工作

### OUT of scope
- pipeline 核心逻辑修改（CLARIFY/ENRICH/OPTIMIZE/REVIEW/VERIFY 等阶段代码）
- metrics 采集逻辑修改
- 其他 dashboard 功能改动
- 数据库 schema 变更

### 依赖的外部条件
- Phase 枚举已包含 CLARIFY、ENRICH、OPTIMIZE 等阶段值
- `_phase_table` 函数当前能正确展示有数据的阶段
- dashboard.html 已有标题区域可插入新内容
- Pipeline 各阶段（CLARIFY→DELIVER）在 daemon 中已注册并可触发

## 目标
### 成功标准
1. `_phase_table` 返回的表格包含 Phase 枚举中所有成员，无数据阶段显示为 0
2. dashboard.html 标题下方可见 pipeline 流程指示条文本
3. 完整 pipeline（CLARIFY → DELIVER）各阶段正常执行无报错
4. 所有现有测试通过（ruff + pytest）

### 验收方式
- 手动检查 `_phase_table` 输出包含 CLARIFY/ENRICH/OPTIMIZE 行
- 浏览器打开 dashboard.html 确认流程指示条可见
- 运行 `python -m pytest tests/ -x` 全部通过
- 运行 `ruff check` 无错误

## 约束
### 不能修改的文件
- `zsiga/pipeline/` 下所有文件（pipeline 核心逻辑）
- `zsiga/daemon.py`（daemon 主循环）
- `tests/` 下所有测试文件（本轮不新增测试）
- `venv2/` 下所有文件

### 项目部署分支
main

### 已知风险
- Phase 枚举定义位置未知，需定位确认枚举成员是否齐全
- `_phase_table` 函数签名和返回格式需确认，避免破坏现有调用方
- pipeline 验证依赖 daemon 完整运行，若中间阶段失败则验证不完整
- dashboard.html 已被截断展示，需确认标题区域确切位置

### 预估 token 消耗
- prompt: ~3000
- completion: ~1500
- 数据来源: 无历史参考
