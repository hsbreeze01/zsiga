# 给 daemon status API 添加 uptime_seconds 字段

## 目标

在 /api/status.json 返回的 daemon 对象中添加 uptime_seconds 字段，显示 daemon 从启动到当前的运行时长（秒）。

## 现状

zsiga/daemon.py 的 _build_status_json 方法（第212行）通过 _read_daemon_state() 获取 daemon 状态，
其中包含 started_at（ISO 格式字符串，来自 DaemonState）。当前 daemon dict 输出了 pid、state、cycle 等字段，
但没有 uptime_seconds。

## 实现方案

在 zsiga/daemon.py 的 _build_status_json 方法中：
1. 从 ds 中取出 started_at（已有）
2. 解析 ISO 时间戳，计算 time.time() - parsed_timestamp
3. 在 daemon dict 中添加 "uptime_seconds": round(uptime, 1)

关键：复用已有的 ds.get("started_at") 作为时间源，不创建新的模块级变量。
如果 started_at 为空或解析失败，uptime_seconds 设为 null。

## 变更文件

zsiga/daemon.py（仅修改 _build_status_json 方法，约增加5行代码）

## 验收标准

1. curl /api/status.json 返回 daemon 对象包含 uptime_seconds 字段（正浮点数或 null）
2. uptime_seconds 值随时间递增（两次请求之间差值 > 0）
3. 不影响其他字段的输出格式
4. 不引入新的 import（time 模块已导入）
