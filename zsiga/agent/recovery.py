"""Failure recovery module — composition layer over EscalationManager and Diagnoser."""

from dataclasses import dataclass
from typing import Optional

from ..transport import Transport
from .. import git_ops
from ..memory.learn import record_lesson
from .escalation import EscalationManager, Strategy, FailureRecord
from ..pipeline.diagnoser import Diagnoser, DiagnosisReport


@dataclass
class RecoveryAction:
    """Returned by record_failure() — tells orchestrator what to do next."""

    strategy: Strategy
    strategy_hint: str
    should_rollback: bool
    attempt: int
    rca_report: Optional[DiagnosisReport] = None


@dataclass
class RecoveryReport:
    """Full diagnostic report written on strategy exhaustion."""

    change_name: str
    total_attempts: int
    failures: list[FailureRecord]
    root_cause: str
    root_cause_confirmed: bool
    strategies_tried: list[str]
    recommended_action: str

    def to_markdown(self) -> str:
        lines = [
            "# Recovery Report",
            "",
            f"**Change:** {self.change_name}",
            f"**Total Attempts:** {self.total_attempts}",
            "",
            "## Failure History",
            "",
        ]
        for f in self.failures:
            lines.append(
                f"- Attempt {f.attempt} ({f.phase}): "
                f"{f.error[:200]} [strategy: {f.strategy_used}]"
            )
        lines.append("")
        lines.append("## Root Cause Analysis")
        lines.append("")
        lines.append(self.root_cause)
        lines.append(
            f"**Confirmed:** {'Yes' if self.root_cause_confirmed else 'No'}"
        )
        lines.append("")
        lines.append("## Strategies Tried")
        lines.append("")
        for s in self.strategies_tried:
            lines.append(f"- {s}")
        lines.append("")
        lines.append("## Recommended Action")
        lines.append("")
        lines.append(self.recommended_action)
        lines.append("")
        return "\n".join(lines)

    def save(self, change_dir: str, transport: Transport) -> None:
        content = self.to_markdown()
        transport.run_shell(
            f"cat > '{change_dir}/recovery-report.md' << 'ZSIGA_RECOVERY_EOF'\n{content}\nZSIGA_RECOVERY_EOF",
            timeout=10,
        )


class RecoveryManager:
    """Orchestrates failure recovery by composing EscalationManager and Diagnoser."""

    def __init__(
        self,
        change_name: str,
        target_path: str = None,
        pre_sha: str = None,
        transport: Transport = None,
        persist_dir: str = None,
        max_failures: int = 3,
    ):
        self.change_name = change_name
        self.target_path = target_path
        self.pre_sha = pre_sha
        self.transport = transport
        self.max_failures = max_failures
        self._escalation = EscalationManager(change_name, persist_dir=persist_dir)
        self._diagnoser = Diagnoser()
        self._rca_reports: list[DiagnosisReport] = []

    def record_failure(
        self, error: str, phase: str = ""
    ) -> RecoveryAction:
        """Record a failure and return a RecoveryAction with strategy + rollback decision."""
        self._escalation.record_failure(error, phase=phase)
        strategy = self._escalation.next_strategy
        hint = self.get_strategy_hint(strategy)
        should_rollback = self._escalation.attempts >= self.max_failures

        rca_report = None
        if self.target_path and self.transport:
            try:
                rca_report = self._diagnoser.diagnose(
                    {"detail": error, "change_name": self.change_name},
                    self.target_path,
                    self.transport,
                )
                self._rca_reports.append(rca_report)
            except Exception:
                rca_report = None

        return RecoveryAction(
            strategy=strategy,
            strategy_hint=hint,
            should_rollback=should_rollback,
            attempt=self._escalation.attempts,
            rca_report=rca_report,
        )

    def get_strategy(self) -> Strategy:
        """Return the current strategy from escalation."""
        return self._escalation.next_strategy

    def get_strategy_hint(self, strategy: Strategy = None) -> str:
        """Return a prompt modifier for the given strategy."""
        if strategy is None:
            strategy = self._escalation.next_strategy
        if strategy == Strategy.DIFFERENT_APPROACH:
            return (
                "\n\n⚠️ 之前多次修复失败。"
                "Try a fundamentally different approach. "
                "Your previous strategy failed multiple times."
            )
        if strategy == Strategy.SIMPLIFY:
            return (
                "\n\n⚠️ Simplify the fix. "
                "Remove complexity rather than adding more code."
            )
        return ""

    def execute_rollback(self) -> bool:
        """Reset git to pre_sha and record a lesson."""
        if not self.target_path or not self.pre_sha:
            return False
        git_ops.reset_hard(self.target_path, self.pre_sha, transport=self.transport)
        record_lesson(
            title=f"ROLLBACK: {self.change_name}",
            context=f"attempts={self._escalation.attempts}",
            takeaway=f"Reverted after {self._escalation.attempts} failures",
            pattern_key="pipeline.fail.rollback",
            source="recovery",
        )
        return True

    def generate_diagnostic_report(self) -> RecoveryReport:
        """Generate a RecoveryReport, save it, and record a lesson."""
        failures = self._escalation.failures
        strategies_tried = list(dict.fromkeys(f.strategy_used for f in failures))

        root_cause = "Unknown"
        root_cause_confirmed = False
        if self._rca_reports:
            best = self._rca_reports[-1]
            root_cause = best.fix_plan.root_cause
            root_cause_confirmed = best.fix_plan.confirmed

        report = RecoveryReport(
            change_name=self.change_name,
            total_attempts=self._escalation.attempts,
            failures=failures,
            root_cause=root_cause,
            root_cause_confirmed=root_cause_confirmed,
            strategies_tried=strategies_tried,
            recommended_action=(
                f"Review root cause: {root_cause}. "
                f"Consider manual intervention."
            ),
        )

        if self.transport:
            try:
                persist_dir = self._escalation._persist_dir
                change_dir = str(persist_dir) if persist_dir else "."
                report.save(change_dir, self.transport)
            except Exception:
                pass

        record_lesson(
            title=f"RECOVERY REPORT: {self.change_name}",
            context=f"attempts={self._escalation.attempts}, root_cause={root_cause}",
            takeaway=f"Recovery exhausted. Root cause: {root_cause}",
            pattern_key="pipeline.fail.recovery",
            source="recovery",
        )
        return report

    def should_rollback(self) -> bool:
        """Check if rollback threshold has been reached."""
        return self._escalation.attempts >= self.max_failures
