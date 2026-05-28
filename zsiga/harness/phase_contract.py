"""Phase contract harness for pipeline boundary I/O validation.

This module validates that each major pipeline phase receives the expected
artifacts and produces the artifacts required by the next phase. It is small by
intent: contracts are deterministic, transport-aware, and fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..pipeline.utils import dir_exists, file_exists, list_files_recursive, read_file
from ..transport import Transport


@dataclass
class ContractViolation:
    """Single phase contract violation."""

    phase: str
    field: str
    message: str


@dataclass
class PhaseContractResult:
    """Result from validating a phase boundary contract."""

    phase: str
    passed: bool
    violations: list[ContractViolation] = field(default_factory=list)

    @property
    def message(self) -> str:
        return "; ".join(v.message for v in self.violations)


class PhaseContractError(RuntimeError):
    """Raised when a phase contract is enforced and fails."""

    def __init__(self, result: PhaseContractResult):
        self.result = result
        super().__init__(result.message)


class PhaseContractHarness:
    """Validate phase input/output artifacts and cross-phase invariants."""

    _CLARIFY_SECTIONS = ("需求拆解", "边界", "目标", "约束")

    def validate(
        self,
        phase: str,
        *,
        change_dir: str,
        target_path: str,
        project: str,
        active_target: str,
        transport: Transport,
        context: dict[str, Any] | None = None,
    ) -> PhaseContractResult:
        context = context or {}
        phase_key = phase.lower()
        violations: list[ContractViolation] = []

        self._validate_invariants(
            phase_key, change_dir, target_path, project, active_target, violations
        )

        validators = {
            "clarify": self._validate_clarify,
            "enrich": self._validate_enrich,
            "implement": self._validate_implement,
            "verify": self._validate_verify,
            "reflect": self._validate_reflect,
        }
        validator = validators.get(phase_key)
        if validator is None:
            violations.append(
                ContractViolation(phase_key, "phase", f"unknown phase contract: {phase}")
            )
        else:
            validator(change_dir, target_path, transport, context, violations)

        return PhaseContractResult(phase=phase_key, passed=not violations, violations=violations)

    def enforce(self, phase: str, **kwargs: Any) -> PhaseContractResult:
        result = self.validate(phase, **kwargs)
        if not result.passed:
            raise PhaseContractError(result)
        return result

    def _validate_invariants(
        self,
        phase: str,
        change_dir: str,
        target_path: str,
        project: str,
        active_target: str,
        violations: list[ContractViolation],
    ) -> None:
        if not change_dir or "/openspec/changes/" not in change_dir:
            violations.append(
                ContractViolation(phase, "change_dir", f"invalid change_dir: {change_dir}")
            )
        if not target_path or not change_dir.startswith(target_path.rstrip("/") + "/"):
            violations.append(
                ContractViolation(
                    phase,
                    "target_path",
                    f"change_dir must be inside target_path: {change_dir}",
                )
            )
        if active_target and project != active_target:
            violations.append(
                ContractViolation(
                    phase,
                    "active_target",
                    f"project {project} does not match active_target {active_target}",
                )
            )

    def _require_file(
        self,
        phase: str,
        path: str,
        transport: Transport,
        violations: list[ContractViolation],
    ) -> str:
        content = read_file(path, transport)
        if content is None:
            violations.append(ContractViolation(phase, path, f"missing required file: {path}"))
            return ""
        if not content.strip():
            violations.append(ContractViolation(phase, path, f"empty required file: {path}"))
        return content or ""

    def _validate_clarify(
        self,
        change_dir: str,
        _target_path: str,
        transport: Transport,
        _context: dict[str, Any],
        violations: list[ContractViolation],
    ) -> None:
        self._require_file("clarify", f"{change_dir}/proposal.md", transport, violations)
        clarify = self._require_file("clarify", f"{change_dir}/clarify.md", transport, violations)
        for section in self._CLARIFY_SECTIONS:
            if section not in clarify:
                violations.append(
                    ContractViolation(
                        "clarify", "clarify.md", f"clarify.md missing section: {section}"
                    )
                )

    def _validate_enrich(
        self,
        change_dir: str,
        _target_path: str,
        transport: Transport,
        _context: dict[str, Any],
        violations: list[ContractViolation],
    ) -> None:
        self._require_file("enrich", f"{change_dir}/proposal.md", transport, violations)
        self._require_file("enrich", f"{change_dir}/clarify.md", transport, violations)
        self._require_file("enrich", f"{change_dir}/design.md", transport, violations)
        tasks = self._require_file("enrich", f"{change_dir}/tasks.md", transport, violations)
        if "- [ ]" not in tasks and "- [x]" not in tasks.lower():
            violations.append(
                ContractViolation("enrich", "tasks.md", "tasks.md must contain checkbox tasks")
            )
        specs_dir = f"{change_dir}/specs"
        if not dir_exists(specs_dir, transport):
            violations.append(ContractViolation("enrich", "specs", f"missing specs dir: {specs_dir}"))
        elif not list_files_recursive(specs_dir, "*.md", transport):
            violations.append(ContractViolation("enrich", "specs", "specs dir has no markdown specs"))

    def _validate_implement(
        self,
        change_dir: str,
        target_path: str,
        transport: Transport,
        context: dict[str, Any],
        violations: list[ContractViolation],
    ) -> None:
        self._validate_enrich(change_dir, target_path, transport, context, violations)
        pre_sha = context.get("pre_sha", "")
        if pre_sha:
            result = transport.run_shell(
                f"git diff --name-only {pre_sha} HEAD",
                cwd=target_path,
                timeout=20,
            )
            changed = [line for line in result.get("stdout", "").splitlines() if line.strip()]
            if result.get("exit_code") != 0:
                violations.append(
                    ContractViolation("implement", "git_diff", "cannot inspect implementation diff")
                )
            elif not changed:
                violations.append(
                    ContractViolation("implement", "git_diff", "implementation produced no committed diff")
                )

    def _validate_verify(
        self,
        change_dir: str,
        _target_path: str,
        transport: Transport,
        _context: dict[str, Any],
        violations: list[ContractViolation],
    ) -> None:
        verify = self._require_file("verify", f"{change_dir}/verify.md", transport, violations)
        if "Verdict:" not in verify:
            violations.append(
                ContractViolation("verify", "verify.md", "verify.md missing Verdict line")
            )
        if "PASS" not in verify and "FAIL" not in verify:
            violations.append(
                ContractViolation("verify", "verify.md", "verify.md must contain PASS or FAIL")
            )

    def _validate_reflect(
        self,
        change_dir: str,
        _target_path: str,
        transport: Transport,
        _context: dict[str, Any],
        violations: list[ContractViolation],
    ) -> None:
        if not file_exists(f"{change_dir}/reflect.md", transport):
            violations.append(
                ContractViolation("reflect", "reflect.md", "missing reflect.md after REFLECT")
            )
