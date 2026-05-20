# Clarify: dashboard-proposal-queue-mobile

## 需求拆解

### 原始需求
改造 dashboard 的 Proposal Queue 区域：合并两个冗余的 queue 区块（静态渲染 + 空的 JS 动态渲染）为统一的 Python 渲染面板，展示当前处理进度（从 daemon_state.json 读取）和排队列表（从 changes 目录扫描）；删除失效的 JS fetch 逻辑；添加手机端 `@media` 适配样式。

### 拆解后的子任务
- [ ] 1. 合并 Proposal Queue 面板：删除静态 `{proposal_queue_section}` 占位和空 `<div id="queue-section">`，改为 Python 端渲染完整 queue 面板 HTML，包含 Current（处理中）和 Queued（排队中）两个子区域 (预估复杂度：高, 预估 token：~8000 / 无历史参考)
- [ ] 2. 当前处理中（Current）子区域：读取 daemon_state.json 的 `current_change`/`current_phase`/`heartbeat` 字段，渲染 proposal 名称、项目、阶段进度条（CLARIFY→DELIVER 八阶段高亮/标绿/灰色）、开始时间；无任务时显示 Idle 状态 (预估复杂度：中, 预估 token：~5000 / 无历史参考)
- [ ] 3. 排队中（Queued）子区域：扫描 openspec/changes/ 目录获取待处理 proposal 列表，渲染序号、名称、项目、proposal.md 首行标题摘要；队列为空时显示 "Queue empty" (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 4. 手机端兼容性：在 `<style>` 中添加 `@media (max-width: 768px)` 查询，包含卡片单列、表格字号缩小、hero 竖排、阶段进度条横滚等规则 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 5. 清理失效 JS：删除 `<script>` 中对 `/api/status.json` 的 fetch 调用、`updateQueueSection` 函数及关联的空占位 div (预估复杂度：低, 预估 token：~1500 / 无历史参考)
- [ ] 6. 阶段进度条样式：为八阶段进度条（CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER）添加 CSS 样式（高亮、标绿、灰色状态）及手机端横滚支持 (预估复杂度：低, 预估 token：~2000 / 无历史参考)

## 边界

### IN scope
- 修改 `zsiga/metrics/dashboard.py` 中 dashboard HTML 生成逻辑
- 合并两个 proposal queue 区块为一个 Python 渲染面板
- 从 daemon_state.json 读取当前处理状态
- 从 openspec/changes/ 目录扫描排队 proposal
- 添加 `@media` 手机端适配 CSS
- 删除失效的 JS fetch 逻辑和空占位 div
- 阶段进度条视觉组件（样式 + 数据绑定）

### OUT of scope
- 修改 daemon.py 或新增 API 端点
- 修改 daemon_state.json 的数据结构
- 后端 API 开发（/api/status.json）
- 修改 dashboard 以外的 Python 模块
- 新增 Python 包依赖

### 依赖的外部条件
- daemon_state.json 文件存在于项目运行目录，包含 `current_change`、`current_phase`、`heartbeat` 字段
- openspec/changes/ 目录结构包含各 proposal 子目录，每个子目录内有 proposal.md
- dashboard.py 已有 HTML 模板渲染机制（现有代码可参考）

## 目标

### 成功标准
1. dashboard.html 中不再存在两个 proposal queue 区块，只有一个由 Python 统一渲染的 queue 面板
2. Queue 面板正确显示 Current（处理中）和 Queued（排队中）两个子区域
3. Current 子区域能从 daemon_state.json 读取并显示当前 proposal 名称、项目、阶段进度条（八阶段）和开始时间；无任务时显示 Idle
4. Queued 子区域能扫描 changes 目录并显示待处理 proposal 列表；为空时显示 "Queue empty"
5. 页面在 ≤768px 宽度下卡片单列、表格可读、hero 竖排、进度条可横滚
6. 不存在对 `/api/status.json` 的 fetch 调用和 `updateQueueSection` 函数
7. 现有 dashboard 测试通过，无 ruff lint 错误

### 验收方式
- 运行 `python -m pytest tests/test_dashboard_api.py tests/test_dashboard_queue.py -x` 确认通过
- 运行 `ruff check zsiga/metrics/dashboard.py` 确认无 lint 错误
- 手动在浏览器中缩放到手机宽度验证响应式布局

## 约束

### 不能修改的文件
- `zsiga/daemon.py`
- `zsiga/metrics/` 目录下除 `dashboard.py` 以外的文件
- 任何新增 API 端点文件
- `requirements.txt` / `pyproject.toml`

### 项目部署分支
- main

### 已知风险
- daemon_state.json 文件可能不存在（首次运行前），需要优雅降级显示 Idle 状态
- openspec/changes/ 目录下的 proposal.md 格式可能不一致，提取首行标题需做防御性解析
- 现有 dashboard.py 的 HTML 模板是字符串拼接，改动幅度较大需注意转义和缩进一致性

### 预估 token 消耗
- prompt: ~12000
- completion: ~8000
- 数据来源: 无历史参考
