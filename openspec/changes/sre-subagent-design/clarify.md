# clarify.md — SRE Sub-Agent

## 需求拆解

### 原始需求

为 zsiga 新增 SRE 子代理角色，具备基础设施运维意图识别和任务分发能力。SRE agent 执行幂等状态变更操作（服务启停、健康检测、日志分析、资源清理），产出运维报告而非代码 commit。SRE pipeline 与现有 code pipeline 通过 intent 路由互斥，首版仅支持 localhost 操作。

### 拆解后的子任务

- [ ] 1. **SRE 意图路由扩展** — 在 intent_router.py 中新增 `sre` 意图类别，定义触发关键词（服务、重启、健康、清理、磁盘、宕机、日志、进程、监控），检测到后路由至 SRE pipeline 而非 code pipeline (预估复杂度：低, 预估 token：~3000 / 无历史参考)
- [ ] 2. **SRE Agent Role 定义** — 在 roles.py 中新增 SRE 角色：name=sre, max_turns=15, read_only=false, allowed_tools=[bash, read_file, search, list_files]，包含 SRE 操作规范 system_prompt（幂等、回滚、白名单命令）及硬编码命令白名单/黑名单 (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 3. **SRE Pipeline 实现** — 新建独立于 code pipeline 的 SRE pipeline，包含 5 个 phase：DIAGNOSE（收集服务状态/日志/资源）→ PLAN（生成白名单内 shell 命令序列）→ EXECUTE（逐步执行+每步断言）→ VERIFY（验证目标状态达成）→ REPORT（输出报告，无 git commit） (预估复杂度：高, 预估 token：~8000 / 无历史参考)
- [ ] 4. **安全边界与审批机制** — 实现命令白名单校验（systemctl start/stop/restart/status, curl, df, free, du, journalctl, dmesg, crontab），黑名单拦截（rm -rf, iptables, sysctl, 密钥操作），每步执行前 snapshot 当前状态用于失败 revert，危险操作 require_approval=true 确认 (预估复杂度：中, 预估 token：~4000 / 无历史参考)
- [ ] 5. **SRE 产物格式与 learnings 注入** — SRE pipeline 产出 execution_report.md（操作步骤/结果/验证），追加运维经验到 learnings.jsonl，CMDB infra_assets 表状态更新能力（预留接口，首版 localhost） (预估复杂度：中, 预估 token：~3500 / 无历史参考)
- [ ] 6. **SRE 子代理集成测试** — 编写测试覆盖：意图路由到 sre vs code 的互斥判定、SRE role 配置校验、pipeline 各 phase 状态流转、白名单/黑名单命令校验、产物格式验证 (预估复杂度：中, 预估 token：~5000 / 无历史参考)

## 边界

### IN scope
- intent_router.py 中新增 sre 意图类别及关键词匹配
- roles.py 中新增 SRE role 定义（含 system_prompt、命令白名单/黑名单）
- 新建独立的 SRE pipeline 模块（5 phase）
- 安全边界：命令白名单校验、snapshot/revert 机制、审批门控
- SRE 产物：execution_report.md、learnings.jsonl 追加
- 集成测试覆盖上述全部功能

### OUT of scope
- SSH transport 远端主机操作（首版仅 localhost，远端作为后续扩展）
- CMDB infra_assets 表的实际数据库写入（仅预留接口）
- 现有 code pipeline 的任何逻辑修改
- dashboard UI 中 SRE 状态展示
- SRE 操作的定时调度/定时巡检能力

### 依赖的外部条件
- intent_router.py 现有意图路由架构支持新增类别
- roles.py 现有 role 注册机制支持扩展
- 现有 pipeline 基础设施可被参考但不被修改
- learnings.jsonl 的现有追加机制可被 SRE pipeline 复用

## 目标

### 成功标准
1. 输入包含 SRE 关键词的用户意图时，intent_router 正确路由到 sre 类别（而非 code）
2. SRE role 配置包含完整的命令白名单/黑名单、max_turns=15、allowed_tools
3. SRE pipeline 可完整走完 DIAGNOSE→PLAN→EXECUTE→VERIFY→REPORT 五个 phase
4. 黑名单命令在 PLAN 或 EXECUTE 阶段被拦截并报错，不可执行
5. SRE pipeline 执行完毕后产出 execution_report.md，不产生 git commit
6. 所有新增测试通过，现有测试不受影响（ruff + pytest 全绿）
7. SRE pipeline 与 code pipeline 在 intent 路由层互斥，不存在交叉执行

### 验收方式
- `pytest tests/test_intent_router.py` — 新增 sre 意图测试用例通过
- `pytest tests/test_roles.py` — 新增 SRE role 校验测试通过
- `pytest tests/test_sub_agent.py` — SRE sub-agent 集成测试通过
- `ruff check <new_files>` — 无 lint 错误
- 手动验证：模拟 SRE 意图输入，确认走 SRE pipeline 而非 code pipeline

## 约束

### 不能修改的文件
- 现有 code pipeline 相关逻辑文件（intent_router.py 中已有 code 路由逻辑不可破坏性修改）
- 现有 roles.py 中已有 role 定义不可删除或重命名
- skills/skill_evolver.py
- site/dashboard.html
- tests/conftest_zsiga.py
- pyproject.toml（不新增依赖）

### 项目部署分支
- main

### 已知风险
- intent_router 新增 sre 类别可能与现有意图优先级冲突，需确保 sre 关键词不会误触发 code pipeline
- SRE pipeline 的 bash 执行权限（read_only=false）在生产环境可能需要额外权限审批
- 命令白名单的完整性：首版硬编码可能遗漏必要命令，需预留扩展机制
- snapshot/revert 机制在复杂状态变更（如 systemd 服务依赖链）中可能不完整
- `daemon.cycle_error` 历史模式显示 tag 冲突风险，需注意分支命名

### 预估 token 消耗
- prompt: ~15000
- completion: ~8000
- 数据来源: 无历史参考（SRE 子代理为全新功能模块）
