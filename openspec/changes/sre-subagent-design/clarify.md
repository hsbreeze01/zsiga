# Clarify: SRE Sub-Agent — 基础设施运维意图分发

## 需求拆解

### 原始需求
为 zsiga 新增 SRE（Site Reliability Engineering）子代理角色，使 zsiga 具备基础设施运维的意图识别和任务分发能力。SRE agent 执行幂等状态变更操作（服务启停、健康检测、日志分析、资源清理），产出运维报告而非代码 commit。SRE pipeline 与现有 code pipeline 通过 intent 路由互斥，不修改任何现有 code pipeline 逻辑。

### 拆解后的子任务

- [ ] 1. **SRE 意图路由扩展** — 在 intent_router.py 中新增 `sre` 意图类别，定义触发关键词（服务、重启、健康、清理、磁盘、宕机、日志、进程、监控），检测到 sre 意图后路由到 SRE pipeline 而非 code pipeline。需同步扩展 orchestrator 的路由分支。 (预估复杂度：中, 预估 token：~6000 / 无历史参考)

- [ ] 2. **SRE Role 定义** — 在 roles.py 中新增 SRE 角色配置：name=sre, max_turns=15, read_only=false, allowed_tools=[bash, read_file, search, list_files]，以及 SRE 操作规范 system_prompt（幂等、回滚、白名单命令约束）。 (预估复杂度：低, 预估 token：~4000 / 无历史参考)

- [ ] 3. **SRE Pipeline 实现** — 新建独立于 code pipeline 的 SRE pipeline，包含 5 个 phase：DIAGNOSE（收集服务状态/日志/资源）、PLAN（生成白名单内 shell 命令序列）、EXECUTE（逐步执行 + 每步断言）、VERIFY（验证目标状态）、REPORT（输出 execution_report，无 git commit）。 (预估复杂度：高, 预估 token：~10000 / 无历史参考)

- [ ] 4. **安全边界与命令白名单** — 实现 SRE 命令白名单守卫（systemctl start/stop/restart/status, curl, df, free, du, journalctl, dmesg, crontab），禁止 rm -rf/iptables/sysctl/密钥操作，每步执行前 snapshot 当前状态支持失败自动 revert，危险操作 require_approval=true 机制。 (预估复杂度：中, 预估 token：~6000 / 无历史参考)

- [ ] 5. **SRE 产物与 Learnings 注入** — SRE pipeline 产出 execution_report.md（操作步骤、结果、验证）和 learnings.jsonl（运维经验追加），不产生 git commit。learnings 注入需复用现有 learnings 基础设施但适配 SRE 场景。 (预估复杂度：中, 预估 token：~5000 / 无历史参考)

- [ ] 6. **Orchestrator 集成** — 在主 orchestrator 中增加 SRE pipeline 分支：当 intent_router 返回 sre 意图时，调用 SRE pipeline 而非 code pipeline；SRE pipeline 完成后直接输出报告，不进入 ENRICH->IMPLEMENT->VERIFY 流程。 (预估复杂度：中, 预估 token：~5000 / 无历史参考)

## 边界

### IN scope
- intent_router.py 中新增 sre 意图类别及关键词匹配
- roles.py 中新增 SRE 角色定义（含 system_prompt、tool 白名单）
- 新建独立的 SRE pipeline 模块（5 phase）
- 命令白名单守卫与危险操作审批机制
- execution_report.md 与 learnings.jsonl 产物输出
- orchestrator 中 SRE 路由分支
- 以上所有功能的单元测试

### OUT of scope
- 现有 code pipeline (ENRICH->IMPLEMENT->VERIFY) 的任何修改
- SSH transport 远端执行（v1 仅支持 localhost）
- CMDB infra_assets 表集成
- dashboard 中 SRE 专用面板
- 跨主机的服务编排（47+49 联动）
- SRE 操作的 GUI/Web 界面

### 依赖的外部条件
- 现有 intent_router.py 可扩展（有明确的意图分类接口）
- 现有 roles.py 可扩展（有角色注册机制）
- 现有 orchestrator 可增加路由分支
- 现有 learnings.jsonl 基础设施可复用
- 测试环境支持 bash 工具调用（mock 即可）

## 目标

### 成功标准
1. intent_router 能正确识别包含 SRE 关键词的用户意图并返回 `sre` 类别
2. SRE role 在 roles.py 中注册成功，配置项（max_turns, allowed_tools 等）可被 pipeline 读取
3. SRE pipeline 5 个 phase 顺序执行：DIAGNOSE -> PLAN -> EXECUTE -> VERIFY -> REPORT
4. 命令白名单守卫拦截非白名单命令，危险操作触发 require_approval
5. SRE pipeline 产出 execution_report.md 和 learnings.jsonl，不产生 git commit
6. orchestrator 根据 intent 路由到 SRE pipeline，与 code pipeline 互斥
7. 所有新增代码通过 ruff lint + pytest

### 验收方式
- `pytest tests/test_spec_sre_subagent_design__*.py` 全部通过
- `ruff check` 无新增 lint 错误
- 手动构造 sre 意图输入，验证路由到 SRE pipeline
- 手动构造 code 意图输入，验证仍路由到 code pipeline（回归）
- 验证非白名单命令被拦截（单元测试）
- 验证 execution_report.md 包含操作步骤、结果、验证三段

## 约束

### 不能修改的文件
- 现有 code pipeline 相关文件（enricher, implementer, verifier 等核心逻辑）
- 现有 code pipeline 的测试文件
- pyproject.toml, requirements.txt（不引入新依赖）
- site/dashboard.html（不在本 scope 内改 dashboard）

### 项目部署分支
- main（基于当前 main 分支开发）

### 已知风险
- SRE pipeline 的 EXECUTE phase 执行 shell 命令存在安全风险，需严格白名单守卫
- learnings.jsonl 追加可能与现有 learnings 系统的 schema 冲突，需适配
- SRE role 的 system_prompt 需要 LLM 配合生成合规命令，测试中需 mock LLM 行为
- orchestrator 路由分支的互斥性需仔细处理，避免 sre 意图泄露到 code pipeline
- 已有 6 个 test_spec_sre_subagent_design__*.py 测试文件存在，可能包含前置断言需满足

### 预估 token 消耗
- prompt: ~30000
- completion: ~12000
- 数据来源: 无历史参考
