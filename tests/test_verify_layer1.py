"""Unit tests for zsiga.pipeline.verify_layer1 and verify integration."""
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from zsiga.pipeline.verify_layer1 import (
    Layer1Result,
    has_non_testable_scenarios,
    load_layer1_result,
    run_layer1_pytest,
)
from zsiga.pipeline.spec_pytest_check import expected_test_path
from zsiga.transport import LocalTransport


# Use the venv python so pytest-the-module is available when we run the
# nested pytest invocation inside Layer 1.
VENV_PY = sys.executable


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def change_layout(tmp_path: Path):
    target = tmp_path / "target"
    (target / "tests").mkdir(parents=True)
    change_dir = target / "openspec" / "changes" / "demo-change"
    (change_dir / "specs").mkdir(parents=True)
    return {
        "target": str(target),
        "change_dir": str(change_dir),
        "specs_dir": change_dir / "specs",
        "tests_dir": target / "tests",
    }


SPEC_PASSING = """\
### Scenario: dummy passes

- **testable**: true
- **target**: zsiga/pipeline/verify_layer1.py::Layer1Result
- **Given** a value
- **When** asserted
- **Then** ok
"""

SPEC_FAILING = """\
### Scenario: dummy fails

- **testable**: true
- **target**: zsiga/pipeline/verify_layer1.py::Layer1Result
- **Given** a value
- **When** asserted
- **Then** wrong
"""

SPEC_NON_TESTABLE = """\
### Scenario: feels right

- **Given** something
- **When** something
- **Then** feels good
"""

SPEC_MIXED = """\
#### Scenario: testable one

- **testable**: true
- **target**: zsiga/pipeline/verify_layer1.py::Layer1Result
- **Given** x
- **When** y
- **Then** z

#### Scenario: subjective two

- **testable**: false
- **Given** x
- **When** y
- **Then** vibes
"""

GOOD_TEST = """\
def test_passes():
    assert True
"""

BAD_TEST = """\
def test_fails():
    assert False, "intentional failure"
"""


# ---------------------------------------------------------------------------
# Vacuous paths
# ---------------------------------------------------------------------------


def test_no_specs_returns_vacuous_pass(change_layout):
    r = run_layer1_pytest(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    assert r.passed is True
    assert r.vacuous is True
    assert r.scenarios_tested == 0


def test_only_non_testable_scenarios_returns_vacuous_pass(change_layout):
    (change_layout["specs_dir"] / "ux.md").write_text(SPEC_NON_TESTABLE)
    r = run_layer1_pytest(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    assert r.vacuous is True
    assert r.passed is True
    assert r.scenarios_tested == 0


def test_testable_scenarios_no_test_files_returns_vacuous_with_warning(change_layout):
    (change_layout["specs_dir"] / "foo.md").write_text(SPEC_PASSING)
    r = run_layer1_pytest(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    assert r.vacuous is True
    assert r.passed is True
    assert r.scenarios_tested == 1
    assert "no test files" in r.warning or "no matching test" in r.warning


# ---------------------------------------------------------------------------
# Real pytest execution
# ---------------------------------------------------------------------------


def _write_test_for_spec(change_layout, spec_filename, source):
    test_path = expected_test_path(
        change_layout["target"], "demo-change", spec_filename,
    )
    Path(test_path).parent.mkdir(parents=True, exist_ok=True)
    Path(test_path).write_text(source)
    return test_path


def test_passing_test_yields_l1_pass(change_layout):
    (change_layout["specs_dir"] / "p.md").write_text(SPEC_PASSING)
    _write_test_for_spec(change_layout, "p.md", GOOD_TEST)
    r = run_layer1_pytest(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
        venv_python=VENV_PY,
    )
    assert r.vacuous is False
    assert r.passed is True
    assert r.scenarios_tested == 1
    assert r.pytest_exit_code == 0
    assert len(r.test_files) == 1


def test_failing_test_yields_l1_fail(change_layout):
    (change_layout["specs_dir"] / "f.md").write_text(SPEC_FAILING)
    _write_test_for_spec(change_layout, "f.md", BAD_TEST)
    r = run_layer1_pytest(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
        venv_python=VENV_PY,
    )
    assert r.vacuous is False
    assert r.passed is False
    assert r.pytest_exit_code != 0
    assert "intentional failure" in r.pytest_output


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


def test_result_is_persisted_as_json(change_layout):
    (change_layout["specs_dir"] / "p.md").write_text(SPEC_PASSING)
    _write_test_for_spec(change_layout, "p.md", GOOD_TEST)
    run_layer1_pytest(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
        venv_python=VENV_PY,
    )
    json_path = Path(change_layout["change_dir"]) / "verify_layer1.json"
    assert json_path.exists()
    data = json.loads(json_path.read_text())
    assert data["passed"] is True
    assert data["scenarios_tested"] == 1


def test_load_layer1_result_round_trip(change_layout):
    (change_layout["specs_dir"] / "p.md").write_text(SPEC_PASSING)
    _write_test_for_spec(change_layout, "p.md", GOOD_TEST)
    original = run_layer1_pytest(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
        venv_python=VENV_PY,
    )
    loaded = load_layer1_result(change_layout["change_dir"], LocalTransport())
    assert loaded is not None
    assert loaded.passed == original.passed
    assert loaded.scenarios_tested == original.scenarios_tested


def test_load_layer1_result_missing_returns_none(tmp_path):
    assert load_layer1_result(str(tmp_path), LocalTransport()) is None


def test_load_layer1_result_corrupt_json_returns_none(tmp_path):
    (tmp_path / "verify_layer1.json").write_text("{not valid json")
    assert load_layer1_result(str(tmp_path), LocalTransport()) is None


# ---------------------------------------------------------------------------
# has_non_testable_scenarios
# ---------------------------------------------------------------------------


def test_has_non_testable_true_when_no_specs(tmp_path):
    (tmp_path / "specs").mkdir()
    assert has_non_testable_scenarios(str(tmp_path), LocalTransport()) is True


def test_has_non_testable_true_when_mixed(change_layout):
    (change_layout["specs_dir"] / "m.md").write_text(SPEC_MIXED)
    assert has_non_testable_scenarios(
        change_layout["change_dir"], LocalTransport(),
    ) is True


def test_has_non_testable_false_when_all_testable(change_layout):
    (change_layout["specs_dir"] / "p.md").write_text(SPEC_PASSING)
    assert has_non_testable_scenarios(
        change_layout["change_dir"], LocalTransport(),
    ) is False


# ---------------------------------------------------------------------------
# summary_line formatting
# ---------------------------------------------------------------------------


def test_summary_line_vacuous():
    r = Layer1Result(
        passed=True, vacuous=True, scenarios_tested=0,
        warning="some reason",
    )
    line = r.summary_line()
    assert "vacuous" in line
    assert "some reason" in line


def test_summary_line_pass():
    r = Layer1Result(
        passed=True, vacuous=False, scenarios_tested=3,
        test_files=["a.py", "b.py"], pytest_exit_code=0,
    )
    line = r.summary_line()
    assert "L1 PASS" in line
    assert "3 testable" in line


def test_summary_line_fail():
    r = Layer1Result(
        passed=False, vacuous=False, scenarios_tested=2,
        test_files=["a.py"], pytest_exit_code=1,
    )
    line = r.summary_line()
    assert "L1 FAIL" in line
    assert "exit=1" in line


# ---------------------------------------------------------------------------
# verifier.verify integration — pure-L1 fast path
# ---------------------------------------------------------------------------


def test_verify_pure_l1_skips_llm(change_layout):
    """When all scenarios are testable and pytest passes, no LLM call is made."""
    (change_layout["specs_dir"] / "p.md").write_text(SPEC_PASSING)
    _write_test_for_spec(change_layout, "p.md", GOOD_TEST)

    from zsiga.pipeline.verifier import verify, read_verdict

    fake_agent = AsyncMock()
    fake_agent.run = AsyncMock()  # should never be called

    result = asyncio.run(verify(
        agent=fake_agent,
        change_dir=change_layout["change_dir"],
        target_path=change_layout["target"],
        pre_impl_sha="HEAD",
        transport=LocalTransport(),
        venv_python=VENV_PY,
    ))
    fake_agent.run.assert_not_called()
    assert result is None
    verdict = read_verdict(change_layout["change_dir"], LocalTransport())
    assert verdict == "PASS"


def test_verify_pure_l1_fail_writes_fail_verdict(change_layout):
    """All scenarios testable but pytest fails → no LLM, verify.md = FAIL."""
    (change_layout["specs_dir"] / "f.md").write_text(SPEC_FAILING)
    _write_test_for_spec(change_layout, "f.md", BAD_TEST)

    from zsiga.pipeline.verifier import verify, read_verdict

    fake_agent = AsyncMock()
    fake_agent.run = AsyncMock()

    result = asyncio.run(verify(
        agent=fake_agent,
        change_dir=change_layout["change_dir"],
        target_path=change_layout["target"],
        pre_impl_sha="HEAD",
        transport=LocalTransport(),
        venv_python=VENV_PY,
    ))
    fake_agent.run.assert_not_called()
    assert result is None
    assert read_verdict(change_layout["change_dir"], LocalTransport()) == "FAIL"


# ---------------------------------------------------------------------------
# verifier._enforce_l1_verdict — defensive override
# ---------------------------------------------------------------------------


def test_enforce_l1_verdict_overrides_when_l1_fail(change_layout):
    from zsiga.pipeline.verifier import _enforce_l1_verdict

    verify_md = Path(change_layout["change_dir"]) / "verify.md"
    verify_md.write_text(
        "Verdict: PASS\nCompleteness: ✓ ok\n"
    )
    layer1 = Layer1Result(
        passed=False, vacuous=False, scenarios_tested=2,
        test_files=["t.py"], pytest_exit_code=1,
    )
    _enforce_l1_verdict(
        change_layout["change_dir"], LocalTransport(), layer1,
    )
    new = verify_md.read_text()
    assert "Verdict: FAIL" in new
    assert "L1 OVERRIDE" in new


def test_enforce_l1_verdict_noop_when_l1_passed(change_layout):
    from zsiga.pipeline.verifier import _enforce_l1_verdict

    verify_md = Path(change_layout["change_dir"]) / "verify.md"
    original = "Verdict: PASS\nLayer 1: PASS — ok\n"
    verify_md.write_text(original)
    layer1 = Layer1Result(
        passed=True, vacuous=False, scenarios_tested=1, test_files=["t.py"],
    )
    _enforce_l1_verdict(
        change_layout["change_dir"], LocalTransport(), layer1,
    )
    assert verify_md.read_text() == original


def test_enforce_l1_verdict_noop_when_vacuous(change_layout):
    from zsiga.pipeline.verifier import _enforce_l1_verdict

    verify_md = Path(change_layout["change_dir"]) / "verify.md"
    original = "Verdict: PASS\nCompleteness: ✓\n"
    verify_md.write_text(original)
    layer1 = Layer1Result(passed=True, vacuous=True, scenarios_tested=0)
    _enforce_l1_verdict(
        change_layout["change_dir"], LocalTransport(), layer1,
    )
    assert verify_md.read_text() == original
