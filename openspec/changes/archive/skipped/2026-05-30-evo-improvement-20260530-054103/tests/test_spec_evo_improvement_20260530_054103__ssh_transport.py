"""Tests for spec: ssh-transport.md
Change: evo-improvement-20260530-054103
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from zsiga.transport import SSHTransport


class TestSSHTransportInit:
    """SSHTransport.__init__ scenarios."""

    def test_constructor_sets_all_attributes(self):
        """Scenario: constructor sets all attributes from arguments."""
        t = SSHTransport(host="srv", user="alice", port=2222, key_path="~/.ssh/id")
        assert t.host == "srv"
        assert t.user == "alice"
        assert t.port == 2222
        assert t.key_path == str(Path("~/.ssh/id").expanduser())
        assert t._control_path is None

    def test_constructor_uses_defaults(self):
        """Scenario: constructor uses defaults for user, port, key_path."""
        t = SSHTransport(host="srv")
        assert t.user is None
        assert t.port == 22
        assert t.key_path is None
        assert t._control_path is None


class TestSSHTransportTarget:
    """SSHTransport._target scenarios."""

    def test_target_with_user_returns_user_at_host(self):
        """Scenario: _target with user returns user@host."""
        t = SSHTransport(host="srv", user="alice")
        assert t._target() == "alice@srv"

    def test_target_without_user_returns_host_only(self):
        """Scenario: _target without user returns host only."""
        t = SSHTransport(host="srv")
        assert t._target() == "srv"


class TestSSHTransportBaseArgs:
    """SSHTransport._base_args scenarios."""

    def test_base_args_default_port_no_key(self):
        """Scenario: _base_args with default port and no key_path."""
        t = SSHTransport(host="srv")
        args = t._base_args()
        assert "ssh" in args
        assert "StrictHostKeyChecking=no" in args
        assert "-p" not in args
        assert "-i" not in args

    def test_base_args_custom_port_and_key(self):
        """Scenario: _base_args with custom port and key_path."""
        t = SSHTransport(host="srv", port=2222, key_path="/key")
        args = t._base_args()
        assert "-p" in args
        assert "2222" in args
        assert "-i" in args
        assert "/key" in args


class TestSSHTransportEnsureControl:
    """SSHTransport._ensure_control scenarios."""

    @patch("zsiga.transport.subprocess.run")
    def test_ensure_control_skips_when_already_set(self, mock_run):
        """Scenario: _ensure_control skips when control_path already set."""
        t = SSHTransport(host="srv")
        t._control_path = "/tmp/ctrl"
        t._ensure_control()
        mock_run.assert_not_called()
        assert t._control_path == "/tmp/ctrl"


class TestSSHTransportRunShell:
    """SSHTransport.run_shell scenarios."""

    @patch("zsiga.transport.subprocess.run")
    def _make_transport(self, mock_run, side_effect=None, return_value=None):
        """Helper: create SSHTransport with _ensure_control as no-op."""
        t = SSHTransport(host="srv", user="alice")
        t._control_path = "/tmp/ctrl"  # skip _ensure_control
        if side_effect:
            mock_run.side_effect = side_effect
        else:
            proc = MagicMock()
            proc.returncode = 0
            proc.stdout = ""
            proc.stderr = ""
            mock_run.return_value = proc
        return t

    def test_run_shell_with_cwd_prepends_cd(self):
        """Scenario: run_shell with cwd prepends cd command."""
        with patch("zsiga.transport.subprocess.run") as mock_run:
            proc = MagicMock()
            proc.returncode = 0
            proc.stdout = ""
            proc.stderr = ""
            mock_run.return_value = proc

            t = SSHTransport(host="srv", user="alice")
            t._control_path = "/tmp/ctrl"
            t.run_shell("ls", cwd="/home/alice")

            call_args = mock_run.call_args[0][0]
            # Last args should contain the remote command
            assert "cd '/home/alice' && ls" in call_args

    def test_run_shell_without_cwd_does_not_prepend_cd(self):
        """Scenario: run_shell without cwd does not prepend cd."""
        with patch("zsiga.transport.subprocess.run") as mock_run:
            proc = MagicMock()
            proc.returncode = 0
            proc.stdout = ""
            proc.stderr = ""
            mock_run.return_value = proc

            t = SSHTransport(host="srv", user="alice")
            t._control_path = "/tmp/ctrl"
            t.run_shell("ls")

            call_args = mock_run.call_args[0][0]
            assert call_args[-1] == "ls"

    def test_run_shell_handles_timeout_expired(self):
        """Scenario: run_shell returns timeout result on TimeoutExpired."""
        with patch("zsiga.transport.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("ssh", 120)

            t = SSHTransport(host="srv", user="alice")
            t._control_path = "/tmp/ctrl"
            result = t.run_shell("sleep 999")

            assert result["exit_code"] == -1
            assert result["stdout"] == ""
            assert "Timeout after 120s" == result["stderr"]

    def test_run_shell_handles_generic_exception(self):
        """Scenario: run_shell returns error result on generic exception."""
        with patch("zsiga.transport.subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("connection lost")

            t = SSHTransport(host="srv", user="alice")
            t._control_path = "/tmp/ctrl"
            result = t.run_shell("ls")

            assert result["exit_code"] == -1
            assert result["stdout"] == ""
            assert "connection lost" in result["stderr"]


class TestSSHTransportClose:
    """SSHTransport.close scenarios."""

    @patch("zsiga.transport.subprocess.run")
    def test_close_sends_exit_and_resets_control_path(self, mock_run):
        """Scenario: close sends exit signal and resets control_path."""
        t = SSHTransport(host="srv", user="alice")
        t._control_path = "/tmp/ctrl"
        t.close()

        call_args = mock_run.call_args[0][0]
        assert "-O" in call_args
        assert "exit" in call_args
        assert t._control_path is None

    @patch("zsiga.transport.subprocess.run")
    def test_close_noop_when_control_path_none(self, mock_run):
        """Scenario: close is no-op when control_path is None."""
        t = SSHTransport(host="srv")
        t._control_path = None
        t.close()

        mock_run.assert_not_called()
