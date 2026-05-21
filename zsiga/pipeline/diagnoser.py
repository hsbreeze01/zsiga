"""Structured diagnosis loop for verify-phase failures."""

import re
from dataclasses import dataclass
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
            "",
            f"**Timestamp:** {self.timestamp}",
            "",
            "## Root Cause",
            f"{self.fix_plan.root_cause}",
            "",
            f"**Confirmed:** {'Yes' if self.fix_plan.confirmed else 'No (best guess)'}",
            "",
            "## Fix Plan",
            f"{self.fix_plan.fix_description}",
            "",
            "## Affected Files",
        ]
        for f in self.fix_plan.affected_files:
            lines.append(f"- `{f}`")
        lines.append("")
        lines.append("## Hypotheses")
        for h in self.hypotheses:
            status = ""
            if h.probe_result:
                status = " ✅ Confirmed" if h.probe_result.confirmed else " ❌ Denied"
            lines.append("")
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
            f"cat > '{change_dir}/diagnosis.md' << 'ZSIGA_DIAG_EOF'\n{safe_content}\nZSIGA_DIAG_EOF",
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

        # Only add generic fallbacks if we have fewer than 3 specific
        # hypotheses.  This ensures real evidence is never displaced by
        # low-confidence generic guesses like "Recent code change …".
        if len(unique) < 3:
            fallbacks: list[tuple[str, str, float]] = [
                (
                    "Recent code change introduced a regression",
                    combined[:120],
                    0.40,
                ),
                (
                    "Missing or incorrect configuration",
                    combined[:120],
                    0.35,
                ),
                (
                    "Environment or dependency issue",
                    combined[:120],
                    0.30,
                ),
            ]
            for fb_desc, fb_ev, fb_conf in fallbacks:
                if fb_desc not in seen and len(unique) < 5:
                    seen.add(fb_desc)
                    unique.append((fb_desc, fb_ev, fb_conf))

        # Ensure at least one hypothesis references actual failure detail
        has_real_evidence = any(
            ev != "verify failure" for _, ev, _ in unique
        )
        if not has_real_evidence and combined.strip():
            snippet = combined[:120]
            unique.append((
                "Error detected in failure output",
                snippet,
                0.45,
            ))

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
        Otherwise generate a specific, actionable fix description from
        the best hypothesis evidence (never the generic
        "Unconfirmed hypothesis … Needs further investigation." string).
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

        # Unconfirmed path: use highest-confidence hypothesis with
        # a specific, actionable fix description derived from evidence.
        best = hypotheses[0] if hypotheses else Hypothesis(
            rank=1, description="Unknown error",
            confidence=0.1, evidence="No evidence available",
        )
        fix_description = self._build_actionable_fix(best)
        return FixPlan(
            root_cause=best.description,
            fix_description=fix_description,
            affected_files=self._extract_affected_files(best.evidence),
            confirmed=False,
        )

    def _build_actionable_fix(self, hypothesis: Hypothesis) -> str:
        """Build a concrete, actionable fix description from hypothesis evidence."""
        evidence = hypothesis.evidence
        desc = hypothesis.description.lower()

        # ImportError / ModuleNotFoundError
        module_match = re.search(
            r"No module named ['\"]([^'\"]+)['\"]", evidence,
        )
        if not module_match:
            module_match = re.search(
                r"cannot import name ['\"]([^'\"]+)['\"]", evidence,
            )
        if module_match:
            module_name = module_match.group(1)
            return (
                f"Missing module '{module_name}'. "
                f"Install the dependency providing '{module_name}' or "
                f"add the missing import. Evidence: {evidence}"
            )

        # Lint errors (E701, E702, etc.)
        lint_match = re.search(
            r"(E\d{3})\s+(.+?)(?:\s*$|\s*-->)", evidence,
        )
        if lint_match:
            rule_code = lint_match.group(1)
            rule_msg = lint_match.group(2).strip()
            files = self._extract_affected_files(evidence)
            file_hint = f" in {files[0]}" if files else ""
            return (
                f"Lint violation {rule_code}: {rule_msg}{file_hint}. "
                f"Fix the code style issue. Evidence: {evidence}"
            )

        # SyntaxError
        if "syntaxerror" in desc or "syntax" in desc:
            files = self._extract_affected_files(evidence)
            file_hint = f" in {files[0]}" if files else ""
            return (
                f"Syntax error{file_hint}. "
                f"Review and fix the syntax. Evidence: {evidence}"
            )

        # AssertionError / test expectation mismatch
        if "assertionerror" in desc or "assert" in desc or "test" in desc:
            # Try to extract test name
            test_match = re.search(
                r"(test_\w+|FAILED\s+(\S+))", evidence,
            )
            test_name = ""
            if test_match:
                test_name = test_match.group(1) if test_match.group(1) else test_match.group(2)
            test_hint = f" in {test_name}" if test_name else ""
            return (
                f"Test expectation mismatch{test_hint}. "
                f"Review test logic and expected values. Evidence: {evidence}"
            )

        # NameError / undefined variable
        name_match = re.search(r"name ['\"](\w+)['\"]", evidence)
        if name_match:
            symbol = name_match.group(1)
            return (
                f"Undefined name '{symbol}'. "
                f"Add missing import or define the variable. Evidence: {evidence}"
            )

        # TypeError / AttributeError
        if "type" in desc:
            return (
                f"Type mismatch in function call or operation. "
                f"Check argument types. Evidence: {evidence}"
            )
        if "attribute" in desc:
            return (
                f"Missing or wrong attribute access. "
                f"Check object type and available attributes. Evidence: {evidence}"
            )

        # Timeout
        if "timeout" in desc or "time" in desc:
            return (
                f"Execution exceeded time budget. "
                f"Optimize slow code path or increase timeout. Evidence: {evidence}"
            )

        # Generic fallback — always include actual evidence snippet
        snippet = evidence[:120] if evidence else "no details"
        return (
            f"Best guess: {hypothesis.description}. "
            f"Evidence: {snippet}"
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


# ---------------------------------------------------------------------------
# Verify pre-check (lightweight import + lint check on changed files)
# ---------------------------------------------------------------------------

@dataclass
class PreCheckResult:
    """Result of a verify pre-check."""
    passed: bool
    error_type: str  # "import_error", "lint_error", ""
    file_path: str   # file that failed, or ""
    message: str     # human-readable description


def verify_precheck(
    target_path: str,
    changed_files: list[str],
    transport: Transport,
) -> PreCheckResult:
    """Run lightweight import and lint pre-checks on changed Python files.

    Returns a PreCheckResult.  If any check fails the caller should skip
    the LLM-based verify and enter the eval-fix loop directly.
    """
    import sys as _sys

    py_files = [f for f in changed_files if f.endswith(".py")]
    if not py_files:
        return PreCheckResult(passed=True, error_type="", file_path="", message="")

    python_bin = _sys.executable

    for rel_path in py_files:
        full_path = f"{target_path}/{rel_path}"

        # --- import check: compile + import attempt ---
        r = transport.run_shell(
            f"{python_bin} -c \"import py_compile; py_compile.compile('{full_path}', doraise=True)\"",
            cwd=target_path,
            timeout=30,
        )
        if r["exit_code"] != 0:
            output = r.get("stdout", "") + r.get("stderr", "")
            return PreCheckResult(
                passed=False,
                error_type="import_error",
                file_path=rel_path,
                message=f"Import/compile error in {rel_path}: {output[:500]}",
            )

        # --- lint check ---
        r = transport.run_shell(
            f"{python_bin} -m ruff check '{full_path}' 2>&1",
            cwd=target_path,
            timeout=30,
        )
        if r["exit_code"] != 0:
            output = r.get("stdout", "")
            return PreCheckResult(
                passed=False,
                error_type="lint_error",
                file_path=rel_path,
                message=f"Lint error in {rel_path}: {output[:500]}",
            )

    return PreCheckResult(passed=True, error_type="", file_path="", message="")


def diagnose_failure(
    failure_info: dict,
    target_path: str,
    transport: Transport,
) -> DiagnosisReport:
    """Convenience: run the full diagnosis cycle with a fresh Diagnoser."""
    return Diagnoser().diagnose(failure_info, target_path, transport)
