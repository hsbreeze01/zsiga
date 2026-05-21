"""Tests for Phase 4: Layer 1 failure block in _build_eval_fix_structured_ctx."""
import json
from pathlib import Path
from types import SimpleNamespace

from zsiga.pipeline.orchestrator import ZsigaOrchestrator
from zsiga.transport import LocalTransport


def _bind_helper(missed=None, coverage=1.0):
    """Build a stand-in orchestrator instance with just enough surface
    for _build_eval_fix_structured_ctx to run."""
    inst = SimpleNamespace()
    inst._last_must_modify_missed = missed or []
    inst._last_must_modify_coverage = coverage
    inst._build_eval_fix_structured_ctx = (
        ZsigaOrchestrator._build_eval_fix_structured_ctx.__get__(inst)
    )
    return inst


def _write_layer1_json(change_dir: Path, **fields):
    payload = {
        "passed": False,
        "vacuous": False,
        "scenarios_tested": 1,
        "test_files": ["tests/test_spec_demo__foo.py"],
        "pytest_exit_code": 1,
        "pytest_output": "FAILED tests/test_spec_demo__foo.py::test_x\n>       assert False\n",
        "pytest_stderr": "",
        "warning": "",
    }
    payload.update(fields)
    (change_dir / "verify_layer1.json").write_text(json.dumps(payload))


def test_includes_layer1_block_when_l1_failed(tmp_path: Path):
    _write_layer1_json(tmp_path)
    inst = _bind_helper()
    out = inst._build_eval_fix_structured_ctx(str(tmp_path), LocalTransport())
    assert "LAYER 1 pytest 失败" in out
    assert "tests/test_spec_demo__foo.py" in out
    assert "pytest exit code: 1" in out
    assert "assert False" in out


def test_no_layer1_block_when_l1_passed(tmp_path: Path):
    _write_layer1_json(tmp_path, passed=True, pytest_exit_code=0, pytest_output="1 passed")
    inst = _bind_helper()
    out = inst._build_eval_fix_structured_ctx(str(tmp_path), LocalTransport())
    assert "LAYER 1 pytest" not in out


def test_no_layer1_block_when_vacuous(tmp_path: Path):
    _write_layer1_json(tmp_path, vacuous=True, passed=True, pytest_exit_code=0)
    inst = _bind_helper()
    out = inst._build_eval_fix_structured_ctx(str(tmp_path), LocalTransport())
    assert "LAYER 1 pytest" not in out


def test_no_layer1_block_when_json_missing(tmp_path: Path):
    inst = _bind_helper()
    out = inst._build_eval_fix_structured_ctx(str(tmp_path), LocalTransport())
    # neither layer1 nor must-modify nor review → empty string
    assert out == ""


def test_no_layer1_block_when_corrupt_json(tmp_path: Path):
    (tmp_path / "verify_layer1.json").write_text("{broken json")
    inst = _bind_helper()
    out = inst._build_eval_fix_structured_ctx(str(tmp_path), LocalTransport())
    assert "LAYER 1 pytest" not in out


def test_layer1_block_combined_with_must_modify(tmp_path: Path):
    _write_layer1_json(tmp_path)
    inst = _bind_helper(missed=["zsiga/foo.py"], coverage=0.5)
    out = inst._build_eval_fix_structured_ctx(str(tmp_path), LocalTransport())
    assert "MUST-MODIFY" in out
    assert "LAYER 1 pytest" in out
    # Order: missed first, then review (none here), then layer1
    assert out.index("MUST-MODIFY") < out.index("LAYER 1")


def test_layer1_block_combined_with_review_critical(tmp_path: Path):
    _write_layer1_json(tmp_path)
    (tmp_path / "review.md").write_text(
        "Verdict: ISSUES_FOUND\n\nIssues:\n1. [CRITICAL] missing import in zsiga/x.py\n"
    )
    inst = _bind_helper()
    out = inst._build_eval_fix_structured_ctx(str(tmp_path), LocalTransport())
    assert "REVIEW 标记的 CRITICAL" in out
    assert "missing import" in out
    assert "LAYER 1 pytest" in out
    assert out.index("REVIEW") < out.index("LAYER 1")


def test_pytest_output_truncated_to_1500_chars(tmp_path: Path):
    huge = "x" * 5000
    _write_layer1_json(tmp_path, pytest_output=huge)
    inst = _bind_helper()
    out = inst._build_eval_fix_structured_ctx(str(tmp_path), LocalTransport())
    # The injected block contains at most 1500 + framing chars
    block_start = out.index("LAYER 1 pytest")
    block = out[block_start:]
    # Strict bound: less than 2500 chars total for the block
    assert len(block) < 2500
