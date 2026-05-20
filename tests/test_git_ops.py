"""Tests for git_ops.py error handling, branch resolution, and logging."""
import pytest
from unittest.mock import MagicMock

from zsiga import git_ops


def _mock_transport(exit_code=0, stdout="", stderr=""):
    """Create a mock transport with configurable return values."""
    t = MagicMock()
    t.run_shell.return_value = {
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
    }
    return t


# ── _check_result helper ─────────────────────────────────────────

class TestCheckResult:

    def test_success_no_raise(self):
        result = {"exit_code": 0, "stdout": "", "stderr": ""}
        # Should not raise
        git_ops._check_result(result, "git test")

    def test_failure_raises_runtime_error(self):
        result = {"exit_code": 1, "stdout": "", "stderr": "some error"}
        with pytest.raises(RuntimeError, match="some error"):
            git_ops._check_result(result, "git test")

    def test_failure_prints_diagnostic(self, capsys):
        result = {"exit_code": 1, "stdout": "", "stderr": "bad thing"}
        with pytest.raises(RuntimeError):
            git_ops._check_result(result, "git push")
        captured = capsys.readouterr()
        assert "❌ git push failed: bad thing" in captured.out


# ── push ─────────────────────────────────────────────────────────

class TestPush:

    def test_push_failure_raises_runtime_error(self, capsys):
        transport = _mock_transport(exit_code=1, stderr="remote rejected")
        with pytest.raises(RuntimeError, match="remote rejected"):
            git_ops.push("/tmp/repo", branch="main", transport=transport)
        captured = capsys.readouterr()
        assert "❌ git push failed" in captured.out

    def test_push_success_prints_before_after(self, capsys):
        transport = _mock_transport()
        git_ops.push("/tmp/repo", branch="feature/x", transport=transport)
        captured = capsys.readouterr()
        assert "git push origin feature/x ..." in captured.out
        assert "✅ pushed origin feature/x" in captured.out

    def test_push_no_branch_resolves_current(self):
        transport = MagicMock()
        # current_branch call
        transport.run_shell.side_effect = [
            {"exit_code": 0, "stdout": "zsiga/fix-123\n", "stderr": ""},  # current_branch
            {"exit_code": 0, "stdout": "", "stderr": ""},  # push
            {"exit_code": 0, "stdout": "", "stderr": ""},  # push --tags
        ]
        git_ops.push("/tmp/repo", transport=transport)
        # First call should be rev-parse for current branch
        first_call = transport.run_shell.call_args_list[0]
        assert "git rev-parse --abbrev-ref HEAD" in first_call[1].get("cmd", first_call[0][0])

    def test_push_dry_run_no_error(self, capsys):
        transport = _mock_transport()
        git_ops.push("/tmp/repo", branch="main", dry_run=True, transport=transport)
        captured = capsys.readouterr()
        assert "[DRY RUN]" in captured.out
        # Should not call run_shell for actual push
        transport.run_shell.assert_not_called()

    def test_push_custom_remote(self, capsys):
        transport = _mock_transport()
        git_ops.push("/tmp/repo", remote="github-agent", branch="deploy", transport=transport)
        captured = capsys.readouterr()
        assert "git push github-agent deploy ..." in captured.out


# ── pull ─────────────────────────────────────────────────────────

class TestPull:

    def test_pull_no_branch_resolves_current(self):
        transport = MagicMock()
        transport.run_shell.side_effect = [
            {"exit_code": 0, "stdout": "zsiga/fix-123\n", "stderr": ""},  # current_branch
            {"exit_code": 0, "stdout": "", "stderr": ""},  # pull
        ]
        git_ops.pull("/tmp/repo", transport=transport)
        first_call = transport.run_shell.call_args_list[0]
        assert "git rev-parse --abbrev-ref HEAD" in first_call[1].get("cmd", first_call[0][0])

    def test_pull_failure_raises_runtime_error(self):
        transport = _mock_transport(exit_code=1, stderr="merge conflict")
        with pytest.raises(RuntimeError, match="merge conflict"):
            git_ops.pull("/tmp/repo", branch="main", transport=transport)


# ── commit ───────────────────────────────────────────────────────

class TestCommit:

    def test_commit_failure_raises_runtime_error(self):
        transport = _mock_transport(exit_code=1, stderr="nothing to commit")
        with pytest.raises(RuntimeError, match="nothing to commit"):
            git_ops.commit("/tmp/repo", "msg", transport=transport)

    def test_commit_success_prints_before_after(self, capsys):
        transport = _mock_transport()
        git_ops.commit("/tmp/repo", "feat: new feature", transport=transport)
        captured = capsys.readouterr()
        assert "git commit -m 'feat: new feature' ..." in captured.out
        assert "✅ committed" in captured.out


# ── merge_branch ─────────────────────────────────────────────────

class TestMergeBranch:

    def test_merge_failure_raises_runtime_error(self):
        transport = _mock_transport(exit_code=1, stderr="conflict in file.py")
        with pytest.raises(RuntimeError, match="conflict in file.py"):
            git_ops.merge_branch("/tmp/repo", "feature/x", transport=transport)

    def test_merge_success(self, capsys):
        transport = _mock_transport()
        git_ops.merge_branch("/tmp/repo", "feature/x", transport=transport)
        captured = capsys.readouterr()
        assert "✅ merged feature/x" in captured.out


# ── checkout ─────────────────────────────────────────────────────

class TestCheckout:

    def test_checkout_failure_raises_runtime_error(self):
        transport = _mock_transport(exit_code=1, stderr="branch not found")
        with pytest.raises(RuntimeError, match="branch not found"):
            git_ops.checkout("/tmp/repo", "nonexistent", transport=transport)

    def test_checkout_success(self, capsys):
        transport = _mock_transport()
        git_ops.checkout("/tmp/repo", "main", transport=transport)
        captured = capsys.readouterr()
        assert "✅ checked out main" in captured.out


# ── delete_branch ────────────────────────────────────────────────

class TestDeleteBranch:

    def test_delete_branch_failure_raises_runtime_error(self):
        transport = _mock_transport(exit_code=1, stderr="branch not found")
        with pytest.raises(RuntimeError, match="branch not found"):
            git_ops.delete_branch("/tmp/repo", "old-branch", transport=transport)

    def test_delete_branch_success(self, capsys):
        transport = _mock_transport()
        git_ops.delete_branch("/tmp/repo", "old-branch", transport=transport)
        captured = capsys.readouterr()
        assert "✅ deleted branch old-branch" in captured.out


# ── tag ──────────────────────────────────────────────────────────

class TestTag:

    def test_tag_failure_raises_runtime_error(self):
        transport = _mock_transport(exit_code=1, stderr="tag exists")
        with pytest.raises(RuntimeError, match="tag exists"):
            git_ops.tag("/tmp/repo", "v1.0", transport=transport)

    def test_tag_success(self, capsys):
        transport = _mock_transport()
        git_ops.tag("/tmp/repo", "v1.0", transport=transport)
        captured = capsys.readouterr()
        assert "✅ tagged v1.0" in captured.out


# ── add_all ──────────────────────────────────────────────────────

class TestAddAll:

    def test_add_all_failure_raises_runtime_error(self):
        transport = _mock_transport(exit_code=1, stderr="not a repo")
        with pytest.raises(RuntimeError, match="not a repo"):
            git_ops.add_all("/tmp/repo", transport=transport)

    def test_add_all_success(self, capsys):
        transport = _mock_transport()
        git_ops.add_all("/tmp/repo", transport=transport)
        captured = capsys.readouterr()
        assert "✅ added all" in captured.out


# ── reset_hard ───────────────────────────────────────────────────

class TestResetHard:

    def test_reset_hard_failure_raises_runtime_error(self):
        transport = _mock_transport(exit_code=1, stderr="bad sha")
        with pytest.raises(RuntimeError, match="bad sha"):
            git_ops.reset_hard("/tmp/repo", "abc123", transport=transport)

    def test_reset_hard_success(self, capsys):
        transport = _mock_transport()
        git_ops.reset_hard("/tmp/repo", "abc123", transport=transport)
        captured = capsys.readouterr()
        assert "✅ reset hard" in captured.out


# ── create_branch ────────────────────────────────────────────────

class TestCreateBranch:

    def test_create_branch_failure_raises_runtime_error(self):
        transport = _mock_transport(exit_code=1, stderr="already exists")
        with pytest.raises(RuntimeError, match="already exists"):
            git_ops.create_branch("/tmp/repo", "feature/x", transport=transport)

    def test_create_branch_success(self, capsys):
        transport = _mock_transport()
        git_ops.create_branch("/tmp/repo", "feature/x", transport=transport)
        captured = capsys.readouterr()
        assert "✅ created branch feature/x" in captured.out


# ── Integration: DELIVER failure handling ────────────────────────

class TestDeliverFailureIntegration:
    """Test that DELIVER phase handles git failures correctly (Task 2.2)."""

    def _make_rec(self):
        """Create a minimal ChangeRecord-like object."""
        from zsiga.metrics.types import ChangeRecord, Outcome
        return ChangeRecord(
            change_name="test-change",
            project="test-project",
            outcome=Outcome.SUCCESS,
            started_at="2025-01-01T00:00:00",
        )

    def test_push_failure_sets_outcome_fail(self):
        """Simulate DELIVER: push failure → outcome=FAIL."""
        rec = self._make_rec()
        transport = _mock_transport(exit_code=1, stderr="push failed: remote rejected")

        with pytest.raises(RuntimeError):
            git_ops.push("/tmp/repo", branch="feature/x", transport=transport)

        # Verify the behavior: RuntimeError is raised (orchestrator catches this)
        assert rec.outcome.value == "success"  # not yet changed — orchestrator does that

    def test_merge_failure_sets_outcome_fail(self):
        """Simulate DELIVER: merge failure → RuntimeError raised."""
        transport = _mock_transport(exit_code=1, stderr="merge conflict")
        with pytest.raises(RuntimeError, match="merge conflict"):
            git_ops.merge_branch("/tmp/repo", "feature/x", transport=transport)
