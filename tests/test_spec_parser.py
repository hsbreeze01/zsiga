"""Unit tests for zsiga.pipeline.spec_parser."""
import pytest

from zsiga.pipeline.spec_parser import (
    Scenario,
    TargetRef,
    UnsupportedTargetKind,
    collect_testable,
    parse_spec,
    parse_target,
)


# ---------------------------------------------------------------------------
# parse_target
# ---------------------------------------------------------------------------


class TestParseTarget:
    def test_simple_function(self):
        ref = parse_target("src/email.py::validate_email")
        assert ref == TargetRef(
            file="src/email.py", symbol="validate_email", kind="python",
        )
        assert ref.is_method is False

    def test_class_method(self):
        ref = parse_target("zsiga/pipeline/orchestrator.py::ZsigaOrchestrator.run")
        assert ref.file == "zsiga/pipeline/orchestrator.py"
        assert ref.symbol == "ZsigaOrchestrator.run"
        assert ref.is_method is True

    def test_strips_whitespace(self):
        ref = parse_target("  zsiga/foo.py::bar  ")
        assert ref.file == "zsiga/foo.py"
        assert ref.symbol == "bar"

    def test_cli_kind_raises_unsupported(self):
        with pytest.raises(UnsupportedTargetKind):
            parse_target("cli:zsiga harness run")

    def test_http_kind_raises_unsupported(self):
        with pytest.raises(UnsupportedTargetKind):
            parse_target("http:GET /api/health")

    def test_missing_file_extension_rejected(self):
        with pytest.raises(ValueError):
            parse_target("src/email::validate_email")

    def test_missing_double_colon_rejected(self):
        with pytest.raises(ValueError):
            parse_target("src/email.py:validate_email")

    def test_empty_target_rejected(self):
        with pytest.raises(ValueError):
            parse_target("")

    def test_whitespace_only_target_rejected(self):
        with pytest.raises(ValueError):
            parse_target("   ")


# ---------------------------------------------------------------------------
# parse_spec — basic shapes
# ---------------------------------------------------------------------------


SPEC_NO_SCENARIOS = """
# Spec: nothing here

Just some prose, no Scenario heading.
"""


def test_spec_without_scenarios_returns_empty():
    assert parse_spec(SPEC_NO_SCENARIOS) == []


def test_empty_input_returns_empty():
    assert parse_spec("") == []


SPEC_LEGACY_NO_TESTABLE = """
### Scenario: dirty tree before checkout

- **Given** working tree has uncommitted file
- **When** pre_checkout_cleanup() is called
- **Then** git status --porcelain returns empty
"""


def test_legacy_scenario_defaults_to_not_testable():
    out = parse_spec(SPEC_LEGACY_NO_TESTABLE)
    assert len(out) == 1
    sc = out[0]
    assert sc.name == "dirty tree before checkout"
    assert sc.testable is False
    assert sc.target is None
    assert "uncommitted file" in sc.given
    assert "pre_checkout_cleanup" in sc.when
    assert "porcelain" in sc.then


SPEC_TESTABLE_TRUE = """
#### Scenario: validate empty email rejected

- **testable**: true
- **target**: src/email.py::validate_email
- **Given** an empty email string
- **When** validate_email("") is called
- **Then** the result SHALL be False
"""


def test_testable_true_with_python_target():
    out = parse_spec(SPEC_TESTABLE_TRUE)
    assert len(out) == 1
    sc = out[0]
    assert sc.testable is True
    assert sc.target == TargetRef(
        file="src/email.py", symbol="validate_email", kind="python",
    )
    assert sc.target_error is None


# ---------------------------------------------------------------------------
# parse_spec — multiple scenarios + mixed flags
# ---------------------------------------------------------------------------


SPEC_MIXED = """
# Spec: Mixed scenarios

## ADDED Requirements

### Requirement: Cleanup is robust

#### Scenario: dirty tree clean after cleanup

- **testable**: true
- **target**: zsiga/pipeline/orchestrator.py::_must_modify_gate
- **Given** dirty tree
- **When** cleanup runs
- **Then** git status --porcelain returns empty

#### Scenario: cleanup preserves intent

- **testable**: false
- **Given** complex change
- **When** cleanup runs
- **Then** logical intent is preserved

#### Scenario: ux feels snappy

- **Given** a user clicks a button
- **When** the button is clicked
- **Then** it feels snappy
"""


def test_multiple_scenarios_with_mixed_testable():
    out = parse_spec(SPEC_MIXED)
    assert len(out) == 3

    by_name = {s.name: s for s in out}

    s1 = by_name["dirty tree clean after cleanup"]
    assert s1.testable is True
    assert s1.target.file == "zsiga/pipeline/orchestrator.py"
    assert s1.target.symbol == "_must_modify_gate"

    s2 = by_name["cleanup preserves intent"]
    assert s2.testable is False
    assert s2.target is None

    # Legacy scenario without testable field stays False
    s3 = by_name["ux feels snappy"]
    assert s3.testable is False
    assert s3.target is None


def test_collect_testable_returns_only_eligible():
    scenarios = parse_spec(SPEC_MIXED)
    testable = collect_testable(scenarios)
    assert len(testable) == 1
    assert testable[0].name == "dirty tree clean after cleanup"


# ---------------------------------------------------------------------------
# parse_spec — error tolerance
# ---------------------------------------------------------------------------


SPEC_TESTABLE_BAD_TARGET = """
### Scenario: target is broken

- **testable**: true
- **target**: not_a_valid_target_at_all
- **Given** something
- **When** something else
- **Then** something happens
"""


def test_invalid_target_forces_testable_false_records_error():
    out = parse_spec(SPEC_TESTABLE_BAD_TARGET)
    assert len(out) == 1
    sc = out[0]
    # Even though the spec said testable: true, an unparseable target
    # demotes it so we don't try to generate a pytest for it.
    assert sc.testable is False
    assert sc.target is None
    assert sc.target_error is not None
    assert "ValueError" in sc.target_error


SPEC_TESTABLE_CLI_TARGET = """
### Scenario: cli target Phase-1 unsupported

- **testable**: true
- **target**: cli:zsiga harness run
- **Given** a cli scenario
- **When** the cli runs
- **Then** it returns 0
"""


def test_unsupported_cli_target_demotes_to_layer2():
    out = parse_spec(SPEC_TESTABLE_CLI_TARGET)
    sc = out[0]
    assert sc.testable is False
    assert sc.target is None
    assert sc.target_error is not None
    assert "UnsupportedTargetKind" in sc.target_error


# ---------------------------------------------------------------------------
# Scenario.slug
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name, expected",
    [
        ("simple name", "simple_name"),
        ("With CAPS and 123 numbers", "with_caps_and_123_numbers"),
        ("punct.uation, marks!", "punct_uation_marks"),
        ("--leading-trailing--", "leading_trailing"),
        ("", "scenario"),
        ("中文 + english mix", "english_mix"),
    ],
)
def test_scenario_slug(name, expected):
    assert Scenario(name=name).slug == expected


# ---------------------------------------------------------------------------
# raw_block preservation (for L2 fallback)
# ---------------------------------------------------------------------------


def test_raw_block_preserves_full_scenario():
    out = parse_spec(SPEC_TESTABLE_TRUE)
    sc = out[0]
    assert "Scenario: validate empty email rejected" in sc.raw_block
    assert "validate_email" in sc.raw_block
    assert "SHALL be False" in sc.raw_block


def test_raw_block_for_each_scenario_independently():
    out = parse_spec(SPEC_MIXED)
    raws = [s.raw_block for s in out]
    # No raw_block should leak content from another scenario
    for sc in out:
        for other in out:
            if sc is other:
                continue
            assert other.name not in sc.raw_block.split(sc.name, 1)[-1]


# ---------------------------------------------------------------------------
# Heading depth tolerance (### / #### / #####)
# ---------------------------------------------------------------------------


def test_handles_various_heading_depths():
    spec = (
        "### Scenario: depth-3\n- **testable**: false\n\n"
        "#### Scenario: depth-4\n- **testable**: true\n- **target**: a/b.py::c\n\n"
        "##### Scenario: depth-5\n- **testable**: false\n"
    )
    out = parse_spec(spec)
    assert [s.name for s in out] == ["depth-3", "depth-4", "depth-5"]
    assert out[1].testable is True
    assert out[1].target.file == "a/b.py"


# ---------------------------------------------------------------------------
# Phase 6: ContractDef + Scenario.contract + parse_contract + to_module_path
# ---------------------------------------------------------------------------

from zsiga.pipeline.spec_parser import ContractDef, parse_contract


class TestTargetRefToModulePath:
    def test_simple_module(self):
        ref = TargetRef(file="zsiga/pipeline/verifier.py", symbol="foo")
        assert ref.to_module_path() == "zsiga.pipeline.verifier"

    def test_class_method_target(self):
        ref = TargetRef(
            file="zsiga/pipeline/orchestrator.py",
            symbol="ZsigaOrchestrator.run",
        )
        # to_module_path() is about the file part only; symbol untouched
        assert ref.to_module_path() == "zsiga.pipeline.orchestrator"

    def test_nested_directory(self):
        ref = TargetRef(file="src/api/handlers/users.py", symbol="get")
        assert ref.to_module_path() == "src.api.handlers.users"

    def test_path_without_py_extension_falls_back_to_dotted(self):
        # Defensive: file accidentally lacks .py — still produce a usable path
        ref = TargetRef(file="src/foo", symbol="bar")
        assert ref.to_module_path() == "src.foo"


class TestParseContract:
    def test_returns_only(self):
        c = parse_contract("    returns: str\n")
        assert c.returns == "str"
        assert c.params == ()
        assert c.raises == ()

    def test_inline_raises_list_form(self):
        c = parse_contract("    raises: [FileNotFoundError, ValueError]\n")
        assert c.raises == ("FileNotFoundError", "ValueError")

    def test_inline_raises_csv_form(self):
        c = parse_contract("    raises: FileNotFoundError, KeyError\n")
        assert c.raises == ("FileNotFoundError", "KeyError")

    def test_empty_raises(self):
        c = parse_contract("    raises: []\n")
        assert c.raises == ()

    def test_nested_params(self):
        block = (
            "    params:\n"
            "      verify_md_content: str\n"
            "      precheck_error_type: str | None = None\n"
            "    returns: str\n"
        )
        c = parse_contract(block)
        assert c.params_dict == {
            "verify_md_content": "str",
            "precheck_error_type": "str | None = None",
        }
        assert c.returns == "str"

    def test_full_contract(self):
        block = (
            "    params:\n"
            "      path: str\n"
            "      strict: bool = False\n"
            "    returns: dict | None\n"
            "    raises: [FileNotFoundError, PermissionError]\n"
        )
        c = parse_contract(block)
        assert c.params_dict == {"path": "str", "strict": "bool = False"}
        assert c.returns == "dict | None"
        assert c.raises == ("FileNotFoundError", "PermissionError")

    def test_unrecognised_lines_silently_ignored(self):
        block = (
            "    # a comment\n"
            "    some_random_line\n"
            "    returns: int\n"
        )
        c = parse_contract(block)
        assert c.returns == "int"

    def test_dataclass_is_hashable(self):
        # ContractDef must be hashable so it can be put in sets/used as dict key
        a = ContractDef(params=(("x", "int"),), returns="int")
        b = ContractDef(params=(("x", "int"),), returns="int")
        assert hash(a) == hash(b)
        assert a == b


class TestParseSpecWithContract:
    SPEC_WITH_CONTRACT = """\
#### Scenario: classify precheck import failure

- **testable**: true
- **target**: zsiga/pipeline/verifier.py::classify_verify_failure
- **contract**:
    params:
      verify_md_content: str
      precheck_error_type: str | None = None
    returns: str
- **Given** a verify precheck result with error_type == "import"
- **When** classify_verify_failure called
- **Then** result is precheck_import
"""

    def test_scenario_carries_contract(self):
        out = parse_spec(self.SPEC_WITH_CONTRACT)
        assert len(out) == 1
        sc = out[0]
        assert sc.testable is True
        assert sc.contract is not None
        assert sc.contract.params_dict == {
            "verify_md_content": "str",
            "precheck_error_type": "str | None = None",
        }
        assert sc.contract.returns == "str"

    def test_scenario_without_contract_field_has_none(self):
        out = parse_spec(SPEC_TESTABLE_TRUE)  # defined earlier in this file
        sc = out[0]
        assert sc.contract is None

    def test_contract_with_raises_only(self):
        spec = """\
#### Scenario: parse missing config

- **testable**: true
- **target**: src/parser.py::parse_config
- **contract**:
    params:
      path: str
    raises: [FileNotFoundError]
- **Given** a missing path
- **When** parse_config called
- **Then** raises
"""
        out = parse_spec(spec)
        sc = out[0]
        assert sc.contract.raises == ("FileNotFoundError",)
        assert sc.contract.returns is None

