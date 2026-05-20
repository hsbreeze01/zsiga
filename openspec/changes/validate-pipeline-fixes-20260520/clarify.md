# Clarify: validate-pipeline-fixes-20260520

## 需求拆解

### 原始需求
验证近期 pipeline 基础设施修复（Review 兜底写入、Verify STALE_LIMIT、CLARIFY/ENRICH/OPTIMIZE/REFLECT 独立阶段）是否生效。通过修改 dashboard 的 Phase Performance 表格和页面标题区域，触发完整 pipeline 流程并观察各阶段 outcome。

### 拆解后的子任务
- [ ] 1. `_phase_table` 函数：确保 Phase 枚举的所有值（CLARIFY / ENRICH / IMPLEMENT / REVIEW / VERIFY / OPTIMIZE / REFLECT / DELIVER）均出现在表格行中，无数据时展示为 0（预估复杂度：低, 预估 token：~2000 / 无历史参考）
- [ ] 2. `site/dashboard.html` 页面标题下方新增一行小字，展示完整 pipeline 流程 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER`（预估复杂度：低, 预估 token：~800 / 无历史参考）

## 边界

### IN scope
- `zsiga/metrics/dashboard.py` 中 `_phase_table` 函数补全 Phase 枚举展示
- `site/dashboard.html` 标题下方添加 pipeline 流程指示行
- 确保 Phase 枚举新增值（CLARIFY / ENRICH / OPTIMIZE）在无 metrics 数据时仍以 0 值出现

### OUT of scope
- 修改 pipeline 核心逻辑（clarify / implement / review / verify 等阶段代码）
- 修改 metrics 数据采集或存储逻辑
- 修改 Phase 枚举定义本身
- 新增测试用例（验证性任务，非功能开发）

### 依赖的外部条件
- Phase 枚举已包含 CLARIFY / ENRICH / OPTIMIZE 等阶段值（近期修复中已添加）
- `metrics/dashboard.py` 的 `_phase_table` 函数已存在并可正常工作
- 现有 dashboard API 端点能返回 phase 维度的 metrics 数据

## 目标

### 成功标准
1. `_phase_table` 输出的表格包含 Phase 枚举的全部 8 个阶段，无数据阶段显示 0 值
2. `site/dashboard.html` 在 `<h1>` 标题下方可见一行小字 pipeline 流程指示
3. 完整 pipeline 流程（CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER）均被触发并产生 outcome 记录
4. 所有修改通过 `ruff check` 和 `pytest`（如有相关测试）

### 验收方式
- 检查 `zsiga/metrics/dashboard.py` 中 `_phase_table` 是否遍历 Phase 枚举全部成员
- 检查 `site/dashboard.html` 是否包含 pipeline 流程指示行
- 观察 pipeline 运行日志确认各阶段均有 outcome 输出
- `ruff check` 和 `pytest` 通过

## 约束

### 不能修改的文件
- pipeline 各阶段实现代码（clarify.py / implement.py / review.py / verify.py / reflect.py 等）
- Phase 枚举定义文件（除非仅读取）
- metrics 数据采集与存储逻辑
- tests/ 目录下已有测试

### 项目部署分支
- main

### 已知风险
- Phase 枚举路径可能与预期不同（需确认枚举定义位置）
- dashboard API 端点返回数据格式可能影响 `_phase_table` 渲染
- pipeline 运行可能因已有未提交文件（daemon_state.json / zsiga.db 等）导致 git checkout 冲突（历史 daemon.cycle_error 模式）

### 预估 token 消耗
- prompt: ~4000
- completion: ~1500
- 数据来源: 无历史参考
