# clarify.md — add-health-check-endpoint

## 需求拆解

### 原始需求
在 `zsiga/daemon.py` 中新增 `GET /api/health` 端点，执行轻量级存活检查：验证 daemon 能连接 SQLite 数据库并读取 `changes` 表。健康时返回 HTTP 200 + `{"status": "healthy", "db_records": N, "timestamp": "ISO8601"}`；不健康时返回 HTTP 503 + `{"status": "unhealthy", "error": "..."}`。

### 拆解后的子任务
- [ ] 1. 实现 `_health_check(db_path: str) -> dict` 函数，封装 SQLite 连接 + `SELECT COUNT(*) FROM changes` 查询，返回标准化 health 字典 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 2. 在 daemon.py 的 HTTP handler 中注册 `/api/health` 路由，调用 `_health_check`，根据返回值映射为 HTTP 200 或 503，注入 `timestamp` 字段 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
- [ ] 3. 编写测试：覆盖 healthy / db-missing / table-missing 三种场景，验证 status code 与 response schema (预估复杂度：中, 预估 token：~3000 / 无历史参考)

## 边界

### IN scope
- `_health_check` 函数实现（SQLite 连接 + COUNT 查询 + 错误捕获）
- `/api/health` HTTP 路由注册（200/503 状态码映射）
- 响应 JSON schema：`status`、`db_records`、`timestamp`（healthy）/ `status`、`error`（unhealthy）
- 单元测试覆盖 happy path 和 failure path

### OUT of scope
- UI / Dashboard 展示健康状态
- 外部监控系统（Prometheus、Alertmanager）集成
- 数据库修复或自动恢复逻辑
- 对现有端点（`/api/status`、`/api/proposal-stats`）的任何修改

### 依赖的外部条件
- `zsiga/daemon.py` 中已存在 HTTP handler 基础设施（可复用现有路由注册模式）
- SQLite 数据库文件路径（`data/zsiga.db`）可通过 daemon 现有配置获取
- `changes` 表已存在于正常运行的数据库中

## 目标

### 成功标准
1. `GET /api/health` 在数据库正常时返回 HTTP 200，body 包含 `"status": "healthy"`、`db_records`（整数）和 `timestamp`（ISO 8601）
2. `GET /api/health` 在数据库文件缺失或表不存在时返回 HTTP 503，body 包含 `"status": "unhealthy"` 和 `error`（字符串描述）
3. 现有端点 `/api/status`、`/api/proposal-stats` 功能不受影响
4. 无新增外部依赖
5. 所有测试通过 `pytest` + `ruff check`

### 验收方式
- `curl http://localhost:58175/api/health` 返回符合 schema 的 JSON
- `pytest tests/test_spec_add_health_check_endpoint__*.py` 全部 PASS
- `ruff check zsiga/daemon.py` 无新增 lint 错误
- 手动测试：临时移走 `data/zsiga.db` 后请求端点，确认返回 503

## 约束

### 不能修改的文件
- `tests/` 目录下与 health-check 无关的测试文件
- `site/dashboard.html`
- `zsiga/config.py`
- `pyproject.toml`、`requirements.txt`（不引入新依赖）

### 项目部署分支
- main

### 已知风险
- `data/zsiga.db` 路径可能在不同运行环境下不一致，需从 daemon 现有配置动态获取而非硬编码
- SQLite WAL 模式下 `COUNT(*)` 可能触发锁等待；`_health_check` 应设置短超时（如 `timeout=2`）避免阻塞 daemon 主循环
- 如果 `changes` 表 schema 与预期不符（列名不同），COUNT 查询仍可工作但需确认表名正确

### 预估 token 消耗
- prompt: ~6000
- completion: ~4000
- 数据来源: 无历史参考（基于单文件变更 + 2 个函数 + 测试的经验估算）
