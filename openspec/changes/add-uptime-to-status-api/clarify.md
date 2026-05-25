## 需求拆解

### 原始需求

在 `/api/status.json` 返回的 daemon 对象中添加 `uptime_seconds` 字段，显示 daemon 从启动到当前的运行时长（秒）。复用已有的 `ds.get("started_at")` 作为时间源，不引入新的模块级变量。`started_at` 为空或解析失败时设为 `null`。

### 拆解后的子任务

- [ ] 1. 在 `zsiga/daemon.py` 的 `_build_status_json` 方法中添加 uptime_seconds 计算与输出 (预估复杂度：低, 预估 token：~2000 / 无历史参考)
  - 从 `ds` 中读取 `started_at`，解析 ISO 时间戳
  - 计算 `time.time() - parsed_timestamp`，`round(uptime, 1)`
  - 构建 daemon dict 时插入 `"uptime_seconds"` 字段
  - 处理 `started_at` 为空或解析失败的边界情况（返回 `None`）

## 边界

### IN scope
- 修改 `zsiga/daemon.py` 中 `_build_status_json` 方法，添加 uptime_seconds 字段
- 编写对应的单元测试验证字段存在、值递增、null 回退

### OUT of scope
- 不修改 API 路由或端点定义
- 不修改 `DaemonState` 结构或 `_read_daemon_state` 方法
- 不修改 dashboard.html 前端展示
- 不引入新的 import（`time` 模块已导入）
- 不创建新的模块级变量或全局状态

### 依赖的外部条件
- `_read_daemon_state()` 返回的 `ds` 中已包含 `started_at`（ISO 格式字符串）
- `time` 模块已在 `zsiga/daemon.py` 中导入

## 目标

### 成功标准
1. `curl /api/status.json` 返回的 daemon 对象包含 `uptime_seconds` 字段（正浮点数或 `null`）
2. `uptime_seconds` 值随时间递增（两次请求之间差值 > 0）
3. 不影响其他字段（pid、state、cycle 等）的输出格式
4. `started_at` 缺失或格式错误时 `uptime_seconds` 为 `null`，不抛异常
5. ruff check 和 pytest 全部通过

### 验收方式
- 单元测试：mock `_read_daemon_state` 返回含 `started_at` 的 dict，断言 `uptime_seconds` 为正浮点数
- 单元测试：mock `_read_daemon_state` 返回空 `started_at`，断言 `uptime_seconds` 为 `None`
- 单元测试：连续两次调用，断言第二次 `uptime_seconds` > 第一次
- ruff check `zsiga/daemon.py` 无 lint 错误

## 约束

### 不能修改的文件
- `zsiga/config.py`
- `site/dashboard.html`
- 任何 `tests/conftest*.py` 文件

### 项目部署分支
main

### 已知风险
- `started_at` 的 ISO 格式如果带时区信息（如 `2025-01-01T00:00:00+08:00`），`datetime.fromisoformat` 在 Python 3.10+ 可正确处理，Python 3.9 则有限制；需确认运行时 Python 版本（pyproject.toml 要求 `>=3.10`）
- 若 `_build_status_json` 在 daemon 未启动时被调用，`started_at` 可能为空字符串或不存在，需防御性处理

### 预估 token 消耗
- prompt: ~1500
- completion: ~800
- 数据来源: 无历史参考（单文件、~5 行增量变更）
