# Clarify: SRE Sub-Agent — 基础设施运维意图分发

## 需求拆解

### 原始需求
为 zsiga 新增 SRE（Site Reliability Engineering）子代理角色，具备基础设施运维的意图识别和任务分发能力。SRE agent 执行幂等状态变更操作（服务启停、健康检测、日志分析、资源清理），产出运维报告而非代码 commit。SRE pipeline 独立于现有 code pipeline，通过 intent 路由互斥分发。

### 拆解后的子任务

- [ ] 1. **SRE 意图路由扩展** — 在 `zsiga/intent_router.py` 中新增 `sre` 意图类别，添加触发关键词集合（服务、重启、健康、清理、磁盘、宕机、日志、进程、监控），实现 sre 意图检测并路由到 SRE pipeline（非 code pipeline），确保 sre 与 code 意图互斥 (预估复杂度：中, 预估 token：~6000 / 无历史参考)

- [ ] 2. **SRE Role 定义** — 在 `zsiga/roles.py` 中新增 SRE 角色配置：name=sre, max_turns=15, read_only=false, allowed_tools=[bash, read_file, search, list_files]，包含 SRE 操作规范 system_prompt（幂等原则、回滚策略、白名单命令约束） (预估复杂度：低, 预估 token：~3000 / 无历史参考)

- [ ] 3. **SRE Pipeline 实现** — 新建 `zsiga/pipeline/sre_pipeline.py`，实现 5 阶段流水线：DIAGNOSE（收集服务状态/日志/资源使用）→ PLAN（生成白名单内 shell 命令序列）→ EXECUTE（逐步执行+每步断言）→ VERIFY（验证目标状态达成）→ REPORT（输出 execution_report.jsonl，不产生 git commit） (预估复杂度：高, 预估 token：~12000 / 无历史参考)

- [ ] 4. **安全边界与命令白名单** — 硬编码命令白名单（systemctl start/stop/restart/status, curl, df, free, du, journalctl, dmesg, crontab）和禁止命令列表（rm -rf, iptables, sysctl, 密钥操作），实现每步执行前 snapshot + 失败自动 revert，危险操作 require_approval=true 机制 (预估复杂度：中, 预估 token：~6000 / 无历史参考)

- [ ] 5. **SRE Orchestrator 集成** — 在 orchestrator 中注册 SRE pipeline，当 intent_router 返回 sre 意图时调度 SRE pipeline 而非 code pipeline，确保两个 pipeline 通过路由互斥、互不干扰 (预估复杂度：中, 预估 token：~5000 / 无历史参考)

- [ ] 6. **SRE 产物与 Learnings** — 实现 execution_report.md 生成（操作步骤、结果、验证），learnings.jsonl 追加运维经验记录，不产生 git commit (预估复杂度：低, 预估 token：~3000 / 无历史参考)

## 边界

### IN scope
- intent_router.py 中新增 sre 意图类别及关键词检测
- roles.py 中新增 SRE 角色定义及 system_prompt
- 新建 sre_pipeline.py 实现 5 阶段流水线（DIAGNOSE→PLAN→EXECUTE→VERIFY→REPORT）
- 命令白名单硬编码与安全校验逻辑
- orchestrator 中 SRE pipeline 注册与调度
- SRE 产物格式：execution_report.md + learnings.jsonl 追加
- 对应单元测试（意图路由、角色定义、pipeline 各阶段、安全边界、产物格式、orchestrator 集成）

### OUT of scope
- SSH transport 远程主机操作（v1 仅支持 localhost）
- CMDB infra_assets 表状态更新
- 服务迁移相关自动化
- dashboard 中 SRE 专属 UI 面板
- 现有 code pipeline 的任何逻辑修改
- 多机部署（47+49）的远程巡检

### 依赖的外部条件
- 现有 `zsiga/intent_router.py` 模块可扩展（已有路由机制）
- 现有 `zsiga/roles.py` 模块可扩展（已有角色注册机制）
- orchestrator 已有 pipeline 调度框架可复用
- 系统需支持 bash 工具执行（localhost shell 命令）

## 目标

### 成功标准
1. intent_router 能正确识别 SRE 关键词并返回 `sre` 意图类别，与 `code` 意图互斥
2. roles.py 中 SRE 角色配置完整（name, max_turns, read_only, allowed_tools, system_prompt）
3. SRE pipeline 5 个阶段按序执行：DIAGNOSE→PLAN→EXECUTE→VERIFY→REPORT
4. 命令白名单校验生效：白名单内命令可执行，禁止命令被拦截
5. SRE pipeline 产出 execution_report.md 和 learnings.jsonl，不产生 git commit
6. orchestrator 能根据 sre 意图调度 SRE pipeline，code pipeline 不受影响
7. 所有新增测试通过（ruff lint + pytest）

### 验收方式
- `pytest tests/test_spec_sre_subagent_design__sre_intent_routing.py` 通过
- `pytest tests/test_spec_sre_subagent_design__sre_role_definition.py` 通过
- `pytest tests/test_spec_sre_subagent_design__sre_pipeline.py` 通过
- `pytest tests/test_spec_sre_subagent_design__sre_security_boundary.py` 通过
- `pytest tests/test_spec_sre_subagent_design__sre_orchestrator_integration.py` 通过
- `pytest tests/test_spec_sre_subagent_design__sre_artifacts_learnings.py` 通过
- `ruff check` 无新增错误
- 现有测试套件无回归

## 约束

### 不能修改的文件
- 现有 code pipeline 相关文件（pipeline 的 enrich/implement/verify 逻辑）
- `site/dashboard.html`（SRE dashboard 面板不在范围内）
- `tests/conftest_zsiga.py`（已有测试基础设施不动）
- `pyproject.toml`、`requirements.txt`（无新依赖）

### 项目部署分支
主分支部署，通过 openspec change 目录管理

### 已知风险
- SRE pipeline 与 code pipeline 的 orchestrator 集成可能触发调度冲突，需确保意图路由互斥性
- 安全白名单硬编码可能在后续需要扩展（如添加 SSH transport 时），设计时预留配置化接口
- bash 工具执行系统命令存在潜在安全风险，白名单校验必须严格且覆盖所有变体（如 `sudo systemctl`）
- 幂等性依赖外部系统状态，测试中需 mock systemctl 等系统命令
- 模式警告 history 显示 `pipeline.review.critical` 和 `daemon.cycle_error` 高频出现，需注意 orchestrator 集成的 review 完整性

### 预估 token 消耗
- prompt: ~20000
- completion: ~35000
- 数据来源: 无历史参考（基于子任务复杂度估算）
