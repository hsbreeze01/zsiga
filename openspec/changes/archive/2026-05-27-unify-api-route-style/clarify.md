# clarify.md — unify-api-route-style

## 需求拆解

### 原始需求
将 `zsiga/daemon.py` 中所有带 `.json` 后缀的 HTTP API 路由统一为 `/api/<resource>` 风格（去掉 `.json` 后缀），同时保留旧路由作为 301 重定向以维持向后兼容性。无 `.json` 后缀的路由（`/api/health`、`/api/proposal-stats`）保持不变。

### 拆解后的子任务

- [ ] 1. 路由重命名：将 `/api/status.json`、`/api/metrics.json`、`/api/current.json` 的处理函数注册路径分别改为 `/api/status`、`/api/metrics`、`/api/current`，确保响应体与逻辑不变 (预估复杂度：低, 预估 token：~1500 / 无历史参考)
- [ ] 2. 添加向后兼容重定向：为旧的 `.json` 路由添加 301 永久重定向到对应的新路径，涵盖 `/api/status.json`→`/api/status`、`/api/metrics.json`→`/api/metrics`、`/api/current.json`→`/api/current` (预估复杂度：低, 预估 token：~800 / 无历史参考)
- [ ] 3. 验证未受影响路由：确认 `/api/health` 和 `/api/proposal-stats` 的注册路径、处理逻辑无任何变更 (预估复杂度：低, 预估 token：~400 / 无历史参考)

## 边界

### IN scope
- 在 `zsiga/daemon.py` 中重命名 3 个带 `.json` 后缀的路由
- 为 3 个旧路径添加 HTTP 301 重定向
- 确认无后缀路由不受影响

### OUT of scope
- Dashboard 前端 UI 变更（`site/dashboard.html`）
- 新增 API 端点
- 修改业务逻辑或响应数据结构
- 修改 `pyproject.toml` 或引入新依赖

### 依赖的外部条件
- `zsiga/daemon.py` 文件存在且包含当前路由定义
- 项目使用的 Web 框架支持 301 重定向（需确认框架类型，如 Flask/httpx 等）

## 目标

### 成功标准
1. `GET /api/status` 返回 200，响应 JSON 与原 `/api/status.json` 完全一致
2. `GET /api/metrics` 返回 200，响应 JSON 与原 `/api/metrics.json` 完全一致
3. `GET /api/current` 返回 200，响应 JSON 与原 `/api/current.json` 完全一致
4. `GET /api/status.json` 返回 301，Location 指向 `/api/status`
5. `GET /api/metrics.json` 返回 301，Location 指向 `/api/metrics`
6. `GET /api/current.json` 返回 301，Location 指向 `/api/current`
7. `/api/health` 和 `/api/proposal-stats` 行为与变更前完全相同
8. 不引入新的外部依赖

### 验收方式
- 使用 `curl -i` 对新旧路径逐一验证状态码和响应体
- 运行现有测试套件 `tests/test_dashboard_api.py` 确认无回归
- 如有测试引用旧路由，需同步更新测试中的路径断言

## 约束

### 不能修改的文件
- `site/dashboard.html`（前端不在范围内）
- `pyproject.toml`（不引入新依赖）
- `requirements.txt`（不引入新依赖）

### 项目部署分支
- 未明确指定（待确认）

### 已知风险
- 前端 `dashboard.html` 中可能硬编码了 `/api/status.json` 等旧路径，本次变更不做前端适配，301 重定向可保证前端暂时仍可工作，但后续需跟进前端路径更新
- 若有外部客户端硬编码旧路径，301 重定向需客户端支持跟随重定向
- 现有测试文件 `tests/test_dashboard_api.py` 中可能引用旧 `.json` 路径，需同步更新否则测试会失败

### 预估 token 消耗
- prompt: ~2500
- completion: ~1500
- 数据来源: 无历史参考
