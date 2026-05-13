# Proposal: Optimize ENRICH Phase Efficiency for Remote Projects

## Summary
ENRICH 阶段在处理远程大项目时效率极低：25 turns / 600s 不够完成 specs/design/tasks 的生成。需要优化探索策略和配置参数。

## Motivation
实际执行中发现的问题：

1. **探索轮次浪费**：16+ turns 全花在逐个 ls/cat/mysql 查询，没有批量
2. **SSH 延迟累积**：每次调用 +1s，20 次调用 = 20s 纯 IO 等待
3. **配置过紧**：enrich_max_turns=25, enrich_timeout=600s 对远程项目不够
4. **项目预取利用率低**：Prefetching 拿到 25K chars 但 agent 仍然重复探索

具体 case：compass 项目（5500+ 股票, 20+ 表, SSH transport）的 ENRICH 在 16 turns 后超时，未生成任何 specs/design/tasks 文件。

## Expected Behavior

### 1. 智能探索策略
- ENRICH 阶段前 5 turns 应该完成所有探索（用批量命令，不是逐个 ls）
- 用一条 bash 命令获取项目全貌：`find . -name '*.py' | head -50 && echo '---' && mysql -e 'SHOW TABLES'`
- 不要逐个 cat 文件 — 用 grep 搜索关键模式
- 项目预取的内容应该被充分利用，不重复探索

### 2. 配置优化
- enrich_max_turns 从 25 提升到 40
- enrich_timeout 从 600s 提升到 1200s
- 新增 enrich 探索预算：前 8 turns 必须完成探索，剩余 turns 专注生成 artifacts

### 3. 探索-生成分离
- ENRICH 内部拆分为两个子阶段：EXPLORE（探索项目）和 GENERATE（生成 specs/design/tasks）
- EXPLORE 阶段有独立的 turn 预算（max 8 turns）
- GENERATE 阶段直接基于探索结果输出，不再回查项目

### 4. 远程项目特殊优化
- SSH transport 的项目，自动将多个 bash 命令合并为一条（用 && 连接）
- 减少 round-trip 次数

## Scope
- IN SCOPE: 配置调整 + enrich skill 优化 + 探索策略改进
- OUT OF SCOPE: 不改 agent loop 核心、不改 sub_agent、不改 compaction
