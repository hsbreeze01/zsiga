# 设计文档：Layer 0 确定性二进制验证体系

> 日期: 2026-05-26
> 状态: Draft
> 关联: pipeline/verifier.py, pipeline/verify_layer0.py (新增), pipeline/enricher.py, memory/learn.py

---

## 一、背景与问题

### 1.1 核心问题：Verify False Positive

zsiga 的 verify 阶段曾出现严重误判：`add-phase-token-cap` 提案涉及 4 个 spec 文件（phase-cap-budget.md, phase-cap-config.md, phase-cap-loop.md, phase-cap-orchestration.md），但实际只实现了 1 个文件（token_budget.py），功能完成度仅 25%。然而 verify 给出了 PASS。

**根因链**：

```
ENRICH 生成 4 个 spec 文件
  → 所有 scenario 的 testable=true
  → spec_pytest_check 发现 ENRICH 没有生成对应的 pytest 文件
  → 将所有 scenario demote 为 testable=false
  → Layer 1 (pytest): vacuous (0 个 testable scenario, 0 tests run)
  → Layer 2 (LLM): 只抽检了 phase-cap-budget.md 一个 spec
  → LLM 判断: "budget.md 的内容实现得不错" → PASS
  → DELIVER: "success"
  → 实际: 75% 的 spec 未实现
```

**同时**：Review 阶段正确发现了 3 个 CRITICAL 问题（config/loop/orchestration 未实现），但 Review FAIL 不阻断 pipeline — zsiga 会尝试修复，修复不成仍继续到 verify。

### 1.2 Learning 系统的同类问题

通过分析 `learnings.jsonl` 中 14 条记录，发现 learning 格式存在同类问题：

**现状**：
```json
{
  "pattern_key": "code.unknown",
  "takeaway": "review error and adjust approach"
}
```

**问题**：
- takeaway 是模糊的"建议"，不是精确的"规则"
- 缺少 case（具体发生了什么）、why（为什么发生）
- 无法转化为可执行的行为改变
- pattern_miner 只统计出现次数和严重度，无法生成精确诊断

**对比**：好的 learning 应该像 `pipeline.verify.false_positive` 这条——有完整的 case + why + rule，agent 读到后能明确知道下次该做什么不同的事。

### 1.3 Review FAIL 不阻断 Pipeline

`run_review_loop()` 的行为：review 发现 CRITICAL issues → 尝试修复 → 修复不成 → 返回 `ISSUES_FOUND`。但 orchestrator 收到 `ISSUES_FOUND` 后不阻断，继续进入 verify。如果 verify 也误判 PASS，feature 就会以不完整状态 DELIVER。

---

## 二、设计理念

### 2.1 理论基础

基于三篇 mindstudio.ai 文章的核心思想：

**文章一 (Self-Improving Feedback Loop)**：
- 精确诊断反馈的质量决定自我改进的质量
- 模糊反馈（"注意安全"）→ 模糊改进
- 精确诊断（"verify 没有检查所有 spec 的代码覆盖"）→ 精确修复

**文章二 (How to Write Evals for AI Agents)**：
- Eval = 把人类判断编码成可运行的测试
- 大多数团队花大量时间调 prompt，却不投资建设评估体系
- 没有评估，调优就是蒙着眼打靶

**文章三 (AutoResearch Eval Loop & Binary Tests)**：
- 二进制测试（yes/no）是 AI 评估的最佳单位
- "评估即产品" — 一旦有了可靠的评估方法，优化就变成系统性的
- 先写测试再写实现（先定义成功标准，再让 Agent 去实现）

### 2.2 设计原则

1. **确定性优于概率性**：在最关键的地方（verify）插入确定性检查，用 yes/no 的二进制测试作为 ground truth，LLM 判断作为补充
2. **先写验收标准再实现**：每个 proposal 必须附带 Binary Acceptance Checks (BAC)，verify 时自动检查
3. **case + why + rule**：learning 记录必须包含三要素——案例、原因、规则。规则必须能转化为代码中的 assert
4. **不破坏现有架构**：Layer 0 作为 verify 的新前置层插入，不改动 Layer 1/Layer 2 的现有逻辑

### 2.3 核心决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Layer 0 放在哪里 | verifier.py 的 verify() 函数开头 | 在 Layer 1/2 之前拦截，避免浪费 LLM 调用 |
| Layer 0 失败时 | 直接 FAIL，不调 LLM | 确定性检查的结果不可被 LLM 推翻 |
| BAC 由谁写 | 人工（我们）或 Reflector 生成 proposal 时自动附带 | 短期人工，长期自动化 |
| Learning 格式 | 新增 case/why/rule 字段，不删除旧字段 | 向后兼容，旧 learning 仍可读取 |
| Review FAIL 是否阻断 | 暂不改动 | Layer 0 已能从 verify 侧拦截不完整 feature |

---

## 三、方案设计

### 3.1 Layer 0: 确定性二进制检查

#### 3.1.1 数据结构

```python
# 文件: zsiga/pipeline/verify_layer0.py

@dataclass
class Layer0Check:
    """单个二进制检查项。"""
    id: str              # e.g. "spec_file_coverage"
    description: str     # e.g. "每个 spec 文件至少有一个对应的代码变更文件"
    passed: bool         # True / False，没有中间地带
    evidence: str        # e.g. "phase-cap-config.md: 无对应文件变更"

@dataclass
class Layer0Result:
    """Layer 0 全部检查的结果。"""
    checks: list[Layer0Check]
    elapsed_seconds: float = 0.0

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def failed_checks(self) -> list[Layer0Check]:
        return [c for c in self.checks if not c.passed]

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def total_count(self) -> int:
        return len(self.checks)

    def summary_line(self) -> str:
        if self.all_passed:
            return f"L0 PASS: {self.total_count}/{self.total_count} checks passed"
        return f"L0 FAIL: {self.passed_count}/{self.total_count} checks passed"
```

#### 3.1.2 检查清单

##### L0-01: spec_file_coverage — 每个 spec 文件都有对应代码变更

**问题**：`add-phase-token-cap` 有 4 个 spec，只有 1 个有代码变更。

**检查逻辑**：
1. 列出 `specs/*.md` 所有 spec 文件
2. 获取 `git diff --name-only` 的变更文件列表
3. 对每个 spec 文件，从文件名和标题中提取关键词（如 `phase-cap-config` → `config`）
4. 检查是否存在变更文件与关键词相关

```python
def check_spec_file_coverage(
    change_dir: str, 
    target_path: str, 
    pre_impl_sha: str, 
    transport: Transport
) -> Layer0Check:
    spec_files = list_files_recursive(f"{change_dir}/specs", "*.md", transport)
    if not spec_files:
        return Layer0Check("spec_file_coverage", "每个 spec 文件至少有一个对应的代码变更", True, "无 spec 文件，跳过")
    
    diff_files = _get_changed_files(target_path, pre_impl_sha, transport)
    diff_content = git_ops.diff(target_path, pre_impl_sha, transport=transport)
    
    uncovered = []
    for spec_path in spec_files:
        spec_filename = os.path.basename(spec_path)
        spec_name = spec_filename.removesuffix(".md")
        keywords = _extract_spec_keywords(spec_path, transport)
        
        covered = False
        for df in diff_files:
            # 匹配策略：关键词出现在变更文件名中，或出现在 diff 内容中
            df_base = os.path.basename(df)
            if any(kw in df_base.lower() for kw in keywords):
                covered = True
                break
            if any(kw in diff_content.lower() for kw in keywords):
                covered = True
                break
        
        if not covered:
            uncovered.append(spec_filename)
    
    passed = len(uncovered) == 0
    evidence = ""
    if uncovered:
        evidence = f"未覆盖的 spec: {', '.join(uncovered)}"
    else:
        evidence = f"全部 {len(spec_files)} 个 spec 文件均有对应代码变更"
    
    return Layer0Check("spec_file_coverage", "每个 spec 文件至少有一个对应的代码变更", passed, evidence)
```

**关键词提取策略**：
- 从 spec 文件名提取：`phase-cap-config.md` → `['config']`
- 从 spec 标题（第一个 `#` 行）提取
- 去除通用词（如 `phase`, `cap`, `token` 等高频词）
- 兜底：如果关键词提取后为空，使用完整 spec 文件名（不含 `.md`）

##### L0-02: tasks_completion — 所有 task 已完成

```python
def check_tasks_completion(change_dir: str, transport: Transport) -> Layer0Check:
    tasks = read_file(f"{change_dir}/tasks.md", transport) or ""
    if not tasks:
        return Layer0Check("tasks_completion", "tasks.md 中所有 task 已勾选", True, "无 tasks.md，跳过")
    
    unchecked = re.findall(r'-\s*\[\s*\]', tasks)
    passed = len(unchecked) == 0
    evidence = f"剩余未完成 task: {len(unchecked)} 个" if unchecked else "所有 task 已完成"
    
    return Layer0Check("tasks_completion", "tasks.md 中所有 task 已勾选", passed, evidence)
```

##### L0-03: testable_not_all_false — 不全是 testable=false

```python
def check_testable_not_all_false(change_dir: str, transport: Transport) -> Layer0Check:
    spec_files = list_files_recursive(f"{change_dir}/specs", "*.md", transport)
    if not spec_files:
        return Layer0Check("testable_not_all_false", "至少存在 testable=true 的 scenario", True, "无 spec 文件，跳过")
    
    total_testable = 0
    total_scenarios = 0
    for spec_path in spec_files:
        spec_text = read_file(spec_path, transport) or ""
        scenarios = parse_spec(spec_text)
        for s in scenarios:
            total_scenarios += 1
            if s.testable:
                total_testable += 1
    
    if total_scenarios == 0:
        return Layer0Check("testable_not_all_false", "至少存在 testable=true 的 scenario", True, "无 scenario，跳过")
    
    passed = total_testable > 0
    evidence = f"{total_scenarios} 个 scenario 中 {total_testable} 个 testable=true"
    
    return Layer0Check("testable_not_all_false", "至少存在 testable=true 的 scenario", passed, evidence)
```

##### L0-04: no_syntax_error — 变更文件无语法错误

```python
def check_no_syntax_error(target_path: str, pre_impl_sha: str, transport: Transport) -> Layer0Check:
    diff_files = _get_changed_files(target_path, pre_impl_sha, transport)
    py_files = [f for f in diff_files if f.endswith('.py')]
    
    syntax_errors = []
    for pf in py_files:
        source = read_file(pf, transport)
        if source is None:
            continue
        ok, err = _py_compile_ok(source)
        if not ok:
            syntax_errors.append(f"{os.path.basename(pf)}: {err.splitlines()[0][:100]}")
    
    passed = len(syntax_errors) == 0
    evidence = "; ".join(syntax_errors) if syntax_errors else f"{len(py_files)} 个 Python 文件语法检查通过"
    
    return Layer0Check("no_syntax_error", "变更的 Python 文件无语法错误", passed, evidence)
```

##### L0-05: spec_scenario_coverage — spec 中的关键要求在 diff 中有痕迹

```python
def check_spec_scenario_coverage(
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport,
) -> Layer0Check:
    """检查每个 spec 中 SHALL/MUST 关键要求是否在 diff 中出现。"""
    spec_files = list_files_recursive(f"{change_dir}/specs", "*.md", transport)
    if not spec_files:
        return Layer0Check("spec_scenario_coverage", "spec 中的关键要求在 diff 中有实现痕迹", True, "无 spec 文件，跳过")
    
    diff_content = git_ops.diff(target_path, pre_impl_sha, transport=transport).lower()
    if not diff_content.strip():
        # diff 为空，无法检查
        return Layer0Check("spec_scenario_coverage", "spec 中的关键要求在 diff 中有实现痕迹", False, "git diff 为空")
    
    uncovered = []
    for spec_path in spec_files:
        spec_text = read_file(spec_path, transport) or ""
        # 提取 SHALL/MUST 后面的关键要求词
        requirements = re.findall(r'SHALL\s+(?:provide|include|accept|return|contain|set|handle|detect|have|use|be)\s+(\S+(?:\s+\S+)?)', spec_text, re.IGNORECASE)
        # 检查这些关键词是否出现在 diff 中
        spec_uncovered = []
        for req in requirements:
            # 取要求的最后一段（最具体的部分）
            keywords = [w.lower() for w in req.split()[-3:] if len(w) > 3]
            if keywords and not any(kw in diff_content for kw in keywords):
                spec_uncovered.append(req.strip()[:60])
        
        if spec_uncovered:
            uncovered.append(f"{os.path.basename(spec_path)}: {', '.join(spec_uncovered[:2])}")
    
    passed = len(uncovered) == 0
    evidence = "; ".join(uncovered) if uncovered else f"全部 {len(spec_files)} 个 spec 的关键要求在 diff 中有痕迹"
    
    return Layer0Check("spec_scenario_coverage", "spec 中的关键要求在 diff 中有实现痕迹", passed, evidence)
```

#### 3.1.3 检查选择策略

不是所有检查每次都跑。根据变更内容选择：

```python
def run_layer0_checks(
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport,
) -> Layer0Result:
    """执行 Layer 0 全部确定性检查。"""
    t_start = time.monotonic()
    
    # 始终执行的检查
    checks = [
        check_spec_file_coverage(change_dir, target_path, pre_impl_sha, transport),
        check_tasks_completion(change_dir, transport),
        check_testable_not_all_false(change_dir, transport),
        check_no_syntax_error(target_path, pre_impl_sha, transport),
        check_spec_scenario_coverage(change_dir, target_path, pre_impl_sha, transport),
    ]
    
    # 条件检查：BAC (如果 proposal.md 中有 BAC 条目)
    bac_checks = check_bac_acceptance(change_dir, target_path, pre_impl_sha, transport)
    checks.extend(bac_checks)
    
    elapsed = time.monotonic() - t_start
    result = Layer0Result(checks=checks, elapsed_seconds=elapsed)
    
    # 持久化
    _persist_layer0_result(change_dir, transport, result)
    
    return result
```

#### 3.1.4 与 verifier.py 的集成

```python
# verifier.py verify() 函数修改

async def verify(agent, change_dir, target_path, pre_impl_sha, transport=None, ...):
    transport = transport or LocalTransport()
    
    # ---- Layer 0: 确定性二进制检查 (NEW) ----
    layer0 = run_layer0_checks(change_dir, target_path, pre_impl_sha, transport)
    print(f"  verify {layer0.summary_line()}", flush=True)
    
    if not layer0.all_passed:
        # 确定性检查失败，直接写 FAIL verify.md，不调用 LLM
        _write_layer0_verify_md(change_dir, transport, layer0)
        return None
    
    # ---- Layer 1: mechanical pytest (existing, unchanged) ----
    layer1 = run_layer1_pytest(change_dir, target_path, transport=transport, venv_python=venv_python)
    # ... 后续逻辑不变 ...
```

#### 3.1.5 Layer 0 FAIL 时的 verify.md 格式

```markdown
Verdict: FAIL
Layer 0: FAIL — 2/5 checks failed

## Failed Checks
1. [CRITICAL] spec_file_coverage: 每个 spec 文件至少需要一个对应的代码变更
   Evidence: 未覆盖的 spec: phase-cap-config.md, phase-cap-loop.md, phase-cap-orchestration.md

2. [CRITICAL] testable_not_all_false: 至少存在 testable=true 的 scenario
   Evidence: 18 个 scenario 中 0 个 testable=true

## Passed Checks (3/5)
- ✓ tasks_completion: 所有 task 已完成
- ✓ no_syntax_error: 2 个 Python 文件语法检查通过
- ✓ spec_scenario_coverage: 全部 4 个 spec 的关键要求在 diff 中有痕迹
```

---

### 3.2 Proposal Eval 规范 (Binary Acceptance Checks)

#### 3.2.1 proposal.md 新增 BAC 段落

在现有 `## Acceptance Criteria` 段落中增加结构化的 Binary Acceptance Checks：

```markdown
## Acceptance Criteria

### Binary Acceptance Checks (automated, Layer 0 verified)
以下每条必须通过 yes/no 判断，不可模糊：

- [BAC-01] `token_budget.py` 中存在 `phase_cap` 属性 (默认 0)
- [BAC-02] `token_budget.py` 中存在 `reset_phase()` 方法
- [BAC-03] `token_budget.py` 中 `record()` 返回 `cap_exceeded` 字段
- [BAC-04] `config.py` 中存在 `PHASE_TOKEN_CAPS` 配置项
- [BAC-05] `config.py` 中存在 `get_phase_cap()` 方法
- [BAC-06] `loop.py` 中引用了 `cap_exceeded` 或 `CAP_EXCEEDED`
- [BAC-07] `orchestrator.py` 中设置了 `budget.phase_cap`
- [BAC-08] `orchestrator.py` 中处理了 `CAP_EXCEEDED` 结果
- [BAC-09] 所有 spec 文件 (4个) 都有对应的代码变更
- [BAC-10] 至少存在 1 个 testable=true 的 scenario

### Behavioral Criteria (LLM-verified, Layer 2)
- BC-01: 当 phase_cap 超限时，phase 优雅终止而不是 crash
- BC-02: 不会影响现有 session_exceeded 的行为
```

#### 3.2.2 BAC 的格式约束

BAC 条目必须遵循以下模式之一：

| 模式 | 格式 | 示例 | 验证方式 |
|------|------|------|---------|
| **存在性** | `` `file` 中存在 `symbol` `` | `config.py` 中存在 `PHASE_TOKEN_CAPS` | grep `PHASE_TOKEN_CAPS` in `config.py` 源码 |
| **引用性** | `` `file` 中引用了 `term` `` | `loop.py` 中引用了 `cap_exceeded` | grep `cap_exceeded` in `loop.py` 源码 |
| **覆盖率** | `所有 spec 文件 (N个) 都有对应代码变更` | (固定格式) | spec 文件名 × diff 文件名交叉 |
| **计数** | `至少存在 N 个 testable=true 的 scenario` | (固定格式) | 解析 specs 统计 |
| **文件存在** | `` `path/pattern` 文件存在 `` | `tests/test_spec_*.py` | glob 匹配 |

#### 3.2.3 BAC 自动验证

```python
# verify_layer0.py

def check_bac_acceptance(
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport,
) -> list[Layer0Check]:
    """解析 proposal.md 中的 BAC 列表，逐条验证。"""
    proposal = read_file(f"{change_dir}/proposal.md", transport)
    if not proposal:
        return []
    
    # 提取 BAC 条目
    bac_items = re.findall(
        r'\[BAC-(\d+)\]\s*(.+?)(?:\n|$)',
        proposal,
    )
    if not bac_items:
        return []
    
    diff_content = git_ops.diff(target_path, pre_impl_sha, transport=transport)
    diff_files = _get_changed_files(target_path, pre_impl_sha, transport)
    
    checks = []
    for bac_num, bac_text in bac_items:
        passed, evidence = _evaluate_single_bac(
            bac_text, diff_content, diff_files, 
            target_path, transport
        )
        checks.append(Layer0Check(
            id=f"bac_{bac_num}",
            description=f"[BAC-{bac_num}] {bac_text.strip()}",
            passed=passed,
            evidence=evidence,
        ))
    
    return checks


def _evaluate_single_bac(
    bac_text: str,
    diff_content: str,
    diff_files: list[str],
    target_path: str,
    transport: Transport,
) -> tuple[bool, str]:
    """评估单个 BAC 条目，返回 (passed, evidence)。"""
    
    # 模式 1: "`file` 中存在 `symbol`"
    m = re.search(r'`([^`]+)`\s*中存在\s*`([^`]+)`', bac_text)
    if m:
        file_name, symbol = m.group(1), m.group(2)
        return _check_symbol_in_file(file_name, symbol, target_path, transport)
    
    # 模式 2: "`file` 中引用了 `term`"
    m = re.search(r'`([^`]+)`\s*中引用了\s*`([^`]+)`', bac_text)
    if m:
        file_name, term = m.group(1), m.group(2)
        return _check_term_in_file(file_name, term, target_path, transport)
    
    # 模式 3: "所有 spec 文件 (N个) 都有对应代码变更"
    if '所有 spec' in bac_text and '对应代码变更' in bac_text:
        # 已由 L0-01 spec_file_coverage 覆盖
        return True, "已由 spec_file_coverage 检查覆盖"
    
    # 模式 4: "至少存在 N 个 testable=true"
    m = re.search(r'至少存在\s*(\d+)\s*个\s*testable=true', bac_text)
    if m:
        min_count = int(m.group(1))
        # 已由 L0-03 覆盖，但这里做精确计数
        return _check_testable_count(change_dir, min_count, transport)
    
    # 无法识别的模式 → 跳过（不阻塞）
    return True, f"无法自动验证，跳过: {bac_text[:60]}"
```

#### 3.2.4 Steward Gate 更新

在 `proposal_gate.py` 的评分维度中新增"验收可测性"：

```python
# proposal_gate.py Steward 评分

# 新增第 6 个维度
dimensions = [
    ("可行性", ...),        # 现有
    ("可执行性", ...),      # 现有
    ("能力匹配", ...),      # 现有
    ("历史风险", ...),      # 现有
    ("范围合理性", ...),    # 现有
    ("验收可测性", ...),    # 新增
]

# 验收可测性评分标准：
# 2分: 有结构化 BAC 列表（≥3 条），每条符合格式约束，覆盖所有 spec 文件
# 1分: 有 Acceptance Criteria 但不够结构化（自然语言描述为主）
# 0分: 没有 Acceptance Criteria 或 AC 全是主观描述

# 验收可测性 = 0 时，总分上限锁定为 5（强制 PUSHBACK）
```

---

### 3.3 Learning 格式重构

#### 3.3.1 新的 Learning 格式

```python
# learn.py record_lesson() 增加 case/why/rule

def record_lesson(
    title: str, 
    context: str, 
    takeaway: str,
    pattern_key: str = None, 
    source: str = "pipeline",
    # 新增参数
    case: dict = None,       # {"what": ..., "expected": ..., "actual": ...}
    why: str = None,         # 因果链描述
    rule: str = None,        # 可操作的行为规则
):
    lesson = {
        "type": "lesson",
        "ts": datetime.now().isoformat(),
        "source": source,
        "title": title,
        "context": context,
        "takeaway": takeaway,  # 保留向后兼容
    }
    
    # 新增结构化字段
    if case:
        lesson["case"] = case
    if why:
        lesson["why"] = why
    if rule:
        lesson["rule"] = rule
    if pattern_key:
        lesson["pattern_key"] = pattern_key
    
    # 写入文件 + DB (不变)
    ...
```

#### 3.3.2 record_outcome() 改进

当 Layer 0 失败时，自动生成精确的 learning：

```python
# verifier.py 或 orchestrator.py 中，Layer 0 失败时：

def _record_layer0_failure(change_name: str, layer0: Layer0Result, change_dir: str):
    """Layer 0 失败时记录精确的 case+why+rule。"""
    failed = layer0.failed_checks
    
    # 构建 case
    case = {
        "what": f"{change_name}: Layer 0 verify FAIL ({len(failed)} checks failed)",
        "failed_checks": [f"{c.id}: {c.evidence}" for c in failed],
    }
    
    # 构建 why — 基于 failed checks 推断
    why_parts = []
    for c in failed:
        if c.id == "spec_file_coverage":
            why_parts.append("部分 spec 文件没有对应的代码变更，实现不完整")
        elif c.id == "testable_not_all_false":
            why_parts.append("所有 scenario 被标记 testable=false，Layer 1 无法提供机械验证")
        elif c.id == "tasks_completion":
            why_parts.append("tasks.md 中有未完成的 task")
    
    # 构建 rule
    rule = "Layer 0 确定性检查必须全部通过才能进入 Layer 1/2"
    
    record_lesson(
        title=f"LAYER0 FAIL: {change_name}",
        context=f"project=zsiga, checks={len(failed)}/{layer0.total_count} failed",
        takeaway=rule,
        pattern_key="verify.layer0.fail",
        source="layer0",
        case=case,
        why="; ".join(why_parts),
        rule=rule,
    )
```

#### 3.3.3 消费端更新

```python
# context.py load_recent_lessons() 更新

def load_recent_lessons(n: int = 20) -> list[str]:
    learnings_file = _MEMORY_DIR / "learnings.jsonl"
    if not learnings_file.exists():
        return []
    lines = learnings_file.read_text(encoding="utf-8").strip().split("\n")
    lines = [l for l in lines if l.strip()]
    if not lines:
        return []
    recent = lines[-n:]
    lessons = []
    for line in recent:
        try:
            obj = json.loads(line)
            # 优先使用 rule（精确规则），回退到 takeaway（模糊建议）
            if obj.get("rule"):
                rule = obj["rule"]
                case_what = obj.get("case", {}).get("what", "")
                if case_what:
                    lessons.append(f"[RULE] {rule} (case: {case_what[:80]})")
                else:
                    lessons.append(f"[RULE] {rule}")
            else:
                pk = obj.get("pattern_key", "")
                tw = obj.get("takeaway", "")
                lessons.append(f"[{pk}] {tw}" if pk else tw)
        except json.JSONDecodeError:
            continue
    return lessons
```

---

## 四、数据流全景图

### 修改前

```
Proposal → ENRICH → IMPLEMENT → REVIEW → VERIFY → DELIVER
                                              ↓
                                    Layer 1: pytest (可能 vacuous)
                                    Layer 2: LLM (可能只看部分 spec)
                                              ↓
                                    可能 PASS on incomplete work
```

### 修改后

```
Proposal (含 BAC)
    ↓
ENRICH → IMPLEMENT → REVIEW → VERIFY → DELIVER
                                    ↓
                              Layer 0: 确定性二进制检查 (NEW)
                                ├─ spec_file_coverage
                                ├─ tasks_completion
                                ├─ testable_not_all_false
                                ├─ no_syntax_error
                                ├─ spec_scenario_coverage
                                └─ BAC acceptance checks
                                    ↓
                              任一 FAIL → 直接 FAIL, 记录精确 learning
                              全部 PASS → 进入 Layer 1 (pytest)
                                    ↓
                              Layer 1: pytest (existing)
                                    ↓
                              Layer 2: LLM judge (existing)
```

---

## 五、影响范围

### 新增文件
- `zsiga/pipeline/verify_layer0.py` — Layer 0 核心模块

### 修改文件
- `zsiga/pipeline/verifier.py` — 在 verify() 开头插入 Layer 0 调用
- `zsiga/memory/learn.py` — record_lesson/record_outcome 增加 case/why/rule
- `zsiga/memory/context.py` — load_recent_lessons 优先展示 rule
- `zsiga/pipeline/proposal_gate.py` — Steward 新增验收可测性维度

### 不修改文件
- `verify_layer1.py` — Layer 1 逻辑不变
- `verify_layer1.py` — spec_pytest_check.py 不变
- `reviewer.py` — Review 逻辑不变
- `enricher.py` — ENRICH 逻辑不变
- `orchestrator.py` — 只在 verify 调用点前插入 Layer 0

---

## 六、验证计划

用 `add-phase-token-cap` 的 wiring（phase_cap 接入 orchestrator/config/loop）作为端到端验证：

1. 写一个包含完整 BAC 的 proposal
2. zsiga 执行实现
3. Layer 0 检查是否正确检测到未完成的 spec
4. 如果全部 wiring 完成，Layer 0 应该 PASS
5. 如果只完成部分（像之前一样），Layer 0 应该 FAIL 并给出精确证据

---

## 七、后续演进

1. **Reflector 自动生成 BAC**：当 Reflector 从 learnings 生成 proposal 时，自动附带 BAC
2. **Layer 0 检查项扩展**：根据新的 failure pattern 持续增加检查项
3. **Layer 0 结果反馈给 Reflector**：Layer 0 失败 → 自动记录精确 learning → Reflector 基于精确 case+why+rule 生成修复 proposal
4. **Review FAIL 阻断**：考虑在 Review 发现 CRITICAL + Layer 0 也 FAIL 时，直接 REVERT 不进入 verify

---

## 八、参考资料

1. [Self-Improving AI Agent Feedback Loop](https://www.mindstudio.ai/blog/self-improving-ai-agent-feedback-loop) — 精确诊断反馈的质量决定自我改进的质量
2. [How to Write Evals for AI Agents](https://www.mindstudio.ai/blog/how-to-write-evals-for-ai-agents) — Eval = 把人类判断编码成可运行的测试
3. [AutoResearch Eval Loop & Binary Tests](https://www.mindstudio.ai/blog/autoresearch-eval-loop-binary-tests-claude-code-skills) — 二进制 yes/no 测试是 AI 评估的最佳单位
