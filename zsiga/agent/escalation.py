"""升级路径 — 3 次修复失败后自动升级，尝试不同策略并生成诊断报告"""
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class EscalationLevel(str, Enum):
    NORMAL = "normal"
    RETRY_DIFFERENT = "retry_different"
    NEEDS_HUMAN = "needs_human"


class Strategy(str, Enum):
    SAME = "same"
    DIFFERENT_APPROACH = "different_approach"
    SIMPLIFY = "simplify"
    SKIP = "skip"


@dataclass
class FailureRecord:
    attempt: int
    timestamp: float
    error: str
    strategy_used: str
    phase: str = ""


@dataclass
class DiagnosisReport:
    change_name: str
    total_attempts: int
    failures: list[FailureRecord] = field(default_factory=list)
    root_cause_hypothesis: str = ""
    recommended_action: str = ""
    needs_human: bool = False

    def to_text(self) -> str:
        lines = [
            f"# 诊断报告: {self.change_name}",
            f"总尝试次数: {self.total_attempts}",
            f"需要人工介入: {'是' if self.needs_human else '否'}",
            "",
            "## 失败记录",
        ]
        for f in self.failures:
            lines.append(f"- 第{f.attempt}次 ({f.phase}): {f.error} [策略: {f.strategy_used}]")
        if self.root_cause_hypothesis:
            lines.extend(["", "## 根因假设", self.root_cause_hypothesis])
        if self.recommended_action:
            lines.extend(["", "## 建议操作", self.recommended_action])
        return "\n".join(lines)


_MAX_ATTEMPTS = 3
_STRATEGY_ROTATION = [Strategy.SAME, Strategy.DIFFERENT_APPROACH, Strategy.SIMPLIFY]


class EscalationManager:
    """管理修复循环的升级逻辑：3 次失败后自动升级。"""

    def __init__(self, change_name: str, persist_dir: str = None):
        self.change_name = change_name
        self.attempts = 0
        self.failures: list[FailureRecord] = []
        self._persist_dir = Path(persist_dir) if persist_dir else None

    @property
    def level(self) -> EscalationLevel:
        if self.attempts < _MAX_ATTEMPTS:
            return EscalationLevel.NORMAL
        if self.attempts < _MAX_ATTEMPTS + 2:
            return EscalationLevel.RETRY_DIFFERENT
        return EscalationLevel.NEEDS_HUMAN

    @property
    def next_strategy(self) -> Strategy:
        idx = min(self.attempts, len(_STRATEGY_ROTATION) - 1)
        return _STRATEGY_ROTATION[idx]

    def record_failure(self, error: str, phase: str = "", strategy: str = "same") -> EscalationLevel:
        self.attempts += 1
        self.failures.append(FailureRecord(
            attempt=self.attempts,
            timestamp=time.time(),
            error=error,
            strategy_used=strategy,
            phase=phase,
        ))
        self._persist_report()
        return self.level

    def should_escalate(self) -> bool:
        return self.attempts >= _MAX_ATTEMPTS

    def should_abort(self) -> bool:
        return self.attempts >= _MAX_ATTEMPTS + 2

    def generate_diagnosis(self) -> DiagnosisReport:
        phases = set(f.phase for f in self.failures if f.phase)
        if len(phases) == 1:
            phase_name = phases.pop()
            hypothesis = f"所有失败发生在同一阶段 ({phase_name})，可能是该阶段的系统性问题"
        else:
            hypothesis = f"失败分布在多个阶段 ({', '.join(phases)})，可能是需求理解或环境问题"

        return DiagnosisReport(
            change_name=self.change_name,
            total_attempts=self.attempts,
            failures=self.failures,
            root_cause_hypothesis=hypothesis,
            recommended_action="暂停并等待人工介入" if self.should_abort() else "尝试不同策略",
            needs_human=self.should_abort(),
        )

    def _persist_report(self):
        if not self._persist_dir:
            return
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        report = self.generate_diagnosis()
        path = self._persist_dir / f"escalation-{self.change_name}.md"
        path.write_text(report.to_text())
