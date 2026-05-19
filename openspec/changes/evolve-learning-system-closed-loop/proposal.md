# Proposal: 闭环学习系统 — 从日志记录到自我进化

## Summary
将 zsiga 的学习系统从"追加日志"升级为"评估→提炼→沉淀→总结→结晶为 skill"的闭环。让 zsiga 不仅能记录失败，还能理解为什么失败、提取可执行的行为改进、并自动将高频模式固化为 skill。

## Motivation
当前学习系统的五个断层：
1. 记录的是"什么失败"而非"为什么失败" — takeaway 只是错误消息的副本
2. pattern_key 粒度太粗 — lint/test/timeout/空proposal全混在同一个桶
3. pipeline 自身的故障（decompose 误判、空 proposal、intent router 错分类）不在学习范围内
4. skill_evolver 生成的 skill 没有行为约束力 — 只是错误日志副本，不是可执行规则
5. 成功经验被忽略 — 17个 pass.deliver 无任何提炼

这导致：zsiga 犯了 110 个 change 的错误，但 decompose 误判和空 proposal 这种 pipeline bug 从未被学习到。

## Expected Behavior

### Phase 1: 结构化失败记录（memory/learn.py 改造）

当前 `record_outcome()` 的 `_classify_error()` 只认识 7 个 lint 错误码。需要扩展为分层分类：

**新增 error taxonomy（错误分类学）：**

第一层 — 故障域（WHERE）：
- `code` — 生成的代码有问题（lint/test 错误）
- `pipeline` — zsiga 自身的 pipeline 逻辑有缺陷
- `infrastructure` — 外部环境问题（SSH超时、磁盘满、API限流）
- `spec` — proposal/specs 本身有歧义或不完整

第二层 — 根因（WHY）：
- `code.lint.e401` — 多行 import
- `code.lint.e702` — 分号语句
- `code.test.assertion` — 测试断言失败
- `code.test.import` — import 错误
- `pipeline.decompose.false_positive` — 跨项目误判
- `pipeline.intent.misclassify` — intent router 错分类
- `pipeline.proposal.empty_read` — 读不到 proposal 文件
- `pipeline.proposal.malformed` — proposal 内容异常
- `infrastructure.ssh.timeout` — SSH 连接超时
- `infrastructure.api.rate_limit` — LLM API 限流
- `infrastructure.disk.full` — 磁盘空间不足
- `spec.ambiguous` — proposal 描述不清
- `spec.scope_too_large` — 单个 change 范围过大

第三层 — 教训（LESSON）：
每条 lesson 必须包含：
- `what_happened`: 现象描述（1 句话）
- `root_cause`: 根因分析（我假设了 X，实际是 Y）
- `prevention`: 具体的预防措施（下次遇到时应该怎么做）
- `fix_applied`: 实际的修复动作

**改造 `record_outcome()` 签名：**
```python
def record_outcome(
    change_name: str,
    project: str,
    success: bool,
    phase: str,
    detail: str = None,
    error_domain: str = None,     # 新增: code/pipeline/infrastructure/spec
    root_cause: str = None,       # 新增: 根因描述
    prevention: str = None,       # 新增: 预防措施
):
```

**改造 `_classify_error()` 为 `_classify_failure()`:**
- 先判断 error_domain（pipeline 级故障由 orchestrator 显式标记）
- 再按 detail 内容细分根因
- 自动生成 prevention 建议

### Phase 2: Pipeline 自诊断钩子（orchestrator.py 改造）

在 pipeline 的每个关键节点增加断言检查，失败时记录到学习系统：

**1. Decompose 后置检查：**
```python
decomp = decompose(proposal_text, available_projects)
if len(decomp.subtasks) > 1:
    # 验证：每个 subtask 的项目上是否真的存在 change_dir
    for subtask in decomp.subtasks:
        sub_transport = self._get_transport(subtask.project)
        check = sub_transport.run_shell(f"test -d '{prop['change_dir']}' && echo EXISTS")
        if "EXISTS" not in check.get("stdout", ""):
            record_outcome(
                change_name=prop['id'],
                project=subtask.project,
                success=False,
                phase="decompose",
                detail=f"change_dir not found on target: {prop['change_dir']}",
                error_domain="pipeline",
                root_cause="decompose matched project via keyword but change_dir only exists on original project",
                prevention="validate change_dir existence before splitting; if not found, force single-project mode",
            )
            # 降级为单项目处理
            decomp = Decomposition(
                original_instruction=proposal_text,
                subtasks=[SubTask(project=prop['project'], description=proposal_text)],
                parallel_groups=[[prop['project']]],
                estimated_total="1 subtask (decompose fallback)",
            )
            break
```

**2. Proposal 读取后置检查：**
```python
proposal_text = read_file(f"{change_dir}/proposal.md", transport) or ""
if not proposal_text.strip():
    record_outcome(
        change_name=change_name,
        project=project_name,
        success=False,
        phase="read_proposal",
        detail=f"empty proposal from {change_dir}",
        error_domain="pipeline",
        root_cause="proposal.md not found or empty on target project",
        prevention="check proposal existence before classify(); if empty, skip with explicit lesson",
    )
    return False
```

**3. Intent classify 后检查：**
```python
intent = classify(proposal_text)
if intent.intent_type == IntentType.OPEN_ENDED and route_path == "ask_user":
    # 在 daemon 模式下，ask_user 意味着跳过 — 记录为什么
    record_outcome(
        change_name=change_name,
        project=project_name,
        success=False,
        phase="intent",
        detail=f"classified as {intent.intent_type.value}, verbalization: {intent.verbalization}",
        error_domain="pipeline",
        root_cause=f"intent router returned open-ended for proposal starting with: {proposal_text[:100]}",
        prevention="if daemon mode, fallback to implementation for proposals with clear action verbs (add/implement/fix/enhance/create/refactor)",
    )
```

### Phase 3: 成功经验提炼（memory/learn.py 新增）

新增 `record_success()`，在 change 成功完成时提取关键知识：

```python
def record_success(change_name: str, project: str, phases: list[dict]):
    """从成功的 change 中提炼可复用知识。"""
    
    # 1. 提取 proposal → 成功的特征
    # 哪些措辞/关键词导致了成功分类
    
    # 2. 提取阶段效率
    # enrich 用了几轮？implement 用了几轮？verify 一次过还是多次？
    first_pass = all(p.get("fix_attempts", 0) == 0 for p in phases)
    
    # 3. 提取项目特征
    # 这个项目的 venv 路径、test 命令、常见模式
    
    lesson = {
        "type": "success_pattern",
        "ts": datetime.now().isoformat(),
        "change_name": change_name,
        "project": project,
        "first_pass": first_pass,
        "total_turns": sum(p.get("turns", 0) for p in phases),
        "total_seconds": sum(p.get("seconds", 0) for p in phases),
    }
    _append_lesson(lesson)
```

### Phase 4: Skill 结晶器（skills/skill_evolver.py 改造）

当前 skill_evolver 的输出没有行为约束力。改造为：

**输入**：pattern_miner 聚类的 patterns + 每条 lesson 的 prevention 字段

**输出**：skills/*.md 文件，包含：
- `## When to Apply` — 什么场景下这个 skill 生效
- `## Rules` — 具体的行为规则（来自 prevention 字段）
- `## Anti-Patterns` — 不要做什么（来自 root_cause 字段）
- `## Examples` — 真实案例（来自 what_happened 字段）

**结晶条件**（满足任一即触发）：
- 同一个 pattern_key 出现 >= 3 次
- 同一个 error_domain 出现 >= 2 次
- 同一个 root_cause 出现 >= 2 次
- 一次 pipeline 级故障（severity=high）

**结晶过程**：
1. 收集同 pattern_key 下所有 lesson 的 prevention/root_cause
2. 用 LLM 总结为不超过 5 条的行为规则（或者如果不用 LLM，用规则模板生成）
3. 写入 skills/{domain}-{pattern}.md
4. 该 skill 文件会在下次 agent 运行时通过 active_context.md 注入

**示例输出（skills/pipeline-decompose-validation.md）：**
```markdown
---
name: pipeline-decompose-validation
description: 跨项目分解前的验证规则
auto_generated: true
---
# Pipeline Decompose Validation

> Auto-generated from 2 pipeline failures.
> Last updated: 2026-05-19

## When to Apply
When decompose() returns >1 subtasks for a change.

## Rules
1. Before splitting cross-project, verify change_dir exists on each target project
2. If change_dir not found on a subtask's project, force single-project fallback
3. Never use keyword matching alone — validate with actual filesystem check

## Anti-Patterns
- Do NOT trust keyword match without validation ("实时" matched stockshark but the change was zsiga-only)
- Do NOT reuse change_dir from original project when switching to a different project's transport

## Examples
- enhance-dashboard proposal matched stockshark via "实时" keyword, but change only existed on zsiga local
```

### Phase 5: 学习循环闭环

整个流程形成闭环：

```
Change 失败/成功
    ↓
record_outcome() / record_success()     ← Phase 1-3: 结构化记录
    ↓
learnings.jsonl (结构化 lesson)
    ↓
pattern_miner.mine_patterns()           ← 按根因聚类
    ↓
skill_evolver.evolve_skills()           ← Phase 4: 结晶为 skill
    ↓
skills/pipeline-decompose-validation.md ← 可执行的行为规则
    ↓
active_context.md 注入                  ← 下次 agent 运行时生效
    ↓
遇到同样场景 → skill 规则生效 → 不再犯同样错误
```

**闭环验证**：每次 skill_evolver 生成新 skill 后，检查过去 10 个同 pattern_key 的 lesson，确认根因不再出现。如果根因消失 → skill 生效确认。如果根因持续 → skill 规则需要迭代。

## Constraints
- 不引入新的外部依赖
- LLM 调用仅用于 skill 结晶阶段的总结（可用 glm-4-flash 降低成本），其余全规则化
- pattern_key 保持向后兼容（新格式 `domain.root_cause` 可从旧格式 `pipeline.fail.X` 迁移）
- 现有 learnings.jsonl 数据需迁移（一次性脚本）
- 所有改动完成后必须 git commit 并 git push
