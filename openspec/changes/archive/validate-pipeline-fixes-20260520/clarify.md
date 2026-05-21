# Clarify: validate-pipeline-fixes-20260520

## 需求拆解

### 原始需求
本次 proposal 是一个验证性任务，目标有二：
1. **Phase Table 完整性**：`metrics/dashboard.py` 的 `_phase_table` 函数当前只展示有数据的 phase 行，需改为展示 Phase 枚举的全部值，无数据的 phase 显示为 0，确保新增的 CLARIFY、ENRICH、OPTIMIZE 等阶段能被呈现。
2. **Pipeline 流程指示器**：在 dashboard 页面（`site/dashboard.html`）标题下方新增一行小字，显示完整 pipeline 流程 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`。

此 change 同时充当 pipeline 修复的端到端验证触发器。

### 拆解后的子任务
- [ ] 1. **Phase Table 枚举完整性**：修改 `zsiga/metrics/dashboard.py` 中 `_phase_table` 函数，使其遍历 Phase 枚举的所有成员生成行，无数据时计数/耗时等字段显示为 0 或 `-`（预估复杂度：低, 预估 token：~1500）
- [ ] 2. **Dashboard Pipeline 流程指示器**：在 `site/dashboard.html` 的标题区域（`<h1>` 下方）新增一行灰色小字，展示 pipeline 完整流程 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`，使用箭头分隔各阶段名称（预估复杂度：低, 预估 token：~800）

## 边界

### IN scope
- 修改 `_phase_table` 函数逻辑，确保所有 Phase 枚举值出现在表格中
- 在 `dashboard.html` 标题下方添加 pipeline 流程指示器文字
- 触发完整 pipeline 各阶段运行以验证基础设施修复

### OUT of scope
- 不修改 pipeline 核心逻辑（phase 定义、状态机、转换规则等）
- 不修改 `zsiga/metrics/dashboard.py` 以外的 Python 源码
- 不修改 `site/dashboard.html` 以外的模板文件
- 不添加新的 Phase 枚举值（Phase 已在 pipeline 修复中新增）
- 不改变 dashboard API 端点或数据结构

### 依赖的外部条件
- Phase 枚举已包含 CLARIFY、ENRICH、OPTIMIZE 等阶段（由前序 pipeline 修复完成）
- `_phase_table` 函数当前存在于 `zsiga/metrics/dashboard.py` 且可正常调用
- dashboard.html 已有标题区域结构可供插入

## 目标

### 成功标准
1. `_phase_table` 函数输出包含 Phase 枚举所有成员的行，无数据阶段显示为 0
2. dashboard.html 标题下方可见一行 pipeline 流程指示器：`CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`
3. 所有既有测试通过（`pytest`），无 lint 错误（`ruff check`）
4. 本次 change 成功走完 CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER 全阶段

### 验收方式
- 检查 `_phase_table` 返回值/渲染结果包含所有 Phase 枚举成员
- 浏览器或 HTML 源码中可见 pipeline 流程指示器文字
- `pytest` 全部通过
- `ruff check` 无错误
- pipeline 各阶段 outcome 均为 success

## 约束

### 不能修改的文件
- `zsiga/pipeline/` 下所有文件（pipeline 核心逻辑）
- `zsiga/daemon/` 下所有文件
- `tests/` 下所有文件（不在本次 scope 内添加新测试）
- `requirements.txt`、`pyproject.toml`

### 项目部署分支
- main

### 已知风险
- `_phase_table` 函数签名或内部实现可能与预期不同，需先确认其当前逻辑再修改
- Phase 枚举的成员名称可能与 proposal 中列出的不完全一致（需确认实际枚举值）
- 本次 change 的主要目的是验证 pipeline，若 pipeline 本身存在未修复的 bug，可能在后续阶段失败

### 预估 token 消耗
- prompt: ~3000
- completion: ~2000
- 数据来源: 无历史参考
