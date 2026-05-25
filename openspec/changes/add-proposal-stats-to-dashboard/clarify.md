# clarify.md — add-proposal-stats-to-dashboard

## 需求拆解

### 原始需求
在 `zsiga/daemon.py` 中新增 `GET /api/proposal-stats` HTTP 端点，从本地 SQLite 数据库（`data/zsiga.db`）的 `changes` 表中读取聚合统计信息并以 JSON 返回。返回结构包含：总提案数 (`total`)、按结果分组计数 (`by_outcome`)、平均耗时 (`avg_duration_seconds`)、最近 5 条记录 (`recent`)。

### 拆解后的子任务

- [ ] 1. **实现 `_build_proposal_stats_json` 数据查询函数** (预估复杂度：中, 预估 token：~3000 / 无历史参考)
  - 文件：`zsiga/daemon.py`
  - 函数签名：`_build_proposal_stats_json(db_path: str) -> dict`
  - 查询 `changes` 表，计算 4 项聚合指标（total、by_outcome、avg_duration_seconds、recent）
  - 使用 `sqlite3` 标准库，纯只读查询
  - 需处理 `changes` 表不存在或字段缺失的防御性异常

- [ ] 2. **注册 `/api/proposal-stats` HTTP 路由** (预估复杂度：低, 预估 token：~1500 / 无历史参考)
  - 文件：`zsiga/daemon.py`
  - 在现有 HTTP handler 中添加路由分支（复用 `/api/status` 的路由分发模式）
  - 调用 `_build_proposal_stats_json` 并以 `application/json` 返回
  - 异常时返回 500 + 错误信息 JSON

- [ ] 3. **编写测试** (预估复杂度：中, 预估 token：~2500 / 无历史参考)
  - 文件：`tests/test_dashboard_api.py`（已有）或新建 `tests/test_spec_add_proposal_stats_to_dashboard__proposal_stats_endpoint.py`
  - 覆盖：正常返回（mock SQLite）、表不存在时的 500 降级、JSON 结构字段完整性
  - 复用项目现有 conftest 中的 daemon test harness

## 边界

### IN scope
- `zsiga/daemon.py` 新增 `_build_proposal_stats_json` 函数和 `/api/proposal-stats` 路由
- 对应的单元测试
- 只读 SQL 查询，不写入、不修改 `changes` 表

### OUT of scope
- 前端 dashboard.html 渲染 proposal-stats 数据
- WebSocket 推送 / 实时流式统计
- 历史趋势图表
- 修改现有 `/api/status`、`/api/metrics`、`/api/current` 端点
- 新增 pip 依赖

### 依赖的外部条件
- `data/zsiga.db` 中存在 `changes` 表且包含 `outcome`、`started_at`、`finished_at`、`change_name`、`id` 字段（需在实现前验证表结构，若不存在需做防御性降级）
- 现有 daemon HTTP server 框架（`_serve_dashboard` 或类似函数）可扩展新路由
- `sqlite3` 模块可用（Python 标准库，无风险）

## 目标

### 成功标准
1. `curl http://localhost:58175/api/proposal-stats` 返回 HTTP 200，Content-Type 为 `application/json`
2. JSON 包含 `total`（int）、`by_outcome`（dict[str,int]）、`avg_duration_seconds`（float or None）、`recent`（list）四个顶层 key
3. `recent` 列表最多包含 5 条记录，每条含 `change_name`、`outcome`、`started_at`、`finished_at`
4. 现有端点 `/api/status`、`/` 行为不变
5. 当 `changes` 表不存在或查询失败时，端点返回 HTTP 500 而非导致 daemon 崩溃
6. `ruff check` 和 `pytest` 全部通过

### 验收方式
- 运行 `curl http://localhost:58175/api/proposal-stats` 确认 200 + JSON 结构
- 运行 `pytest tests/ -x` 确认所有测试通过（含新增测试）
- 运行 `ruff check zsiga/daemon.py` 确认无 lint 错误
- 手动验证现有 `/api/status` 端点仍正常工作

## 约束

### 不能修改的文件
- `site/dashboard.html`（前端不在范围内）
- `zsiga/config.py`（无需配置变更）
- `requirements.txt` / `pyproject.toml`（无新依赖）
- 现有路由处理逻辑（仅添加新分支，不改旧分支）

### 项目部署分支
- `zsiga/add-proposal-stats-to-dashboard`

### 已知风险
- **`changes` 表结构未验证**：proposal 假设 `changes` 表包含 `outcome`、`started_at`、`finished_at`、`change_name`、`id` 字段，但并行探索未确认该表是否存在或 schema 是否匹配。需在实现首步验证，若不存在须做防御性降级（返回空统计 + 200，或 503）
- **历史同类任务失败**：`dashboard-add-feedback-loop-metrics` 在 implement/verify 阶段连续失败 4 次（向 dashboard 添加聚合统计指标的同类任务）。需严格遵循项目现有代码模式，避免引入新抽象
- **daemon 代码修改**：daemon 是核心运行时组件，修改需确保异常隔离——新增路由的任何错误不得影响现有端点和主循环

### 预估 token 消耗
- prompt: ~8000
- completion: ~5000
- 数据来源: 无历史参考（同类任务 dashboard-add-feedback-loop-metrics 失败，不可作为基准）
