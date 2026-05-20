"""Self-Reflection Loop: scans internal signals and generates proposals.

Read-only consumer of learnings, metrics, diagnosis files.
Producer of proposals into openspec/changes/.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from ..memory.pattern_miner import mine_patterns

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    type: str  # "recurring_failure" | "metric_degradation" | "recurring_root_cause"
    priority: str  # "high" | "medium"
    pattern_key: str  # unique identifier for dedup
    title: str  # human-readable title
    data: dict = field(default_factory=dict)


class Reflector:
    """Scans three categories of internal signals and generates proposals."""

    # ------------------------------------------------------------------
    # Signal scanning
    # ------------------------------------------------------------------

    def scan_signals(self, base_path: str | Path) -> list[Signal]:
        """Scan all signal sources and return a list of detected signals."""
        base = Path(base_path)
        signals: list[Signal] = []
        signals.extend(self._scan_recurring_failures(base))
        signals.extend(self._scan_metric_degradation(base))
        signals.extend(self._scan_recurring_root_causes(base))
        return signals

    def _scan_recurring_failures(self, base: Path) -> list[Signal]:
        """Scan learnings.jsonl for high-severity recurring patterns."""
        learnings_path = base / "memory" / "learnings.jsonl"
        if not learnings_path.exists():
            return []

        patterns = mine_patterns(
            min_occurrences=3,
            learnings_path=learnings_path,
        )

        signals: list[Signal] = []
        changes_dir = base / "openspec" / "changes"
        existing_dirs = self._list_change_dirs(changes_dir)

        for p in patterns:
            if p.severity != "high":
                continue

            sanitized = self._sanitize_key(p.key)

            # Check if a proposal already covers this pattern
            already_covered = any(sanitized in d for d in existing_dirs)
            if already_covered:
                continue

            signals.append(Signal(
                type="recurring_failure",
                priority="high",
                pattern_key=p.key,
                title=f"Recurring failure: {p.key}",
                data={
                    "count": p.count,
                    "recent_takeaways": p.recent_takeaways[:3],
                    "first_seen": p.first_seen,
                    "last_seen": p.last_seen,
                },
            ))
        return signals

    def _scan_metric_degradation(self, base: Path) -> list[Signal]:
        """Scan current stats and compare against prior snapshot."""
        signals: list[Signal] = []

        # Load current stats
        current_stats = self._load_current_stats(base)
        if not current_stats:
            return signals

        # Check metric thresholds
        success_rate = current_stats.get("success_rate_pct", 100)
        if success_rate < 70:
            signals.append(Signal(
                type="metric_degradation",
                priority="high" if success_rate < 50 else "medium",
                pattern_key="success_rate",
                title=f"Low success rate: {success_rate}%",
                data={"metric": "success_rate", "value": success_rate},
            ))

        verify_rate = current_stats.get("verify_pass_rate_pct", 100)
        if verify_rate < 50:
            signals.append(Signal(
                type="metric_degradation",
                priority="high" if verify_rate < 30 else "medium",
                pattern_key="verify_pass_rate",
                title=f"Low verify pass rate: {verify_rate}%",
                data={"metric": "verify_pass_rate", "value": verify_rate},
            ))

        # Check budget exceed rate
        budget_signal = self._check_budget_exceed_rate(base)
        if budget_signal:
            signals.append(budget_signal)

        # Compare against prior snapshot
        prior_stats = self._load_prior_snapshot(base)
        if prior_stats:
            signals.extend(
                self._check_metric_drops(current_stats, prior_stats)
            )

        return signals

    def _check_budget_exceed_rate(self, base: Path) -> Signal | None:
        """Check if ≥ 3 of last 10 changes have outcome BUDGET_EXCEEDED."""
        changes = self._load_recent_changes(base, limit=10)
        if not changes:
            return None

        budget_exceeded = sum(
            1 for c in changes if c.get("outcome") == "BUDGET_EXCEEDED"
        )
        if budget_exceeded >= 3:
            return Signal(
                type="metric_degradation",
                priority="high",
                pattern_key="budget_exceed_rate",
                title=f"High budget exceed rate: {budget_exceeded}/10",
                data={
                    "metric": "budget_exceed_rate",
                    "value": budget_exceeded,
                },
            )
        return None

    def _check_metric_drops(
        self, current: dict, prior: dict
    ) -> list[Signal]:
        """Check if any metric dropped > 10% compared to prior snapshot."""
        signals: list[Signal] = []
        metrics_to_check = [
            "success_rate_pct",
            "verify_pass_rate_pct",
            "first_pass_test_rate_pct",
        ]
        for metric in metrics_to_check:
            cur_val = current.get(metric, 0)
            prior_val = prior.get(metric, 0)
            if prior_val > 0 and (prior_val - cur_val) > 10:
                signals.append(Signal(
                    type="metric_degradation",
                    priority="high",
                    pattern_key=f"{metric}_drop",
                    title=f"{metric} dropped from {prior_val}% to {cur_val}%",
                    data={
                        "metric": metric,
                        "value": cur_val,
                        "prior_value": prior_val,
                        "drop": prior_val - cur_val,
                    },
                ))
        return signals

    def _scan_recurring_root_causes(self, base: Path) -> list[Signal]:
        """Scan reverted changes for recurring root causes."""
        changes = self._load_recent_changes(base, limit=10)
        reverted = [c for c in changes if c.get("outcome") == "reverted"]
        if not reverted:
            return []

        # Read diagnosis.md for each reverted change
        root_cause_counts: dict[str, list[str]] = {}
        changes_dir = base / "openspec" / "changes"

        for c in reverted:
            name = c.get("change_name", "")
            root_cause = self._extract_root_cause(changes_dir, name)
            if root_cause:
                root_cause_counts.setdefault(root_cause, []).append(name)

        signals: list[Signal] = []
        for root_cause, change_names in root_cause_counts.items():
            if len(change_names) >= 2:
                signals.append(Signal(
                    type="recurring_root_cause",
                    priority="high",
                    pattern_key=self._sanitize_key(root_cause),
                    title=f"Recurring root cause: {root_cause}",
                    data={
                        "root_cause": root_cause,
                        "occurrences": len(change_names),
                        "changes": change_names,
                    },
                ))
        return signals

    # ------------------------------------------------------------------
    # Dedup and rate limiting
    # ------------------------------------------------------------------

    def should_propose(self, signal: Signal, base_path: str | Path) -> bool:
        """Check if a proposal should be generated for the given signal."""
        base = Path(base_path)

        # Check for external proposals
        if self._has_external_proposals(base):
            return False

        # Check rate limit
        if self._rate_limit_reached(base):
            return False

        # Check dedup
        if self._is_duplicate(base, signal):
            return False

        return True

    def _has_external_proposals(self, base: Path) -> bool:
        """Check if there are non-auto proposals in openspec/changes/."""
        changes_dir = base / "openspec" / "changes"
        if not changes_dir.exists():
            return False
        for entry in changes_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("auto-"):
                if entry.name != "archive":
                    return True
        return False

    def _rate_limit_reached(self, base: Path) -> bool:
        """Check if 3 proposals already generated in past 24 hours."""
        history = self._load_history(base)
        cutoff = datetime.now() - timedelta(hours=24)
        recent = [
            e for e in history
            if self._parse_ts(e.get("timestamp", "")) > cutoff
        ]
        return len(recent) >= 3

    def _is_duplicate(self, base: Path, signal: Signal) -> bool:
        """Check if same signal_type + pattern_key proposed within 24h."""
        history = self._load_history(base)
        cutoff = datetime.now() - timedelta(hours=24)
        for entry in history:
            ts = self._parse_ts(entry.get("timestamp", ""))
            if ts <= cutoff:
                continue
            if (
                entry.get("signal_type") == signal.type
                and entry.get("pattern_key") == signal.pattern_key
            ):
                return True
        return False

    # ------------------------------------------------------------------
    # Proposal generation
    # ------------------------------------------------------------------

    def generate_proposal(
        self, signal: Signal, base_path: str | Path
    ) -> str | None:
        """Generate a proposal directory and return its path."""
        base = Path(base_path)
        changes_dir = base / "openspec" / "changes"
        changes_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime("%Y%m%d")
        sanitized_key = self._sanitize_key(signal.pattern_key)
        dir_name = f"auto-{signal.type}-{sanitized_key}-{today}"

        # Handle duplicate directory names
        proposal_dir = changes_dir / dir_name
        counter = 2
        while proposal_dir.exists():
            dir_name = f"auto-{signal.type}-{sanitized_key}-{today}-{counter}"
            proposal_dir = changes_dir / dir_name
            counter += 1

        proposal_dir.mkdir(parents=True, exist_ok=True)

        # Generate proposal.md content
        content = self._render_proposal_md(signal)
        (proposal_dir / "proposal.md").write_text(content, encoding="utf-8")

        # Record in history
        self._record_history(base, signal, dir_name)

        return str(proposal_dir)

    def _render_proposal_md(self, signal: Signal) -> str:
        """Render proposal.md from template based on signal type."""
        templates = {
            "recurring_failure": self._template_recurring_failure,
            "metric_degradation": self._template_metric_degradation,
            "recurring_root_cause": self._template_recurring_root_cause,
        }
        renderer = templates.get(signal.type)
        if renderer:
            return renderer(signal)

        # Fallback generic template
        return self._template_generic(signal)

    def _template_recurring_failure(self, signal: Signal) -> str:
        count = signal.data.get("count", 0)
        takeaways = signal.data.get("recent_takeaways", [])
        takeaway_lines = "\n".join(f"- {t}" for t in takeaways)
        return f"""# Proposal: Fix Recurring Failure Pattern

## Summary

Fix recurring pipeline failure pattern `{signal.pattern_key}` (seen {count} times).

## Motivation

The pattern `{signal.pattern_key}` has been observed {count} times in recent learnings.
This indicates a systematic issue that should be addressed to improve reliability.

Recent examples:
{takeaway_lines}

## Expected Behavior

Reduce or eliminate occurrences of the `{signal.pattern_key}` failure pattern.
The root cause should be identified and a targeted fix applied.

## Constraints

- This proposal is auto-generated by the zsiga self-reflection loop.
- Scope: project=zsiga
- All changes must pass `pytest` and `ruff` before delivery.
"""

    def _template_metric_degradation(self, signal: Signal) -> str:
        metric = signal.data.get("metric", "unknown")
        value = signal.data.get("value", 0)
        prior_value = signal.data.get("prior_value")
        drop_info = ""
        if prior_value is not None:
            drop_info = f"\nThis represents a drop of {prior_value - value:.1f}% from the previous value of {prior_value}%."
        return f"""# Proposal: Investigate Metric Degradation

## Summary

Investigate and improve `{metric}` (currently at {value}{'' if 'rate' not in metric else '%'}).

## Motivation

The metric `{metric}` is currently at {value}{'' if 'rate' not in metric else '%'}, which is below the acceptable threshold.{drop_info}

## Expected Behavior

The `{metric}` metric should be improved above threshold levels.
Root causes of the degradation should be identified and addressed.

## Constraints

- This proposal is auto-generated by the zsiga self-reflection loop.
- Scope: project=zsiga
- All changes must pass `pytest` and `ruff` before delivery.
"""

    def _template_recurring_root_cause(self, signal: Signal) -> str:
        root_cause = signal.data.get("root_cause", "unknown")
        occurrences = signal.data.get("occurrences", 0)
        return f"""# Proposal: Address Recurring Root Cause

## Summary

Address recurring root cause `{root_cause}` (seen {occurrences} times).

## Motivation

The root cause `{root_cause}` has been identified in {occurrences} separate reverted changes.
This recurring issue is causing repeated failures and should be systematically fixed.

## Expected Behavior

Eliminate the `{root_cause}` root cause from the codebase.
Prevent future occurrences through improved patterns or guardrails.

## Constraints

- This proposal is auto-generated by the zsiga self-reflection loop.
- Scope: project=zsiga
- All changes must pass `pytest` and `ruff` before delivery.
"""

    def _template_generic(self, signal: Signal) -> str:
        return f"""# Proposal: {signal.title}

## Summary

{signal.title}

## Motivation

Signal detected: type={signal.type}, pattern_key={signal.pattern_key}

## Expected Behavior

Investigate and resolve the identified issue.

## Constraints

- This proposal is auto-generated by the zsiga self-reflection loop.
- Scope: project=zsiga
- All changes must pass `pytest` and `ruff` before delivery.
"""

    # ------------------------------------------------------------------
    # Run entry point
    # ------------------------------------------------------------------

    def run(self, base_path: str | Path) -> list[str]:
        """Main entry point: scan → filter → generate.

        Returns list of generated proposal directory paths.
        """
        signals = self.scan_signals(base_path)
        proposals: list[str] = []
        for signal in signals:
            if self.should_propose(signal, base_path):
                result = self.generate_proposal(signal, base_path)
                if result:
                    proposals.append(result)
                    logger.info(
                        f"🔄 Reflector generated proposal: {result}"
                    )
        return proposals

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_key(key: str) -> str:
        """Sanitize a key for filesystem safety."""
        return re.sub(r"[^a-zA-Z0-9_-]", "-", key).lower()

    @staticmethod
    def _list_change_dirs(changes_dir: Path) -> list[str]:
        """List directory names under openspec/changes/."""
        if not changes_dir.exists():
            return []
        return [
            e.name
            for e in changes_dir.iterdir()
            if e.is_dir() and e.name != "archive"
        ]

    def _load_current_stats(self, base: Path) -> dict | None:
        """Load current stats from the metrics database."""
        try:
            from ..metrics.collector import compute_stats
            return compute_stats()
        except Exception:
            return None

    def _load_prior_snapshot(self, base: Path) -> dict | None:
        """Load the prior stats snapshot."""
        try:
            from ..metrics.db import load_latest_snapshot
            return load_latest_snapshot()
        except Exception:
            return None

    def _load_recent_changes(
        self, base: Path, limit: int = 10
    ) -> list[dict]:
        """Load recent changes from metrics."""
        try:
            from ..metrics.collector import load_all_changes
            changes = load_all_changes()
            return changes[-limit:] if changes else []
        except Exception:
            return []

    def _extract_root_cause(
        self, changes_dir: Path, change_name: str
    ) -> str | None:
        """Extract root_cause from a diagnosis.md file."""
        # Check both active and archived locations
        for prefix in ["", "archive/"]:
            diag_path = changes_dir / prefix / change_name / "diagnosis.md"
            if diag_path.exists():
                try:
                    content = diag_path.read_text(encoding="utf-8")
                    # Look for "Root Cause" section
                    match = re.search(
                        r"## Root Cause\s*\n\s*(.+?)(?:\n|$)",
                        content,
                    )
                    if match:
                        return match.group(1).strip()
                except (OSError, UnicodeDecodeError):
                    pass
        return None

    def _load_history(self, base: Path) -> list[dict]:
        """Load reflector_history.jsonl entries."""
        history_path = base / "data" / "reflector_history.jsonl"
        if not history_path.exists():
            return []
        entries: list[dict] = []
        try:
            for line in history_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass
        return entries

    def _record_history(
        self, base: Path, signal: Signal, directory: str
    ) -> None:
        """Append an entry to reflector_history.jsonl."""
        history_path = base / "data" / "reflector_history.jsonl"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "signal_type": signal.type,
            "pattern_key": signal.pattern_key,
            "directory": directory,
        }
        with open(history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    @staticmethod
    def _parse_ts(ts_str: str) -> datetime:
        """Parse a timestamp string, returning epoch=0 on failure."""
        try:
            return datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            return datetime.min
