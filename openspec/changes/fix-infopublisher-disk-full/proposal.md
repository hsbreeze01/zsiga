## Why

服务器 47.99.57.152 磁盘 40G 使用率 100%（紧急清理后 96%）。MySQL 8.0 在 5/18 16:28 因磁盘满被 SIGKILL，无法重启，导致所有依赖 MySQL 的服务（infopublisher、compass、datafactory）断联近 19 小时。资讯数据从 5/18 开始缺失。

根因：`stock_analysis.ibd` 5.2G 持续增长无清理机制。需要建立自动化的磁盘空间管理。

## What Changes

- 在 compass 的 pipeline.py 中增加 `stock_analysis` 表的定期清理：保留最近 N 天分析结果，删除过期记录
- 增加 MySQL binlog 过期时间配置（如 binlog_expire_logs_seconds=259200）
- 增加 cron 任务监控磁盘使用率，>= 85% 时告警
- infopublisher 增加启动时 MySQL 连接健康检查，连接失败时 graceful degradation（缓存最近数据）

## Capabilities

### New Capabilities

- `disk-space-monitor`: 磁盘空间自动监控 — cron 定期检查磁盘使用率，>= 85% 时写入告警日志并发通知
- `analysis-data-retention`: 分析数据生命周期管理 — stock_analysis 表按日期自动清理过期记录，保留最近 N 天，OPTIMIZE TABLE 回收空间

### Modified Capabilities

- （无现有 spec 需要修改）

## Impact

- 修改代码：`compass/scripts/pipeline.py`（清理逻辑）、infopublisher 启动脚本（健康检查）
- 修改配置：MySQL binlog 过期时间、新增 cron 任务
- 目标服务器：47.99.57.152 (d8q-intelligentengine-stockcompass + d8q-intelligentengine-infopublisher)
- 风险：清理 stock_analysis 数据需确认 compass 的 strategy_group 功能不依赖历史分析结果
