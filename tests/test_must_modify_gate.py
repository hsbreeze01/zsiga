"""Unit tests for the must-modify gate (Tier 1) helpers + structured
   eval-fix context builder (Tier 5)."""
from types import SimpleNamespace

import pytest

from zsiga.pipeline.utils import must_modify_coverage


# ---- Tier 1 helpers ------------------------------------------------------


def test_coverage_full_hit():
    cov, missed = must_modify_coverage(["a.py", "b.py"], ["a.py", "b.py", "c.py"])
    assert cov == 1.0
    assert missed == []


def test_coverage_partial_hit():
    cov, missed = must_modify_coverage(["a.py", "b.py", "c.py"], ["a.py", "b.py"])
    assert cov == pytest.approx(2 / 3)
    assert missed == ["c.py"]


def test_coverage_zero_hit():
    cov, missed = must_modify_coverage(["a.py", "b.py"], ["other.py"])
    assert cov == 0.0
    assert missed == ["a.py", "b.py"]


def test_coverage_empty_must_files_returns_full_coverage():
    cov, missed = must_modify_coverage([], ["a.py"])
    assert cov == 1.0
    assert missed == []


def test_coverage_preserves_must_file_order_in_missed():
    cov, missed = must_modify_coverage(
        ["zsiga/x.py", "tests/test_x.py", "zsiga/y.py"],
        ["zsiga/x.py"],
    )
    assert cov == pytest.approx(1 / 3)
    assert missed == ["tests/test_x.py", "zsiga/y.py"]


# ---- Tier 5: _build_eval_fix_structured_ctx ------------------------------
# We construct a minimal stand-in for ZsigaOrchestrator and exercise the
# helper directly; this keeps the test independent of LLM / git plumbing.


class _StubTransport:
    """Just enough Transport surface for read_file()."""

    def __init__(self, files: dict[str, str]):
        self.files = files

    def run_shell(self, cmd, **_):
        # read_file calls `cat <path>` — pull path out of the cmd
        # (works for our LocalTransport-like helper).
        if cmd.startswith("cat "):
            path = cmd.split("cat ", 1)[1].strip().strip("'\"")
            content = self.files.get(path)
            if content is None:
                return {"exit_code": 1, "stdout": "", "stderr": "no such file"}
            return {"exit_code": 0, "stdout": content, "stderr": ""}
        return {"exit_code": 0, "stdout": "", "stderr": ""}


def _build_stub_orchestrator(missed=None, coverage=1.0, review_md=None, change_dir="/c"):
    from zsiga.pipeline.orchestrator import ZsigaOrchestrator

    inst = SimpleNamespace()
    inst._last_must_modify_missed = missed or []
    inst._last_must_modify_coverage = coverage
    inst._build_eval_fix_structured_ctx = (
        ZsigaOrchestrator._build_eval_fix_structured_ctx.__get__(inst)
    )
    files = {}
    if review_md is not None:
        files[f"{change_dir}/review.md"] = review_md
    return inst, _StubTransport(files), change_dir


def test_structured_ctx_empty_when_nothing_to_report():
    inst, tr, cd = _build_stub_orchestrator()
    assert inst._build_eval_fix_structured_ctx(cd, tr) == ""


def test_structured_ctx_includes_missed_files_block():
    inst, tr, cd = _build_stub_orchestrator(
        missed=["zsiga/foo.py", "tests/test_foo.py"], coverage=0.5,
    )
    out = inst._build_eval_fix_structured_ctx(cd, tr)
    assert "MUST-MODIFY 仍未覆盖的文件" in out
    assert "coverage=50%" in out
    assert "`zsiga/foo.py`" in out
    assert "`tests/test_foo.py`" in out


def test_structured_ctx_includes_review_critical_only():
    review = (
        "Verdict: ISSUES_FOUND\n\n"
        "Issues:\n"
        "1. [CRITICAL] missing import in zsiga/foo.py\n"
        "2. [SUGGESTION] consider renaming variable x\n"
        "3. [CRITICAL] dashboard.py phase table empty\n"
    )
    inst, tr, cd = _build_stub_orchestrator(review_md=review)
    out = inst._build_eval_fix_structured_ctx(cd, tr)
    assert "REVIEW 标记的 CRITICAL 问题" in out
    assert "missing import in zsiga/foo.py" in out
    assert "dashboard.py phase table empty" in out
    # SUGGESTION lines must NOT leak into the eval-fix context
    assert "consider renaming variable" not in out


def test_structured_ctx_combines_missed_and_review():
    review = "1. [CRITICAL] something broken in zsiga/bar.py"
    inst, tr, cd = _build_stub_orchestrator(
        missed=["zsiga/bar.py"], coverage=0.0, review_md=review,
    )
    out = inst._build_eval_fix_structured_ctx(cd, tr)
    assert "MUST-MODIFY" in out and "REVIEW 标记的 CRITICAL" in out


def test_structured_ctx_caps_critical_lines_at_5():
    review = "\n".join(
        f"{i}. [CRITICAL] issue number {i}" for i in range(1, 9)
    )
    inst, tr, cd = _build_stub_orchestrator(review_md=review)
    out = inst._build_eval_fix_structured_ctx(cd, tr)
    assert "issue number 1" in out
    assert "issue number 5" in out
    assert "issue number 6" not in out
