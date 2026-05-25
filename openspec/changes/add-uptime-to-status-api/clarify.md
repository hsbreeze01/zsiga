## 需求拆解

### 原始需求

在 `/api/status.json` 返回的 daemon 对象中添加 `uptime_seconds` 字段，显示 daemon 从启动到当前的运行时长（秒）。复用已有的 `ds.get("started_at")` 作为时间源，不创建新的模块级变量。如果 `started_at` 为空或解析失败，`uptime_seconds` 设为 `null`。

### 拆解后的子任务

- [ ] 1. 在 `_build_status_json` 方法中添加 uptime_seconds 计算逻辑：解析 `started_at` ISO 时间戳，计算 `time.time() - parsed_timestamp`，写入 daemon dict，处理 `started_at` 缺失/解析失败的 null 回退 (预估复杂度：低, 预估 token：~3000 / 无历史参考)
- [ ] 2. 为 uptime_seconds 字段编写测试：覆盖正常递增、started_at 缺失返回 null、解析失败返回 null、不影响其他字段 (预估复杂度：低, 预估 token：~2500 / 无历史参考)

## 边界

### IN scope
- 修改 `zsiga/daemon.py` 的 `_build_status_json` 方法，添加 `uptime_seconds` 字段计算与输出
- 为新增字段编写对应的单元测试
- 处理 `started_at` 为空或格式异常时的 null 回退

### OUT of scope
- 不修改 `DaemonState` 或 `_read_daemon_state()` 的数据结构
- 不新增模块级变量或全局启动时间记录
- 不修改 dashboard.html 前端展示
- 不修改 `/api/status.json` 的路由注册或其他 API 端点
- 不引入新的 import（`time` 模块已导入）

### 依赖的外部条件
- `ds.get("started_at")` 已在 `_build_status_json` 中可用且为 ISO 格式字符串
- `time` 模块已在 `zsiga/daemon.py` 中导入
- 现有 `_build_status_json` 方法位于约第 212 行，输出包含 pid、state、cycle 等字段的 daemon dict

## 目标

### 成功标准
1. `curl /api/status.json` 返回的 daemon 对象包含 `uptime_seconds` 字段（正浮点数，保留 1 位小数）
2. 当 `started_at` 为空或解析失败时，`uptime_seconds` 值为 `null`（JSON None）
3. `uptime_seconds` 值随时间递增（两次请求之间差值 > 0）
4. 不影响 daemon dict 中其他字段（pid、state、cycle 等）的输出格式和值
5. 通过 ruff lint 检查，无新增 warning

### 验收方式
- 单元测试：mock `started_at` 为已知 ISO 时间戳，断言 `uptime_seconds` 为正浮点且 `round` 到 1 位小数
- 单元测试：mock `started_at` 为空字符串，断言 `uptime_seconds` 为 `None`
- 单元测试：mock `started_at` 为非法格式，断言 `uptime_seconds` 为 `None`
- 单元测试：断言 `_build_status_json` 返回的其他字段数量和值未被改变
- `ruff check zsiga/daemon.py` 通过
- `pytest tests/test_spec_add_uptime_to_status_api__uptime_seconds_field.py` 通过

## 约束

### 不能修改的文件
- `zsiga/daemon.py` 中除 `_build_status_json` 方法外的其他方法
- `site/dashboard.html`
- `zsiga/config.py`
- `tests/conftest_zsiga.py`

### 项目部署分支
main

### 已知风险
- `started_at` 的 ISO 格式可能包含时区信息（如 `+08:00`）或为 UTC 无后缀格式，解析逻辑需兼容两种情况
- `datetime.fromisoformat()` 在 Python 3.9 以下不支持 `Z` 后缀，需注意兼容性（项目要求 Python >= 3.10，可安全使用）

### 预估 token 消耗
- prompt: ~4000
- completion: ~2000
- 数据来源: 无历史参考
