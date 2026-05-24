# clarify.md — 给 daemon status API 添加 uptime_seconds 字段

## 需求拆解

### 原始需求

在 `/api/status.json` 返回的 daemon 对象中添加 `uptime_seconds` 字段，显示 daemon 从启动到当前的运行时长（秒）。利用已有的 `started_at`（ISO 格式字符串，来自 `DaemonState`）作为时间源，在 `_build_status_json` 方法中计算差值并输出。当 `started_at` 缺失或解析失败时，字段值为 `null`。

### 拆解后的子任务

- [ ] 1. **在 `_build_status_json` 中添加 uptime_seconds 计算与输出** (预估复杂度：低, 预估 token：~2000)
  - 从 `ds` dict 中取出 `started_at` 字段
  - 使用 `time.time()` 减去解析后的 ISO 时间戳，得到运行秒数
  - 将 `"uptime_seconds": round(uptime, 1)` 加入返回的 daemon dict
  - 处理 `started_at` 缺失 / 解析失败时设为 `None`
  - 文件范围：`zsiga/daemon.py`（仅 `_build_status_json` 方法，约 5 行新增）
- [ ] 2. **补充测试用例验证 uptime_seconds 字段** (预估复杂度：低, 预估 token：~1500)
  - 测试正常场景：`started_at` 有效时 `uptime_seconds` 为正浮点数
  - 测试缺失场景：`started_at` 为空时 `uptime_seconds` 为 `None`
  - 测试递增场景：两次调用间 `uptime_seconds` 差值 > 0
  - 测试不影响现有字段输出
  - 文件范围：`tests/test_daemon_state.py` 或新建 `tests/test_uptime_seconds.py`

## 边界

### IN scope

- 在 `zsiga/daemon.py` 的 `_build_status_json` 方法中添加 uptime_seconds 计算逻辑
- 处理 `started_at` 缺失或解析失败的边界情况（返回 `null`）
- 编写对应的 pytest 测试用例
- 使用 `time` 模块（已导入）和标准库 `datetime` 解析 ISO 时间戳

### OUT of scope

- 修改 `DaemonState` 的数据结构或序列化逻辑
- 添加新的模块级全局变量（如独立的 `_start_time`）
- 修改 daemon 启动流程或 `_write_daemon_state` / `_read_daemon_state` 的序列化
- 修改 HTTP 路由注册或 API 端点路径
- 修改 dashboard 前端展示

### 依赖的外部条件

- `started_at` 字段已存在于 `DaemonState` 中，且在 `_read_daemon_state()` 返回的 dict 中可获取
- `time` 模块已在 `zsiga/daemon.py` 中导入
- `_build_status_json` 方法存在于 `zsiga/daemon.py` 第 212 行附近

## 目标

### 成功标准

1. `GET /api/status.json` 返回的 JSON 中 `daemon` 对象包含 `uptime_seconds` 字段（正浮点数或 `null`）
2. `uptime_seconds` 值随时间单调递增（两次请求之间差值 > 0）
3. 当 `started_at` 缺失或无法解析时，`uptime_seconds` 为 `null` 而非抛出异常
4. 现有字段（`pid`、`state`、`cycle` 等）的输出格式不受影响
5. `ruff check` 和 `pytest` 全部通过

### 验收方式

- 运行 `pytest tests/test_daemon_state.py`（或相关测试文件）确认新增测试通过
- 运行 `pytest` 全套测试确认无回归
- 运行 `ruff check zsiga/daemon.py` 确认无 lint 问题
- 手动验证：若 daemon 可本地启动，`curl /api/status.json` 返回包含 `uptime_seconds` 字段

## 约束

### 不能修改的文件

- `zsiga/config.py` — 配置文件
- `zsiga/server.py` — HTTP 路由注册
- `zsiga/client.py` — 客户端调用
- `site/dashboard.html` — 前端展示
- 任何非 daemon 相关的模块

### 项目部署分支

- main

### 已知风险

- **`started_at` 可能不存在**：历史教训多次指出 proposal 声称存在的符号实际不存在（`_start_time`、`started_at` 等曾被确认未定义）。必须在实现前用 `grep` / `ast_search` 确认 `started_at` 在 `DaemonState` 和 `_read_daemon_state` 返回值中真实存在。若不存在，需先补充 `started_at` 的初始化逻辑，范围将扩大。
- **ISO 格式解析兼容性**：`started_at` 的 ISO 格式可能包含时区信息（`+08:00`）或不含时区，解析时需用 `datetime.fromisoformat()` 并处理两种情况，避免 `ValueError`。
- **`_build_status_json` 行号漂移**：proposal 引用第 212 行，但代码可能已变更，需重新定位。

### 预估 token 消耗

- prompt: ~3000
- completion: ~1500
- 数据来源: 无历史参考（同类任务无成功/失败记录，按低复杂度单方法变更估算）
