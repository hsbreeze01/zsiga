"""Tests for evolution engine _pre_scan_module and proposal quality improvements.

Verifies:
1. _pre_scan_module extracts symbols, lint issues, and complexity
2. _scan_code_structure populates module_scans for untested modules
3. _render_explore_proposal includes concrete function names, line numbers, and binary BACs
4. _render_test_proposal includes concrete function names and binary BACs
5. Proposals pass Steward scoring criteria (actionability, eval)
"""

import textwrap

import pytest


class TestPreScanModule:
    """Verify _pre_scan_module static analysis output."""

    @pytest.fixture
    def evo_engine(self, tmp_path):
        from zsiga.intake.evolution import EvolutionEngine, EvolutionConfig
        engine = EvolutionEngine(str(tmp_path), EvolutionConfig())
        return engine

    def test_extracts_functions_with_signatures(self, tmp_path, evo_engine):
        target = tmp_path / "zsiga" / "sample.py"
        target.parent.mkdir(parents=True)
        target.write_text(textwrap.dedent("""\
            def hello(name: str) -> str:
                return f"hello {name}"

            def add(a: int, b: int) -> int:
                return a + b

            async def fetch(url: str) -> dict:
                return {}
        """))

        scan = evo_engine._pre_scan_module("zsiga/sample.py")

        assert scan["total_lines"] >= 7
        assert len(scan["symbols"]) == 3

        names = [s["name"] for s in scan["symbols"]]
        assert "hello" in names
        assert "add" in names
        assert "fetch" in names

        hello = next(s for s in scan["symbols"] if s["name"] == "hello")
        assert hello["kind"] == "function"
        assert hello["line"] == 1
        assert "name" in hello["args"]
        assert hello["lines"] >= 2

    def test_extracts_classes_with_methods(self, tmp_path, evo_engine):
        target = tmp_path / "zsiga" / "classes.py"
        target.parent.mkdir(parents=True)
        target.write_text(textwrap.dedent("""\
            class Calculator:
                def __init__(self, precision: int = 2):
                    self.precision = precision

                def compute(self, x: float) -> float:
                    return round(x, self.precision)
        """))

        scan = evo_engine._pre_scan_module("zsiga/classes.py")

        class_syms = [s for s in scan["symbols"] if s["kind"] == "class"]
        assert len(class_syms) == 1
        assert class_syms[0]["name"] == "Calculator"
        assert "__init__" in class_syms[0]["methods"]
        assert "compute" in class_syms[0]["methods"]

    def test_handles_syntax_error_gracefully(self, tmp_path, evo_engine):
        target = tmp_path / "zsiga" / "broken.py"
        target.parent.mkdir(parents=True)
        target.write_text("def broken(\n")

        scan = evo_engine._pre_scan_module("zsiga/broken.py")

        assert scan["symbols"] == []
        assert scan["total_lines"] == 2

    def test_handles_missing_file(self, tmp_path, evo_engine):
        scan = evo_engine._pre_scan_module("zsiga/nonexistent.py")

        assert scan["symbols"] == []
        assert scan["lint_issues"] == []
        assert scan["complexity"] == []
        assert scan["total_lines"] == 0

    def test_extracts_ruff_lint_issues(self, tmp_path, evo_engine):
        target = tmp_path / "zsiga" / "linty.py"
        target.parent.mkdir(parents=True)
        target.write_text(textwrap.dedent("""\
            import os
            import sys

            def unused_var():
                x = 1
                return 42
        """))

        scan = evo_engine._pre_scan_module("zsiga/linty.py")

        assert len(scan["lint_issues"]) > 0
        codes = [iss["code"] for iss in scan["lint_issues"]]
        assert any(c in codes for c in ["F401", "F841"]), f"Expected lint issues, got {codes}"
        for iss in scan["lint_issues"]:
            assert iss["line"] > 0
            assert iss["code"]
            assert iss["message"]

    def test_complexity_from_lizard(self, tmp_path, evo_engine):
        target = tmp_path / "zsiga" / "complex.py"
        target.parent.mkdir(parents=True)
        target.write_text(textwrap.dedent("""\
            def simple():
                return 1

            def complex_func(x):
                if x > 0:
                    if x > 10:
                        if x > 100:
                            return 3
                        return 2
                    return 1
                return 0
        """))

        scan = evo_engine._pre_scan_module("zsiga/complex.py")

        if scan["complexity"]:
            names = [c["name"] for c in scan["complexity"]]
            assert "simple" in names
            assert "complex_func" in names
            complex_fn = next(c for c in scan["complexity"] if c["name"] == "complex_func")
            assert complex_fn["cc"] >= 3
            assert complex_fn["line"] > 0


class TestScanCodeStructureWithScans:
    """Verify _scan_code_structure now populates module_scans."""

    @pytest.fixture
    def evo_engine(self, tmp_path):
        from zsiga.intake.evolution import EvolutionEngine, EvolutionConfig
        engine = EvolutionEngine(str(tmp_path), EvolutionConfig())
        return engine

    def test_module_scans_populated_for_untested(self, tmp_path, evo_engine):
        zsiga_dir = tmp_path / "zsiga"
        zsiga_dir.mkdir()
        (zsiga_dir / "alpha.py").write_text(textwrap.dedent("""\
            def alpha_func(x: int) -> int:
                return x * 2
        """))
        (zsiga_dir / "beta.py").write_text(textwrap.dedent("""\
            def beta_func(y: str) -> str:
                return y.upper()
        """))

        result = evo_engine._scan_code_structure()

        assert "module_scans" in result
        assert "alpha" in result["module_scans"]
        assert "beta" in result["module_scans"]

        alpha_scan = result["module_scans"]["alpha"]
        assert any(s["name"] == "alpha_func" for s in alpha_scan["symbols"])

    def test_tested_modules_not_in_scans(self, tmp_path, evo_engine):
        zsiga_dir = tmp_path / "zsiga"
        zsiga_dir.mkdir()
        (zsiga_dir / "tested_mod.py").write_text("def fn(): pass\n")
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_tested_mod.py").write_text("def test_fn(): pass\n")

        result = evo_engine._scan_code_structure()

        assert "tested_mod" not in result["modules_without_tests"]
        assert "tested_mod" not in result["module_scans"]


class TestExploreProposalQuality:
    """Verify _render_explore_proposal produces concrete, Steward-passable proposals."""

    @pytest.fixture
    def evo_engine(self, tmp_path):
        from zsiga.intake.evolution import EvolutionEngine, EvolutionConfig
        engine = EvolutionEngine(str(tmp_path), EvolutionConfig())
        return engine

    def test_proposal_contains_function_names(self, tmp_path, evo_engine):
        module_path = tmp_path / "zsiga" / "git_ops.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text(textwrap.dedent("""\
            def rev_parse(target_path: str, transport=None, ref: str = "HEAD") -> str:
                return "abc123"

            def reset_hard(target_path: str, sha: str, transport=None) -> None:
                pass

            def push(target_path: str, remote: str = "origin", branch: str = "main") -> None:
                pass
        """))
        (tmp_path / "tests").mkdir()

        scan = evo_engine._pre_scan_module("zsiga/git_ops.py")
        facts = {
            "code_structure": {
                "module_scans": {"git_ops": scan},
            },
        }
        finding = {"type": "explore_module", "module": "zsiga/git_ops.py"}

        result = evo_engine._render_explore_proposal(finding, facts)

        assert "rev_parse" in result
        assert "reset_hard" in result
        assert "push" in result
        assert "L1" in result

    def test_proposal_has_binary_bac(self, tmp_path, evo_engine):
        module_path = tmp_path / "zsiga" / "parser.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text(textwrap.dedent("""\
            def parse_line(line: str) -> dict:
                return {}
        """))
        (tmp_path / "tests").mkdir()

        scan = evo_engine._pre_scan_module("zsiga/parser.py")
        facts = {"code_structure": {"module_scans": {"parser": scan}}}
        finding = {"type": "explore_module", "module": "zsiga/parser.py"}

        result = evo_engine._render_explore_proposal(finding, facts)

        assert "BAC-01" in result
        assert "BAC-02" in result
        assert "BAC-03" in result
        assert "BAC-04" in result
        assert "tests/test_parser.py" in result
        assert "`test_parse_line`" in result
        assert "存在" in result
        assert "退出码 0" in result

    def test_proposal_no_subjective_bac(self, tmp_path, evo_engine):
        module_path = tmp_path / "zsiga" / "utils.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text(textwrap.dedent("""\
            def helper(x: int) -> int:
                return x + 1
        """))
        (tmp_path / "tests").mkdir()

        scan = evo_engine._pre_scan_module("zsiga/utils.py")
        facts = {"code_structure": {"module_scans": {"utils": scan}}}
        finding = {"type": "explore_module", "module": "zsiga/utils.py"}

        result = evo_engine._render_explore_proposal(finding, facts)

        assert "实质性改进" not in result
        assert "完成分析" not in result
        assert "探索" not in result.split("\n")[0]

    def test_proposal_contains_static_analysis_section(self, tmp_path, evo_engine):
        module_path = tmp_path / "zsiga" / "target.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text(textwrap.dedent("""\
            import os
            import sys

            def func_a() -> None:
                pass

            def func_b(x: int) -> int:
                if x > 0:
                    if x > 10:
                        return 3
                    return 2
                return 1
        """))
        (tmp_path / "tests").mkdir()

        scan = evo_engine._pre_scan_module("zsiga/target.py")
        facts = {"code_structure": {"module_scans": {"target": scan}}}
        finding = {"type": "explore_module", "module": "zsiga/target.py"}

        result = evo_engine._render_explore_proposal(finding, facts)

        assert "静态分析" in result
        assert "总行数" in result
        assert "函数数" in result


class TestTestProposalQuality:
    """Verify _render_test_proposal includes concrete function data."""

    @pytest.fixture
    def evo_engine(self, tmp_path):
        from zsiga.intake.evolution import EvolutionEngine, EvolutionConfig
        engine = EvolutionEngine(str(tmp_path), EvolutionConfig())
        return engine

    def test_test_proposal_has_function_names(self, tmp_path, evo_engine):
        module_path = tmp_path / "zsiga" / "validator.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text(textwrap.dedent("""\
            def validate_input(data: dict) -> bool:
                return bool(data)

            def sanitize(text: str) -> str:
                return text.strip()
        """))
        (tmp_path / "tests").mkdir()

        scan = evo_engine._pre_scan_module("zsiga/validator.py")
        facts = {
            "code_structure": {
                "module_scans": {"validator": scan},
                "modules_without_tests": ["zsiga/validator.py"],
            },
        }
        finding = {
            "type": "add_tests",
            "count": 1,
            "modules": ["zsiga/validator.py"],
        }

        result = evo_engine._render_test_proposal(finding, facts)

        assert "`validate_input`" in result
        assert "`sanitize`" in result
        assert "tests/test_validator.py" in result
        assert "`test_validate_input`" in result
        assert "BAC-01" in result
        assert "BAC-04" in result
        assert "退出码 0" in result

    def test_test_proposal_no_vague_language(self, tmp_path, evo_engine):
        module_path = tmp_path / "zsiga" / "simple.py"
        module_path.parent.mkdir(parents=True)
        module_path.write_text("def do_work() -> None: pass\n")
        (tmp_path / "tests").mkdir()

        scan = evo_engine._pre_scan_module("zsiga/simple.py")
        facts = {
            "code_structure": {
                "module_scans": {"simple": scan},
                "modules_without_tests": ["zsiga/simple.py"],
            },
        }
        finding = {
            "type": "add_tests",
            "count": 1,
            "modules": ["zsiga/simple.py"],
        }

        result = evo_engine._render_test_proposal(finding, facts)

        assert "分析目标模块的公开 API" not in result
        assert "tests/ 目录中存在对应的测试文件" not in result


class TestFixLoopDetection:
    """Verify fix-loop detection skips fix path when evo-fix rejections accumulate."""

    @pytest.fixture
    def evo_engine(self, tmp_path):
        from zsiga.intake.evolution import EvolutionEngine, EvolutionConfig
        engine = EvolutionEngine(str(tmp_path), EvolutionConfig())
        return engine

    def test_scan_pending_before_archive(self, tmp_path, evo_engine):
        changes = tmp_path / "openspec" / "changes"
        changes.mkdir(parents=True)

        pending = changes / "evo-fix-20260527-180000"
        pending.mkdir()
        (pending / "proposal.md").write_text("# fix-x\n## 失败模式 `x`\n")
        (pending / "steward-review.md").write_text("## Verdict: REJECT\n")

        archive_sub = changes / "archive" / "2026-05-27"
        archive_sub.mkdir(parents=True)
        old = archive_sub / "evo-fix-20260527-170000"
        old.mkdir()
        (old / "proposal.md").write_text("# fix-y\n")

        rejections = evo_engine._collect_recent_evo_rejections()

        assert len(rejections) >= 1
        assert rejections[0]["dir"] == "evo-fix-20260527-180000"

    def test_skip_fix_with_accumulated_rejections(self, tmp_path, evo_engine):
        changes = tmp_path / "openspec" / "changes"
        changes.mkdir(parents=True)

        for i in range(4):
            d = changes / f"evo-fix-20260527-{180000 + i * 100}"
            d.mkdir()
            (d / "proposal.md").write_text(f"# fix-p{i}\n")
            (d / "steward-review.md").write_text("## Verdict: REJECT\n")

        rejections = evo_engine._collect_recent_evo_rejections()
        fix_rejections = sum(1 for r in rejections if "evo-fix-" in r.get("dir", ""))

        assert fix_rejections >= 3
        assert fix_rejections == 4

    def test_phase2_reflect_skips_fix_when_loop_detected(self, tmp_path, evo_engine):
        zsiga_dir = tmp_path / "zsiga"
        zsiga_dir.mkdir()
        (zsiga_dir / "untested.py").write_text("def fn(): pass\n")
        (tmp_path / "tests").mkdir()


        changes = tmp_path / "openspec" / "changes"
        changes.mkdir(parents=True)
        for i in range(5):
            d = changes / f"evo-fix-20260527-{180000 + i * 100}"
            d.mkdir()
            (d / "proposal.md").write_text(f"# fix-p{i}\n")
            (d / "steward-review.md").write_text("## Verdict: REJECT\n")

        facts = evo_engine._phase1_intake()
        insights = evo_engine._phase2_reflect(facts)

        if insights.get("priority_finding"):
            assert insights["priority_finding"]["type"] != "fix_failure", \
                "Should skip fix_failure when evo-fix rejections >= 3"

    def test_phase2_reflect_skips_fix_when_historical_loop_detected(self, evo_engine):
        facts = {
            "findings": ["recurring_failure:pipeline.fail.verify.diagnosed"],
            "recent_evo_rejections": [],
            "historical_evo_rejections": [
                {"dir": f"evo-fix-old-{i}", "pattern_key": "pipeline.fail.verify.diagnosed"}
                for i in range(3)
            ],
            "patterns": [],
        }

        insights = evo_engine._phase2_reflect(facts)

        assert insights["priority_finding"] is None


class TestEvolutionControlGates:
    def test_proposal_preflight_blocks_placeholders(self, tmp_path):
        from zsiga.intake.evolution import EvolutionEngine

        engine = EvolutionEngine(str(tmp_path))
        bad = """# add-tests

## Acceptance Criteria
- [BAC-01] `test_(待分析)` exists
- [BAC-02] 至少 0 个 def test_ 函数
"""

        assert engine._proposal_preflight_error(bad) is not None

    def test_proposal_preflight_accepts_concrete_bac(self, tmp_path):
        from zsiga.intake.evolution import EvolutionEngine

        engine = EvolutionEngine(str(tmp_path))
        good = """# add-tests

## Acceptance Criteria
- [BAC-01] `test_run_pytest_returns_reports` passes
- [BAC-02] 至少 1 个 def test_ 函数覆盖目标行为
"""

        assert engine._proposal_preflight_error(good) is None

    def test_render_test_proposal_without_functions_has_concrete_bac(self, tmp_path):
        from zsiga.intake.evolution import EvolutionEngine

        engine = EvolutionEngine(str(tmp_path))
        proposal = engine._render_test_proposal(
            {"modules": ["zsiga/no_functions.py"], "count": 1},
            {"code_structure": {"module_scans": {"no_functions": {"symbols": []}}}},
        )

        assert "待分析" not in proposal
        assert "至少 0 个" not in proposal
        assert "test_module_import" in proposal
        assert engine._proposal_preflight_error(proposal) is None

    def test_render_explore_proposal_without_functions_has_concrete_bac(self, tmp_path):
        from zsiga.intake.evolution import EvolutionEngine

        engine = EvolutionEngine(str(tmp_path))
        proposal = engine._render_explore_proposal(
            {"module": "zsiga/no_functions.py"},
            {"code_structure": {"module_scans": {"no_functions": {"symbols": []}}}},
        )

        assert "待分析" not in proposal
        assert "至少 0 个" not in proposal
        assert "test_module_import" in proposal
        assert engine._proposal_preflight_error(proposal) is None

    def test_rejection_breaker_ignores_previous_window_reviews(self, tmp_path):
        import os
        import time
        from zsiga.intake.evolution import EvolutionConfig, EvolutionEngine

        changes = tmp_path / "openspec" / "changes"
        changes.mkdir(parents=True)
        old_ts = time.time() - 48 * 3600
        for i in range(5):
            evo_dir = changes / f"evo-improvement-old-{i}"
            evo_dir.mkdir()
            (evo_dir / "proposal.md").write_text("# proposal\n")
            review = evo_dir / "steward-review.md"
            review.write_text("## Verdict: REJECT\n")
            os.utime(review, (old_ts, old_ts))

        engine = EvolutionEngine(
            str(tmp_path),
            EvolutionConfig(window_start_hour=0, window_end_hour=23),
        )

        assert engine._collect_recent_evo_rejections() == []
        assert len(engine._collect_recent_evo_rejections(include_previous_windows=True)) == 5

    def test_pushback_counts_as_evo_rejection(self, tmp_path):
        from zsiga.intake.evolution import EvolutionEngine

        evo_dir = tmp_path / "openspec" / "changes" / "evo-improvement-1"
        evo_dir.mkdir(parents=True)
        (evo_dir / "proposal.md").write_text("# proposal\n")
        (evo_dir / "steward-review.md").write_text("## Verdict: PUSHBACK\n")

        rejections = EvolutionEngine(str(tmp_path))._collect_recent_evo_rejections()

        assert rejections and rejections[0]["dir"] == "evo-improvement-1"

    def test_should_evolve_resets_counter_for_new_window(self, tmp_path, monkeypatch):
        import json
        from datetime import datetime, timedelta
        from zsiga.intake.evolution import EvolutionConfig, EvolutionEngine

        monkeypatch.setattr("zsiga.config.load_runtime_state", lambda: {"active_target": "zsiga"})
        engine = EvolutionEngine(
            str(tmp_path),
            EvolutionConfig(
                window_start_hour=datetime.now().hour,
                window_end_hour=(datetime.now().hour + 1) % 24,
                max_proposals_per_window=1,
            ),
        )
        old_state = {
            "proposals_generated": 1,
            "last_proposal_at": "",
            "window_start_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "total_cycles": 0,
        }
        state_path = tmp_path / "data" / "evolution_state.json"
        state_path.parent.mkdir()
        state_path.write_text(json.dumps(old_state))

        assert engine.should_evolve() is True
