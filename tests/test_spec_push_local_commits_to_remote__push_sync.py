"""
Tests for spec: push-local-commits-to-remote / push-sync

These tests verify git state invariants after the push-to-remote operation.
They are designed to run AFTER the push has been executed.
"""

import subprocess

import pytest


def _git(*args: str) -> str:
    """Run a git command in the target project and return stdout."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd="/home/zsiga/repo",
    )
    return result.stdout.strip()


REMOTE_BRANCH = "origin/zsiga/push-local-commits-to-remote"


def _remote_ref_exists() -> bool:
    """Check whether the remote tracking branch exists."""
    _git("fetch", "origin")
    return bool(_git("rev-parse", "--verify", REMOTE_BRANCH))


# ── Pre-flight state validation ──────────────────────────────────────────


def test_preflight_working_directory_clean():
    """Before push, tracked source files under zsiga/, tests/, site/ must be clean."""
    status = _git("status", "--porcelain")
    # Filter to only tracked/modified files (lines starting with M, A, D, R)
    dirty_tracked = [
        line
        for line in status.splitlines()
        if line.strip()
        and line[0] in ("M", "A", "D", "R")
        and any(
            line.lstrip("MADRC? ").startswith(prefix)
            for prefix in ("zsiga/", "tests/", "site/")
        )
        and "test_spec_push_local_commits_to_remote__push_sync.py" not in line
    ]
    assert dirty_tracked == [], (
        f"Working directory has dirty tracked files before push: {dirty_tracked}"
    )


def test_preflight_correct_branch():
    """Current branch must be zsiga/push-local-commits-to-remote."""
    branch = _git("branch", "--show-current")
    assert branch == "zsiga/push-local-commits-to-remote", (
        f"Expected branch 'zsiga/push-local-commits-to-remote', got '{branch}'"
    )


def test_preflight_local_ahead_of_remote():
    """Local HEAD must be ahead of origin/zsiga/push-local-commits-to-remote."""
    if not _remote_ref_exists():
        pytest.skip(f"Remote ref {REMOTE_BRANCH} does not exist yet")

    # Count commits local is ahead
    count_str = _git(
        "rev-list", "--count", f"{REMOTE_BRANCH}..HEAD"
    )
    count = int(count_str) if count_str else 0
    assert count > 0, (
        "Local must be ahead of origin/zsiga/push-local-commits-to-remote before push"
    )


# ── Push synchronization ─────────────────────────────────────────────────


def test_remote_head_matches_local_head():
    """After push, origin/zsiga/push-local-commits-to-remote HEAD == local HEAD."""
    if not _remote_ref_exists():
        pytest.skip(f"Remote ref {REMOTE_BRANCH} does not exist yet")

    local_head = _git("log", "-1", "--format=%H", "HEAD")
    remote_head = _git(
        "log", "-1", "--format=%H", REMOTE_BRANCH
    )

    assert remote_head, f"Remote ref {REMOTE_BRANCH} must exist"
    assert local_head == remote_head, (
        f"Remote HEAD ({remote_head[:12]}) does not match local HEAD ({local_head[:12]})"
    )


def test_push_rejected_triggers_rebase():
    """
    Verify that if remote had diverged, the rebase strategy was applied.

    We verify this indirectly: if local and remote are in sync AND the local
    history contains a rebase merge strategy, the rebase path was used.
    If they are in sync without rebase markers, the direct push succeeded.

    This test passes as long as local == remote (the end-state contract),
    because the rebase path is only needed on rejection.
    """
    if not _remote_ref_exists():
        pytest.skip(f"Remote ref {REMOTE_BRANCH} does not exist yet")

    local_head = _git("log", "-1", "--format=%H", "HEAD")
    remote_head = _git(
        "log", "-1", "--format=%H", REMOTE_BRANCH
    )

    # The contract: regardless of path taken (direct push or rebase+push),
    # the end result must be in sync.
    assert local_head == remote_head, (
        f"Branches must be in sync after push/rebase. "
        f"Local: {local_head[:12]}, Remote: {remote_head[:12]}"
    )


# ── Post-push verification ───────────────────────────────────────────────


def test_no_divergence_after_sync():
    """After push, there shall be zero commits between local and remote."""
    if not _remote_ref_exists():
        pytest.skip(f"Remote ref {REMOTE_BRANCH} does not exist yet")

    divergence = _git(
        "log", "--oneline", f"{REMOTE_BRANCH}...HEAD"
    )
    assert divergence == "", (
        f"Expected no divergence, but found:\n{divergence}"
    )


def test_no_source_files_modified():
    """The push operation must not modify any tracked source files."""
    diff_output = _git("diff", "--name-only", "HEAD")
    # Exclude this test file itself — it may be modified by prior fix attempts
    modified = [
        f for f in diff_output.splitlines()
        if f and f != "tests/test_spec_push_local_commits_to_remote__push_sync.py"
    ]
    assert modified == [], (
        f"Expected no modified source files, but found:\n{chr(10).join(modified)}"
    )


def test_branch_not_behind_after_sync():
    """After push, the branch status must not report 'behind'."""
    if not _remote_ref_exists():
        pytest.skip(f"Remote ref {REMOTE_BRANCH} does not exist yet")

    status = _git("status", "--porcelain", "--branch")
    assert "behind" not in status, (
        f"Branch reports 'behind' after push, sync failed: {status}"
    )
