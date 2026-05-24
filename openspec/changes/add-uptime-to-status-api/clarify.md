# clarify.md — add-uptime-to-status-api

## 需求拆解

### 原始需求

在 `/api/status.json` 返回的 daemon 对象中添加 `uptime_seconds` 字段，显示 daemon 从启动到当前的运行时长（秒）。实现方式为复用 `DaemonState` 中已有的 `started_at`（ISO 格式字符串），解析后计算差值，不引入新的模块级变量或 import。

### 拆解后的子任务

- [ ] 1. **在 `_build_status_json` 中计算并注入 uptime_seconds 字段** — 从 `_read_daemon_state()` 返回的 dict 中取出 `started_at`，解析 ISO 时间戳，计算 `time.time() - parsed`，将结果 `round(uptime, 1)` 写入 daemon dict；`started_at` 为空或解析失败时设为 `None`（预估复杂度：低, 预估 token：~1500 / 无历史参考）
- [ ] 2. **编写 / 更新单元测试覆盖 uptime_seconds** — 测试正常计算（返回正浮点数）、`started_at` 缺失时返回 `None`、格式错误时返回 `None`、不影响其他字段（预估复杂度：低, 预估 token：~2000 / 无历史参考）

## 边界

### IN scope

- 修改 `zsiga/daemon.py` 中 `_build_status_json` 方法，增加约 5 行 uptime 计算逻辑
- 编写或更新测试文件验证 uptime_seconds 字段的正确性
- 确保复用已有 `ds.get("started_at")` 作为时间源，不新建模块级变量
- 确保失败时优雅降级为 `null`（`None`）

### OUT of scope

- 不修改 `DaemonState` dataclass 定义或序列化逻辑
- 不修改 `_read_daemon_state` / `_write_daemon_state` 方法
- 不新增 import（`time` 模块已导入）
- 不修改 `/api/status.json` 的路由注册或其他字段的输出格式
- 不添加格式化的人类可读 uptime 字符串（如 "2h 30m"）

### 依赖的外部条件

- `DaemonState` 中 `started_at` 字段必须已被正确写入 daemon state（启动时设置 ISO 格式字符串）
- `time` 模块已在 `zsiga/daemon.py` 中导入
- `_build_status_json` 方法存在于 `zsiga/daemon.py` 第 212 行附近

## 目标

### 成功标准

1. `GET /api/status.json` 返回的 daemon 对象包含 `uptime_seconds` 字段（正浮点数或 `null`）
2. `uptime_seconds` 值随时间递增——两次请求间隔 > 0 秒时，第二次返回值大于第一次
3. `started_at` 缺失或格式非法时，`uptime_seconds` 为 `null` 而非抛异常
4. 现有字段（`pid`、`state`、`cycle` 等）的输出格式和值不受影响
5. `pytest` 全部通过 + `ruff check` 无新增错误

### 验收方式

- 单元测试覆盖：正常路径（有 `started_at`）、缺失路径（`started_at` 为 `None`）、格式错误路径（非 ISO 字符串）
- 手动验证：`curl /api/status.json | jq '.daemon.uptime_seconds'` 返回正浮点数
- 差值验证：连续两次 curl 之间 sleep 1s，第二次 uptime_seconds > 第一次

## 约束

### 不能修改的文件

- `zsiga/daemon.py` 中 `_build_status_json` 以外的方法签名和逻辑（最小侵入）
- `_read_daemon_state` / `_write_daemon_state` 方法
- `DaemonState` dataclass 定义
- 路由注册代码（`server.py` 或同等文件）

### 项目部署分支

- main

### 已知风险

- **`started_at` 可能不存在**：proposal 声称 `DaemonState` 已有 `started_at` 字段，但历史教训（proposal_gate pushback 记录）多次指出 `started_at` 在代码库中不存在。实现前必须先确认 `ds.get("started_at")` 是否能返回有效值；若不能，需在 `_build_status_json` 中做 `None` 兜底（proposal 已考虑此情况）
- **ISO 格式解析**：`started_at` 的具体格式（是否带时区、微秒等）未明确，需使用 `datetime.fromisoformat()` 兼容处理，解析失败时返回 `None`
- **测试文件已存在**：项目 tree 中已有 `tests/test_spec_add_uptime_to_status_api__uptime_seconds_field.py`，需检查其内容是空骨架还是已有断言，避免重复或冲突

### 预估 token 消耗

- prompt: ~2500
- completion: ~1500
- 数据来源: 无历史参考（按 proposal 描述的 ~5 行核心代码 + 测试用例估算）
