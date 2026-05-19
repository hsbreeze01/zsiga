# design.md — l5-self-review: 自我审查循环模块

## 架构决策

### 1. 审查循环位于 IMPLEMENT 和 VERIFY 之间

**决策**: 在 `_run_phases()` 中，IMPLEMENT 成功后（包括 mechanical verification 通过后），在 VERIFY 阶段之前插入 REVIEW 阶段。

**理由**: 
- VERIFY 阶段关注 specs → 代码的一致性验证，而 REVIEW 阶段关注代码质量和最佳实践
- 先让 REVIEW 清理代码质量问题，再让 VERIFY 做最终验证，减少 VERIFY 的 fix 轮次
- 如果 IMPLEMENT 的 mechanical verification 就失败了，说明代码有基础问题，不需要浪费 review

### 2. 审查循环使用 orchestrator agent 执行修复

**决策**: 修复阶段复用主 agent（self.agent）而非派发新的 implement-role 子代理。

**理由**:
- 主 agent 已有项目上下文和文件访问权限
- 避免额外创建子代理的 LLM 开销
- 与现有 `_fix_loop` 和 `_eval_fix_loop` 模式一致
- 修复范围受 `changed_files` 约束，与现有 fix 循环安全边界一致

### 3. SUGGESTION 级别不触发修复

**决策**: 只有 CRITICAL 级别问题触发自动修复，SUGGESTION 级别仅记录。

**理由**:
- SUGGESTION 通常是优化建议而非错误，自动修复可能引入新问题
- 避免无限循环：修复 SUGGESTION 可能引发新的 SUGGESTION
- 保持审查循环的确定性和收敛性

### 4. 审查失败不阻止流程

**决策**: 即使审查循环最终仍有 CRITICAL 问题（达到 max_rounds），系统继续进入 VERIFY 阶段而非 revert。

**理由**:
- VERIFY 阶段本身有完整的失败处理机制（_eval_fix_loop + revert）
- Review 是质量提升而非必须通过的门控
- 避免过度保守导致过多 revert

## 数据流

```
IMPLEMENT (done)
    │
    ▼
mechanical verification
    │ (passed)
    ▼
┌─────────────────────────────────────┐
│ REVIEW LOOP (max_rounds = N)        │
│                                     │
│  round 1:                           │
│    run_review() → review.md         │
│    parse_review_verdict()           │
│    ├── CLEAN → break                │
│    ├── SUGGESTION-only → break      │
│    └── CRITICAL found:              │
│         _review_fix() (max_turns=6) │
│         → continue to round 2       │
│                                     │
│  round 2: (same as round 1)         │
│    ...                              │
│                                     │
│  record PhaseRecord(REVIEW)         │
└─────────────────────────────────────┘
    │
    ▼
VERIFY (existing)
    │
    ▼
DELIVER
```

## 需要修改的文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `zsiga/agent/reviewer.py` | 修改 | 新增 `run_review_loop()` 函数，封装审查循环逻辑 |
| `zsiga/pipeline/orchestrator.py` | 修改 | 在 `_run_phases()` 中 IMPLEMENT 后插入 REVIEW 阶段调用 |
| `zsiga/config.py` | 修改 | 添加 `review_max_rounds` 范围校验 warning |
| `tests/test_reviewer.py` | 新增 | 测试审查循环逻辑（parse_verdict、round counting、fix trigger） |

## 关键函数设计

### `run_review_loop()`

```python
async def run_review_loop(
    agent: AgentLoop,
    change_dir: str,
    target_path: str,
    pre_impl_sha: str,
    transport: Transport = None,
    max_rounds: int = 2,
    review_max_turns: int = 10,
    review_timeout: int = 180,
    fix_max_turns: int = 6,
) -> ReviewLoopResult:
    """Execute review loop: review → fix → re-review, up to max_rounds.
    
    Returns ReviewLoopResult with final verdict, total rounds, fix attempts,
    elapsed time, and issues from the last review.
    """
```

### `ReviewLoopResult` dataclass

```python
@dataclass
class ReviewLoopResult:
    final_verdict: str          # "CLEAN", "ISSUES_FOUND", "UNKNOWN"
    rounds_executed: int        # 实际执行的轮数
    fix_attempts: int           # 修复尝试次数
    elapsed_seconds: float      # 总耗时
    last_issues: list[dict]     # 最后一轮的 issues
    had_critical: bool          # 是否曾发现 CRITICAL 问题
```

### orchestrator `_run_phases()` 变更

在 IMPLEMENT PhaseRecord 记录之后、VERIFY 之前，插入：

```python
# Phase 2.5: REVIEW (self-review loop)
if self.config.pipeline.review_max_rounds > 0:
    review_result = await run_review_loop(
        self.agent, change_dir, target_path, pre_sha, transport,
        max_rounds=self.config.pipeline.review_max_rounds,
        review_max_turns=self.config.pipeline.review_max_turns,
        review_timeout=self.config.pipeline.review_timeout,
        fix_max_turns=self.config.pipeline.review_fix_max_turns,
    )
    # Record metrics
    rec.phases.append(PhaseRecord(
        phase=Phase.REVIEW,
        outcome=Outcome.SUCCESS if review_result.final_verdict == "CLEAN" else Outcome.FAIL,
        seconds_used=review_result.elapsed_seconds,
        fix_attempts=review_result.fix_attempts,
        detail=_summarize_issues(review_result.last_issues),
    ))
```
