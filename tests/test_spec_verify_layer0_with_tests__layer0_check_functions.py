"""Spec tests for layer0-check-functions.md.

Covers Layer0Check, Layer0Result, and all check_* functions in
zsiga.pipeline.verify_layer0.
"""
from __future__ import annotations

import os
import re

from zsiga.pipeline.verify_layer0 import (
    Layer0Check,
    Layer0Result,
    Transport,
    check_bac_acceptance,
    check_no_syntax_error,
    check_secret_scan,
    check_spec_file_coverage,
    check_spec_scenario_coverage,
    check_tasks_completion,
    check_testable_not_all_false,
    run_layer0_checks,
)


# ---------------------------------------------------------------------------
# Helpers: FakeTransport that simulates shell commands over a virtual FS
# ---------------------------------------------------------------------------

class FakeTransport(Transport):
    """Transport backed by an in-memory dict of file contents.

    Supports the subset of run_shell commands used by verify_layer0:
      cat, find, git diff --name-only, git diff, cat > (write).
    """

    def __init__(self, files: dict[str, str] | None = None):
        self._files: dict[str, str] = dict(files or {})
        self._diff_content: str = ""
        self._changed_files: list[str] = []
        self.commands: list[tuple[str, dict]] = []

    def add_file(self, path: str, content: str) -> None:
        self._files[path] = content

    def set_diff(self, content: str, changed_files: list[str] | None = None) -> None:
        self._diff_content = content
        self._changed_files = changed_files or []

    def run_shell(self, cmd: str, **kwargs) -> dict:
        self.commands.append((cmd, kwargs))

        # cat 'path'  — read file
        m = re.match(r"^cat\s+'(.+?)'$", cmd)
        if m:
            path = m.group(1)
            if path in self._files:
                return {"exit_code": 0, "stdout": self._files[path], "stderr": ""}
            return {"exit_code": 1, "stdout": "", "stderr": "No such file"}

        # find 'base' -name 'pat' | sort
        m = re.match(r"^find\s+'(.+?)'\s+-name\s+'(.+?)'\s*\|\s*sort$", cmd)
        if m:
            base, pat = m.group(1), m.group(2)
            import fnmatch as _fn
            matches = sorted(
                p for p in self._files
                if p.startswith(base) and _fn.fnmatch(os.path.basename(p), pat)
            )
            return {"exit_code": 0, "stdout": "\n".join(matches), "stderr": ""}

        # git diff --name-only ... (get changed files)
        if "git diff --name-only" in cmd or "git ls-files" in cmd:
            return {
                "exit_code": 0,
                "stdout": "\n".join(self._changed_files),
                "stderr": "",
            }

        # git diff SHA HEAD  (diff content)
        m2 = re.match(r"^git diff\s+\S+\s+HEAD$", cmd)
        if m2:
            return {"exit_code": 0, "stdout": self._diff_content, "stderr": ""}

        # cat > write
        if cmd.startswith("cat > "):
            return {"exit_code": 0, "stdout": "", "stderr": ""}

        return {"exit_code": 0, "stdout": "", "stderr": ""}


# ===================== Scenario tests =====================


def test_layer0_check_construction_and_serialization():
    """Layer0Check stores fields and to_dict returns correct dict."""
    check = Layer0Check(
        id="spec_file_coverage",
        description="desc",
        passed=True,
        evidence="ev",
    )
    d = check.to_dict()
    assert d == {
        "id": "spec_file_coverage",
        "description": "desc",
        "passed": True,
        "evidence": "ev",
    }


def test_layer0_result_mixed_pass_and_fail():
    """Layer0Result aggregates 3 pass + 2 fail correctly."""
    checks = [
        Layer0Check(id="a", description="", passed=True, evidence=""),
        Layer0Check(id="b", description="", passed=True, evidence=""),
        Layer0Check(id="c", description="", passed=True, evidence=""),
        Layer0Check(id="d", description="", passed=False, evidence="err1"),
        Layer0Check(id="e", description="", passed=False, evidence="err2"),
    ]
    result = Layer0Result(checks=checks)

    assert result.all_passed is False
    assert result.passed_count == 3
    assert result.total_count == 5
    assert len(result.failed_checks) == 2
    assert result.failed_checks[0].id == "d"
    assert result.failed_checks[1].id == "e"


def test_layer0_result_all_pass():
    """Layer0Result with all passing checks has all_passed=True."""
    checks = [
        Layer0Check(id="x", description="", passed=True, evidence=""),
        Layer0Check(id="y", description="", passed=True, evidence=""),
    ]
    result = Layer0Result(checks=checks)

    assert result.all_passed is True
    assert result.passed_count == 2
    assert result.failed_checks == []


def test_spec_file_coverage_pass():
    """check_spec_file_coverage passes when spec keywords match diff."""
    t = FakeTransport()
    # Spec file with title containing "budget"
    t.add_file(
        "/tmp/change/specs/phase-cap-budget.md",
        "# Phase Cap Budget\n\nSome spec content.",
    )
    # Diff content and changed files with "budget" keyword
    t.set_diff("def token_budget(): pass", changed_files=["zsiga/token_budget.py"])

    result = check_spec_file_coverage("/tmp/change", "/tmp/target", "abc123", t)
    assert result.passed is True
    assert result.id == "spec_file_coverage"


def test_spec_file_coverage_fail():
    """check_spec_file_coverage fails when spec has no matching diff."""
    t = FakeTransport()
    # Multiple spec files with keywords that won't match
    t.add_file("/tmp/change/specs/phase-cap-config.md", "# Config\n")
    t.add_file("/tmp/change/specs/phase-cap-loop.md", "# Loop\n")
    t.add_file("/tmp/change/specs/phase-cap-orchestration.md", "# Orchestration\n")
    # Diff with unrelated changes
    t.set_diff("def unrelated(): pass", changed_files=["zsiga/unrelated.py"])

    result = check_spec_file_coverage("/tmp/change", "/tmp/target", "abc123", t)
    assert result.passed is False
    assert "未覆盖" in result.evidence or "uncovered" in result.evidence.lower()


def test_tasks_completion_pass():
    """check_tasks_completion passes when all tasks are checked."""
    t = FakeTransport()
    t.add_file("/tmp/change/tasks.md", "- [x] Task 1\n- [x] Task 2\n")

    result = check_tasks_completion("/tmp/change", t)
    assert result.passed is True
    assert result.id == "tasks_completion"


def test_tasks_completion_fail():
    """check_tasks_completion fails when unchecked tasks exist."""
    t = FakeTransport()
    t.add_file("/tmp/change/tasks.md", "- [x] Done\n- [ ] Pending\n")

    result = check_tasks_completion("/tmp/change", t)
    assert result.passed is False
    assert "未完成" in result.evidence or "1" in result.evidence


def test_tasks_completion_empty():
    """check_tasks_completion passes with skip when no tasks.md exists."""
    t = FakeTransport()  # no files added

    result = check_tasks_completion("/tmp/change", t)
    assert result.passed is True
    assert "跳过" in result.evidence


def test_testable_not_all_false_pass():
    """check_testable_not_all_false passes when at least one testable=true."""
    t = FakeTransport()
    t.add_file(
        "/tmp/change/specs/test.md",
        "#### Scenario: foo\n\n- **testable**: true\n- **target**: a.py::b\n"
        "- **Given** x\n- **When** y\n- **Then** z\n",
    )

    result = check_testable_not_all_false("/tmp/change", t)
    assert result.passed is True


def test_testable_not_all_false_fail():
    """check_testable_not_all_false fails when all scenarios are testable=false."""
    t = FakeTransport()
    t.add_file(
        "/tmp/change/specs/test.md",
        "#### Scenario: foo\n\n- **testable**: false\n"
        "- **Given** x\n- **When** y\n- **Then** z\n",
    )

    result = check_testable_not_all_false("/tmp/change", t)
    assert result.passed is False


def test_no_syntax_error_pass():
    """check_no_syntax_error passes with valid Python source."""
    t = FakeTransport()
    t.add_file("/tmp/target/valid.py", "x = 1\n")
    t.set_diff("", changed_files=["valid.py"])

    result = check_no_syntax_error("/tmp/target", "abc123", t)
    assert result.passed is True
    assert result.id == "no_syntax_error"


def test_no_syntax_error_fail():
    """check_no_syntax_error fails with invalid Python source."""
    t = FakeTransport()
    t.add_file("/tmp/target/bad.py", "def foo(\n")
    t.set_diff("", changed_files=["bad.py"])

    result = check_no_syntax_error("/tmp/target", "abc123", t)
    assert result.passed is False


def test_spec_scenario_coverage_pass():
    """check_spec_scenario_coverage passes when SHALL terms appear in diff."""
    t = FakeTransport()
    t.add_file(
        "/tmp/change/specs/phase-cap.md",
        "### Requirement: Phase Cap\n\nThe system SHALL provide phase_cap.\n",
    )
    t.set_diff("+ def phase_cap(): pass", changed_files=["zsiga/cap.py"])

    result = check_spec_scenario_coverage("/tmp/change", "/tmp/target", "abc123", t)
    assert result.passed is True


def test_spec_scenario_coverage_fail():
    """check_spec_scenario_coverage fails when SHALL terms are absent from diff."""
    t = FakeTransport()
    t.add_file(
        "/tmp/change/specs/phase-cap.md",
        "### Requirement: Phase Cap\n\nThe system SHALL provide get_phase_cap.\n",
    )
    t.set_diff("+ def unrelated(): pass", changed_files=["zsiga/other.py"])

    result = check_spec_scenario_coverage("/tmp/change", "/tmp/target", "abc123", t)
    assert result.passed is False


def test_bac_acceptance_symbol_exists():
    """check_bac_acceptance passes when BAC symbol exists in source."""
    t = FakeTransport()
    # BAC format requires backtick-quoted file and symbol names
    t.add_file(
        "/tmp/change/proposal.md",
        "## Acceptance Criteria\n"
        "- [BAC-01] `config.py` 中存在 `PHASE_TOKEN_CAPS`\n",
    )
    t.add_file("/tmp/target/config.py", "PHASE_TOKEN_CAPS = {}\n")
    t.set_diff("", changed_files=[])

    checks = check_bac_acceptance("/tmp/change", "/tmp/target", "abc123", t)
    assert len(checks) >= 1
    assert checks[0].passed is True
    assert "PHASE_TOKEN_CAPS" in checks[0].evidence


def test_bac_acceptance_symbol_missing():
    """check_bac_acceptance fails when BAC symbol is absent from source."""
    t = FakeTransport()
    # BAC format requires backtick-quoted file and symbol names
    t.add_file(
        "/tmp/change/proposal.md",
        "## Acceptance Criteria\n"
        "- [BAC-01] `loop.py` 中存在 `handle_cap_exceeded`\n",
    )
    t.add_file("/tmp/target/loop.py", "def other_function(): pass\n")
    t.set_diff("", changed_files=[])

    checks = check_bac_acceptance("/tmp/change", "/tmp/target", "abc123", t)
    assert len(checks) >= 1
    assert checks[0].passed is False


def test_run_layer0_checks_all_pass():
    """run_layer0_checks returns all_passed=True when no specs or tasks."""
    t = FakeTransport()
    # Empty change_dir: no specs, no tasks, no BAC -> all skip/pass

    result = run_layer0_checks("/tmp/change", "/tmp/target", "abc123", transport=t)
    assert result.all_passed is True


def test_secret_scan_blocks_added_api_key():
    t = FakeTransport()
    t.set_diff(
        "diff --git a/app.py b/app.py\n"
        "+++ b/app.py\n"
        "+api_key = 'live_abcdefghijklmnopqrstuvwxyz123456'\n",
        changed_files=["app.py"],
    )
    result = run_layer0_checks("/tmp/change", "/tmp/target", "abc123", transport=t)
    failed_ids = [c.id for c in result.failed_checks]
    assert "secret_scan" in failed_ids


def test_secret_scan_ignores_env_placeholder():
    check = check_secret_scan(
        snapshot=type(
            "Snapshot",
            (),
            {"diff_content": "+++ b/zsiga.yaml\n+api_key: ${ZHIPUAI_API_KEY}\n"},
        )(),
    )
    assert check.passed is True


def test_run_layer0_checks_partial_fail():
    """run_layer0_checks detects failure when tasks.md has unchecked items."""
    t = FakeTransport()
    t.add_file("/tmp/change/tasks.md", "- [ ] pending task\n")

    result = run_layer0_checks("/tmp/change", "/tmp/target", "abc123", transport=t)
    assert result.all_passed is False
    failed_ids = [c.id for c in result.failed_checks]
    assert "tasks_completion" in failed_ids
