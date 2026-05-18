"""Structured diagnosis loop for verify-phase failures."""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..transport import Transport


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ProbeResult:
    confirmed: bool
    evidence: str
    probe_type: str  # "file_read", "search", "diagnostics", "bash"


@dataclass
class Hypothesis:
    rank: int
    description: str
    confidence: float
    evidence: str
    probe_result: Optional[ProbeResult] = None


@dataclass
class FixPlan:
    root_cause: str
    fix_description: str
    affected_files: list[str]
    confirmed: bool


@dataclass
class DiagnosisReport:
    change_name: str
    hypotheses: list[Hypothesis]
    confirmed_hypothesis: Optional[Hypothesis]
    fix_plan: FixPlan
    timestamp: str

    def to_markdown(self) -> str:
        lines = [
            f"# Diagnosis Report: {self.change_name}",
            f"",
            f"**Timestamp:** {self.timestamp}",
            f"",
            f"## Root Cause",
            f"{self.fix_plan.root_cause}",
            f"",
            f"**Confirmed:** {'Yes' if self.fix_plan.confirmed else 'No (best guess)'}",
            f"",
            f"## Fix Plan",
            f"{self.fix_plan.fix_description}",
            f"",
            f"## Affected Files",
        ]
        for f in self.fix_plan.affected_files:
            lines.append(f"- `{f}`")
        lines.append("")
        lines.append("## Hypotheses")
        for h in self.hypotheses:
            status = ""
            if h.probe_result:
                status = " ✅ Confirmed" if h.probe_result.confirmed else " ❌ Denied"
            lines.append(f"")
            lines.append(f"### #{h.rank}: {h.description}")
            lines.append(f"- Confidence: {h.confidence:.2f}")
            lines.append(f"- Evidence: {h.evidence}")
            if h.probe_result:
                lines.append(f"- Probe ({h.probe_result.probe_type}): {status}")
                lines.append(f"- Probe evidence: {h.probe_result.evidence}")
        lines.append("")
        return "\n".join(lines)

    def save(self, change_dir: str, transport: Transport) -> None:
        content = self.to_markdown()
        # Escape single quotes in content for shell safety
        safe_content = content.replace("'", "'\\''")
        transport.run_shell(
            f"cat > '{change_dir}/diagnosis.md' << 'ZSIGA_DIAG_EOF'\n{content}\nZSIGA_DIAG_EOF",
            timeout=10,
        )


# ---------------------------------------------------------------------------
# Error pattern → hypothesis rules
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[str, str, float]] = [
    (r"ImportError|ModuleNotFoundError", "Missing or incorrect import / dependency", 0.90),
    (r"NameError", "Undefined variable or missing import", 0.85),
    (r"AssertionError|assert", "Test expectation mismatch", 0.80),
    (r"SyntaxError|E70[0-9]|E501|E[0-9]{3}\b", "Code style or syntax violation", 0.75),
    (r"TypeError", "Type mismatch in function call or operation", 0.70),
    (r"AttributeError", "Missing attribute or wrong object type", 0.70),
    (r"FAILED|test session", "Test assertion failed", 0.60),
    (r"[Tt]imeout|[Tt]imed?\s*out", "Execution exceeded time budget", 0.50),
]


def _match_patterns(detail: str) -> list[tuple[str, str, float]]:
    """Return (description, evidence, confidence) for each matched pattern."""
    results: list[tuple[str, str, float]] = []
    for pattern, desc, confidence in _PATTERNS:
        m = re.search(pattern, detail)
        if m:
            results.append((desc, m.group(0), confidence))
    if not results:
        results.append(("Unknown error – no specific pattern matched", detail[:120], 0.30))
    return results


# ---------------------------------------------------------------------------
# Diagnoser class
# ---------------------------------------------------------------------------

class Diagnoser:
    """Rule-based structured diagnosis for verify-phase failures."""

    def hypothesize(self, failure_info: dict) -> list[Hypothesis]:
        """Generate 3–5 ranked hypotheses from failure information.

        Parameters
        ----------
        failure_info : dict
            Must contain ``detail`` (str, the error output) and optionally
            ``verify_feedback`` (str, content of verify.md).

        Returns
        -------
        list[Hypothesis]
            Sorted by confidence descending, with rank 1..N.
        """
        detail = failure_info.get("detail", "")
        verify_feedback = failure_info.get("verify_feedback", "")

        combined = f"{detail}\n{verify_feedback}"

        matched = _match_patterns(combined)
        # Deduplicate by description
        seen: set[str] = set()
        unique: list[tuple[str, str, float]] = []
        for desc, evidence, conf in matched:
            if desc not in seen:
                seen.add(desc)
                unique.append((desc, evidence, conf))

        # Always generate at least 3 hypotheses by adding generic fallbacks
        fallbacks: list[tuple[str, str, float]] = [
            ("Recent code change introduced a regression", "verify failure", 0.40),
            ("Missing or incorrect configuration", "verify failure", 0.35),
            ("Environment or dependency issue", "verify failure", 0.30),
        ]
        for fb_desc, fb_ev, fb_conf in fallbacks:
            if fb_desc not in seen:
                seen.add(fb_desc)
                unique.append((fb_desc, fb_ev, fb_conf))

        # Sort by confidence descending
        unique.sort(key=lambda x: x[2], reverse=True)

        # Cap at 5
        unique = unique[:5]

        hypotheses: list[Hypothesis] = []
        for i, (desc, evidence, conf) in enumerate(unique):
            hypotheses.append(Hypothesis(
                rank=i + 1,
                description=desc,
                confidence=conf,
                evidence=evidence,
            ))
        return hypotheses

    def instrument(self, hypotheses: list[Hypothesis],
                   target_path: str,
                   transport: Transport) -> list[Hypothesis]:
        """Run read-only probes for the top hypotheses.

        Only probes the first 3 hypotheses (to conserve turns).
        """
        max_probes = 3
        for h in hypotheses[:max_probes]:
            h.probe_result = self._probe(h, target_path, transport)
        return hypotheses

    def _probe(self, hypothesis: Hypothesis,
               target_path: str,
               transport: Transport) -> ProbeResult:
        """Execute a single read-only probe for one hypothesis."""
        desc = hypothesis.description.lower()

        # Probe strategy based on hypothesis type
        if "import" in desc or "dependency" in desc or "module" in desc:
            return self._probe_import(hypothesis, target_path, transport)
        if "syntax" in desc or "style" in desc:
            return self._probe_diagnostics(hypothesis, target_path, transport)
        if "type" in desc:
            return self._probe_search(hypothesis, target_path, transport)

        # Generic probe: run diagnostics
        return self._probe_diagnostics(hypothesis, target_path, transport)

    def _probe_import(self, hypothesis: Hypothesis,
                      target_path: str,
                      transport: Transport) -> ProbeResult:
        """Search for missing imports using grep."""
        # Extract the module name from evidence
        module_match = re.search(r"'([^']+)'", hypothesis.evidence)
        if not module_match:
            module_match = re.search(r'"([^"]+)"', hypothesis.evidence)
        module_name = module_match.group(1) if module_match else ""

        if module_name:
            r = transport.run_shell(
                f"grep -rn 'import {module_name}' '{target_path}' --include='*.py' | head -5",
                timeout=15,
            )
            if r["exit_code"] == 0 and r["stdout"].strip():
                return ProbeResult(
                    confirmed=True,
                    evidence=f"Found import references for '{module_name}': {r['stdout'][:200]}",
                    probe_type="search",
                )
            return ProbeResult(
                confirmed=False,
                evidence=f"No import references found for '{module_name}'",
                probe_type="search",
            )

        return ProbeResult(
            confirmed=False,
            evidence="Could not extract module name from error",
            probe_type="search",
        )

    def _probe_diagnostics(self, hypothesis: Hypothesis,
                           target_path: str,
                           transport: Transport) -> ProbeResult:
        """Run ruff diagnostics on relevant files."""
        # Try to extract file from evidence
        file_match = re.search(r"([^\s:]+\.py)", hypothesis.evidence)
        target_file = file_match.group(1) if file_match else ""

        if target_file:
            full_path = f"{target_path}/{target_file}" if not target_file.startswith("/") else target_file
            r = transport.run_shell(
                f"python -m ruff check '{full_path}' 2>&1 | head -20",
                cwd=target_path, timeout=30,
            )
            output = r.get("stdout", "")
            if r["exit_code"] != 0 and output.strip():
                return ProbeResult(
                    confirmed=True,
                    evidence=f"Lint issues found: {output[:300]}",
                    probe_type="diagnostics",
                )

        return ProbeResult(
            confirmed=False,
            evidence="No lint issues found or file not accessible",
            probe_type="diagnostics",
        )

    def _probe_search(self, hypothesis: Hypothesis,
                      target_path: str,
                      transport: Transport) -> ProbeResult:
        """Search for the relevant symbol in the codebase."""
        # Extract a symbol name from evidence
        symbol_match = re.search(r"name '(\w+)'", hypothesis.evidence)
        if not symbol_match:
            symbol_match = re.search(r"'(\w+)'", hypothesis.evidence)
        symbol = symbol_match.group(1) if symbol_match else ""

        if symbol:
            r = transport.run_shell(
                f"grep -rn '{symbol}' '{target_path}' --include='*.py' | head -10",
                timeout=15,
            )
            if r["exit_code"] == 0 and r["stdout"].strip():
                return ProbeResult(
                    confirmed=True,
                    evidence=f"Found references to '{symbol}': {r['stdout'][:200]}",
                    probe_type="search",
                )

        return ProbeResult(
            confirmed=False,
            evidence="No references found or could not extract symbol",
            probe_type="search",
        )

    def targeted_fix(self, hypotheses: list[Hypothesis]) -> FixPlan:
        """Select the most likely root cause and produce a FixPlan.

        If a hypothesis was confirmed by probe, use that.
        Otherwise fall back to the highest-confidence hypothesis.
        """
        confirmed = None
        for h in hypotheses:
            if h.probe_result and h.probe_result.confirmed:
                confirmed = h
                break

        if confirmed:
            return FixPlan(
                root_cause=confirmed.description,
                fix_description=f"Fix confirmed issue: {confirmed.description}. "
                               f"Evidence: {confirmed.probe_result.evidence}",
                affected_files=self._extract_affected_files(confirmed.evidence),
                confirmed=True,
            )

        # Fallback: use highest-confidence hypothesis
        best = hypotheses[0] if hypotheses else Hypothesis(
            rank=1, description="Unknown error",
            confidence=0.1, evidence="No evidence available",
        )
        return FixPlan(
            root_cause=best.description,
            fix_description=f"Unconfirmed hypothesis: {best.description}. "
                           f"Needs further investigation.",
            affected_files=self._extract_affected_files(best.evidence),
            confirmed=False,
        )

    def _extract_affected_files(self, evidence: str) -> list[str]:
        """Extract file paths from evidence text."""
        files = re.findall(r"([^\s:]+\.py)", evidence)
        return list(dict.fromkeys(files))[:5]

    def diagnose(self, failure_info: dict,
                 target_path: str,
                 transport: Transport) -> DiagnosisReport:
        """Run the full diagnosis cycle: hypothesize → instrument → targeted_fix."""
        hypotheses = self.hypothesize(failure_info)
        hypotheses = self.instrument(hypotheses, target_path, transport)
        fix_plan = self.targeted_fix(hypotheses)

        confirmed_hyp = None
        for h in hypotheses:
            if h.probe_result and h.probe_result.confirmed:
                confirmed_hyp = h
                break

        return DiagnosisReport(
            change_name=failure_info.get("change_name", "unknown"),
            hypotheses=hypotheses,
            confirmed_hypothesis=confirmed_hyp,
            fix_plan=fix_plan,
            timestamp=datetime.now().isoformat(),
        )
