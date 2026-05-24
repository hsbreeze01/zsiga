# Proposal: SRE Sub-Agent — 基础设施运维意图分发

## Summary

为 zsiga 新增 SRE（Site Reliability Engineering）子代理角色，使 zsiga 具备基础设施运维的意图识别和任务分发能力。SRE agent 执行幂等状态变更操作（服务启停、健康检测、日志分析、资源清理），产出运维报告而非代码 commit。

## Motivation

zsiga 当前的 pipeline 假设所有工作都表达为 proposal -> spec -> code -> test -> commit。但实际运维场景：

1. **服务宕机恢复**：StockShark/InfoPublisher 迁移后 47 上残留 disabled 服务和 SSH 隧道，需要清理
2. **健康检测**：多机部署（47 + 49）的服务状态巡检
3. **资源管理**：磁盘清理、日志轮转、内存回收
4. **故障排查**：查看日志、检查进程、分析 dmesg

这些任务不产生代码变更，无法走现有 ENRICH->IMPLEMENT->VERIFY pipeline。

## Expected Behavior

### 1. 意图路由扩展
在 intent_router.py 中新增 sre 意图类别：
- 触发关键词：服务、重启、健康、清理、磁盘、宕机、日志、进程、监控
- 检测到 sre 意图 -> 路由到 SRE pipeline（非 code pipeline）

### 2. SRE Agent Role
在 roles.py 中新增 SRE 角色：
- name: sre
- max_turns: 15
- read_only: false（需要执行 systemctl 等）
- allowed_tools: [bash, read_file, search, list_files]
- system_prompt: SRE 操作规范（幂等、回滚、白名单命令）

### 3. SRE Pipeline（独立于 code pipeline）

Phase 1 - DIAGNOSE: 收集当前状态（服务状态、日志、资源使用）
Phase 2 - PLAN: 生成操作步骤（白名单内的 shell 命令序列）
Phase 3 - EXECUTE: 逐步执行 + 每步断言
Phase 4 - VERIFY: 验证目标状态达成
Phase 5 - REPORT: 输出 execution_report.jsonl（无 git commit）

### 4. 安全边界
- 命令白名单：systemctl start/stop/restart/status, curl, df, free, du, journalctl, dmesg, crontab
- 禁止：rm -rf, iptables, sysctl, 任何涉及密钥的操作
- 每步执行前 snapshot 当前状态，失败时自动 revert
- 危险操作需要 require_approval=true 确认

### 5. 产物格式
不产生 git commit，产出：
- execution_report.md：操作步骤、结果、验证
- learnings.jsonl 追加运维经验
- CMDB infra_assets 表状态更新（如服务迁移）

## Constraints

- 不修改现有 code pipeline 的任何逻辑
- SRE pipeline 与 code pipeline 通过 intent 路由互斥
- 安全白名单硬编码在 SRE role 配置中
- 第一个版本仅支持 localhost 操作（通过 SSH transport 扩展到远端）
