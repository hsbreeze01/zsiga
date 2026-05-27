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

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from ..memory.learn import record_lesson, search_learnings
from ..memory.pattern_miner import mine_patterns

logger = logging.getLogger(__name__)

_EVO_PREFIX = "evo-"
_BACKDOOR_FILE = ".evolution-pause"


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
        state = self._load_state()
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
        updated = self._phase3_learn(facts, insights)
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

        facts: dict = {
            "recent_outcomes": self._collect_recent_outcomes(),
            "patterns": mine_patterns(min_occurrences=2, learnings_path=self.base / "memory" / "learnings.jsonl"),
            "code_structure": self._scan_code_structure(),
            "learnings_count": self._count_learnings(),
            "recent_failures": search_learnings(["fail", "revert", "error", "critical"], pattern_key=None)[:10],
            "recent_successes": search_learnings(["success", "pass", "deliver"], pattern_key=None)[:5],
            "recent_evo_rejections": recent_evo_rejections,
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

        facts["findings"] = findings
        facts["actionable"] = len(findings) > 0
        return facts

    # ------------------------------------------------------------------
    # Phase 2: 反思校验 — validate and prioritize
    # ------------------------------------------------------------------

    def _phase2_reflect(self, facts: dict) -> dict:
        findings = facts.get("findings", [])
        insights: dict = {
            "priority_finding": None,
            "proposal_type": "improvement",
            "scope": "zsiga",
            "confidence": "low",
        }

        # Priority: fix failures > fill gaps > proactive improvement
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

        if not insights["priority_finding"]:
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
                if finding.startswith("explore_untested:"):
                    module = finding.split(":", 1)[1]
                    insights["priority_finding"] = {
                        "type": "explore_module",
                        "module": module,
                    }
                    insights["proposal_type"] = "improvement"
                    insights["confidence"] = "low"
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
        module_lines = "\n".join(f"- `{m}`" for m in modules)

        # Pick first module as the concrete target
        target_module = modules[0] if modules else "unknown"

        return f"""# add-tests-for-untested-modules

## Summary
为 {count} 个缺少测试的模块编写单元测试，优先覆盖 `{target_module}`。

## Problem
以下模块缺少测试覆盖，是潜在的风险点：

{module_lines}

## Technical Design
1. 分析目标模块的公开 API 和关键函数
2. 为每个公开函数编写正向和反向测试用例
3. 使用 mock/fixture 隔离外部依赖
4. 确保测试可在 CI 环境中独立运行

### Target Files
- `tests/test_{os.path.basename(target_module).replace('.py', '')}.py` (新建)

## Acceptance Criteria
- [BAC-01] tests/ 目录中存在对应的测试文件
- [BAC-02] 测试文件中存在至少 3 个 test_ 函数
- [BAC-03] pytest 执行全部通过

## Scope
- In scope: 为 1 个模块编写测试
- Out of scope: 不修改生产代码

## Risk
- Impact: None — 只添加测试
- Reversibility: 删除测试文件

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成
- project=zsiga
"""

    def _render_explore_proposal(self, finding: dict, facts: dict) -> str:
        module = finding.get("module", "unknown")
        module_name = os.path.basename(module).replace(".py", "")

        return f"""# explore-and-improve-{module_name}

## Summary
探索模块 `{module}` 的代码质量，识别可优化项并实施改进。

## Problem
模块 `{module}` 缺少测试覆盖且可能有改进空间。通过主动探索发现潜在问题。

## Technical Design
1. 阅读 `{module}` 源码，理解其职责和 API
2. 识别代码异味：过长函数、重复代码、缺失错误处理
3. 对发现的问题实施针对性改进
4. 添加基本测试覆盖

### Target Files
- `{module}` (分析)
- `tests/test_{module_name}.py` (新建，如不存在)

## Acceptance Criteria
- [BAC-01] 完成对 `{module}` 的代码分析
- [BAC-02] 实施至少 1 项实质性改进（非格式化）
- [BAC-03] 所有变更通过 pytest 和 ruff

## Scope
- In scope: 分析 1 个模块，实施小范围改进
- Out of scope: 不做大范围重构

## Risk
- Impact: Low — 小范围改进
- Reversibility: git revert

## Constraints
- 此 proposal 由 zsiga 自演进引擎生成
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

    # ------------------------------------------------------------------
    # Proposal writing
    # ------------------------------------------------------------------

    def _write_proposal(self, content: str, proposal_type: str) -> str:
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
        """Scan archived evo- proposals for REJECT verdicts."""
        rejections: list[dict] = []
        changes_dir = self.base / "openspec" / "changes"

        evo_dirs: list[Path] = []
        if changes_dir.exists():
            for entry in changes_dir.iterdir():
                if entry.is_dir() and entry.name.startswith("evo-"):
                    evo_dirs.append(entry)
        archive_dir = changes_dir / "archive"
        for sub in ("skipped", "completed"):
            sub_dir = archive_dir / sub
            if sub_dir.exists():
                for entry in sub_dir.iterdir():
                    if entry.is_dir() and entry.name.startswith("evo-"):
                        evo_dirs.append(entry)

        for evo_dir in evo_dirs[-10:]:
            for review_file in sorted(evo_dir.glob("steward-review*.md"))[-1:]:
                try:
                    content = review_file.read_text(encoding="utf-8")
                    if "REJECT" in content:
                        pattern_key = ""
                        for line in content.splitlines():
                            m = re.match(r".*模式\s*`(\S+)`.*", line)
                            if m:
                                pattern_key = m.group(1)
                                break
                        rejections.append({
                            "dir": evo_dir.name,
                            "pattern_key": pattern_key,
                            "review": content[:200],
                        })
                except OSError:
                    pass

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
        for pf in py_files:
            basename = os.path.basename(pf).replace(".py", "")
            if basename not in test_files and basename != "__init__":
                modules_without_tests.append(pf)

            full_path = self.base / pf
            try:
                size = os.path.getsize(full_path)
                if size > 10000:  # > 10KB
                    large_files.append(f"{pf} ({size // 1024}KB)")
            except OSError:
                pass

        return {
            "py_files_count": len(py_files),
            "test_files_count": len(test_files),
            "modules_without_tests": modules_without_tests,
            "large_files": large_files,
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

    def reset_window(self) -> None:
        """Reset proposal counter for a new evolution window."""
        state = self._load_state()
        state.proposals_generated = 0
        state.window_start_at = datetime.now().isoformat()
        self._save_state(state)
        logger.info("🧬 Evolution window reset")
