# clarify.md — 给 daemon status API 添加 uptime_seconds 字段

## 需求拆解

### 原始需求

在 `/api/status.json` 返回的 daemon 对象中添加 `uptime_seconds` 字段，显示 daemon 从启动到当前的运行时长（秒）。数据源为 DaemonState 中已有的 `started_at`（ISO 格式字符串），计算 `time.time() - parsed_timestamp`，结果保留一位小数。若 `started_at` 缺失或解析失败，返回 `null`。

### 拆解后的子任务

- [ ] 1. **在 `_build_status_json` 中计算并注入 uptime_seconds** — 从 `ds` dict 取 `started_at`，解析 ISO 时间戳，计算差值，将 `"uptime_seconds": round(uptime, 1)` 加入 daemon 输出 dict；解析失败时设为 `None`（序列化为 `null`）。仅修改 `zsiga/daemon.py` 的 `_build_status_json` 方法，约 5 行新增逻辑。（预估复杂度：低, 预估 token：~800）

- [ ] 2. **补充/更新单元测试** — 在 `tests/test_spec_add_uptime_to_status_api__uptime_seconds_field.py` 中覆盖：正常 uptime 为正浮点数、`started_at` 缺失返回 null、两次调用间值递增。（预估复杂度：低, 预估 token：~600）

## 边界

### IN scope
- `zsiga/daemon.py` 的 `_build_status_json` 方法内新增 uptime 计算逻辑
- `tests/test_spec_add_uptime_to_status_api__uptime_seconds_field.py` 测试覆盖
- 复用已有的 `started_at` 字段和已导入的 `time` 模块

### OUT of scope
- 新增模块级全局变量（如 `_start_time`）
- 修改 DaemonState 的定义或序列化逻辑
- 修改 `/api/status.json` 路由注册或 HTTP handler
- 新增 import 语句
- 修改其他字段（pid、state、cycle 等）的输出格式

### 依赖的外部条件
- `zsiga/daemon.py` 中 `_build_status_json` 方法存在且可被测试 hook 调用
- `ds.get("started_at")` 能返回合法 ISO 格式字符串（由 `_read_daemon_state()` 提供）
- `time` 模块已在文件顶部导入
- `tests/test_spec_add_uptime_to_status_api__uptime_seconds_field.py` 可被 pytest 发现并执行

## 目标

### 成功标准
1. `curl /api/status.json` 返回 JSON 中 daemon 对象包含 `uptime_seconds` 字段，类型为正浮点数或 `null`
2. `uptime_seconds` 值在两次请求（间隔 > 0.1s）之间严格递增
3. 当 `started_at` 为空字符串或不可解析时，`uptime_seconds` 为 `null`
4. 现有字段（pid、state、cycle 等）的输出格式不变
5. `ruff check zsiga/daemon.py` 零错误
6. `pytest tests/test_spec_add_uptime_to_status_api__uptime_seconds_field.py` 全部通过

### 验收方式
- 单元测试覆盖正常路径、缺失路径、递增断言三条 case
- ruff lint 通过
- 不引入新 import

## 约束

### 不能修改的文件
- `zsiga/daemon.py` 中 `_build_status_json` 之外的逻辑（除非 `started_at` 字段确认不存在，需回退处理）
- 现有路由注册和 HTTP handler
- 其他 `tests/test_*.py` 文件

### 项目部署分支
- main

### 已知风险
- **`started_at` 可能不存在**：历史教训多次指出 `started_at`、`_start_time` 等符号在代码库中未找到定义。若 `_read_daemon_state()` 返回的 dict 中无 `started_at` 键，`uptime_seconds` 将始终为 `null`，功能名存实亡。实施前需先用 grep/AST 确认 `started_at` 在 DaemonState 中的存在性。
- **`_build_status_json` 方法名/行号可能不准确**：proposal 声称第 212 行，但历史教训显示方法名曾被误报为 `_build_status_json` vs `get_status()`。实施前需定位实际方法。
- **daemon 相关变更历史风险高**：daemon 模块曾因 `NameError: name 'Path' is not defined` 连续失败，属于高频出错区域。

### 预估 token 消耗
- prompt: ~2000
- completion: ~1200
- 数据来源: historical（daemon 相关变更多次失败，但本任务范围极小，约 5 行新增代码）
