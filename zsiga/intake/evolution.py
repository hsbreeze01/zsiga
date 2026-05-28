"""EvolutionEngine: 事实摄入 → 反思校验 → 学习更新 → 沉淀固化

Self-evolution loop that runs during designated evolution windows.
Unlike Reflector (passive, failure-only), EvolutionEngine actively explores
the codebase, learns from outcomes, and generates high-quality proposals
with Technical Design and BAC.

Learning closed loop:
  ┌──────┐   ┌──────┐   ┌──────┐   ┌─────┐
  │事实  │ → │反思  │ → │学习  │ → │沉淀 │
  │摄入  │   │校验  │   │更新  │   │固化 │
  └──────┘   └──────┘   └──────┘   └─────┘

Phase 1 (事实摄入): collect facts — recent outcomes, learnings, code structure
Phase 2 (反思校验): validate — what worked, what failed, what patterns emerge
Phase 3 (学习更新): update — record new lessons, adjust strategy
Phase 4 (沉淀固化): solidify — generate next proposal from accumulated knowledge
"""

import ast
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from ..memory.learn import record_lesson, search_learnings
from ..memory.pattern_miner import mine_patterns
from .langfuse_reader import get_metrics as get_langfuse_metrics

logger = logging.getLogger(__name__)

_EVO_PREFIX = "evo-"
_BACKDOOR_FILE = ".evolution-pause"
# Adaptive token budget: computed from historical per-phase usage
# rather than a static hard cap. See _compute_token_budget_cap().
# During testing/verification phase, use elevated limits to avoid
# blocking capability development.
_TOKEN_BUDGET_BASE_CAP = 80_000_000  # 80M floor (testing phase)
_TOKEN_BUDGET_SAFETY_MARGIN = 1.5  # allow 50% above baseline before triggering


@dataclass
class EvolutionConfig:
    enabled: bool = True
    window_start_hour: int = 22       # 22:00 local time
    window_end_hour: int = 10         # 10:00 next day
    max_proposals_per_window: int = 12
    min_cycle_gap_minutes: int = 15   # gap between evo proposals
    backdoor_file: str = ".evolution-pause"  # touch this file to pause evolution


@dataclass
class EvolutionState:
    proposals_generated: int = 0
    last_proposal_at: str = ""
    window_start_at: str = ""
    total_cycles: int = 0


class EvolutionEngine:

    def __init__(self, base_path: str | Path, config: EvolutionConfig | None = None):
        self.base = Path(base_path)
        self.config = config or EvolutionConfig()
        self._state_path = self.base / "data" / "evolution_state.json"

    def _compute_token_budget_cap(self, langfuse_metrics) -> int:
        """Compute adaptive 24h token budget cap from historical usage.

        Derives cap from budget_analyzer's per-phase data (same source as
        orchestrator's _adaptive_timeout), then applies a safety margin.
        Falls back to _TOKEN_BUDGET_BASE_CAP if budget_analyzer is unavailable.
        """
        try:
            from ..metrics.budget_analyzer import compute_budget_analysis, get_phase_budget_from_config
            from ..config import load_config
            db_path = str(self.base / "data" / "zsiga.db")
            cfg = load_config(self.base / "zsiga.yaml")
            config_budgets = get_phase_budget_from_config(cfg)
            analysis = compute_budget_analysis(db_path, config_budgets)
            if analysis.get("error"):
                return _TOKEN_BUDGET_BASE_CAP

            per_phase_avg_tokens = 0
            phase_count = 0
            for phase_name, phase_info in analysis.get("phases", {}).items():
                tokens = phase_info.get("tokens", {}).get("avg_total", 0)
                sample = phase_info.get("sample_count", 0)
                if sample > 0 and tokens > 0:
                    per_phase_avg_tokens += tokens
                    phase_count += 1

            if phase_count == 0:
                return _TOKEN_BUDGET_BASE_CAP

            # Estimate: avg tokens per complete pipeline run × estimated daily runs
            # daily_runs ≈ 24h / avg_cycle_duration (rough estimate from sample count)
            total_records = analysis.get("total_records", 0)
            daily_runs = max(total_records / 7, 3) if total_records > 0 else 3
            baseline = int(per_phase_avg_tokens * phase_count * daily_runs)
            cap = max(int(baseline * _TOKEN_BUDGET_SAFETY_MARGIN), _TOKEN_BUDGET_BASE_CAP)
            return cap
        except Exception:
            return _TOKEN_BUDGET_BASE_CAP

    # ------------------------------------------------------------------
    # Window control
    # ------------------------------------------------------------------

    def is_in_window(self) -> bool:
        if not self.config.enabled:
            return False
        now = datetime.now()
        h = now.hour
        start = self.config.window_start_hour
        end = self.config.window_end_hour
        if start > end:
            return h >= start or h < end
        return start <= h < end

    def is_paused(self) -> bool:
        return (self.base / _BACKDOOR_FILE).exists()

    def should_evolve(self) -> bool:
        if not self.is_in_window():
            return False
        if self.is_paused():
            logger.info("Evolution paused (backdoor file present)")
            return False
        try:
            from ..config import load_runtime_state
            rs = load_runtime_state()
            if rs.get("active_target", "zsiga") != "zsiga":
                logger.info("Evolution paused: non-zsiga target active (%s)", rs.get("active_target"))
                return False
        except Exception:
            pass
        recent_rejections = self._collect_recent_evo_rejections()
        if len(recent_rejections) >= 5:
            logger.warning(
                "Evolution paused: %d recent evo proposals were rejected/pushed back",
                len(recent_rejections),
            )
            return False
        state = self._load_state()
        window_start = self._current_window_start().isoformat()
        if state.window_start_at != window_start:
            state.proposals_generated = 0
            state.window_start_at = window_start
            self._save_state(state)
        if state.proposals_generated >= self.config.max_proposals_per_window:
            return False
        if state.last_proposal_at:
            last = datetime.fromisoformat(state.last_proposal_at)
            gap = datetime.now() - last
            if gap < timedelta(minutes=self.config.min_cycle_gap_minutes):
                return False
        return True

    # ------------------------------------------------------------------
    # Main evolution loop: 事实摄入 → 反思校验 → 学习更新 → 沉淀固化
    # ------------------------------------------------------------------

    def run_evolution_cycle(self) -> str | None:
        """Execute one full evolution cycle. Returns proposal dir or None."""
        facts = self._phase1_intake()
        if not facts.get("actionable"):
            logger.info("Evolution: no actionable findings this cycle")
            return None

        insights = self._phase2_reflect(facts)
        self._phase3_learn(facts, insights)
        proposal_path = self._phase4_solidify(facts, insights)

        if proposal_path:
            state = self._load_state()
            state.proposals_generated += 1
            state.last_proposal_at = datetime.now().isoformat()
            state.total_cycles += 1
            self._save_state(state)
            logger.info(f"🧬 Evolution generated: {proposal_path}")

        return proposal_path

    # ------------------------------------------------------------------
    # Phase 1: 事实摄入 — collect raw facts
    # ------------------------------------------------------------------

    def _phase1_intake(self) -> dict:
        recent_evo_rejections = self._collect_recent_evo_rejections()
        langfuse_metrics = get_langfuse_metrics(limit=10, hours=24)

        facts: dict = {
            "recent_outcomes": self._collect_recent_outcomes(),
            "patterns": mine_patterns(min_occurrences=2, learnings_path=self.base / "memory" / "learnings.jsonl"),
            "code_structure": self._scan_code_structure(),
            "learnings_count": self._count_learnings(),
            "recent_failures": search_learnings(["fail", "revert", "error", "critical"], pattern_key=None)[:10],
            "recent_successes": search_learnings(["success", "pass", "deliver"], pattern_key=None)[:5],
            "recent_evo_rejections": recent_evo_rejections,
            "langfuse_metrics": langfuse_metrics,
            "actionable": False,
        }

        excluded_patterns = set()
        for rej in recent_evo_rejections:
            pattern = rej.get("pattern_key", "")
            if pattern:
                excluded_patterns.add(pattern)

        high_patterns = [p for p in facts["patterns"]
                        if p.severity == "high"
                        and p.key not in excluded_patterns
                        and not p.key.startswith("evolution.")]

        findings = []

        if high_patterns:
            findings.append(f"recurring_failure:{high_patterns[0].key}")

        # Check for recent failures with no fix attempt
        recent_fails = [f for f in facts["recent_failures"]
                       if self._is_recent(f.get("ts", ""), hours=24)]
        if len(recent_fails) >= 2:
            findings.append(f"unresolved_failures:{len(recent_fails)}")

        # Check for code structure gaps
        structure = facts["code_structure"]
        if structure.get("modules_without_tests"):
            findings.append(f"missing_tests:{len(structure['modules_without_tests'])}")

        # Check for stale code / tech debt signals
        if structure.get("large_files"):
            findings.append(f"large_files:{len(structure['large_files'])}")

        # Check for learning gaps — things we keep failing at but haven't extracted rules
        no_rule_lessons = [f for f in facts["recent_failures"]
                          if not f.get("rule") and not f.get("why")]
        if len(no_rule_lessons) >= 3:
            findings.append("learning_gaps:need_better_failure_analysis")

        # Proactive exploration: pick a random untested module
        if structure.get("modules_without_tests"):
            import random
            untested = structure["modules_without_tests"]
            if untested:
                target = random.choice(untested[:5])
                findings.append(f"explore_untested:{target}")

        # Proactive: look at what succeeded and find similar patterns to apply
        if facts["recent_successes"]:
            findings.append("reinforce_success:analyze_and_extend")

        # Langfuse-driven findings: token cost anomalies and trends
        lm = langfuse_metrics
        if lm.trace_count >= 3:
            if lm.costliest_phase and lm.costliest_phase_tokens > 0:
                findings.append(f"high_cost_phase:{lm.costliest_phase}:{lm.costliest_phase_tokens}")
            if lm.token_trend > 0.5:
                findings.append(f"token_cost_rising:{lm.token_trend:.1%}")
            if lm.avg_tokens_per_trace > 50000:
                findings.append(f"avg_trace_expensive:{int(lm.avg_tokens_per_trace)}")

        # Token budget hard cap: if 24h usage exceeds cap, force cost optimization
        budget_cap = self._compute_token_budget_cap(lm)
        if lm.total_tokens >= budget_cap:
            findings.append(
                f"token_budget_exceeded:{lm.total_tokens}:{budget_cap}"
            )

        facts["findings"] = findings
        facts["actionable"] = len(findings) > 0
        return facts

    # ------------------------------------------------------------------
    # Phase 2: 反思校验 — validate and prioritize
    # ------------------------------------------------------------------

    def _phase2_reflect(self, facts: dict) -> dict:
        findings = facts.get("findings", [])
        recent_rejections = facts.get("recent_evo_rejections", [])
        insights: dict = {
            "priority_finding": None,
            "proposal_type": "improvement",
            "scope": "zsiga",
            "confidence": "low",
        }

        recent_fix_rejections = sum(
            1 for r in recent_rejections
            if "evo-fix-" in r.get("dir", "")
        )
        skip_fix_types = recent_fix_rejections >= 3 or len(recent_rejections) >= 5

        # Token budget hard cap override: only allow cost optimization
        budget_exceeded = any(
            f.startswith("token_budget_exceeded:") for f in findings
        )
        if budget_exceeded:
            for finding in findings:
                if finding.startswith("token_budget_exceeded:"):
                    parts = finding.split(":")
                    used = int(parts[1]) if len(parts) > 1 else 0
                    cap = int(parts[2]) if len(parts) > 2 else 0
                    insights["priority_finding"] = {
                        "type": "enforce_budget_cap",
                        "used": used,
                        "cap": cap,
                    }
                    insights["proposal_type"] = "improvement"
                    insights["confidence"] = "high"
                    insights["scope"] = "cost_only"
                    break

            for finding in findings:
                if finding.startswith("high_cost_phase:"):
                    parts = finding.split(":")
                    pf = insights["priority_finding"]
                    if pf:
                        pf["costliest_phase"] = parts[1] if len(parts) > 1 else ""
                        pf["phase_tokens"] = int(parts[2]) if len(parts) > 2 else 0
                    break

            return insights

        if not skip_fix_types:
            for finding in findings:
                if finding.startswith("recurring_failure:"):
                    key = finding.split(":", 1)[1]
                    patterns = [p for p in facts["patterns"] if p.key == key]
                    insights["priority_finding"] = {
                        "type": "fix_failure",
                        "key": key,
                        "count": patterns[0].count if patterns else 0,
                        "takeaways": patterns[0].recent_takeaways if patterns else [],
                    }
                    insights["proposal_type"] = "fix"
                    insights["confidence"] = "high"
                    break

        if not insights["priority_finding"] and not skip_fix_types:
            for finding in findings:
                if finding.startswith("unresolved_failures:"):
                    count = finding.split(":")[1]
                    insights["priority_finding"] = {
                        "type": "diagnose_failures",
                        "count": int(count),
                        "failures": facts["recent_failures"][:3],
                    }
                    insights["proposal_type"] = "fix"
                    insights["confidence"] = "medium"
                    break

        if not insights["priority_finding"]:
            for finding in findings:
                if finding.startswith("explore_untested:"):
                    module = finding.split(":", 1)[1]
                    insights["priority_finding"] = {
                        "type": "explore_module",
                        "module": module,
                    }
                    insights["proposal_type"] = "improvement"
                    insights["confidence"] = "medium"
                    break

        if not insights["priority_finding"]:
            for finding in findings:
                if finding.startswith("missing_tests:"):
                    count = finding.split(":")[1]
                    structure = facts["code_structure"]
                    insights["priority_finding"] = {
                        "type": "add_tests",
                        "count": int(count),
                        "modules": structure.get("modules_without_tests", [])[:3],
                    }
                    insights["proposal_type"] = "improvement"
                    insights["confidence"] = "medium"
                    break

        if not insights["priority_finding"]:
            for finding in findings:
                if finding.startswith("reinforce_success"):
                    successes = facts.get("recent_successes", [])
                    insights["priority_finding"] = {
                        "type": "reinforce_success",
                        "successes": successes[:2],
                    }
                    insights["proposal_type"] = "improvement"
                    insights["confidence"] = "low"
                    break

        # Langfuse-driven optimization: reduce token cost of expensive phases
        if not insights["priority_finding"]:
            lm = facts.get("langfuse_metrics")
            if lm and lm.costliest_phase:
                for finding in findings:
                    if finding.startswith("high_cost_phase:"):
                        parts = finding.split(":")
                        phase = parts[1] if len(parts) > 1 else ""
                        tokens = int(parts[2]) if len(parts) > 2 else 0
                        insights["priority_finding"] = {
                            "type": "optimize_cost",
                            "phase": phase,
                            "tokens": tokens,
                            "avg_per_trace": lm.avg_tokens_per_trace,
                            "trend": lm.token_trend,
                        }
                        insights["proposal_type"] = "improvement"
                        insights["confidence"] = "medium"
                        break

        return insights

    # ------------------------------------------------------------------
    # Phase 3: 学习更新 — record learnings from this reflection
    # ------------------------------------------------------------------

    def _phase3_learn(self, facts: dict, insights: dict) -> bool:
        finding = insights.get("priority_finding")
        if not finding:
            return False

        ftype = finding.get("type", "")
        if ftype == "fix_failure":
            record_lesson(
                title=f"Evolution: identified recurring failure {finding['key']}",
                context=f"Pattern appeared {finding.get('count', 0)} times, generating fix proposal",
                takeaway=f"Auto-generating targeted fix for {finding['key']}",
                pattern_key=f"evolution.fix.{finding['key']}",
                source="evolution",
                case={"pattern_key": finding["key"], "count": finding.get("count", 0)},
                why=f"Recurring pattern {finding['key']} degrades pipeline reliability",
                rule=f"Monitor {finding['key']} after fix; if recurs within 48h, escalate to manual",
            )
        elif ftype == "add_tests":
            record_lesson(
                title=f"Evolution: found {finding.get('count', 0)} modules without tests",
                context=f"Modules: {', '.join(finding.get('modules', [])[:3])}",
                takeaway="Untested modules are latent risk; add tests proactively",
                pattern_key="evolution.test_gap",
                source="evolution",
            )
        elif ftype == "optimize_cost":
            record_lesson(
                title=f"Evolution: {finding.get('phase', '')} phase costs {finding.get('tokens', 0)} tokens",
                context=f"avg_per_trace={finding.get('avg_per_trace', 0)}, trend={finding.get('trend', 0):.1%}",
                takeaway=f"Optimize {finding.get('phase', '')} to reduce token usage",
                pattern_key=f"evolution.cost.{finding.get('phase', 'unknown')}",
                source="evolution",
            )
        elif ftype == "enforce_budget_cap":
            record_lesson(
                title=f"Token budget hard cap exceeded: {finding.get('used', 0):,} / {finding.get('cap', 0):,}",
                context="24h token usage hit hard cap, restricting to cost-only proposals",
                takeaway="Reduce token consumption before generating new feature proposals",
                pattern_key="evolution.budget_cap_hit",
                source="evolution",
            )
        return True

    # ------------------------------------------------------------------
    # Phase 4: 沉淀固化 — generate proposal from accumulated knowledge
    # ------------------------------------------------------------------

    def _phase4_solidify(self, facts: dict, insights: dict) -> str | None:
        finding = insights.get("priority_finding")
        if not finding:
            return None

        ftype = finding.get("type", "")

        if ftype == "fix_failure":
            content = self._render_fix_proposal(finding, facts)
        elif ftype == "diagnose_failures":
            content = self._render_diagnose_proposal(finding, facts)
        elif ftype == "add_tests":
            content = self._render_test_proposal(finding, facts)
        elif ftype == "explore_module":
            content = self._render_explore_proposal(finding, facts)
        elif ftype == "reinforce_success":
            content = self._render_reinforce_proposal(finding, facts)
        elif ftype == "optimize_cost":
            content = self._render_cost_proposal(finding, facts)
        elif ftype == "enforce_budget_cap":
            content = self._render_budget_cap_proposal(finding, facts)
        else:
            return None

        return self._write_proposal(content, insights.get("proposal_type", "improvement"))

    # ------------------------------------------------------------------
    # Proposal renderers — high-quality proposals with Technical Design + BAC
    # ------------------------------------------------------------------

    def _render_fix_proposal(self, finding: dict, facts: dict) -> str:
        key = finding.get("key", "unknown")
        count = finding.get("count", 0)
        takeaways = finding.get("takeaways", [])
        takeaway_lines = "\n".join(f"- {t}" for t in takeaways[:3])
        now = datetime.now().strftime("%Y%m%d-%H%M")

        # Search for related learnings to enrich the proposal
        related = search_learnings([key])[:5]
        related_ctx = ""
        if related:
            related_ctx = "\n## Related Learnings\n"
            for r in related[:3]:
                related_ctx += f"- [{r.get('ts', '')[:10]}] {r.get('takeaway', r.get('title', ''))}\n"

        return f"""# fix-{key}-{now}

## Summary
修复反复出现的 pipeline 失败模式 `{key}`（已出现 {count} 次），通过分析根因并实施确定性修复。

## Problem
模式 `{key}` 在最近运行中反复出现（{count} 次），导致 pipeline 可靠性下降。

近期案例：
{takeaway_lines if takeaway_lines else "- 暂无具体案例"}
{related_ctx}

## Technical Design
1. 在 `zsiga/` 中定位触发 `{key}` 的代码路径
2. 分析每次失败的上下文，提取共性根因
3. 实现确定性修复（非 workaround）
4. 添加防御性检查或 guard 防止复发

### Target Files
- 需要在实施阶段通过代码分析确定

## Acceptance Criteria
- [BAC-01] 修复后 `{key}` 模式不再出现于连续 3 次 pipeline 运行
- [BAC-02] 所有现有测试仍然通过
- [BAC-03] 新增至少 1 个针对该失败模式的防御性测试

## Scope
- In scope: 修复 `{key}` 根因，添加防御性检查
- Out of scope: 不重构无关代码

## Risk
- Impact: Medium — 修改 pipeline 相关代码
- Reversibility: git revert 即可
- Blast radius: 失败模式对应的模块

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成
- project=zsiga
"""

    def _render_diagnose_proposal(self, finding: dict, facts: dict) -> str:
        count = finding.get("count", 0)
        failures = finding.get("failures", [])
        failure_lines = "\n".join(
            f"- {f.get('title', 'unknown')} ({f.get('ts', '')[:16]})"
            for f in failures
        )

        return f"""# diagnose-recent-failures

## Summary
诊断最近 {count} 次未解决的 pipeline 失败，分析根因模式并实施针对性修复。

## Problem
最近 24 小时内有 {count} 次失败未被修复：

{failure_lines}

## Technical Design
1. 分析每次失败的 diagnosis.md 和 verify.md
2. 提取共性根因（如果存在）
3. 对可修复的问题实施针对性修复
4. 对不可修复的问题记录 learning 并标记 capability boundary

## Acceptance Criteria
- [BAC-01] 至少分析 2 个失败案例的根因
- [BAC-02] 对可修复的根因实施修复
- [BAC-03] 修复后相关测试通过

## Scope
- In scope: 分析失败、实施修复、记录 learnings
- Out of scope: 不改动无关模块

## Risk
- Impact: Low-Medium — 取决于失败类型
- Reversibility: git revert

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成
- project=zsiga
"""

    def _render_test_proposal(self, finding: dict, facts: dict) -> str:
        modules = finding.get("modules", [])
        count = finding.get("count", 0)

        target_module = modules[0] if modules else "unknown"
        target_basename = os.path.basename(target_module).replace(".py", "")

        module_scans = facts.get("code_structure", {}).get("module_scans", {})
        scan = module_scans.get(target_basename, self._pre_scan_module(target_module))

        symbols = scan.get("symbols", [])
        func_list = [s for s in symbols if s.get("kind") == "function"]
        total_lines = scan.get("total_lines", 0)
        lint_issues = scan.get("lint_issues", [])
        complexity = scan.get("complexity", [])

        avg_cc = sum(c.get("cc", 0) for c in complexity) / len(complexity) if complexity else 0

        func_lines = "\n".join(
            f"- `{s['name']}({', '.join(s.get('args', []))})` L{s['line']}-L{s['end_line']} (~{s['lines']}L)"
            for s in func_list[:10]
        ) if func_list else "- (无法提取函数列表)"

        target_funcs = [f["name"] for f in func_list[:3]] if func_list else []
        bac_test_names = ", ".join(f"`test_{n}`" for n in target_funcs)
        min_tests = min(len(func_list), 3) if func_list else 1

        module_lines = "\n".join(f"- `{m}`" for m in modules)

        return f"""# add-tests-for-{target_basename}

## Summary
为 {count} 个缺少测试的模块编写单元测试，优先覆盖 `{target_module}` ({total_lines} 行, {len(func_list)} 函数, 平均 CC {avg_cc:.1f})。

## Problem
以下模块缺少测试覆盖，是潜在的风险点：

{module_lines}

### `{target_basename}` 静态分析
- 总行数: {total_lines}, 函数数: {len(func_list)}, lint 问题: {len(lint_issues)}
- 函数列表:
{func_lines}

## Technical Design
1. 为 `{target_module}` 的公开函数编写单元测试
2. 优先覆盖: {', '.join(f'`{f["name"]}`' for f in func_list[:3]) if func_list else '(待分析)'}
3. 使用 mock 隔离外部依赖（LLM 调用、文件 I/O、subprocess）
4. 确保每个测试可独立运行

### Target Files
- `tests/test_{target_basename}.py` (新建)
- `{target_module}` (仅读取分析，不修改)

## Acceptance Criteria
- [BAC-01] 文件 `tests/test_{target_basename}.py` 存在
- [BAC-02] `tests/test_{target_basename}.py` 中存在 {bac_test_names}
- [BAC-03] `tests/test_{target_basename}.py` 中存在至少 {min_tests} 个 `def test_` 函数
- [BAC-04] `python -m pytest tests/test_{target_basename}.py` 退出码 0

## Scope
- In scope: 为 1 个模块编写测试
- Out of scope: 不修改生产代码

## Risk
- Impact: None — 只添加测试
- Reversibility: 删除测试文件

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成（含静态分析数据）
- project=zsiga
"""

    def _render_explore_proposal(self, finding: dict, facts: dict) -> str:
        module = finding.get("module", "unknown")
        module_name = os.path.basename(module).replace(".py", "")

        module_scans = facts.get("code_structure", {}).get("module_scans", {})
        scan = module_scans.get(module_name, self._pre_scan_module(module))

        symbols = scan.get("symbols", [])
        lint_issues = scan.get("lint_issues", [])
        complexity = scan.get("complexity", [])
        total_lines = scan.get("total_lines", 0)

        func_list = [s for s in symbols if s.get("kind") == "function"]
        class_list = [s for s in symbols if s.get("kind") == "class"]
        high_cc = [c for c in complexity if c.get("cc", 0) > 10]

        func_lines = "\n".join(
            f"- `{s['name']}({', '.join(s.get('args', []))})` L{s['line']}-L{s['end_line']} (~{s['lines']}L)"
            for s in func_list[:10]
        ) if func_list else "- (无法提取函数列表)"

        class_lines = "\n".join(
            f"- `{s['name']}` L{s['line']}-L{s['end_line']} methods={s.get('methods', [])}"
            for s in class_list[:5]
        ) if class_list else ""

        lint_lines = "\n".join(
            f"- L{iss['line']} [{iss['code']}]: {iss['message']}"
            for iss in lint_issues[:5]
        ) if lint_issues else "- 无 lint 问题"

        cc_lines = "\n".join(
            f"- `{c['name']}` L{c['line']} CC={c['cc']} ({c['length']}L)"
            for c in high_cc
        ) if high_cc else "- 无高复杂度函数 (CC>10)"

        avg_cc = sum(c.get("cc", 0) for c in complexity) / len(complexity) if complexity else 0

        target_funcs_for_bac = [f["name"] for f in func_list[:3]] if func_list else ["(待分析)"]
        bac_test_names = ", ".join(f"`test_{n}`" for n in target_funcs_for_bac)

        class_section = f"""
### 类结构
{class_lines}
""" if class_lines else ""

        return f"""# add-tests-{module_name}

## Summary
为无测试模块 `{module}` ({total_lines} 行, {len(func_list)} 函数{f', {len(class_list)} 类' if class_list else ''}) 添加单元测试覆盖。

## Problem
模块 `{module}` 缺少测试文件 `tests/test_{module_name}.py`，是潜在风险点。

### 当前状态（静态分析数据）
- 总行数: {total_lines}
- 函数数: {len(func_list)}，类数: {len(class_list)}
- ruff lint 问题: {len(lint_issues)}
- 圈复杂度: 平均 {avg_cc:.1f}，高 CC(>10) 函数 {len(high_cc)} 个

### 函数列表
{func_lines}
{class_section}
### Lint 问题
{lint_lines}

### 高复杂度函数 (CC > 10)
{cc_lines}

## Technical Design
1. 为 `{module}` 中的公开函数编写单元测试
2. 优先覆盖高复杂度函数: {', '.join(f'`{c["name"]}`' for c in high_cc[:3]) if high_cc else '(无高 CC 函数)'}
3. 使用 mock 隔离外部依赖（LLM 调用、文件 I/O、subprocess）
4. 确保每个测试可独立运行，不依赖运行时环境

### Target Files
- `tests/test_{module_name}.py` (新建)
- `{module}` (仅读取分析，不修改)

## Acceptance Criteria
- [BAC-01] 文件 `tests/test_{module_name}.py` 存在
- [BAC-02] `tests/test_{module_name}.py` 中存在 {bac_test_names}
- [BAC-03] `tests/test_{module_name}.py` 中存在至少 {min(len(func_list), 3)} 个 `def test_` 函数
- [BAC-04] `python -m pytest tests/test_{module_name}.py` 退出码 0

## Scope
- In scope: 为 `{module}` 编写测试，覆盖公开函数
- Out of scope: 不修改 `{module}` 源码

## Risk
- Impact: None — 只添加测试
- Reversibility: 删除测试文件

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成（含静态分析数据）
- project=zsiga
"""

    def _render_reinforce_proposal(self, finding: dict, facts: dict) -> str:
        successes = finding.get("successes", [])
        success_lines = "\n".join(
            f"- {s.get('title', 'unknown')} ({s.get('ts', '')[:16]})"
            for s in successes
        )

        return f"""# reinforce-success-patterns

## Summary
分析最近成功的 pipeline 运行，提取成功模式并应用到其他模块。

## Problem
最近的失败表明部分领域需要改进。通过分析成功案例，找到可复制的模式。

近期成功案例：
{success_lines if success_lines else "- 暂无"}

## Technical Design
1. 分析成功案例的关键因素（scope 大小、spec 质量、测试覆盖）
2. 识别与失败案例的差异点
3. 将成功模式固化为 learnings 或代码改进
4. 应用到最需要改进的模块

## Acceptance Criteria
- [BAC-01] 分析至少 1 个成功案例和 1 个失败案例
- [BAC-02] 提取至少 1 条可复制的 success rule
- [BAC-03] 将 rule 固化到 learnings.jsonl

## Scope
- In scope: 分析成功/失败模式，记录 learnings
- Out of scope: 不直接修改生产代码（除非发现明显的改进机会）

## Risk
- Impact: None — 主要为分析和记录
- Reversibility: N/A

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成
- project=zsiga
"""

    def _render_cost_proposal(self, finding: dict, facts: dict) -> str:
        phase = finding.get("phase", "unknown")
        tokens = finding.get("tokens", 0)
        avg = finding.get("avg_per_trace", 0)
        trend = finding.get("trend", 0)
        trend_desc = "上升" if trend > 0 else "下降"
        lm = facts.get("langfuse_metrics")

        phase_breakdown = ""
        if lm and lm.phase_avg_tokens:
            phase_lines = [f"  - {p}: {t:.0f} tokens/trace" for p, t in lm.phase_avg_tokens.items()]
            phase_breakdown = "\n".join(phase_lines)

        return f"""# optimize-{phase}-token-cost

## Summary
优化 `{phase}` phase 的 token 消耗（当前 {tokens} tokens / 24h），降低 pipeline 运行成本。

## Problem
Langfuse 数据显示 `{phase}` 是 token 消耗最高的阶段：
- 24h 累计: {tokens} tokens
- 平均每 trace: {avg:.0f} tokens
- 趋势: {trend_desc} ({abs(trend):.1%})

各 phase token 分布：
{phase_breakdown if phase_breakdown else "- 暂无详细数据"}

## Technical Design
1. 分析 `{phase}` phase 的 agent prompt，识别冗余上下文
2. 检查 compaction 策略是否生效（减少历史对话的 token 浪费）
3. 评估 sub-agent 调用是否可以合并（减少重复上下文注入）
4. 对 prompt 进行精简，保留核心指令，移除重复约束

### Target Files
- `zsiga/agent/roles.py` (prompt 定义)
- `zsiga/agent/loop.py` (context 管理)
- `zsiga/pipeline/orchestrator.py` (phase 编排)

## Acceptance Criteria
- [BAC-01] 分析 `{phase}` phase 的 token 使用分布
- [BAC-02] 实施至少 1 项 token 优化（prompt 精简/compaction 改进）
- [BAC-03] 优化后同类 proposal 的 `{phase}` phase token 消耗降低 >= 15%

## Scope
- In scope: 分析并优化 `{phase}` phase 的 token 消耗
- Out of scope: 不修改其他 phase 的逻辑

## Risk
- Impact: Low — prompt 和上下文管理优化
- Reversibility: git revert

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成（基于 Langfuse 可观测数据）
- project=zsiga
"""

    def _render_budget_cap_proposal(self, finding: dict, facts: dict) -> str:
        used = finding.get("used", 0)
        cap = finding.get("cap", 0)
        pct = used / cap * 100 if cap else 0
        costliest = finding.get("costliest_phase", "")
        phase_tokens = finding.get("phase_tokens", 0)
        phase_section = ""
        if costliest:
            phase_section = f"\n消耗最高阶段: `{costliest}` ({phase_tokens:,} tokens)"

        return f"""# token-budget-cap-enforcement

## Summary
24h token 消耗已达自适应 cap ({used:,} / {cap:,} = {pct:.1f}%)，必须降低 token 消耗才能继续。

## Problem
Langfuse 24h token 使用量超过自适应 budget cap：
{phase_section}
- 当前用量: {used:,} tokens ({pct:.1f}% of cap)
- 自适应 cap 基于 budget_analyzer 历史数据 × {_TOKEN_BUDGET_SAFETY_MARGIN}x 安全系数计算
- 除非显著降低 token 消耗，否则新 proposal 会继续推高成本

## Technical Design
1. 审查 agent prompt，移除冗余上下文（重复的约束、过长的 system prompt）
2. 精简 IMPLEMENT/ENRICH 阶段的 context 注入，只保留必要信息
3. 减少 sub-agent 调用次数（合并相似探索任务）
4. 优化 compaction 策略（更积极的对话历史压缩）
5. 协同 budget_analyzer 的 phase-level 自适应：在整体超 cap 时，主动收紧各 phase budget

### Target Files
- `zsiga/agent/roles.py`
- `zsiga/agent/loop.py`
- `zsiga/pipeline/enricher.py`
- `zsiga/pipeline/implementer.py`

## Acceptance Criteria
- [BAC-01] 审计并精简至少 2 个 agent 的 system prompt
- [BAC-02] 优化后 24h token 消耗降低 >= 20%
- [BAC-03] 不影响 pipeline 成功率（不低于当前 67%）

## Scope
- In scope: 降低 token 消耗（prompt 精简、context 压缩、phase budget 收紧）
- Out of scope: 不修改 pipeline 逻辑和 L0 checks

## Risk
- Impact: Medium — prompt 修改可能影响生成质量
- Reversibility: git revert

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成（adaptive token budget cap 触发）
- 自适应 cap 基于 budget_analyzer 历史数据，与 phase-level timeout/turns 自适应联动
- project=zsiga
"""

    # ------------------------------------------------------------------
    # Proposal writing
    # ------------------------------------------------------------------

    def _write_proposal(self, content: str, proposal_type: str) -> str | None:
        preflight_error = self._proposal_preflight_error(content)
        if preflight_error:
            logger.warning("Evolution proposal blocked by preflight: %s", preflight_error)
            record_lesson(
                title="Evolution proposal blocked by preflight",
                context=preflight_error,
                takeaway="Generated proposals must have concrete BACs and no placeholders before entering OpenSpec",
                pattern_key="evolution.proposal_preflight",
                source="evolution",
            )
            return None

        changes_dir = self.base / "openspec" / "changes"
        changes_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_type = re.sub(r"[^a-z0-9]", "-", proposal_type.lower())
        dir_name = f"{_EVO_PREFIX}{safe_type}-{timestamp}"

        proposal_dir = changes_dir / dir_name
        counter = 2
        while proposal_dir.exists():
            dir_name = f"{_EVO_PREFIX}{safe_type}-{timestamp}-{counter}"
            proposal_dir = changes_dir / dir_name
            counter += 1

        proposal_dir.mkdir(parents=True, exist_ok=True)
        (proposal_dir / "proposal.md").write_text(content, encoding="utf-8")

        return str(proposal_dir)

    # ------------------------------------------------------------------
    # Fact collectors
    # ------------------------------------------------------------------

    def _collect_recent_outcomes(self) -> list[dict]:
        try:
            from ..metrics.db import load_all_changes
            changes = load_all_changes()
            recent = changes[-10:] if changes else []
            return [
                {
                    "name": c.get("change_name", ""),
                    "outcome": c.get("outcome", ""),
                    "ts": c.get("started_at", ""),
                }
                for c in recent
            ]
        except Exception:
            return []

    def _collect_recent_evo_rejections(self) -> list[dict]:
        """Scan evo- proposals for REJECT verdicts from Steward.

        Priority order: pending changes first, then archive, newest first.
        """
        changes_dir = self.base / "openspec" / "changes"

        pending_dirs: list[Path] = []
        if changes_dir.exists():
            for entry in sorted(changes_dir.iterdir(), key=lambda p: p.name, reverse=True):
                if entry.is_dir() and entry.name.startswith("evo-"):
                    pending_dirs.append(entry)

        archive_dirs: list[Path] = []
        archive_dir = changes_dir / "archive"
        if archive_dir.exists():
            for sub_dir in archive_dir.iterdir():
                if sub_dir.is_dir():
                    for entry in sub_dir.iterdir():
                        if entry.is_dir() and entry.name.startswith("evo-"):
                            archive_dirs.append(entry)
            archive_dirs.sort(key=lambda p: p.name, reverse=True)

        rejections: list[dict] = []
        scanned = 0
        for evo_dir in pending_dirs + archive_dirs:
            if scanned >= 20:
                break
            scanned += 1

            has_reject = False
            for review_file in evo_dir.glob("steward-review*.md"):
                try:
                    content = review_file.read_text(encoding="utf-8")
                    verdict_text = content.upper()
                    if "REJECT" in verdict_text or "PUSHBACK" in verdict_text:
                        has_reject = True
                        break
                except OSError:
                    pass

            if has_reject:
                proposal_path = evo_dir / "proposal.md"
                pattern_key = ""
                try:
                    proposal_text = proposal_path.read_text(encoding="utf-8")
                    m = re.search(r"失败模式\s*`(\S+)`", proposal_text)
                    if m:
                        pattern_key = m.group(1)
                except OSError:
                    pass

                rejections.append({
                    "dir": evo_dir.name,
                    "pattern_key": pattern_key,
                })

        return rejections

    def _scan_code_structure(self) -> dict:
        zsiga_dir = self.base / "zsiga"
        if not zsiga_dir.exists():
            return {}

        py_files: list[str] = []
        for root, _dirs, files in os.walk(zsiga_dir):
            for f in files:
                if f.endswith(".py") and not f.startswith("__"):
                    rel = os.path.relpath(os.path.join(root, f), self.base)
                    py_files.append(rel)

        tests_dir = self.base / "tests"
        test_files: set[str] = set()
        if tests_dir.exists():
            for f in os.listdir(tests_dir):
                if f.startswith("test_") and f.endswith(".py"):
                    test_module = f.replace("test_", "").replace(".py", "")
                    test_files.add(test_module)

        modules_without_tests: list[str] = []
        large_files: list[str] = []
        module_scans: dict[str, dict] = {}

        for pf in py_files:
            basename = os.path.basename(pf).replace(".py", "")
            if basename not in test_files and basename != "__init__":
                modules_without_tests.append(pf)
                scan = self._pre_scan_module(pf)
                if scan["symbols"] or scan["lint_issues"] or scan["complexity"]:
                    module_scans[basename] = scan

            full_path = self.base / pf
            try:
                size = os.path.getsize(full_path)
                if size > 10000:
                    large_files.append(f"{pf} ({size // 1024}KB)")
            except OSError:
                pass

        return {
            "py_files_count": len(py_files),
            "test_files_count": len(test_files),
            "modules_without_tests": modules_without_tests,
            "large_files": large_files,
            "module_scans": module_scans,
        }

    # ------------------------------------------------------------------
    # Module static analysis: ast + ruff + lizard
    # ------------------------------------------------------------------

    def _pre_scan_module(self, rel_path: str) -> dict:
        """Run deterministic static analysis on a single module.

        Uses stdlib ast for symbol extraction, ruff for lint issues,
        and lizard (if available) for cyclomatic complexity.

        Returns a dict with:
          - symbols: list of {name, kind, line, end_line, lines, args}
          - lint_issues: list of {code, message, line}
          - complexity: list of {name, line, cc}  (empty if lizard unavailable)
          - total_lines: int
        """
        full_path = self.base / rel_path
        if not full_path.exists():
            return {"symbols": [], "lint_issues": [], "complexity": [], "total_lines": 0}

        try:
            source = full_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return {"symbols": [], "lint_issues": [], "complexity": [], "total_lines": 0}

        total_lines = source.count("\n") + 1

        # --- ast: symbol extraction ---
        symbols: list[dict] = []
        try:
            tree = ast.parse(source)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    end = node.end_lineno or node.lineno
                    args = [a.arg for a in node.args.args if a.arg != "self"]
                    symbols.append({
                        "name": node.name,
                        "kind": "function",
                        "line": node.lineno,
                        "end_line": end,
                        "lines": end - node.lineno + 1,
                        "args": args,
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = [
                        n.name for n in node.body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]
                    symbols.append({
                        "name": node.name,
                        "kind": "class",
                        "line": node.lineno,
                        "end_line": node.end_lineno or node.lineno,
                        "lines": (node.end_lineno or node.lineno) - node.lineno + 1,
                        "methods": methods,
                    })
        except SyntaxError:
            pass

        # --- ruff: lint issues ---
        lint_issues: list[dict] = []
        try:
            r = subprocess.run(
                ["python3", "-m", "ruff", "check", str(full_path),
                 "--output-format=json"],
                capture_output=True, text=True, timeout=10,
            )
            if r.stdout and r.stdout.strip().startswith("["):
                items = json.loads(r.stdout)
                for item in items[:10]:
                    lint_issues.append({
                        "code": item.get("code", ""),
                        "message": item.get("message", "")[:120],
                        "line": item.get("location", {}).get("row", 0),
                    })
        except Exception:
            pass

        # --- lizard: cyclomatic complexity (optional) ---
        complexity: list[dict] = []
        try:
            import lizard as _lizard
            result = _lizard.analyze_file(str(full_path))
            for fn in result.function_list:
                complexity.append({
                    "name": fn.name,
                    "line": fn.start_line,
                    "cc": fn.cyclomatic_complexity,
                    "length": fn.length,
                })
        except ImportError:
            pass
        except Exception:
            pass

        return {
            "symbols": symbols,
            "lint_issues": lint_issues,
            "complexity": complexity,
            "total_lines": total_lines,
        }

    def _count_learnings(self) -> int:
        learnings_path = self.base / "memory" / "learnings.jsonl"
        if not learnings_path.exists():
            return 0
        try:
            return sum(1 for line in learnings_path.read_text(encoding="utf-8").splitlines() if line.strip())
        except OSError:
            return 0

    @staticmethod
    def _is_recent(ts_str: str, hours: int = 24) -> bool:
        if not ts_str:
            return False
        try:
            ts = datetime.fromisoformat(ts_str)
            return datetime.now() - ts < timedelta(hours=hours)
        except (ValueError, TypeError):
            return False

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _load_state(self) -> EvolutionState:
        if self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text(encoding="utf-8"))
                return EvolutionState(
                    proposals_generated=data.get("proposals_generated", 0),
                    last_proposal_at=data.get("last_proposal_at", ""),
                    window_start_at=data.get("window_start_at", ""),
                    total_cycles=data.get("total_cycles", 0),
                )
            except (json.JSONDecodeError, OSError):
                pass
        return EvolutionState()

    def _save_state(self, state: EvolutionState) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "proposals_generated": state.proposals_generated,
            "last_proposal_at": state.last_proposal_at,
            "window_start_at": state.window_start_at,
            "total_cycles": state.total_cycles,
        }
        self._state_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _current_window_start(self) -> datetime:
        now = datetime.now()
        start = self.config.window_start_hour
        end = self.config.window_end_hour
        if start > end and now.hour < end:
            base = now - timedelta(days=1)
        else:
            base = now
        return datetime(base.year, base.month, base.day, start)

    def reset_window(self) -> None:
        """Reset proposal counter for a new evolution window."""
        state = self._load_state()
        state.proposals_generated = 0
        state.window_start_at = self._current_window_start().isoformat()
        self._save_state(state)
        logger.info("🧬 Evolution window reset")

    @staticmethod
    def _proposal_preflight_error(content: str) -> str | None:
        placeholder_markers = ["待分析", "TODO", "TBD", "至少 0 个", "test_("]
        for marker in placeholder_markers:
            if marker in content:
                return f"proposal contains placeholder marker: {marker}"
        bac_lines = [line for line in content.splitlines() if "[BAC-" in line]
        if not bac_lines:
            return "proposal has no binary acceptance criteria"
        if "def test_" in content:
            test_count_pattern = r"至少\s*[1-9]\d*\s*个.*def test_"
            named_test_pattern = r"test_[a-zA-Z0-9_]+"
            if not (
                re.search(test_count_pattern, content)
                or re.search(named_test_pattern, content)
            ):
                return "proposal test BACs do not name concrete tests or a positive test count"
        return None
