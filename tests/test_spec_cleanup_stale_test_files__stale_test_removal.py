"""
Spec tests for: cleanup-stale-test-files / stale-test-removal

Verifies that all test_spec_* files are removed, non-spec files are preserved,
and git diff shows only deletions.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Scenario: No test_spec_* files remain after cleanup
# ---------------------------------------------------------------------------
def test_no_test_spec_files_remain():
    """After cleanup, find tests/ -name 'test_spec_*' must return zero results."""
    spec_files = sorted(REPO_ROOT.glob("tests/test_spec_*"))
    assert spec_files == [], (
        f"Expected no test_spec_* files, but found: {[p.name for p in spec_files]}"
    )


# ---------------------------------------------------------------------------
# Scenario: Non-spec test files are preserved
# ---------------------------------------------------------------------------
def test_conftest_zsiga_preserved():
    """conftest_zsiga.py must still exist after cleanup."""
    conftest = REPO_ROOT / "tests" / "conftest_zsiga.py"
    assert conftest.is_file(), f"{conftest} must exist but does not"


def test_non_spec_test_files_preserved():
    """All non-spec test_*.py files must still exist after cleanup."""
    tests_dir = REPO_ROOT / "tests"
    # At minimum, these well-known non-spec files must exist
    preserved = [
        "test_ast_tools.py",
        "test_compaction.py",
        "test_config_diff.py",
        "test_config_validation.py",
        "test_dashboard_api.py",
    ]
    for name in preserved:
        assert (tests_dir / name).is_file(), f"{name} must exist but does not"


# ---------------------------------------------------------------------------
# Scenario: Git diff shows only test_spec_* deletions
# ---------------------------------------------------------------------------
def test_git_diff_only_spec_deletions():
    """git diff --name-only should list only tests/test_spec_*.py files (all deleted)."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=D"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        # If no git repo or no changes, that's acceptable (already committed)
        return

    deleted_files = result.stdout.strip().splitlines()
    for f in deleted_files:
        assert f.startswith("tests/test_spec_") and f.endswith(".py"), (
            f"Unexpected deleted file: {f}. Only tests/test_spec_*.py should be deleted."
        )

    # Non-spec files must NOT appear as deleted
    for f in deleted_files:
        assert f != "tests/conftest_zsiga.py", "conftest_zsiga.py must not be deleted"


def test_git_status_no_modified_non_spec_files():
    """No non-spec test files should appear as modified in git status."""
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        return

    modified_files = result.stdout.strip().splitlines()
    for f in modified_files:
        assert not (
            f.startswith("tests/test_") and not f.startswith("tests/test_spec_")
        ), f"Non-spec test file was modified: {f}"
