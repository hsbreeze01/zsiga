# Proposal: 自主反思闭环 — daemon cycle 结束后自动检测改进点并生成 proposal

## Summary
在 daemon_loop 的 run_cycle() 之后新增 self_reflect() 阶段。当连续空闲 >= 3 个 cycle 时，Reflector 自动扫描 pattern_warnings + metrics 退化信号 + 回滚诊断，生成改进 proposal 到 openspec/changes/，下一个 cycle 自动拾取执行。

这是 zsiga 从"被动执行外部 proposal"到"主动发现自身问题并修复"的关键一步。

## Motivation
当前 zsiga 的所有 proposal 都由外部人类写入。zsiga 虽然有 learnings、pattern_miner、diagnoser 等学习模块，但这些模块只产生"记录"（写入文件），不产生"行动"（生成 proposal）。闭环断裂。

具体表现：
- pipeline.fail.implement 在 learnings 中出现 6 次，但没有自动生成 proposal 来改进 implement 阶段
- verify_pass_rate 只有 30-40%，但没有自动触发"改进 verifier"的提案
- 多个 change 因 BUDGET_EXCEEDED 失败，但没有自动调整 max_tokens 的提案
- diagnosis.md 生成了但内容为空，没有 proposal 来修复 diagnoser

## Expected Behavior

### 新增文件: `zsiga/intake/reflector.py`

```python
class Reflector:
    """自主反思引擎 — 从内部信号生成自我改进 proposal。"""
    
    def scan_signals(self, base_path: str) -> list[Signal]:
        """扫描三类内部信号源，返回需要关注的信号列表。"""
        
    def should_propose(self, signal: Signal, base_path: str) -> bool:
        """检查是否应该生成 proposal：去重（24h 内同 pattern_key 不重复）+ 限频（每天最多 3 个）。"""
        
    def generate_proposal(self, signal: Signal, base_path: str) -> str:
        """从信号模板生成 proposal.md 内容。纯规则，不调用 LLM。"""
        
    def run(self, base_path: str) -> int:
        """主入口：scan → filter → generate → 写入。返回生成的 proposal 数量。"""
```

### 信号源定义

#### Signal Type 1: 重复失败模式（来自 pattern_miner）
- 读取 memory/learnings.jsonl，用 mine_patterns(min_occurrences=3) 获取 patterns
- 过滤 severity="high" 的 patterns
- 对每个 high-severity pattern，检查 openspec/changes/ 中是否已有对应的 proposal（文件名包含 pattern_key 的核心词）
- 如果没有 → 生成 Signal(type="recurring_failure", pattern_key=..., count=..., examples=[最近3条 takeaway])

#### Signal Type 2: 指标退化（来自 metrics/collector）
- 调用 compute_stats() 获取当前统计
- 检查以下退化条件：
  - success_rate_pct < 70 → 生成 Signal(type="metric_degradation", metric="success_rate", value=...)
  - verify_pass_rate_pct < 50 → 生成 Signal(type="metric_degradation", metric="verify_pass_rate", value=...)
  - 最近 10 个 change 中 BUDGET_EXCEEDED 出现 >= 3 次 → 生成 Signal(type="metric_degradation", metric="budget_exceed_rate", value=...)
- 与上次 snapshot 对比（读取 data/stats_snapshot.json），如果指标下降 >10% → 提升 Signal 优先级

#### Signal Type 3: 回滚诊断（来自 diagnosis.md）
- 读取 metrics/changes.jsonl 中最近 10 个 outcome=reverted 的 change
- 对每个 reverted change，检查 openspec/changes/{name}/diagnosis.md 是否存在且非空
- 如果存在，提取 FixPlan.root_cause
- 相同 root_cause 出现 >= 2 次 → 生成 Signal(type="recurring_root_cause", root_cause=..., occurrences=...)

### Proposal 模板

生成的 proposal.md 使用以下模板（纯字符串拼接，不调 LLM）：

```markdown
# Proposal: {title}

## Summary
{signal_type 对应的摘要描述}

## Motivation
自动检测到以下内部信号：

{根据 signal_type 填充具体数据}

## Expected Behavior
{根据 signal_type 给出通用改进方向}

## Constraints
- 这是 zsiga 自主生成的 proposal
- 只修改 zsiga 自身代码（project=zsiga）
- 实现后运行 pytest + ruff
```

### 限频与去重

**去重**：在 data/reflector_history.jsonl 中记录每次生成的 proposal（timestamp + signal_type + pattern_key）。相同 signal_type + pattern_key 在 24 小时内不重复生成。

**限频**：每天最多生成 3 个自我改进 proposal。reflector_history.jsonl 中过去 24h 的记录 >= 3 条时不生成。

**不干扰外部 proposal**：如果 openspec/changes/ 中已有外部写入的 proposal（非 auto- 开头），优先处理外部 proposal，Reflector 不抢占。

### 集成到 daemon.py

在 daemon_loop 中，`run_cycle()` 之后、`generate_dashboard()` 之前，插入：

```python
# Self-reflection: generate proposals from internal signals (only during idle)
if idle_cycles >= 3 and processed_count == 0:
    try:
        from .intake.reflector import Reflector
        reflector = Reflector()
        n = reflector.run(base_path=str(Path(__file__).resolve().parent.parent))
        if n > 0:
            print(f"  🪞 Reflector generated {n} proposal(s)")
            # Immediately re-cycle to pick up new proposals
            continue
    except Exception as e:
        print(f"  ⚠ Reflector error: {e}")
```

触发条件：`idle_cycles >= 3` 且当前 cycle 没处理任何 change。避免在忙碌时浪费资源。

### 文件命名

自动生成的 proposal 目录命名格式：`auto-{signal_type}-{sanitized_key}-{YYYYMMDD}`
- 例如：`auto-recurring_failure-pipeline-fail-implement-20260520`
- 以 `auto-` 前缀区分外部 proposal

## Constraints
- 新增文件：zsiga/intake/reflector.py
- 修改文件：zsiga/daemon.py（在 daemon_loop 中调用 Reflector）
- Reflector 不调用 LLM，纯规则驱动（pattern_miner 已有现成逻辑）
- 不修改 pattern_miner.py、collector.py、learn.py 等现有模块
- reflector_history.jsonl 存放在 data/ 目录
- 实现后运行 pytest + ruff 确保通过
- 测试：tests/test_reflector.py 覆盖 scan_signals、should_propose、generate_proposal、去重、限频
