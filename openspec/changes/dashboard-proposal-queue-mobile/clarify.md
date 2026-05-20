# Clarify: dashboard-proposal-queue-mobile

## 需求拆解

### 原始需求
改造 dashboard 的 Proposal Queue 区域：合并两个重复的 proposal queue 区块（一个 Python 静态渲染有数据，一个 JS 动态渲染永远空）为统一的 Python 渲染面板，包含"当前处理中"和"排队中"两个子区域；同时删除失效的 JS fetch 逻辑；并对整个页面做手机端兼容性改造。

### 拆解后的子任务

- [ ] 1. **合并 Proposal Queue 面板为统一 Python 渲染** — 删除静态 `{proposal_queue_section}` 占位和空的 `<div id="queue-section">`，改为在 `dashboard.py` 中渲染完整 queue 面板 HTML，含 Current（从 `daemon_state.json` 读 `current_change`/`current_phase`/heartbeat）和 Queued（扫描 `openspec/changes/` 目录）两个子区域。Current 区域含阶段进度条（8 阶段：CLARIFY→DELIVER），Queued 区域含序号、名称、项目、摘要。无数据时显示 Idle/Queue empty 占位文案。 (预估复杂度：高, 预估 token：~8000 / 无历史参考)

- [ ] 2. **阶段进度条组件** — 在 Current 区域实现 `CLARIFY → ENRICH → IMPLEMENT → REVIEW → VERIFY → OPTIMIZE → REFLECT → DELIVER` 的可视化进度条。当前阶段高亮，已完成标绿，未到灰色。数据来源为 `daemon_state.json` 的 `current_phase` 字段。 (预估复杂度：中, 预估 token：~3000 / 无历史参考)

- [ ] 3. **手机端兼容性 `@media` 查询** — 在 `<style>` 中添加 `@media (max-width: 768px)` 规则：卡片网格单列、hero 竖排、表格字号缩小、阶段进度条横滚、body padding 缩小。 (预估复杂度：低, 预估 token：~1500 / 无历史参考)

- [ ] 4. **删除失效 JS fetch 逻辑** — 删除 `<script>` 中对 `/api/status.json` 的 fetch 调用、`updateQueueSection` 函数、以及 `<div id="queue-section">` 空占位 div。 (预估复杂度：低, 预估 token：~800 / 无历史参考)

## 边界

### IN scope
- 修改 `zsiga/metrics/dashboard.py` 中的 Python 端渲染逻辑和 HTML 模板
- 修改 `site/dashboard.html` 的 `<style>` 添加 `@media` 查询
- 从 `daemon_state.json` 读取当前处理状态（`current_change`, `current_phase`, heartbeat）
- 扫描 `openspec/changes/` 目录获取排队中的 proposal 列表
- 删除失效的 JS fetch 逻辑和空占位 div

### OUT of scope
- 修改 `daemon.py` 或新增 API 端点
- 修改 `/api/status.json` 相关后端路由（直接删除前端调用）
- 修改 dashboard 以外的页面或模块
- 修改 Python 后端框架或路由层
- 新增 Python 依赖包

### 依赖的外部条件
- `daemon_state.json` 文件格式稳定，包含 `current_change`、`current_phase`、heartbeat 字段
- `openspec/changes/` 目录结构稳定，每个子目录含 `proposal.md`
- 现有深色主题 CSS 变量/色值体系保持不变

## 目标

### 成功标准
1. Dashboard 页面只存在一个 Proposal Queue 面板，由 Python 渲染，包含 Current + Queued 两个子区域
2. Current 区域正确显示当前处理的 proposal 名称、项目、阶段、进度条、开始时间；无 proposal 时显示 Idle 占位
3. 阶段进度条正确标注 8 个阶段，当前高亮、已完成标绿、未到灰色
4. Queued 区域列出所有待处理 proposal（序号、名称、项目、摘要）；无排队时显示 empty 占位
5. 页面在 ≤768px 宽度下布局正常：单列卡片、竖排 hero、可横滚进度条
6. 无 `/api/status.json` 的 fetch 调用，浏览器控制台无 404 错误
7. `ruff check` 通过，无 lint 错误

### 验收方式
- 在桌面浏览器打开 dashboard，验证 queue 面板内容正确
- 在手机或浏览器 DevTools 模拟 768px 宽度，验证响应式布局
- 检查浏览器控制台无 `/api/status.json` 404 错误
- 运行 `ruff check zsiga/metrics/dashboard.py` 通过
- 运行 `pytest tests/test_dashboard_api.py tests/test_dashboard_queue.py` 通过

## 约束

### 不能修改的文件
- `zsiga/daemon.py`
- `zsiga/` 下除 `metrics/dashboard.py` 以外的所有文件
- `requirements.txt` / `pyproject.toml`
- 任何 API 路由文件

### 项目部署分支
- main（默认分支）

### 已知风险
- `daemon_state.json` 中 `current_phase` 字段值可能与 8 阶段枚举不完全匹配，需做防御性映射
- `openspec/changes/` 下的目录可能包含非 proposal 子目录（如 `.phase_state` 文件），需过滤
- 合并 queue 面板可能影响依赖旧 HTML 结构的测试用例

### 预估 token 消耗
- prompt: ~6000
- completion: ~5000
- 数据来源: 无历史参考
