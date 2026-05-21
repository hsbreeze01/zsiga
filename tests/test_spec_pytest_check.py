"""Unit tests for zsiga.pipeline.spec_pytest_check."""
from pathlib import Path

import pytest

from zsiga.pipeline.spec_pytest_check import (
    CONFTEST_ZSIGA,
    SpecPytestReport,
    _demote_in_spec,
    _slugify,
    ensure_conftest,
    expected_test_path,
    validate_testable_artifacts,
)
from zsiga.transport import LocalTransport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def change_layout(tmp_path: Path):
    """Create change_dir + target_path skeleton."""
    target = tmp_path / "target_proj"
    (target / "tests").mkdir(parents=True)

    change_dir = target / "openspec" / "changes" / "demo-change-id"
    (change_dir / "specs").mkdir(parents=True)

    return {
        "tmp": tmp_path,
        "target": str(target),
        "change_dir": str(change_dir),
        "specs_dir": change_dir / "specs",
    }


SPEC_ONE_TESTABLE = """\
# Spec foo

## ADDED Requirements

### Requirement: validate_email rejects empty

#### Scenario: empty email

- **testable**: true
- **target**: src/email.py::validate_email
- **contract**:
    params:
      addr: str
    returns: bool
- **Given** an empty string
- **When** validate_email("") is called
- **Then** returns False
"""

SPEC_ONE_NOT_TESTABLE = """\
# Spec bar

### Scenario: ux feels snappy

- **Given** a button
- **When** clicked
- **Then** feels snappy
"""

SPEC_MIXED = """\
# Spec mix

#### Scenario: testable one

- **testable**: true
- **target**: zsiga/foo.py::bar
- **contract**:
    params:
      x: int
    returns: int
- **Given** x
- **When** y
- **Then** z

#### Scenario: not testable two

- **testable**: false
- **Given** x
- **When** y
- **Then** subjective
"""

GOOD_TEST_SOURCE = """\
def test_validate_email_rejects_empty():
    # Phase 1 just checks compile, not run
    assert (lambda: False)() is False
"""

BROKEN_TEST_SOURCE = """\
def test_validate_email_rejects_empty(:
    assert False
"""


# ---------------------------------------------------------------------------
# _slugify / expected_test_path
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("phase-progress-bar", "phase_progress_bar"),
        ("Some Spec.md", "some_spec_md"),
        ("---weird---", "weird"),
        ("", "x"),
    ],
)
def test_slugify(raw, expected):
    assert _slugify(raw) == expected


def test_expected_test_path_combines_change_and_spec():
    p = expected_test_path("/proj", "dashboard-X", "phase-progress-bar.md")
    assert p == "/proj/tests/test_spec_dashboard_x__phase_progress_bar.py"


# ---------------------------------------------------------------------------
# _demote_in_spec
# ---------------------------------------------------------------------------


def test_demote_in_spec_replaces_first_testable_line():
    out = _demote_in_spec(SPEC_ONE_TESTABLE, "empty email", "test missing")
    # original true line gone
    assert "**testable**: true" not in out
    # demoted line in
    assert "**testable**: false  <!-- demoted by zsiga: test missing -->" in out
    # other content preserved
    assert "validate_email" in out
    assert "src/email.py::validate_email" in out


def test_demote_in_spec_only_touches_named_scenario():
    out = _demote_in_spec(SPEC_MIXED, "testable one", "fail")
    # The targeted line was demoted
    assert "demoted by zsiga: fail" in out
    # The other scenario's "testable: false" line is untouched (no demoted comment)
    second_block = out.split("Scenario: not testable two", 1)[1]
    assert "demoted by zsiga" not in second_block


def test_demote_in_spec_returns_input_when_scenario_not_found():
    assert _demote_in_spec(SPEC_ONE_TESTABLE, "nonexistent", "x") == SPEC_ONE_TESTABLE


# ---------------------------------------------------------------------------
# ensure_conftest
# ---------------------------------------------------------------------------


def test_ensure_conftest_writes_when_missing(change_layout):
    written = ensure_conftest(change_layout["target"], LocalTransport())
    assert written is True
    p = Path(change_layout["target"]) / "tests" / "conftest_zsiga.py"
    assert p.exists()
    assert "tmp_repo" in p.read_text()
    assert "mock_transport" in p.read_text()


def test_ensure_conftest_skips_when_present(change_layout):
    p = Path(change_layout["target"]) / "tests" / "conftest_zsiga.py"
    p.write_text("# pre-existing\n")
    written = ensure_conftest(change_layout["target"], LocalTransport())
    assert written is False
    # original content preserved
    assert p.read_text() == "# pre-existing\n"


def test_conftest_template_compiles():
    """The shipped CONFTEST_ZSIGA template must itself be valid Python."""
    import ast
    ast.parse(CONFTEST_ZSIGA)


# ---------------------------------------------------------------------------
# validate_testable_artifacts — happy path
# ---------------------------------------------------------------------------


def test_validate_with_no_specs_returns_empty_report(change_layout):
    report = validate_testable_artifacts(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    assert isinstance(report, SpecPytestReport)
    assert report.total_testable_declared == 0
    assert report.total_demoted == 0


def test_validate_legacy_spec_no_demotion(change_layout):
    """Spec without testable=true triggers no test-file expectation."""
    (change_layout["specs_dir"] / "ux.md").write_text(SPEC_ONE_NOT_TESTABLE)
    report = validate_testable_artifacts(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    assert report.total_testable_declared == 0
    assert report.total_demoted == 0
    assert report.conftest_written is True   # tests/ folder exists, conftest absent


def test_validate_with_good_test_file_validates(change_layout):
    (change_layout["specs_dir"] / "email.md").write_text(SPEC_ONE_TESTABLE)
    test_path = expected_test_path(
        change_layout["target"], "demo-change-id", "email.md",
    )
    Path(test_path).parent.mkdir(parents=True, exist_ok=True)
    Path(test_path).write_text(GOOD_TEST_SOURCE)

    report = validate_testable_artifacts(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    assert report.total_testable_declared == 1
    assert report.total_testable_validated == 1
    assert report.total_demoted == 0
    # spec untouched
    spec_text = (change_layout["specs_dir"] / "email.md").read_text()
    assert "**testable**: true" in spec_text
    assert "demoted" not in spec_text


# ---------------------------------------------------------------------------
# validate_testable_artifacts — demotion paths
# ---------------------------------------------------------------------------


def test_validate_with_missing_test_file_demotes(change_layout):
    (change_layout["specs_dir"] / "email.md").write_text(SPEC_ONE_TESTABLE)

    report = validate_testable_artifacts(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    assert report.total_testable_declared == 1
    assert report.total_testable_validated == 0
    assert report.total_demoted == 1

    spec_text = (change_layout["specs_dir"] / "email.md").read_text()
    assert "**testable**: true" not in spec_text
    assert "**testable**: false" in spec_text
    assert "test file missing" in spec_text


def test_validate_with_broken_test_file_deletes_and_demotes(change_layout):
    (change_layout["specs_dir"] / "email.md").write_text(SPEC_ONE_TESTABLE)
    test_path = expected_test_path(
        change_layout["target"], "demo-change-id", "email.md",
    )
    Path(test_path).parent.mkdir(parents=True, exist_ok=True)
    Path(test_path).write_text(BROKEN_TEST_SOURCE)

    report = validate_testable_artifacts(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    assert report.total_demoted == 1
    # Broken test file should be gone
    assert not Path(test_path).exists()
    # Spec scenario demoted with compile reason
    spec_text = (change_layout["specs_dir"] / "email.md").read_text()
    assert "compile failed" in spec_text


def test_validate_mixed_specs_demotes_only_affected(change_layout):
    """One spec has good test, another spec has missing test —
    demote only happens on the second."""
    (change_layout["specs_dir"] / "email.md").write_text(SPEC_ONE_TESTABLE)
    test_path = expected_test_path(
        change_layout["target"], "demo-change-id", "email.md",
    )
    Path(test_path).parent.mkdir(parents=True, exist_ok=True)
    Path(test_path).write_text(GOOD_TEST_SOURCE)

    (change_layout["specs_dir"] / "missing.md").write_text(SPEC_ONE_TESTABLE)
    # Note: missing.md uses same scenario name "empty email" — we
    # purposely don't create its test file.

    report = validate_testable_artifacts(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    assert report.total_testable_declared == 2
    assert report.total_testable_validated == 1
    assert report.total_demoted == 1

    # email.md untouched, missing.md demoted
    assert "demoted" not in (change_layout["specs_dir"] / "email.md").read_text()
    assert "demoted" in (change_layout["specs_dir"] / "missing.md").read_text()


# ---------------------------------------------------------------------------
# Report summary
# ---------------------------------------------------------------------------


def test_summary_line_format(change_layout):
    (change_layout["specs_dir"] / "email.md").write_text(SPEC_ONE_TESTABLE)
    report = validate_testable_artifacts(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    line = report.summary_line()
    assert "spec→pytest" in line or "spec\u2192pytest" in line
    assert "0/1" in line or "0 / 1" in line  # 0 validated of 1 declared
    assert "1 demoted" in line



# ---------------------------------------------------------------------------
# Phase 6: contract-presence demotion (strict mode)
# ---------------------------------------------------------------------------


SPEC_TESTABLE_NO_CONTRACT = """\
### Scenario: testable but no contract

- **testable**: true
- **target**: src/legacy.py::do_thing
- **Given** an input
- **When** do_thing("x") is called
- **Then** something happens
"""


def test_phase6_strict_demotes_testable_without_contract(change_layout):
    """Default (allow_inferred_contract=False) demotes any testable
    scenario that lacks a `contract:` block."""
    (change_layout["specs_dir"] / "no_contract.md").write_text(
        SPEC_TESTABLE_NO_CONTRACT
    )
    report = validate_testable_artifacts(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    assert report.total_testable_declared == 1
    assert report.total_testable_validated == 0
    assert report.total_demoted == 1
    spec_text = (change_layout["specs_dir"] / "no_contract.md").read_text()
    assert "**testable**: false" in spec_text
    assert "missing contract" in spec_text


def test_phase6_strict_does_not_demote_when_contract_present(change_layout):
    """Scenarios with a contract block survive strict mode and proceed
    to the normal test-file existence check (which then demotes for the
    expected `test file missing` reason)."""
    (change_layout["specs_dir"] / "email.md").write_text(SPEC_ONE_TESTABLE)
    report = validate_testable_artifacts(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    assert report.total_testable_declared == 1
    assert report.total_demoted == 1
    # demotion reason should be test-file-missing, NOT missing-contract
    spec_text = (change_layout["specs_dir"] / "email.md").read_text()
    assert "test file missing" in spec_text
    assert "missing contract" not in spec_text


def test_phase6_allow_inferred_contract_escape_hatch(change_layout):
    """When the project explicitly opts into the legacy inferred-signature
    path, scenarios without contract are NOT demoted by Phase-6 logic;
    they fall through to the normal test-file check."""
    (change_layout["specs_dir"] / "no_contract.md").write_text(
        SPEC_TESTABLE_NO_CONTRACT
    )
    report = validate_testable_artifacts(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
        allow_inferred_contract=True,
    )
    assert report.total_testable_declared == 1
    # Demoted, but reason is missing-test-file (not missing-contract)
    assert report.total_demoted == 1
    spec_text = (change_layout["specs_dir"] / "no_contract.md").read_text()
    assert "test file missing" in spec_text
    assert "missing contract" not in spec_text


def test_phase6_strict_demotes_only_no_contract_in_mixed_spec(change_layout):
    """One testable+contract scenario passes; one testable-no-contract
    scenario gets demoted; the false scenario is untouched."""
    spec = (
        SPEC_MIXED
        + "\n\n#### Scenario: testable but no contract\n\n"
        + "- **testable**: true\n"
        + "- **target**: zsiga/baz.py::qux\n"
        + "- **Given** x\n"
        + "- **When** y\n"
        + "- **Then** z\n"
    )
    (change_layout["specs_dir"] / "mix.md").write_text(spec)
    report = validate_testable_artifacts(
        change_layout["change_dir"], change_layout["target"], LocalTransport(),
    )
    # 2 declared testable; 1 (no contract) demoted by Phase 6, the other
    # also demoted because no test file.
    assert report.total_testable_declared == 2
    spec_text = (change_layout["specs_dir"] / "mix.md").read_text()
    assert "missing contract" in spec_text  # the no-contract scenario got demoted
    # the false scenario is unchanged
    assert spec_text.count("**testable**: false") >= 2  # original false + demoted no-contract



# ---------------------------------------------------------------------------
# Phase 6: conftest ruff_runner fixture
# ---------------------------------------------------------------------------


def test_conftest_template_includes_ruff_runner():
    """The shipped conftest_zsiga.py must offer a ruff_runner fixture
    that uses shutil.which + pytest.skip when ruff is unavailable."""
    from zsiga.pipeline.spec_pytest_check import CONFTEST_ZSIGA
    assert "def ruff_runner" in CONFTEST_ZSIGA
    assert "shutil.which" in CONFTEST_ZSIGA
    assert 'pytest.skip("ruff binary not on PATH' in CONFTEST_ZSIGA

