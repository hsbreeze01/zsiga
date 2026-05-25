"""
Spec tests for cleanup-stale-test-files / stale-test-removal.

Verifies that all test_spec_* files belonging to archived or deleted proposals
have been removed, non-spec files are untouched, and changes are confined to tests/.
"""
import subprocess
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
THIS_FILE = Path(__file__).resolve().name

# Non-stale test_spec_* files that test real project code and must be kept
NON_STALE_SPEC_FILES = {
    "test_spec_parser.py",
    "test_spec_pytest_check.py",
}

# Known stale proposal prefixes that MUST be gone
STALE_PREFIXES = [
    "test_spec_add_health_check_endpoint__",
    "test_spec_add_proposal_stats_to_dashboard__",
    "test_spec_add_uptime_to_status_api__",
    "test_spec_dashboard_add_feedback_loop_metrics__",
    "test_spec_sre_subagent_design__",
    "test_spec_auto_metric_degradation_",
    "test_spec_push_local_commits_to_remote__",
    "test_spec_enable_sub_agent_gates__",
    "test_spec_fix_learnings_noise_and_inject__",
    "test_spec_unify_api_route_style__",
]

# Non-spec test files that MUST be preserved (spot-check subset)
PRESERVED_FILES = [
    "conftest_zsiga.py",
    "test_ast_tools.py",
    "test_compaction.py",
    "test_config_diff.py",
    "test_config_validation.py",
    "test_daemon_cycle_resilience.py",
    "test_git_ops.py",
    "test_logging.py",
    "test_spec_parser.py",
    "test_venv_usage.py",
]


def test_no_stale_test_spec_files_remain():
    """Scenario: No test_spec_* files remain after cleanup.
    All test_spec_* files from archived/deleted proposals must be gone.
    This file (the current proposal's own test) is excluded from the check.
    """
    remaining = []
    for f in sorted(TESTS_DIR.glob("test_spec_*.py")):
        if f.name == THIS_FILE:
            continue
        if f.name in NON_STALE_SPEC_FILES:
            continue
        remaining.append(f.name)
    assert remaining == [], (
        f"Found test_spec_* files that should have been removed: {remaining}"
    )


def test_non_spec_files_preserved():
    """Scenario: Non-spec test files are preserved.
    A representative set of non-spec test files must still exist.
    """
    missing = []
    for filename in PRESERVED_FILES:
        if not (TESTS_DIR / filename).exists():
            missing.append(filename)
    assert missing == [], f"Non-spec test files missing after cleanup: {missing}"


def test_conftest_preserved():
    """Scenario: conftest_zsiga.py is preserved.
    The shared conftest must still exist and contain content.
    """
    conftest = TESTS_DIR / "conftest_zsiga.py"
    assert conftest.exists(), "conftest_zsiga.py was deleted during cleanup"
    content = conftest.read_text()
    assert len(content) > 0, "conftest_zsiga.py is empty"
    # Verify it still looks like a conftest (has fixture definitions)
    assert "def " in content or "fixture" in content, (
        "conftest_zsiga.py appears truncated or corrupted"
    )


def test_deleted_files_recoverable_from_git():
    """Scenario: Deleted files are recoverable from git history.
    Git must show the deleted test_spec_* files in its log so they can be restored.
    """
    result = subprocess.run(
        ["git", "log", "--all", "--diff-filter=D", "--name-only", "--pretty=format:",
         "--", "tests/test_spec_*.py"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"git log failed: {result.stderr}"
    deleted_files = [line for line in result.stdout.strip().splitlines() if line.strip()]
    # At least one test_spec_* file must have been recorded as deleted
    assert len(deleted_files) > 0, (
        "No test_spec_* files found in git deletion history — "
        "cleanup may not have been committed, or files were never tracked"
    )


def test_no_changes_outside_tests_dir():
    """Scenario: No files outside tests/ are modified.
    All git changes must be under tests/.
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"git diff failed: {result.stderr}"
    changed = [line for line in result.stdout.strip().splitlines() if line.strip()]
    outside = [p for p in changed if not p.startswith("tests/")]
    assert outside == [], (
        f"Files modified outside tests/ during cleanup: {outside}"
    )
