"""Layer 1 of the two-layer VERIFY: run mechanical pytest checks against
the testable scenarios produced by ENRICH (P1-5 Phase 3).

A spec scenario is *testable* when it carries
``- **testable**: true`` plus a parseable ``- **target**: <file>::<sym>``
field, and the ENRICH agent has produced a companion test file at
``<target>/tests/test_spec_<change_slug>__<spec_slug>.py``. This module:

1. walks ``<change_dir>/specs/*.md``
2. counts declared-testable scenarios per spec
3. resolves the expected pytest file paths
4. invokes ``<venv_python> -m pytest -x --tb=short -q ...`` on the
   collected files (no network, no Layer-2 LLM call)
5. returns a :class:`Layer1Result` and persists ``verify_layer1.json``
   under the change dir so the eval-fix loop (Phase 4) can pick up the
   structured failure summary without re-running pytest

Vacuous cases (no testable scenarios, or testable scenarios but no test
files on disk) return ``passed=True, vacuous=True`` so the surrounding
verifier knows to defer the verdict to Layer 2.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field

from ..transport import LocalTransport, Transport
from .spec_parser import parse_spec
from .spec_pytest_check import expected_test_path
from .utils import list_files_recursive, read_file


PYTEST_TOTAL_TIMEOUT = 240         # transport-level wall clock
PYTEST_OUTPUT_TAIL = 3000          # stdout tail kept on disk
PYTEST_STDERR_TAIL = 1000


@dataclass
class Layer1Result:
    """Outcome of the mechanical pytest pass."""

    passed: bool
    vacuous: bool
    scenarios_tested: int
    test_files: list[str] = field(default_factory=list)
    pytest_exit_code: int = 0
    pytest_output: str = ""
    pytest_stderr: str = ""
    warning: str = ""

    def summary_line(self) -> str:
        if self.vacuous:
            return (
                "L1 vacuous (no testable scenarios" +
                (f"; warning={self.warning}" if self.warning else "") +
                ")"
            )
        verdict = "PASS" if self.passed else "FAIL"
        return (
            f"L1 {verdict}: {self.scenarios_tested} testable scenarios, "
            f"{len(self.test_files)} test files, exit={self.pytest_exit_code}"
        )

    def to_dict(self) -> dict:
        return asdict(self)


def _persist_result(change_dir: str, transport: Transport, result: Layer1Result) -> None:
    """Persist ``verify_layer1.json`` for the eval-fix loop to consume.

    Failure here is not fatal (the in-memory result is still returned),
    so we trap exceptions and just log a warning to stdout.
    """
    payload = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    target = os.path.join(change_dir, "verify_layer1.json")
    try:
        # Use heredoc form so transport-side shells can write multi-line files.
        transport.run_shell(
            f"cat > '{target}' <<'ZSIGA_LAYER1_EOF'\n"
            f"{payload}\n"
            f"ZSIGA_LAYER1_EOF",
            timeout=10,
        )
    except Exception as exc:  # pragma: no cover - defensive
        print(f"  ⚠ failed to persist verify_layer1.json: {exc}", flush=True)


def load_layer1_result(change_dir: str, transport: Transport | None = None) -> Layer1Result | None:
    """Read back the persisted L1 result, or return ``None`` if missing."""
    transport = transport or LocalTransport()
    raw = read_file(os.path.join(change_dir, "verify_layer1.json"), transport)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    # Guard against schema drift — only consume known fields
    fields = {
        "passed", "vacuous", "scenarios_tested", "test_files",
        "pytest_exit_code", "pytest_output", "pytest_stderr", "warning",
    }
    return Layer1Result(**{k: v for k, v in data.items() if k in fields})


def _collect_layer1_inputs(
    change_dir: str, target_path: str, transport: Transport,
) -> tuple[int, list[str], str]:
    """Return ``(testable_count, existing_test_files, warning)``.

    Walks every spec, sums declared-testable scenarios, and resolves
    which corresponding test files actually exist on disk. ``warning``
    is non-empty when scenarios were declared but their companion test
    file is missing — that case is vacuous-with-warning.
    """
    specs_dir = os.path.join(change_dir, "specs")
    spec_files = list_files_recursive(specs_dir, "*.md", transport)
    if not spec_files:
        return 0, [], ""

    change_id = os.path.basename(os.path.normpath(change_dir))
    testable_count = 0
    test_files_to_run: list[str] = []
    missing: list[str] = []

    for spec_path in spec_files:
        spec_text = read_file(spec_path, transport) or ""
        scenarios = parse_spec(spec_text)
        spec_filename = os.path.basename(spec_path)
        testable = [s for s in scenarios if s.testable]
        if not testable:
            continue
        testable_count += len(testable)
        test_path = expected_test_path(target_path, change_id, spec_filename)
        # Use ``read_file`` to test existence so SSH transports work too
        if read_file(test_path, transport) is not None:
            test_files_to_run.append(test_path)
        else:
            missing.append(spec_filename)

    warning = ""
    if missing and not test_files_to_run:
        warning = (
            f"declared {testable_count} testable scenarios across "
            f"{len(missing)} specs, but no matching test files were "
            f"generated by ENRICH"
        )
    elif missing:
        warning = (
            f"some specs missing companion test files: "
            f"{', '.join(missing[:3])}"
            f"{'...' if len(missing) > 3 else ''}"
        )

    return testable_count, test_files_to_run, warning


def run_layer1_pytest(
    change_dir: str,
    target_path: str,
    transport: Transport | None = None,
    venv_python: str | None = None,
) -> Layer1Result:
    """Run the Layer 1 pytest check; persist & return :class:`Layer1Result`."""
    transport = transport or LocalTransport()

    testable_count, test_files, warning = _collect_layer1_inputs(
        change_dir, target_path, transport,
    )

    if testable_count == 0:
        result = Layer1Result(
            passed=True, vacuous=True, scenarios_tested=0,
            warning=warning,
        )
        _persist_result(change_dir, transport, result)
        return result

    if not test_files:
        result = Layer1Result(
            passed=True, vacuous=True, scenarios_tested=testable_count,
            warning=warning or "no test files on disk",
        )
        _persist_result(change_dir, transport, result)
        return result

    py = venv_python or "python3"
    rel_files = [os.path.relpath(p, target_path) for p in test_files]
    cmd = (
        f"{py} -m pytest -x --tb=short -q --no-header "
        + " ".join(f"'{p}'" for p in rel_files)
    )
    r = transport.run_shell(cmd, cwd=target_path, timeout=PYTEST_TOTAL_TIMEOUT)

    result = Layer1Result(
        passed=(r["exit_code"] == 0),
        vacuous=False,
        scenarios_tested=testable_count,
        test_files=rel_files,
        pytest_exit_code=r["exit_code"],
        pytest_output=(r.get("stdout") or "")[-PYTEST_OUTPUT_TAIL:],
        pytest_stderr=(r.get("stderr") or "")[-PYTEST_STDERR_TAIL:],
        warning=warning,
    )
    _persist_result(change_dir, transport, result)
    return result


def has_non_testable_scenarios(
    change_dir: str, transport: Transport | None = None,
) -> bool:
    """True if any spec scenario in the change is non-testable.

    A spec with zero scenarios still counts as needing Layer 2 (so we
    don't accidentally short-circuit for empty specs).
    """
    transport = transport or LocalTransport()
    specs_dir = os.path.join(change_dir, "specs")
    spec_files = list_files_recursive(specs_dir, "*.md", transport)
    if not spec_files:
        return True
    saw_any_scenario = False
    for spec_path in spec_files:
        spec_text = read_file(spec_path, transport) or ""
        scenarios = parse_spec(spec_text)
        if not scenarios:
            # spec has no scenarios at all — Layer 2 should still inspect
            # its prose
            return True
        saw_any_scenario = True
        for sc in scenarios:
            if not sc.testable:
                return True
    # All specs had only testable scenarios
    return not saw_any_scenario  # if nothing seen, default True so L2 runs
