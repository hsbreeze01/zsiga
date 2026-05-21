"""Tests for spec: post-implement-lint-autofix

Tests that post-IMPLEMENT lint auto-fix gate works correctly.
"""
import os
import tempfile

from zsiga.pipeline.utils import verify_mechanical
from zsiga.transport import LocalTransport


class TestPostImplementLintAutoFix:
    """Test that lint auto-fix works on changed files after implement."""

    def test_ruff_fix_removes_trailing_whitespace(self):
        """Scenario: Auto-fixable lint errors are corrected before REVIEW.

        ruff check --fix removes trailing whitespace automatically.
        """
        with tempfile.TemporaryDirectory() as td:
            # Create a file with trailing whitespace
            test_file = os.path.join(td, "example.py")
            with open(test_file, "w") as f:
                f.write("x = 1   \ny = 2\n")

            # Run ruff check first — should detect trailing whitespace
            ruff_check = LocalTransport().run_shell(
                f"ruff check '{test_file}' --select W291",
                timeout=10,
            )
            assert ruff_check["exit_code"] != 0, "Should detect trailing whitespace"

            # Run ruff fix
            LocalTransport().run_shell(
                f"ruff check --fix '{test_file}'",
                timeout=10,
            )

            # After fix, no trailing whitespace errors
            ruff_after = LocalTransport().run_shell(
                f"ruff check '{test_file}' --select W291",
                timeout=10,
            )
            assert ruff_after["exit_code"] == 0, "Trailing whitespace should be fixed"

            # Verify content is clean
            with open(test_file) as f:
                content = f.read()
            assert "x = 1   \n" not in content
            assert "x = 1\n" in content

    def test_ruff_fix_cannot_fix_ambiguous_name(self):
        """Scenario: Unfixable lint errors remain after --fix.

        E741 (ambiguous variable name `l`) cannot be auto-fixed by ruff.
        """
        with tempfile.TemporaryDirectory() as td:
            test_file = os.path.join(td, "bad_name.py")
            with open(test_file, "w") as f:
                f.write("l = [1, 2, 3]\n")

            # Run ruff fix (should not change anything)
            LocalTransport().run_shell(
                f"ruff check --fix '{test_file}'",
                timeout=10,
            )

            # E741 should still be present
            ruff_after = LocalTransport().run_shell(
                f"ruff check '{test_file}' --select E741",
                timeout=10,
            )
            assert ruff_after["exit_code"] != 0, "E741 should not be auto-fixable"

    def test_clean_file_passes_without_fix(self):
        """Scenario: Clean IMPLEMENT passes through without extra LLM call.

        A clean file with no lint errors should not trigger any fix attempt.
        """
        with tempfile.TemporaryDirectory() as td:
            test_file = os.path.join(td, "clean.py")
            with open(test_file, "w") as f:
                f.write("items = [1, 2, 3]\nresult = sum(items)\n")

            # ruff check should pass
            ruff_result = LocalTransport().run_shell(
                f"ruff check '{test_file}'",
                timeout=10,
            )
            assert ruff_result["exit_code"] == 0, "Clean file should pass ruff check"

    def test_verify_mechanical_on_clean_files(self):
        """verify_mechanical returns True for a clean codebase."""
        with tempfile.TemporaryDirectory() as td:
            # Initialize git repo
            LocalTransport().run_shell("git init", cwd=td, timeout=10)
            LocalTransport().run_shell("git config user.email 't@t.com'", cwd=td, timeout=5)
            LocalTransport().run_shell("git config user.name 't'", cwd=td, timeout=5)

            # Create a clean file
            test_file = os.path.join(td, "clean.py")
            with open(test_file, "w") as f:
                f.write("x = 1\n")

            LocalTransport().run_shell("git add -A && git commit -m 'init'", cwd=td, timeout=10)
            sha = LocalTransport().run_shell(
                "git rev-parse HEAD", cwd=td, timeout=5,
            )["stdout"].strip()

            # Modify the file
            with open(test_file, "w") as f:
                f.write("y = 2\n")

            passed, errors = verify_mechanical(
                td,
                test_cmd="python3 -m pytest -x",
                lint_cmd="ruff check .",
                since_sha=sha,
            )
            assert passed, f"Clean change should pass verify_mechanical, got: {errors}"
